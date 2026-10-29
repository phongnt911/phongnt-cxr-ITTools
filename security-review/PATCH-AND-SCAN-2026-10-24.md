# Bản vá và kết quả kiểm tra — 24/10/2026

## Đã thay đổi

- Kết quả quét LAN và port dùng DOM/textContent/addEventListener, không ghép hostname hoặc target vào HTML/inline handler. Nhật ký sao lưu trình duyệt cũng hiển thị bằng textContent.
- Kiểm tra host/IP ở backend, kể cả IPv6 scope. WinRM chỉ nhận host đã kiểm tra. Lưu mật khẩu bằng Windows CredWriteW, không đưa mật khẩu vào command line; xóa credential dùng danh sách đối số, không dùng shell.
- Tạo tài khoản chia sẻ bằng tham số dữ liệu PowerShell; chỉ thêm vào nhóm Users, không tự cấp Administrators hoặc ghi mật khẩu vào log.
- Quy trình One Click chuyển sang SFC /scannow chính thức; không thay file hệ thống từ assets. Các nhánh sửa máy in khác giữ RPC privacy, yêu cầu quyền quản trị khi cài driver và chặn insecure guest authentication.
- Backend từ chối tắt Defender/UAC/SmartScreen. Bỏ chức năng bỏ chặn tải xuống hàng loạt và thay đổi SaveZoneInformation. Chỉ cho bỏ chặn từng file; không coi bỏ chặn là quét virus.
- Hướng dẫn kiểm tra pin dùng powercfg /batteryreport, bỏ tải script từ xa rồi chạy bằng iex.
- Bộ cài Office và WebView2 phải qua kiểm tra chữ ký Microsoft hợp lệ trước khi chạy. WebView2 tải vào thư mục tạm riêng.
- Payload bản sao lưu trình duyệt mới được mã hóa bằng DPAPI current-user trước khi ghi đĩa, thư mục được giới hạn ACL. Khôi phục giải mã trước khi thay file; ghi file qua file tạm cùng thư mục rồi đổi tên. Bản sao lưu mới chỉ dành cho cùng tài khoản Windows/hồ sơ DPAPI, không dùng làm bản di chuyển máy hoặc cài lại Windows. Giao diện có thông báo giới hạn này trước khi sao lưu. Bản sao lưu cũ không được tự mã hóa lại.
- Cập nhật pip lên 26.2.2. Shortcut hiện mở EXE thành phẩm thay vì phụ thuộc vào .venv.

## Kiểm thử và build

- 10 kiểm thử Python thành công trên Windows ngoài sandbox, gồm luồng sao lưu/khôi phục hồ sơ trình duyệt giả, kiểm tra dữ liệu giả đã mã hóa và từ chối dữ liệu hỏng. Không dùng credential hoặc dữ liệu trình duyệt thật trong kiểm thử.
- Kiểm thử JavaScript xác nhận dữ liệu mạng chỉ được dùng như văn bản, clipboard và các nút thao tác vẫn có callback, kết quả rỗng được xử lý.
- pip check: không xung đột. pip-audit sau cập nhật: không có advisory được báo cho môi trường kiểm tra; dữ liệu gốc: dependency-audit-after.json.
- PyInstaller build thành công, xem build.log. Kiểm tra archive xác nhận có security_utils và không đóng gói spooler_clean/spooler_clean_win10. Binary gốc vẫn giữ trong repository để kiểm kê, không được dùng trong quy trình SFC mới.
- Đã mở EXE trên Windows: tiến trình phản hồi và cổng IPC 127.0.0.1:49285 thuộc tiến trình EXE mới. Chưa kiểm thử toàn bộ giao diện hoặc chạy các chức năng can thiệp hệ thống thật.

File: `dist/IT_Tool_SAGS_CXR_2026.exe`

SHA-256: `75536C6698230589CE8D9518023388799D7438D3B761C461D8979267FC4906A8`

## Kiểm tra online các binary cũ

Đã đọc báo cáo VirusTotal hiện có cho 16 file EXE/DLL trong assets, tương ứng 15 SHA-256 duy nhất. Tất cả hiển thị 0 hãng gắn cờ trong báo cáo đã đọc; mẫu số từ 66 đến 72. Một số báo cáo có timeout/type unsupported. Ngày phân tích từ 2021 đến 2026: đây là dữ liệu lịch sử, không phải quét mới và không bảo đảm file sạch.

Xem `virustotal-assets.csv`: đầy đủ hash, file, số hãng, ngày phân tích và URL từng báo cáo. Không upload các file này và chưa yêu cầu reanalysis.

## Phần quét còn chưa hoàn tất

- Hash EXE thành phẩm được tra cứu trên VirusTotal và trả về Item not found. Chưa có kết quả quét đa antivirus cho bản thành phẩm. Muốn quét mới phải upload EXE; bước đó chia sẻ mẫu và gắn với điều khoản dịch vụ.
- Defender của máy không chạy; lần thử trước trả lỗi 0x80004005. Không thay đổi chính sách antivirus để ép chạy Defender.
- Đã thử gọi FortiClient av_task cho assets và EXE. Chưa thu được báo cáo/counter xác nhận quét đã hoàn tất, do đó không ghi nhận là quét thành công hoặc sạch. Script hỗ trợ run-local-scans.ps1 được lưu để chạy trong phiên Administrator có thể kiểm tra output, nhưng mã thoát riêng lẻ cũng không đủ để kết luận sạch.
- Yêu cầu nâng quyền ở phiên trước từng bị hệ thống duyệt tự động từ chối do hết hạn mức; không phải kết luận thao tác không an toàn. Phiên tiếp tục đã cho phép yêu cầu mở scanner, nhưng vẫn chưa có kết quả scan kiểm chứng được.

## Giới hạn

Bản vá xử lý các vấn đề và đường gọi nêu trên, không phải chứng nhận toàn bộ phần mềm an toàn. Các module quản trị Windows vẫn có nhiều thao tác đặc quyền cần kiểm thử riêng trong máy ảo. Các binary đóng gói mới từ Python/.NET cũng chưa được phân tích độc lập từng file bằng sandbox malware. Chưa ký số EXE bằng chứng thư phát hành.
