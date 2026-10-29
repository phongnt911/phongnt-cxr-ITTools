"""Module quản lý, giám sát và chẩn đoán Camera IP trong mạng LAN nội bộ."""
import concurrent.futures
from datetime import datetime
import json
import os
from pathlib import Path
import re
import socket
import time
import webbrowser

try:
    from security_utils import validate_ip
except ImportError:
    def validate_ip(ip: str) -> bool:
        if not ip or not isinstance(ip, str):
            return False
        parts = ip.strip().split(".")
        if len(parts) != 4:
            return False
        for p in parts:
            if not p.isdigit() or not 0 <= int(p) <= 255:
                return False
        return True

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = BASE_DIR / "config" / "cameras.json"

DEFAULT_CAMERAS = [
    {
        "id": "cam-01",
        "name": "Khu Vực Soi Chiếu An Ninh A",
        "ip": "10.90.39.201",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Tầng 1 - Ga Đi Quốc Nội",
        "notes": "Hikvision 4MP DarkFighter"
    },
    {
        "id": "cam-02",
        "name": "Băng Chuyền Trả Hành Lý 1",
        "ip": "10.90.39.202",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Tầng Trệt - Ga Đến",
        "notes": "Dahua WizSense IR"
    },
    {
        "id": "cam-03",
        "name": "Cửa Ra Tàu Bay (Boarding Gate 1)",
        "ip": "10.90.39.203",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Phòng Chờ Cách Ly",
        "notes": "Uniview Dome 2MP"
    },
    {
        "id": "cam-04",
        "name": "Quầy Thủ Tục Check-in 01-05",
        "ip": "10.90.39.204",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Sảnh Công Cộng Ga Đi",
        "notes": "KBVision Dome HD"
    }
]


