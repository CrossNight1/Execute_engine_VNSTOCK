import re

with open("/Users/leoinv/Documents/CODE/Execute_engine_VNSTOCK/static/index.html", "r") as f:
    html = f.read()

desc_content = """    <div class="card" id="desc-tab" style="display: none;">
        <div class="guide-content">
            <h2>MÔ TẢ CHI TIẾT LOGIC VÀ QUY ĐỊNH DỮ LIỆU CỦA ENGINE</h2>
            
            <h3>I. TỔNG QUAN VỀ ENGINE</h3>
            <p>Execute Engine là một hệ thống tự động giao dịch, hoạt động trực tiếp trên máy tính của bạn. Hệ thống này kết nối với luồng dữ liệu thời gian thực (WebSocket) của DNSE để giám sát biến động giá và khối lượng trên thị trường. Khi các điều kiện bạn thiết lập được thỏa mãn, hệ thống sẽ tự động gửi lệnh mua/bán (API) lên Sở Giao dịch ngay lập tức.</p>
            
            <p>Hệ thống hoạt động với 2 chế độ (Mode) chính:</p>

            <h4>1. Chế độ Thường (NORMAL) - Theo dõi Giá & Thanh khoản</h4>
            <ul>
                <li><strong>Mục đích:</strong> Săn lệnh hoặc chốt lời/cắt lỗ tự động khi thị trường đạt mức giá mong muốn với thanh khoản phù hợp.</li>
                <li><strong>Điều kiện kích hoạt MUA:</strong> Giá Bán Rẻ Nhất (Best Offer) &lt;= Giá Mục Tiêu <strong>VÀ</strong> Khối lượng chờ bán ở mức giá đó &lt;= Ngưỡng kích hoạt.</li>
                <li><strong>Điều kiện kích hoạt BÁN:</strong> Giá Mua Đắt Nhất (Best Bid) &gt;= Giá Mục Tiêu <strong>VÀ</strong> Khối lượng chờ mua ở mức giá đó &lt;= Ngưỡng kích hoạt.</li>
                <li><strong>Thực thi Đặt Lệnh:</strong>
                    <ul>
                        <li>Nếu chọn <strong>LO</strong>: Gửi lệnh giới hạn đúng với mức Giá Mục Tiêu.</li>
                        <li>Nếu chọn <strong>MTL</strong>: Gửi lệnh thị trường (chấp nhận khớp mọi giá cho đến khi đủ số lượng, quét thanh khoản).</li>
                    </ul>
                </li>
            </ul>

            <h4>2. Chế độ Hẹn Giờ / Đợi T+ (TPLUS) - Giao dịch theo thời gian thực thi</h4>
            <ul>
                <li><strong>Mục đích:</strong> Dành cho các chiến lược giao dịch tại một thời điểm cụ thể trong tương lai (ví dụ: bán hàng T+ về tài khoản ngay đầu phiên ATC, hoặc mua vớt ATO).</li>
                <li><strong>Theo dõi:</strong> Quét thời gian hiện tại mỗi 0.5s so với <code>time_execute</code>. Lệnh kích hoạt khi đồng hồ vượt mốc thời gian này.</li>
                <li><strong>Thực thi Đặt Lệnh:</strong>
                    <ul>
                        <li><strong>Trùng khung ATO (09:00 - 09:15):</strong> Đổi thành lệnh ATO (giá = 0), bỏ qua cấu hình giá.</li>
                        <li><strong>Trùng khung ATC (14:30 - 14:45):</strong> Đổi thành lệnh ATC (giá = 0), bỏ qua cấu hình giá.</li>
                        <li><strong>Ngoài các khung trên (trong phiên):</strong> Dùng đúng Loại lệnh setup. 
                            <br>- <strong>LO</strong>: Gửi kèm Giá mục tiêu bắt buộc phải nhập.
                            <br>- <strong>MTL</strong>: Engine lấy giá tốt nhất lưu log và gửi lệnh Market (giá = 0).
                        </li>
                    </ul>
                </li>
            </ul>

            <h3>II. QUY ĐỊNH NHẬP DỮ LIỆU</h3>
            <ul>
                <li><strong>Mã Cổ Phiếu:</strong> Nhập hoa hoặc thường đều được (VD: VND, hpg).</li>
                <li><strong>Khối lượng:</strong> Nhập số lượng nguyên (VD: 100, 1000). Nút "Kiểm tra sức mua / bán" tự động đối chiếu với hạn mức DNSE.</li>
                <li><strong>Giá:</strong> <strong>BẮT BUỘC</strong> dùng thang giá "Nghìn VNĐ". VD: Giá 25.500 VND nhập <code>25.5</code>. Code tự động x1000 lúc gửi lệnh.</li>
                <li><strong>Ngưỡng KL Kích Hoạt:</strong> Chỉ dùng cho chế độ NORMAL, giúp bảo vệ bạn không khớp lệnh khi thanh khoản quá lớn (VD: 50000).</li>
                <li><strong>Loại Khớp Lệnh:</strong> 
                    <ul>
                        <li><strong>LO:</strong> Yêu cầu nhập Giá mục tiêu. Lệnh giới hạn.</li>
                        <li><strong>MTL:</strong> Không yêu cầu biến giá trên giao diện (gửi ngầm = 0). Lệnh thị trường.</li>
                    </ul>
                </li>
            </ul>
        </div>
    </div>"""

