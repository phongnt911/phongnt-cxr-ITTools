"""Module quản lý, kết nối RustDesk Direct IP nội bộ và Wake-on-LAN."""
import binascii
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess

try:
    from security_utils import validate_host
except ImportError:
    def validate_host(value):
        h = str(value).strip()
        parts = h.split(".")
        if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            return h
        raise ValueError("Địa chỉ IP không hợp lệ.")

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
MAC_REGEX = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")


def validate_mac(mac: str) -> bool:
    """Kiểm tra tính hợp lệ của địa chỉ MAC (dạng AA:BB:CC:DD:EE:FF hoặc AA-BB-CC-DD-EE-FF)."""
    if not mac or not isinstance(mac, str):
        return False
    return bool(MAC_REGEX.fullmatch(mac.strip()))


def create_magic_packet(mac: str) -> bytes:
    """Tạo gói tin Magic Packet chuẩn Wake-on-LAN (102 bytes)."""
    clean_mac = mac.strip().replace(":", "").replace("-", "")
    mac_bytes = binascii.unhexlify(clean_mac)
    return b"\xff" * 6 + mac_bytes * 16


def send_wake_on_lan(mac_address: str, broadcast_ip: str = "255.255.255.255", port: int = 9) -> dict:
    """Gửi gói Magic Packet bật máy tính từ xa qua mạng LAN."""
    mac = str(mac_address).strip()
    if not validate_mac(mac):
        return {"success": False, "message": f"Địa chỉ MAC không hợp lệ: {mac_address}. Định dạng chuẩn: AA:BB:CC:DD:EE:FF"}

    target_broadcast = str(broadcast_ip).strip() or "255.255.255.255"
    try:
        packet = create_magic_packet(mac)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(2.0)
            sock.sendto(packet, (target_broadcast, port))
        return {
            "success": True,
            "message": f"Đã phát gói Magic Packet đánh thức thiết bị MAC [{mac}] qua {target_broadcast}:{port}."
        }
    except Exception as exc:
        return {"success": False, "message": f"Lỗi phát gói tin Wake-on-LAN: {exc}"}


def find_rustdesk_executable() -> str | None:
    """Tìm đường dẫn file thực thi rustdesk.exe trên hệ điều hành Windows."""
    candidates = []
    # 1. Các thư mục chuẩn
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")

    candidates.append(os.path.join(program_files, "RustDesk", "rustdesk.exe"))
    candidates.append(os.path.join(program_files_x86, "RustDesk", "rustdesk.exe"))
    if local_appdata:
        candidates.append(os.path.join(local_appdata, "Programs", "RustDesk", "rustdesk.exe"))
    if appdata:
        candidates.append(os.path.join(appdata, "RustDesk", "rustdesk.exe"))

    # 2. PATH
    which_path = shutil.which("rustdesk") or shutil.which("rustdesk.exe")
    if which_path:
        candidates.insert(0, which_path)

    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


def get_rustdesk_service_status() -> str:
    """Truy vấn trạng thái dịch vụ Windows Service 'rustdesk'."""
    try:
        proc = subprocess.run(
            ["sc.exe", "query", "rustdesk"],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
            timeout=3.0
        )
        out = proc.stdout.upper()
        if "RUNNING" in out:
            return "RUNNING"
        elif "STOPPED" in out:
            return "STOPPED"
        elif "PAUSED" in out:
            return "PAUSED"
        elif "1060" in out or "DOES NOT EXIST" in out:
            return "NOT_INSTALLED"
        return "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def check_direct_ip_listening(port: int = 21118) -> bool:
    """Kiểm tra xem RustDesk có đang mở cổng lắng nghe Direct IP cục bộ (21118 / 21116) hay không."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.3)
    try:
        sock.connect(("127.0.0.1", port))
        return True
    except (socket.timeout, OSError):
        return False
    finally:
        sock.close()


def get_local_ips() -> list[str]:
    """Lấy danh sách các địa chỉ IPv4 LAN của máy hiện tại để hiển thị cho đối tác kết nối."""
    ips = []
    try:
        host_name = socket.gethostname()
        for info in socket.getaddrinfo(host_name, None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return ips


def get_rustdesk_info() -> dict:
    """Tổng hợp toàn bộ thông tin về RustDesk trên máy cục bộ."""
    exe_path = find_rustdesk_executable()
    service_status = get_rustdesk_service_status()
    direct_listening = check_direct_ip_listening(21118) or check_direct_ip_listening(21116)
    local_ips = get_local_ips()

    return {
        "installed": exe_path is not None,
        "exe_path": exe_path,
        "service_status": service_status,
        "direct_ip_listening": direct_listening,
        "direct_port": 21118,
        "local_ips": local_ips,
        "primary_ip": local_ips[0] if local_ips else "127.0.0.1"
    }


def connect_direct_ip(target_ip: str) -> dict:
    """Khởi chạy RustDesk kết nối thẳng tới IP tĩnh nội bộ của máy cần hỗ trợ."""
    try:
        safe_ip = validate_host(target_ip)
    except ValueError as exc:
        return {"success": False, "message": f"Địa chỉ IP không hợp lệ: {exc}"}

    exe = find_rustdesk_executable()
    if not exe:
        return {
            "success": False,
            "message": "Không tìm thấy file thực thi rustdesk.exe trên máy này. Vui lòng cài đặt RustDesk hoặc đặt file rustdesk.exe vào Program Files."
        }

    try:
        # Gọi rustdesk.exe <safe_ip>
        subprocess.Popen([exe, safe_ip], creationflags=CREATE_NO_WINDOW)
        return {
            "success": True,
            "message": f"Đã khởi động RustDesk kết nối trực tiếp tới IP: {safe_ip}"
        }
    except Exception as exc:
        return {"success": False, "message": f"Lỗi khởi động RustDesk: {exc}"}


def restart_rustdesk_service() -> dict:
    """Khởi động lại Windows Service của RustDesk khi bị đơ/treo kết nối."""
    try:
        # 1. Dừng service
        subprocess.run(
            ["net.exe", "stop", "rustdesk"],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
            timeout=5.0
        )
        # 2. Khởi động lại
        proc = subprocess.run(
            ["net.exe", "start", "rustdesk"],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
            timeout=5.0
        )
        if proc.returncode == 0 or "started successfully" in proc.stdout.lower() or "đã được khởi chạy" in proc.stdout.lower():
            return {"success": True, "message": "Đã khởi động lại dịch vụ RustDesk thành công."}
        else:
            return {"success": False, "message": f"Không thể bật lại RustDesk Service: {proc.stderr or proc.stdout}"}
    except Exception as exc:
        return {"success": False, "message": f"Lỗi thao tác dịch vụ: {exc}"}
