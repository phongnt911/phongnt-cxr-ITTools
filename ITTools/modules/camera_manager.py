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
        "name": "Kho Hang - Ban Can",
        "ip": "172.16.112.149",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Phía trên bàn cân kho hàng",
        "device_type": "DS-2CD2955FWD-I",
        "serial": "DS-2CD2955FWD-I20200229AAWR243357071",
        "mac": "ac-cb-51-34-e2-99",
        "notes": "Model: DS-2CD2955FWD-I | SN: DS-2CD2955FWD-I20200229AAWR243357071 | MAC: ac-cb-51-34-e2-99"
    },
    {
        "id": "cam-02",
        "name": "DH SAGS-CXR",
        "ip": "172.16.112.150",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Phòng Điều hành",
        "device_type": "DS-2CD2420F-IW",
        "serial": "DS-2CD2420F-IW20161026AAWR666404905",
        "mac": "a4-14-37-c2-d3-90",
        "notes": "Model: DS-2CD2420F-IW | SN: DS-2CD2420F-IW20161026AAWR666404905 | MAC: a4-14-37-c2-d3-90"
    },
    {
        "id": "cam-03",
        "name": "LNF QN STORE",
        "ip": "172.16.112.151",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Kho LNF Quốc nội",
        "device_type": "DS-2CD1023G2-LIUF",
        "serial": "DS-2CD1023G2-LIUF20240425AAWRFD4486454",
        "mac": "04-03-12-cd-2e-f4",
        "notes": "Model: DS-2CD1023G2-LIUF | SN: DS-2CD1023G2-LIUF20240425AAWRFD4486454 | MAC: 04-03-12-cd-2e-f4"
    },
    {
        "id": "cam-04",
        "name": "P.4",
        "ip": "172.16.112.152",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Phòng 4 PVHK",
        "device_type": "DS-2CD2420F-IW",
        "serial": "DS-2CD2420F-IW20170610AAWR774849377",
        "mac": "18-68-cb-cb-21-92",
        "notes": "Model: DS-2CD2420F-IW | SN: DS-2CD2420F-IW20170610AAWR774849377 | MAC: 18-68-cb-cb-21-92"
    },
    {
        "id": "cam-05",
        "name": "Xuong Sua Chua",
        "ip": "172.16.112.153",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Khu vực XSC",
        "device_type": "DS-2CD2055FWD-I",
        "serial": "DS-2CD2055FWD-I20170905AAWR829301652",
        "mac": "4c-bd-8f-d2-b9-83",
        "notes": "Model: DS-2CD2055FWD-I | SN: DS-2CD2055FWD-I20170905AAWR829301652 | MAC: 4c-bd-8f-d2-b9-83"
    },
    {
        "id": "cam-06",
        "name": "TICKET QT",
        "ip": "172.16.112.154",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Quầy vé Quốc tế",
        "device_type": "DS-2CD1321-I",
        "serial": "DS-2CD1321-I20171229AAWR160753978",
        "mac": "64-db-8b-36-8f-95",
        "notes": "Model: DS-2CD1321-I | SN: DS-2CD1321-I20171229AAWR160753978 | MAC: 64-db-8b-36-8f-95"
    },
    {
        "id": "cam-07",
        "name": "IPCamera 12",
        "ip": "172.16.112.155",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Phòng PVTT",
        "device_type": "IPC2122LR3-PF40M-D",
        "serial": "210235C32TF18A000561",
        "mac": "48-ea-63-90-0a-2c",
        "notes": "Model: IPC2122LR3-PF40M-D | SN: 210235C32TF18A000561 | MAC: 48-ea-63-90-0a-2c"
    },
    {
        "id": "cam-08",
        "name": "IPCamera 13",
        "ip": "172.16.112.156",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Phòng PVSĐ",
        "device_type": "IPC2122LR3-PF40M-D",
        "serial": "210235C32TF18A001175",
        "mac": "48-ea-63-90-0c-92",
        "notes": "Model: IPC2122LR3-PF40M-D | SN: 210235C32TF18A001175 | MAC: 48-ea-63-90-0c-92"
    },
    {
        "id": "cam-09",
        "name": "IPCamera 16",
        "ip": "172.16.112.157",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Phía trước PVTT",
        "device_type": "DS-2CD2021G1-I",
        "serial": "DS-2CD2021G1-I20190710AAWRD35150556",
        "mac": "bc-ba-c2-1b-a7-19",
        "notes": "Model: DS-2CD2021G1-I | SN: DS-2CD2021G1-I20190710AAWRD35150556 | MAC: bc-ba-c2-1b-a7-19"
    },
    {
        "id": "cam-10",
        "name": "PVSD_Front",
        "ip": "172.16.112.158",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Phía trước Đội PVSĐ",
        "device_type": "DS-2CD2021G1-I",
        "serial": "DS-2CD2021G1-I20190710AAWRD35150660",
        "mac": "bc-ba-c2-1b-a7-81",
        "notes": "Model: DS-2CD2021G1-I | SN: DS-2CD2021G1-I20190710AAWRD35150660 | MAC: bc-ba-c2-1b-a7-81"
    },
    {
        "id": "cam-11",
        "name": "PVSD-BAY- RIGHT",
        "ip": "172.16.112.159",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Phía trước bên phải hội trường sân đỗ",
        "device_type": "DS-2CD2643G1-IZ",
        "serial": "DS-2CD2643G1-IZ20190807AAWRD47358055",
        "mac": "bc-ba-c2-75-06-ee",
        "notes": "Model: DS-2CD2643G1-IZ | SN: DS-2CD2643G1-IZ20190807AAWRD47358055 | MAC: bc-ba-c2-75-06-ee"
    },
    {
        "id": "cam-12",
        "name": "PVSD-BAY -LEFT",
        "ip": "172.16.112.160",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Phía trước bên trái hội trường sân đỗ",
        "device_type": "DS-2CD2643G1-IZ",
        "serial": "DS-2CD2643G1-IZ20190807AAWRD47358053",
        "mac": "bc-ba-c2-75-06-ec",
        "notes": "Model: DS-2CD2643G1-IZ | SN: DS-2CD2643G1-IZ20190807AAWRD47358053 | MAC: bc-ba-c2-75-06-ec"
    },
    {
        "id": "cam-13",
        "name": "LNF QN",
        "ip": "172.16.112.163",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Quầy LNF Quốc nội",
        "device_type": "DS-2CD2021G1-I",
        "serial": "DS-2CD2021G1-I20200114AAWRE09888126",
        "mac": "ac-cb-51-0d-08-22",
        "notes": "Model: DS-2CD2021G1-I | SN: DS-2CD2021G1-I20200114AAWRE09888126 | MAC: ac-cb-51-0d-08-22"
    },
    {
        "id": "cam-14",
        "name": "Meeting Room 3",
        "ip": "172.16.112.164",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Phòng họp số 3 sân bay",
        "device_type": "DS-2CD2063G2-IU",
        "serial": "DS-2CD2063G2-IU20220510AAWRJ92403122",
        "mac": "80-7c-62-bd-6e-2c",
        "notes": "Model: DS-2CD2063G2-IU | SN: DS-2CD2063G2-IU20220510AAWRJ92403122 | MAC: 80-7c-62-bd-6e-2c"
    },
    {
        "id": "cam-15",
        "name": "PVTT",
        "ip": "172.16.112.54",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Khu vực bồn dầu",
        "device_type": "CMIP8222",
        "serial": "CMIP822220160121AAWR571405503",
        "mac": "28-57-be-7e-5a-59",
        "notes": "Model: CMIP8222 | SN: CMIP822220160121AAWR571405503 | MAC: 28-57-be-7e-5a-59"
    },
    {
        "id": "cam-16",
        "name": "DH SAGS-CXR BACK",
        "ip": "192.168.102.10",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Phòng Điều hành",
        "device_type": "DS-2CD2021G1-I",
        "serial": "DS-2CD2021G1-I20200114AAWRE09887734",
        "mac": "ac-cb-51-0d-06-9a",
        "notes": "Model: DS-2CD2021G1-I | SN: DS-2CD2021G1-I20200114AAWRE09887734 | MAC: ac-cb-51-0d-06-9a"
    },
    {
        "id": "cam-17",
        "name": "HLQT BC CD",
        "ip": "192.168.102.11",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "PVHL Quốc tế Đảo C-D",
        "device_type": "DS-2CD2021G1-I",
        "serial": "DS-2CD1021G0-I20240731AAWRFK2192911",
        "mac": "5c-34-5b-71-4f-5b",
        "notes": "Model: DS-2CD2021G1-I | SN: DS-2CD1021G0-I20240731AAWRFK2192911 | MAC: 5c-34-5b-71-4f-5b"
    },
    {
        "id": "cam-18",
        "name": "PVHL BC GH",
        "ip": "192.168.102.12",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "PVHL Quốc tế Đảo G-H",
        "device_type": "DS-2CD2021G1-I",
        "serial": "DS-2CD1021G0-I20240801AAWRFK4285993",
        "mac": "5c-34-5b-7d-b1-f6",
        "notes": "Model: DS-2CD2021G1-I | SN: DS-2CD1021G0-I20240801AAWRFK4285993 | MAC: 5c-34-5b-7d-b1-f6"
    },
    {
        "id": "cam-19",
        "name": "HLQT BC AB",
        "ip": "192.168.102.13",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "PVHL Quốc tế Đảo A-B",
        "device_type": "DS-2CD2021G1-I",
        "serial": "DS-2CD1021G0-I20241216AAWRFU3999316",
        "mac": "54-8c-81-89-05-81",
        "notes": "Model: DS-2CD2021G1-I | SN: DS-2CD1021G0-I20241216AAWRFU3999316 | MAC: 54-8c-81-89-05-81"
    },
    {
        "id": "cam-20",
        "name": "LNF QT KHO",
        "ip": "192.168.102.3",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Kho LNF Quốc tế",
        "device_type": "DS-2CD2063G2-IU",
        "serial": "DS-2CD2063G2-IU20211013AAWRG85434825",
        "mac": "ac-b9-2f-b8-d5-bb",
        "notes": "Model: DS-2CD2063G2-IU | SN: DS-2CD2063G2-IU20211013AAWRG85434825 | MAC: ac-b9-2f-b8-d5-bb"
    },
    {
        "id": "cam-21",
        "name": "LNF QT Front",
        "ip": "192.168.102.4",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Quầy LNF Quốc tế",
        "device_type": "DS-2CD2063G2-IU",
        "serial": "DS-2CD2063G2-IU20211013AAWRG85434816",
        "mac": "ac-b9-2f-b8-d5-b2",
        "notes": "Model: DS-2CD2063G2-IU | SN: DS-2CD2063G2-IU20211013AAWRG85434816 | MAC: ac-b9-2f-b8-d5-b2"
    },
    {
        "id": "cam-22",
        "name": "PVHK QT",
        "ip": "192.168.102.5",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Phòng PVHK Quốc tế",
        "device_type": "DS-2CD1321-I",
        "serial": "DS-2CD1321-I20171229AAWR160754246",
        "mac": "64-db-8b-36-90-a1",
        "notes": "Model: DS-2CD1321-I | SN: DS-2CD1321-I20171229AAWR160754246 | MAC: 64-db-8b-36-90-a1"
    },
    {
        "id": "cam-23",
        "name": "PVHL BC EF",
        "ip": "192.168.102.6",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "PVHL Quốc tế Đảo E-F",
        "device_type": "DS-2CD1221-I3",
        "serial": "DS-2CD1221-I320180427AAWR212421060",
        "mac": "94-e1-ac-73-46-63",
        "notes": "Model: DS-2CD1221-I3 | SN: DS-2CD1221-I320180427AAWR212421060 | MAC: 94-e1-ac-73-46-63"
    },
    {
        "id": "cam-24",
        "name": "IT SAGS CXR",
        "ip": "192.168.102.7",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Phòng IT",
        "device_type": "DS-2CD2021G1-I",
        "serial": "DS-2CD2021G1-I20180711AAWRC31439145",
        "mac": "94-e1-ac-e3-ef-6b",
        "notes": "Model: DS-2CD2021G1-I | SN: DS-2CD2021G1-I20180711AAWRC31439145 | MAC: 94-e1-ac-e3-ef-6b"
    },
    {
        "id": "cam-25",
        "name": "IPCamera 14",
        "ip": "192.168.102.8",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Quầy thủ tục đảo C T1",
        "device_type": "IPC324LR3-VSPF40-D",
        "serial": "210235C341F188000008",
        "mac": "48-ea-63-8d-0a-08",
        "notes": "Model: IPC324LR3-VSPF40-D | SN: 210235C341F188000008 | MAC: 48-ea-63-8d-0a-08"
    },
    {
        "id": "cam-26",
        "name": "IPCamera 15",
        "ip": "192.168.102.9",
        "port_web": 80,
        "port_rtsp": 554,
        "location": "Quầy thủ tục đảo D T1",
        "device_type": "IPC324LR3-VSPF40-D",
        "serial": "210235C3413188000116",
        "mac": "48-ea-63-91-c2-62",
        "notes": "Model: IPC324LR3-VSPF40-D | SN: 210235C3413188000116 | MAC: 48-ea-63-91-c2-62"
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

        item = {
            "id": str(cam.get("id") or f"cam-{idx + 1}"),
            "name": str(cam.get("name") or f"Camera {ip}").strip(),
            "ip": ip,
            "port_web": port_web,
            "port_rtsp": port_rtsp,
            "location": str(cam.get("location", "")).strip(),
            "notes": str(cam.get("notes", "")).strip()
        }
        if "device_type" in cam:
            item["device_type"] = str(cam.get("device_type", "")).strip()
        if "serial" in cam:
            item["serial"] = str(cam.get("serial", "")).strip()
        if "mac" in cam:
            item["mac"] = str(cam.get("mac", "")).strip()
        sanitized.append(item)

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

    status_res = {
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
    if "device_type" in camera:
        status_res["device_type"] = camera.get("device_type")
    if "serial" in camera:
        status_res["serial"] = camera.get("serial")
    if "mac" in camera:
        status_res["mac"] = camera.get("mac")
    return status_res


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
                err_item = {
                    "id": orig.get("id"),
                    "name": orig.get("name"),
                    "ip": orig.get("ip"),
                    "location": orig.get("location", ""),
                    "is_online": False,
                    "rtsp_open": False,
                    "web_open": False,
                    "latency_ms": 0.0,
                    "error": str(exc),
                    "last_checked": datetime.now().strftime("%H:%M:%S")
                }
                if "device_type" in orig:
                    err_item["device_type"] = orig.get("device_type")
                if "mac" in orig:
                    err_item["mac"] = orig.get("mac")
                results.append(err_item)

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
