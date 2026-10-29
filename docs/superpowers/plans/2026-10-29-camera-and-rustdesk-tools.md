# Camera IP Manager & RustDesk Direct LAN Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng phân hệ Quản lý & Chẩn đoán Camera IP độc lập và Tích hợp điều khiển từ xa RustDesk qua IP tĩnh nội bộ cùng tính năng Wake-on-LAN cho IT Helpdesk quản lý 100 máy tính.

**Architecture:** Kiến trúc module hóa theo tiêu chuẩn dự án IT Tool SAGS-CXR 2026: Backend Python (`camera_manager.py` và `rustdesk_manager.py`) tận dụng chuẩn thư viện chuẩn (`socket`, `concurrent.futures`, `json`, `subprocess` với cờ `CREATE_NO_WINDOW` khử chớp), kết nối qua `web_api.py` tới giao diện Edge WebView2 HTML/JS với bảng điều khiển trực quan, kiểm tra trạng thái song song siêu tốc (<1s).

**Tech Stack:** Python 3.10+ (Standard Library `socket`, `concurrent.futures`, `json`, `re`), Windows native APIs (`sc.exe`, `net.exe`, `rundll32`/`ShellExecute`), HTML5/Tailwind/ES6 WebView2 frontend.

**Spec:** Yêu cầu từ IT Helpdesk:
1. Camera IP tạo thành 1 nhánh phân hệ riêng biệt (xem danh sách, ping watchdog, mở web quản trị, dò tìm camera qua port 554 RTSP/80 HTTP/8000 SDK).
2. Tạm dừng nâng cấp máy in theo yêu cầu người dùng.
3. RustDesk kết nối trực tiếp qua IP tĩnh nội bộ LAN (Direct IP Access), kiểm tra trạng thái dịch vụ, khởi động lại khi treo, và đánh thức máy từ xa qua Wake-on-LAN (WoL).

## Global Constraints

- Không cài thêm bất kỳ thư viện third-party mới nào vào `.venv` / PyInstaller (YAGNI / Ponytail).
- Mọi câu lệnh subprocess chạy ngầm tuyệt đối phải sử dụng cờ `CREATE_NO_WINDOW` và cơ chế escape tham số qua `security_utils.py` để không nhấp nháy cửa sổ đen cmd.
- Thẩm tra địa chỉ IP và MAC nghiêm ngặt (chống command injection và path traversal).
- Lưu cấu hình danh sách camera tại `ITTools/config/cameras.json` an toàn, có sẵn danh sách mẫu và tự tạo nếu tệp chưa tồn tại.
- Mọi hàm API mới phải có unit tests và được đăng ký đầy đủ trong `web_api.py`.

## Review Focus

1. **IP & Port Injection**: Dữ liệu IP nhập từ người dùng phải được thẩm tra bằng regex IPv4 hợp lệ trước khi thực hiện socket hoặc gọi lệnh CLI.
2. **Timeout Socket Hangs**: Các kết nối kiểm tra socket (RTSP 554, Web 80, RustDesk 21118) phải có timeout tối đa 1.0s, chạy trên ThreadPool để không bao giờ làm đơ UI giao diện.
3. **RustDesk Executable Missing**: Khi máy người dùng chưa cài đặt RustDesk, hệ thống phải báo lỗi rõ ràng kèm link tải/hướng dẫn thay vì crash.
4. **WoL Broadcast Failure**: Khi gửi gói Magic Packet tới dải subnet cụ thể hoặc broadcast 255.255.255.255, bắt ngoại lệ socket socket.error / PermissionError một cách êm ái.
5. **Config File Corruption**: Khi tệp `cameras.json` bị lỗi cú pháp JSON hoặc rỗng, hệ thống tự động khôi phục cấu hình mặc định an toàn.

---

### Task 1: Module Backend `camera_manager.py` & Unit Tests

**Files:**
- Create: `ITTools/modules/camera_manager.py`
- Create: `ITTools/config/cameras.json`
- Test: `tests/test_camera_manager.py`

