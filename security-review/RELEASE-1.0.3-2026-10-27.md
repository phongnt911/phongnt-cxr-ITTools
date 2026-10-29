# Kiểm thử và phát hành Windows 1.0.3 — 27/10/2026

## Kết luận

Đã build gói dùng cuối `dist/ITTool-SAGS-CXR-2026-v1.0.3-Windows-x64.zip` và EXE `dist/release-1.0.3/IT_Tool_SAGS_CXR_2026.exe`.
Đã mở EXE thực: cửa sổ có tiêu đề phiên bản 1.0.3 và trạng thái Responding=True. Shortcut trong thư mục dự án trỏ tới đúng bản này.

| Kiểm tra ngày 27/10/2026 | Kết quả |
|---|---|
| Python unittest (bảo mật, DPAPI/profile mẫu, chức năng, FluentCleaner) | 48/48 đạt |
| JavaScript | Test renderer mạng đạt, tất cả JS qua kiểm tra cú pháp |
| Mã nguồn | compileall và git diff --check đạt |
| Phụ thuộc | pip check đạt; pip-audit không tìm thấy lỗ hổng đã công bố |
| 44 API chỉ đọc trên Windows | 42 PASS; AD chưa có domain/RSAT, iSCSI cần quyền/dịch vụ phù hợp |
| Chính EXE 1.0.3 | 45/45 kiểm tra đạt, exit code 0 |
| Gói ZIP | Giải kiểm CRC toàn bộ và đối chiếu SHA-256 từng file đạt |
| EXE mặc định | Hash trùng bản phát hành |

45 kiểm tra EXE gồm WinForms, `_tkinter`, 28 module, tạo/hủy Tk ẩn; gọi 11 API thật (metadata, cấu hình, Startup, ứng dụng, máy in, mạng, dịch vụ, boot, ổ đĩa, ngày giờ, browser backup); xác minh manifest FluentCleaner; mã hóa/giải mã dữ liệu DPAPI giả; kiểm tra HTML/script/logo được đóng gói.
Báo cáo chỉ ghi loại dữ liệu/khóa phản hồi, không ghi danh sách phần mềm, thông tin mạng hoặc dữ liệu trình duyệt thực.

## Các lỗi bổ sung đã sửa

- Services: không còn dựa vào chữ SUCCESS/PENDING trong stdout. Chỉ báo hoàn tất sau khi SCM xác nhận trạng thái đích; hết thời gian chờ trả pending để tải lại.
- Restart service: dừng và xác nhận stopped trước khi start; stop lỗi thì dừng luồng, không gọi start tiếp.
- Dùng argument list cho `sc.exe`, không nội suy tên dịch vụ vào shell. Tên không hợp lệ bị từ chối.
- Kiểu khởi động: từ chối giá trị lạ thay vì tự đổi thành Automatic, giữ đúng Automatic (Delayed).
- Boot: xóa chỉ nhận GUID đầy đủ, kiểm tra return code; không nhận cụm từ "not successfully completed" như thành công. Timeout chỉ nhận số nguyên 0–999 theo giao diện.
- Phục hồi browser: chỉ lập kế hoạch cho trình duyệt được chọn, không tự thêm trình duyệt theo tên thư mục.
- Phục hồi browser: tôn trọng lựa chọn bookmarks/passwords/history/extensions/full profile; không ghi đè dữ liệu ngoài loại đã chọn; không đếm browser thành công khi không chép được file nào. Truyền options=None vào module giữ tương thích phục hồi toàn profile; giao diện gửi lựa chọn cụ thể.

Các lỗi được tái hiện bằng kiểm thử thất bại trước khi vá; xem release-red.log, release-restore-red.log và kết quả đạt release-tests.log. File test dùng mock cho lệnh hệ thống, profile giả trong thư mục scratch.

## Giới hạn kiểm thử

Không tuyên bố mọi chức năng đã được kiểm thử đầu cuối. Các thao tác đổi IP/DNS/IPv6, BitLocker/EFS, sửa boot/phân vùng, firewall, shutdown/restart, dọn dữ liệu, cài/gỡ phần mềm thật và Office cần VM có snapshot hoặc thiết bị thử. Không chạy các thao tác này trên máy đang sử dụng để vượt kiểm thử.
Chưa xác nhận chất lượng camera/microphone/loa, bản in vật lý, phần cứng và môi trường Windows Server/AD/iSCSI đích. Trạng thái MSiSCSI hiện tại được kiểm tra riêng, không tự bật dịch vụ.
Kết quả điều hướng 29 tab của phiên trước (24/10) nằm trong qa-ui.json; đợt 27/10 sửa backend, không tuyên bố bấm lại toàn bộ nút trên native WebView.
Phụ thuộc không có lỗ hổng đã công bố không đồng nghĩa EXE được chứng nhận sạch malware. Không upload EXE trong đợt phát hành này.

## Sử dụng

Giải nén ZIP rồi mở EXE, chấp nhận UAC. Không cần Python; cần Edge WebView2 cho giao diện và Windows App Runtime 2.0.1 x64 cho FluentCleaner (nút tải trong công cụ). Bấm X thu nhỏ vào khay; chọn Thoát ở khay để đóng hoàn toàn.
Backup trình duyệt dùng DPAPI cùng tài khoản Windows trên máy hiện tại; Firefox dùng chung places.sqlite cho bookmarks/history.

- EXE SHA-256: `4CDE910CB76F59B80E8DBC0F36359924B127540DA9CD84F0E88D712A8980146F`
- ZIP SHA-256: `E895589FCB053E239FABF7071FB59C7B590E53E14FB57ADAF7CC8FCC7B813954`
- Gói có HUONG_DAN.txt, LICENSE.txt, SHA256SUMS.txt.
- Bằng chứng: release-runtime.json, release-tests.log, release-api.json, release-dependencies.json, release-build-environment.txt, release-build.log, release-manifest.json.