def load_cameras(config_path=None) -> list:
    """Nạp danh sách camera từ tệp JSON cấu hình."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(json.dumps(DEFAULT_CAMERAS, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
        return list(DEFAULT_CAMERAS)

    try:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return list(DEFAULT_CAMERAS)
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return list(DEFAULT_CAMERAS)
    except Exception:
        return list(DEFAULT_CAMERAS)


def save_cameras(cameras: list, config_path=None) -> dict:
    """Lưu danh sách camera với thẩm tra tính hợp lệ của IP và Port."""
    if not isinstance(cameras, list):
        return {"success": False, "message": "Dữ liệu danh sách camera không đúng định dạng"}

    sanitized = []
    for idx, cam in enumerate(cameras):
        if not isinstance(cam, dict):
            continue
        ip = str(cam.get("ip", "")).strip()
        if not validate_ip(ip):
            return {"success": False, "message": f"Địa chỉ IP không hợp lệ tại mục #{idx + 1}: {ip}"}

        try:
            port_web = int(cam.get("port_web", 80))
            if not 1 <= port_web <= 65535:
                port_web = 80
        except (ValueError, TypeError):
            port_web = 80

        try:
            port_rtsp = int(cam.get("port_rtsp", 554))
            if not 1 <= port_rtsp <= 65535:
                port_rtsp = 554
        except (ValueError, TypeError):
            port_rtsp = 554

        sanitized.append({
            "id": str(cam.get("id") or f"cam-{idx + 1}"),
            "name": str(cam.get("name") or f"Camera {ip}").strip(),
            "ip": ip,
            "port_web": port_web,
            "port_rtsp": port_rtsp,
            "location": str(cam.get("location", "")).strip(),
            "notes": str(cam.get("notes", "")).strip()
        })

    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sanitized, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"success": True, "message": f"Đã lưu thành công {len(sanitized)} camera", "data": sanitized}
    except Exception as exc:
        return {"success": False, "message": f"Lỗi ghi tệp cấu hình: {exc}"}


def probe_port(ip: str, port: int, timeout: float = 0.8) -> tuple[bool, float]:
    """Kiểm tra mở cổng TCP và đo độ trễ (latency ms)."""
    if not validate_ip(ip) or not (1 <= port <= 65535):
        return False, 0.0

    start_time = time.perf_counter()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((ip, port))
        latency = (time.perf_counter() - start_time) * 1000.0
        return True, round(latency, 1)
    except (socket.timeout, OSError):
        return False, 0.0
    finally:
        sock.close()


def check_camera_status(camera: dict, timeout: float = 0.8) -> dict:
    """Kiểm tra toàn diện trạng thái camera (RTSP, Web, ICMP/TCP ping)."""
    ip = str(camera.get("ip", "")).strip()
    port_rtsp = int(camera.get("port_rtsp", 554))
    port_web = int(camera.get("port_web", 80))

    rtsp_open, rtsp_lat = probe_port(ip, port_rtsp, timeout=timeout)
    web_open, web_lat = probe_port(ip, port_web, timeout=timeout)

    is_online = rtsp_open or web_open
    latency = rtsp_lat if rtsp_open else (web_lat if web_open else 0.0)

    # Nếu cả RTSP và Web đóng, thử cổng dịch vụ camera phổ biến khác (8000, 37777, 8899)
    if not is_online:
        for aux_port in (8000, 37777, 8899):
            aux_open, aux_lat = probe_port(ip, aux_port, timeout=min(timeout, 0.5))
            if aux_open:
                is_online = True
                latency = aux_lat
                break

    return {
        "id": camera.get("id"),
        "name": camera.get("name"),
        "ip": ip,
        "port_web": port_web,
        "port_rtsp": port_rtsp,
        "location": camera.get("location", ""),
        "notes": camera.get("notes", ""),
        "is_online": is_online,
        "rtsp_open": rtsp_open,
        "web_open": web_open,
        "latency_ms": latency,
        "last_checked": datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    }


def ping_all_cameras(cameras: list = None, max_workers: int = 25, timeout: float = 0.8) -> list:
    """Kiểm tra song song hàng loạt camera với ThreadPool."""
    cams = cameras if cameras is not None else load_cameras()
    if not cams:
        return []

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(cams) or 1)) as executor:
        future_map = {executor.submit(check_camera_status, cam, timeout): cam for cam in cams}
        for future in concurrent.futures.as_completed(future_map):
            try:
                results.append(future.result())
            except Exception as exc:
                orig = future_map[future]
                results.append({
                    "id": orig.get("id"),
                    "name": orig.get("name"),
                    "ip": orig.get("ip"),
                    "is_online": False,
                    "rtsp_open": False,
                    "web_open": False,
                    "latency_ms": 0.0,
                    "error": str(exc),
                    "last_checked": datetime.now().strftime("%H:%M:%S")
                })

    # Giữ nguyên thứ tự ID ban đầu
    id_order = {cam.get("id"): idx for idx, cam in enumerate(cams)}
    results.sort(key=lambda r: id_order.get(r.get("id"), 999))
    return results


def scan_camera_range(base_subnet: str, start: int = 1, end: int = 50, timeout: float = 0.5) -> dict:
    """Dò tìm các thiết bị Camera trong dải IP (quét port 554, 80, 8000, 37777, 8899)."""
    # Chuẩn hóa base_subnet, ví dụ '10.90.39' hoặc '10.90.39.0'
    base = base_subnet.strip().rstrip(".")
    if base.count(".") == 3:
        base = ".".join(base.split(".")[:3])
    parts = base.split(".")
    if len(parts) != 3 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        return {"success": False, "message": "Dải mạng không hợp lệ (Ví dụ hợp lệ: 10.90.39 hoặc 192.168.1)"}

    start = max(1, min(start, 254))
    end = max(start, min(end, 254))

    candidate_ports = [554, 80, 8000, 37777, 8899]
    found_devices = []

    def check_host(host_ip: str):
        detected_ports = []
        for port in candidate_ports:
            is_open, _ = probe_port(host_ip, port, timeout=timeout)
            if is_open:
                detected_ports.append(port)
        if detected_ports:
            vendor_guess = "Unknown Camera"
            if 8000 in detected_ports:
                vendor_guess = "Hikvision / Ezviz"
            elif 37777 in detected_ports:
                vendor_guess = "Dahua / KBVision / IMOU"
            elif 554 in detected_ports and 8899 in detected_ports:
                vendor_guess = "ONVIF Generic / Xiongmai"
            elif 554 in detected_ports:
                vendor_guess = "RTSP IP Camera"

            return {
                "ip": host_ip,
                "ports": detected_ports,
                "vendor_guess": vendor_guess,
                "has_rtsp": 554 in detected_ports,
                "has_web": 80 in detected_ports
            }
        return None

    ips = [f"{base}.{i}" for i in range(start, end + 1)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(check_host, ip) for ip in ips]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                found_devices.append(res)

    found_devices.sort(key=lambda d: [int(p) for p in d["ip"].split(".")])
    return {
        "success": True,
        "scanned_range": f"{base}.{start} - {base}.{end}",
        "count": len(found_devices),
        "devices": found_devices
    }


def open_camera_web(ip: str, port: int = 80) -> dict:
    """Mở giao diện Web quản trị của Camera trên trình duyệt."""
    if not validate_ip(ip):
        return {"success": False, "message": "Địa chỉ IP camera không hợp lệ"}
    try:
        url = f"http://{ip}:{port}" if port != 80 else f"http://{ip}"
        webbrowser.open(url)
        return {"success": True, "message": f"Đang mở trang quản trị: {url}"}
    except Exception as exc:
        return {"success": False, "message": f"Không thể mở trình duyệt: {exc}"}