- [ ] **Step 1: Viết test thất bại (Red)**:
  Tạo `tests/test_camera_manager.py` kiểm tra:
  - `load_cameras()` nạp danh sách camera và xử lý fallback khi tệp không tồn tại/lỗi cú pháp.
  - `save_cameras()` lưu danh sách camera hợp lệ và từ chối các bản ghi sai cấu trúc IP.
  - `check_camera_status()` trả về `is_online`, `latency_ms`, `ports_open` (554 RTSP, 80 HTTP, 8000).
  - `ping_all_cameras()` chạy đa luồng cho kết quả tổng hợp.
  - `scan_camera_range()` từ chối dải IP không hợp lệ và quét các cổng camera đặc thù.

- [ ] **Step 2: Chạy test để xác nhận Red**:
  `python -m unittest tests/test_camera_manager.py`

- [ ] **Step 3: Triển khai mã nguồn tối thiểu (Green)**:
  Tạo `ITTools/modules/camera_manager.py`:
  - `CONFIG_PATH = Path(BASE_DIR) / "config" / "cameras.json"`
  - `load_cameras()`, `save_cameras(cameras)`
  - `probe_socket(ip, port, timeout=1.0)`
  - `check_camera_status(ip, ports=[554, 80, 8000], timeout=1.0)`
  - `ping_all_cameras(cameras=None, max_workers=20)`
  - `scan_camera_range(ip_prefix, start=1, end=50)`
  Tạo file `ITTools/config/cameras.json` mẫu với vài vị trí camera mẫu.

- [ ] **Step 4: Chạy test để xác nhận Green**:
  `python -m unittest tests/test_camera_manager.py`

---

### Task 2: Module Backend `rustdesk_manager.py` & Unit Tests

**Files:**
- Create: `ITTools/modules/rustdesk_manager.py`
- Test: `tests/test_rustdesk_manager.py`

- [ ] **Step 1: Viết test thất bại (Red)**:
  Tạo `tests/test_rustdesk_manager.py` kiểm tra:
  - `validate_mac()` nhận diện đúng các định dạng MAC `AA:BB:CC:DD:EE:FF`, `AA-BB-CC-DD-EE-FF` và từ chối MAC sai.
  - `create_magic_packet()` tạo payload chính xác 102 bytes (`6 x 0xFF + 16 x MAC bytes`).
  - `send_wake_on_lan()` gửi gói UDP broadcast thành công.
  - `get_rustdesk_status()` phát hiện đường dẫn cài đặt, trạng thái service, các port lắng nghe 21116/21118.
  - `connect_direct_ip()` từ chối IP không hợp lệ và tạo lệnh chạy an toàn không nhấp nháy cửa sổ.
  - `restart_rustdesk_service()` bắt lỗi và trả về dictionary chuẩn `{success, message}`.

- [ ] **Step 2: Chạy test để xác nhận Red**:
  `python -m unittest tests/test_rustdesk_manager.py`

- [ ] **Step 3: Triển khai mã nguồn tối thiểu (Green)**:
  Tạo `ITTools/modules/rustdesk_manager.py`:
  - `find_rustdesk_executable()` tìm trong Program Files, LocalAppData.
  - `get_rustdesk_service_status()` dùng `sc query rustdesk` qua `security_utils`.
  - `check_direct_ip_listening(port=21118)` kiểm tra socket cục bộ.
  - `connect_direct_ip(target_ip)` gọi `subprocess.Popen([exe, target_ip], creationflags=CREATE_NO_WINDOW)`.
  - `restart_rustdesk_service()` gọi `net stop rustdesk` & `net start rustdesk`.
  - `send_wake_on_lan(mac_address, broadcast_ip='255.255.255.255', port=9)` gửi socket UDP.

- [ ] **Step 4: Chạy test để xác nhận Green**:
  `python -m unittest tests/test_rustdesk_manager.py`

---

### Task 3: Tích hợp vào Web API (`ITTools/web_api.py`) & Hồi quy

**Files:**
- Modify: `ITTools/web_api.py`
- Modify: `tests/test_functional_regressions.py`

- [ ] **Step 1: Thêm API methods vào `web_api.py`**:
  - `get_camera_list()`
  - `save_camera_list(cameras)`
  - `ping_cameras()`
  - `scan_cameras_lan(ip_range)`
  - `get_rustdesk_info()`
  - `connect_rustdesk_ip(target_ip)`
  - `restart_rustdesk()`
  - `wake_on_lan(mac_address, broadcast_ip)`
  - Thêm tên các API mới vào danh sách bảo vệ `_public_methods`.