guide_content = """    <div class="card" id="guide-tab" style="display: none;">
        <div class="guide-content">
            <h2>HƯỚNG DẪN SỬ DỤNG GIAO DIỆN WEB (VNSTOCK ENGINE)</h2>
            
            <h3>I. QUẢN LÝ TÀI KHOẢN (Multi-Account)</h3>
            <p>Hệ thống cho phép bạn điều khiển nhiều tài khoản DNSE cùng lúc một cách độc lập.</p>
            <ul>
                <li><strong>Thêm tài khoản mới:</strong> Chuyển sang tab "Quản Lý Tài Khoản" trên Menu chính. Điền Tên Gợi Nhớ (VD: TK Vợ), API KEY và API SECRET (từ DNSE) -> Nhấn Thêm Tài Khoản.</li>
                <li><strong>Quản lý luồng xử lý:</strong> Sau khi thêm tài khoản, ở góc phải thanh Header sẽ có Menu thả xuống (Dropdown). <strong>HÃY NHỚ CHỌN TÀI KHOẢN MÀ BẠN MUỐN THAO TÁC.</strong> Mọi cấu hình lệnh, "Sức mua / bán" hay chạy/dừng Engine đều áp dụng trên Tài Khoản Hiện Đang Chọn.</li>
            </ul>

            <h3>II. TẠO CẤU HÌNH LỆNH</h3>
            <ul>
                <li><strong>Chế độ NORMAL (Săn lệnh giá/thanh khoản):</strong> 
                    <ul>
                        <li>Bắt buộc nhập <em>Mã, Loại Lệnh (MUA/BÁN), KL, Khớp Lệnh (LO/MTL)</em>, <em>Giá mục tiêu</em> và <em>Ngưỡng KL kích hoạt</em>.</li>
                        <li>BƯỚC QUAN TRỌNG: Phải click <strong>🔍 Kiểm tra sức mua / bán</strong>. Nếu khối lượng vượt hạn mức, hệ thống sẽ báo đỏ, bạn phải tick ô "Vẫn tiếp tục dù vượt sức mua/bán" để ghi đè.</li>
                    </ul>
                </li>
                <li><strong>Chế độ TPLUS (Hẹn giờ chạy ATO/ATC/Trong phiên):</strong>
                    <ul>
                        <li>Bắt buộc nhập <em>Thời gian thực hiện</em> (chuẩn HH:MM:SS, VD: 14:30:00).</li>
                        <li>Ô nhập Giá chỉ hiện nếu Loại Khớp Lệnh là <strong>LO</strong>. Nếu MTL, ô Giá tự ẩn. (Chế độ này không kiểm tra sức mua nghiêm ngặt trước khi lưu).</li>
                    </ul>
                </li>
            </ul>

            <h3>III. VẬN HÀNH ENGINE</h3>
            <ul>
                <li>Đảm bảo đã chọn đúng tài khoản trên Dropdown ở thanh Header.</li>
                <li>Lấy mã Smart OTP 6 số từ ứng dụng DNSE, nhập vào ô và Click <strong>🚀 Chạy Engine</strong>. Giao diện báo RUN.</li>
                <li>Bảng Theo Dõi Thời Gian Thực sẽ liên tục cập nhật mỗi 1 giây: Giá mua/bán tốt nhất, số đếm ngược, tín hiệu. Bạn có thể chuyển đổi qua lại giữa các Tài Khoản ở Dropdown để xem bảng của từng TK độc lập.</li>
            </ul>

            <h3>IV. XỬ LÝ SỰ CỐ CƠ BẢN (TROUBLESHOOTING)</h3>
            <ul>
                <li><strong>API MISSING:</strong> Chưa thêm tài khoản nào, hoặc API Key/Secret bị sai.</li>
                <li><strong>Engine tắt ngang (Bảng dừng nhảy):</strong> Thường do Smart OTP hết hạn hoặc Web socket đứt kết nối. Hãy lấy OTP mới và chạy lại.</li>
                <li><strong>Lệnh bị Rejected (Từ chối):</strong> Hệ thống đã bắn lệnh nhưng Sàn/DNSE từ chối. Thường do: (1) Sức mua/bán không đủ lúc trigger; (2) Giá LO đặt ngoài biên độ Trần/Sàn; (3) Khối lượng lô lẻ sai quy định HOSE.</li>
            </ul>
        </div>
    </div>"""

# Replace desc-tab
html = re.sub(r'<div class="card" id="desc-tab" style="display: none;">.*?(?=<div class="card" id="guide-tab" style="display: none;">)', desc_content + "\n\n", html, flags=re.DOTALL)

# Replace guide-tab
html = re.sub(r'<div class="card" id="guide-tab" style="display: none;">.*?(?=<script>)', guide_content + "\n\n    ", html, flags=re.DOTALL)

with open("/Users/leoinv/Documents/CODE/Execute_engine_VNSTOCK/static/index.html", "w") as f:
    f.write(html)
print("Updated index.html tabs")
