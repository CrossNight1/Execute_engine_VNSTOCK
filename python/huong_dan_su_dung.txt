## Cấu hình API
1. Chọn **Cập nhật API** trên menu chính.
2. Nhập `API_KEY` và `API_SECRET`.
3. Hệ thống sẽ lưu thông tin vào file `.env` và tự động tải lại biến môi trường.

### Trạng thái API:
- ✅ **OK** → API hợp lệ.
- ❌ **Missing** → API chưa được cài đặt.

---

## Quản lý cấu hình lệnh

### Xem cấu hình
Hiển thị tất cả cấu hình hiện tại, bao gồm:
- Mã cổ phiếu.
- Loại lệnh (MUA/BÁN).
- Khối lượng.
- Giá mục tiêu.
- Ngưỡng khối lượng.
- Gói vay.
- Thời gian thực hiện.
- Trạng thái.

### Thêm cấu hình
1. Nhập mã cổ phiếu.
2. Chọn chế độ:
   - **Thường**: Cần đủ sức mua/bán.
   - **Đợi T+**: Không cần đủ sức mua/bán, bắt buộc nhập thời gian.
3. Chọn loại lệnh: **MUA** hoặc **BÁN**.
4. Nhập giá mục tiêu (áp dụng cho chế độ **Thường**).
5. Nhập khối lượng. Hệ thống sẽ kiểm tra giới hạn tối đa và cảnh báo nếu vượt.
6. Nhập ngưỡng khối lượng kích hoạt (áp dụng cho chế độ **Thường**).
7. Nhập thời gian thực hiện (bắt buộc nếu chọn chế độ **T+**).

Cấu hình sẽ được lưu vào file `config.json`.

### Xoá cấu hình
1. Chọn cấu hình cần xoá từ danh sách.
2. Hệ thống sẽ xóa cấu hình và cập nhật file `config.json`.

---

## Chạy Engine
1. Chọn **Chạy Engine** trên menu.
2. Nhập OTP để lấy token giao dịch.
3. Engine sẽ kết nối WebSocket và thực hiện lệnh theo cấu hình.

### Dừng Engine
- Nhấn **Ctrl+C**:
  - Lần đầu: Hiển thị cảnh báo.
  - Lần hai: Thoát hẳn.

---

## File lưu trữ

| File          | Mục đích                          |
|---------------|-----------------------------------|
| `.env`        | Lưu `API_KEY` & `API_SECRET`.    |
| `config.json` | Lưu danh sách cấu hình lệnh.     |
| `session.json`| Lưu thông tin phiên, số tài khoản.|

---

## Phím tắt

- **Ctrl+C**: Thoát menu hoặc dừng Engine.
- **Nhấn Enter**: Tiếp tục khi có thông báo.
- **Nhấn Space**: Chọn danh mục/list

---

## Lưu ý quan trọng
- Phải cập nhật API trước khi thêm cấu hình hoặc chạy Engine.
- Khi copy đổi tài khoản nên xóa file **session.json**
- Chế độ **T+** yêu cầu nhập thời gian thực hiện.
- Nếu khối lượng vượt giới hạn, hệ thống sẽ cảnh báo. Người dùng cần xác nhận nếu muốn tiếp tục.
- Engine sẽ chạy liên tục theo cấu hình cho đến khi nhấn **Ctrl+C**.

---

## Lưu ý khi gặp lỗi
1. **API không hợp lệ**:
   - Kiểm tra lại `API_KEY` và `API_SECRET` trong file `.env`.
   - Đảm bảo đã chọn **Cập nhật API** trên menu.

2. **Không thể kết nối WebSocket**:
   - Kiểm tra kết nối mạng.
   - Đảm bảo token giao dịch hợp lệ.

3. **Cấu hình không được lưu**:
   - Kiểm tra quyền ghi file trong thư mục chứa `config.json`.
   - Đảm bảo không có lỗi cú pháp khi nhập cấu hình.

4. **Engine không thực hiện lệnh**:
   - Kiểm tra trạng thái API.
   - Đảm bảo cấu hình lệnh hợp lệ và đã được lưu.

5. **Lỗi khối lượng vượt giới hạn**:
   - Xác nhận lại khối lượng nhập vào.
   - Điều chỉnh cấu hình nếu cần thiết.

Nếu các lỗi trên vẫn không được khắc phục, hãy kiểm tra log hệ thống hoặc liên hệ 
*zalo: 0876 065 535*

---

## Hướng dẫn cập nhật
Khi có bản cập nhật mới, hãy thực hiện các bước sau:

1. Tải bản cập nhật từ: [https://github.com/CrossNight1/Execute_engine_VNSTOCK.git](https://github.com/CrossNight1/Execute_engine_VNSTOCK.git).
2. Giải nén file vừa tải về để tạo thư mục mới.
3. Truy cập vào thư mục vừa giải nén, mở file Python.
4. Xóa file **.env** trong thư mục mới.
5. Copy toàn bộ file trong thư mục mới và dán vào thư mục ứng dụng đang sử dụng → **Replace all files**.
6. Kiểm tra lại file **.env** để đảm bảo `API_KEY` và `API_SECRET` không bị thay đổi. Nếu có, vui lòng xóa và nhập lại thông tin API.