- [ ] **Step 2: Cập nhật `tests/test_functional_regressions.py`**:
  - Bổ sung các API mới vào kiểm tra danh sách API frontend không trùng lặp và tương thích.
  - Chạy `python -m unittest discover -s tests -p "test_*.py"`.

---

### Task 4: Giao diện Người dùng (HTML/JS) cho Camera IP & RustDesk

**Files:**
- Modify: `ITTools/web/index.html`
- Create: `ITTools/web/js/camera_manager.js`
- Create: `ITTools/web/js/rustdesk_tool.js`
- Modify: `ITTools/web/app.js`

- [ ] **Step 1: Tạo Tab Camera IP trong `index.html`**:
  - Thêm menu sidebar `📹 Quản Lý Camera` (tab `tab-camera-manager`) trong nhóm `2. MẠNG & MÁY IN`.
  - Thiết kế bảng quản lý Camera:
    - Thanh điều khiển: Nút "⚡ Kiểm Tra Tất Cả (Ping All)", nút "🔍 Dò Tìm Camera LAN", nút "➕ Thêm Camera", ô tìm kiếm camera theo tên/IP.
    - Bảng danh sách: Cột STT, Tên Vị Trí, Địa Chỉ IP, Cổng (RTSP/Web), Trạng Thái (Badge Xanh/Đỏ/Đang kiểm tra, Độ trễ ms), Thao Tác (Mở Web Admin, Test RTSP, Sửa, Xóa).
    - Modal Thêm / Chỉnh sửa Camera (Tên, IP, Port Web, Port RTSP, Ghi chú).
    - Khu vực Dò tìm Camera mới: Nhập dải IP ➔ Quét ➔ Nút "Thêm vào danh sách" 1-click.

- [ ] **Step 2: Tạo Widget RustDesk & WoL**:
  - Đặt Widget RustDesk Direct IP trực quan ngay trong tab `tab-ip-manager` hoặc `tab-server-tools`:
    - Thẻ trạng thái RustDesk: Trạng thái Service (Đang chạy/Dừng), Port 21118 (Lắng nghe/Chưa mở), IP LAN máy hiện tại.
    - Nút 1-Click: "Mở RustDesk", "Khởi Động Lại Dịch Vụ".
    - Ô kết nối nhanh Direct IP: Nhập IP máy đích (VD: `10.90.39.88`) ➔ Bấm "Kết Nối Ngay".
    - Ô Wake-on-LAN: Nhập MAC (VD: `D8:5E:D3:12:34:56`) ➔ Bấm "Bật Máy Từ Xa".

- [ ] **Step 3: Triển khai JavaScript**:
  - `ITTools/web/js/camera_manager.js`: Xử lý nạp danh sách, ping hàng loạt với hiệu ứng spinner, mở URL web camera, thêm/xóa/sửa camera, quét dải IP.
  - `ITTools/web/js/rustdesk_tool.js`: Xử lý hiển thị trạng thái RustDesk, kích hoạt kết nối Direct IP, gửi lệnh WoL.
  - Tích hợp 2 tệp script vào `index.html` và khởi tạo trong `app.js`.

---

### Task 5: Kiểm thử Toàn diện & Tự Chẩn Đoán

**Files:**
- Modify: `ITTools/runtime_diagnostics.py` (bổ sung check camera_manager và rustdesk_manager)
- Test: Toàn bộ suite test

- [ ] **Step 1: Cập nhật `runtime_diagnostics.py`**:
  - Thêm kiểm tra import `modules.camera_manager` và `modules.rustdesk_manager` trong `--self-test`.
- [ ] **Step 2: Chạy kiểm thử tự động**:
  - `python -m unittest discover -s tests -p "test_*.py"`
  - `python ITTools/main.py --self-test ITTools/scratch/self-test-report.json`
- [ ] **Step 3: Xác minh giao diện người dùng**:
  - Chạy `tests/qa_preview.py` hoặc mở thử app để đảm bảo giao diện hiển thị mượt mà, chuyển tab trơn tru, không có lỗi console.

