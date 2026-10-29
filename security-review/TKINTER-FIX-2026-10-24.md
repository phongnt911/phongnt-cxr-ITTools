# Sửa lỗi mất _tkinter sau khi dọn Temp

## Nguyên nhân xác minh được

Bản EXE trước có `_tkinter.pyd`, Tcl/Tk DLL và các thư mục script trong archive.
Tuy nhiên thư mục runtime đang hoạt động dưới `%TEMP%\_MEI0000c0482` chỉ còn
21 file, chủ yếu là DLL/PYD đã được Windows giữ khóa; `_tkinter.pyd` và nhiều
tài nguyên khác đã biến mất. Lịch sử FluentCleaner có lượt dọn lúc 07:30:45
ngày 24/10/2026 ngay trước khi báo lỗi. Các module nhập tkinter muộn vì vậy
không còn tìm được extension. Không phải từng chức năng riêng lẻ thiếu code.

## Bản sửa 1.0.1

- PyInstaller giải nén vào `%LOCALAPPDATA%\ITToolSAGSCXR\Runtime`, thay vì Temp.
  Biến môi trường được bootloader Windows mở rộng trên máy đích.
- Trước khi mở FluentCleaner, bổ sung ngoại lệ PATH cho thư mục ITToolSAGSCXR
  và runtime hiện tại. Bật GlobalExclusionsEnabled, giữ nguyên các thiết lập
  khác và không thêm trùng quy tắc. Không chạy dọn dẹp để kiểm thử.
- Build dừng ngay nếu môi trường Python không nạp được _tkinter/Tcl.
  Batch build ưu tiên .venv và dùng đúng tên EXE mới.
- Thêm `--self-test <report.json>` để kiểm tra chính bản đóng gói: nạp .NET
  trước, import các module trong luồng nền như API, tạo rồi đóng cửa sổ Tk ẩn.

## Kết quả

- 14 kiểm thử Python đạt, gồm kiểm thử ngoại lệ và bảo toàn cấu hình cleaner.
- Kiểm tra runtime trong EXE: tất cả 31 check đạt, gồm _tkinter, Tk window,
  WinForms và 28 module. Xem `runtime-frozen-fixed.json`.
- Đường dẫn giải nén thực tế của EXE đã nằm dưới LocalAppData/ITToolSAGSCXR/Runtime,
  không còn dưới Temp.
- Đã đóng phiên cũ đang lỗi, mở bản 1.0.1 và cập nhật shortcut. Ba file EXE
  tại dist/, dist/integrated/ và dist/tk-fix/ đều được thay bằng cùng bản sửa.

SHA-256: `0DE9D82B8A494550DA5EB7AB49636477E1DA15B3C5537F47F22E260397B551E9`

Kiểm tra này xác minh import/runtime; không khẳng định đã thao tác mọi chức năng
đặc quyền trên Windows thật. Không chạy dọn Temp của người dùng để tái hiện lỗi.
