import re

html_content = """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Execute Engine VNSTOCK - Dashboard</title>
    <style>
        :root {
            --bg-main: #000000;
            --bg-card: #111111;
            --border: #333333;
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --buy: #10b981;
            --sell: #ef4444;
            --text-main: #e2e8f0;
            --text-muted: #94a3b8;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg-main);
            color: var(--text-main);
            min-height: 100vh;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            font-size: 14px;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 1rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
        }

        .logo-section h1 { font-size: 1.2rem; font-weight: bold; color: #fff; }
        .logo-section p { color: var(--text-muted); font-size: 0.8rem; }

        .status-badge { display: flex; align-items: center; gap: 0.5rem; padding: 0.25rem 0.5rem; font-weight: bold; background: #000; border: 1px solid var(--border); }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #6b7280; }
        .status-dot.active { background: var(--buy); }

        .tabs { 
            display: flex; 
            gap: 0.5rem; 
            background: var(--bg-card); 
            border: 1px solid var(--border); 
            padding: 0.5rem; 
            border-radius: 8px; 
            margin-bottom: 0.5rem; 
        }
        .tab-btn { 
            background: transparent; 
            border: 1px solid transparent; 
            color: var(--text-muted); 
            cursor: pointer; 
            font-size: 0.95rem; 
            padding: 0.5rem 1rem; 
            border-radius: 6px; 
            transition: all 0.2s ease;
        }
        .tab-btn:hover {
            color: var(--text-main);
            background: rgba(255, 255, 255, 0.05);
        }
        .tab-btn.active { 
            color: #fff; 
            background: #222; 
            border-color: var(--border);
            font-weight: bold; 
        }

        .tab-badge {
            font-size: 0.65rem;
            padding: 2px 6px;
            border-radius: 4px;
            margin-left: 6px;
            vertical-align: middle;
            background: #000;
            color: var(--text-muted);
            border: 1px solid var(--border);
        }
        .tab-badge.ok { background: rgba(16, 185, 129, 0.2); color: var(--buy); border-color: rgba(16, 185, 129, 0.5); }
        .tab-badge.warn { background: rgba(245, 158, 11, 0.2); color: #f59e0b; border-color: rgba(245, 158, 11, 0.5); }

        .main-grid { display: grid; grid-template-columns: 300px 1fr; gap: 1rem; flex-grow: 1; }
        @media (max-width: 1024px) { .main-grid { grid-template-columns: 1fr; } }

        .card { background: var(--bg-card); border: 1px solid var(--border); padding: 1rem; display: flex; flex-direction: column; gap: 1rem; }
        h2 { font-size: 1.1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-bottom: 0.5rem; }

        .form-group { display: flex; flex-direction: column; gap: 0.25rem; }
        label { font-size: 0.8rem; color: var(--text-muted); }
        input, select { background: #000; border: 1px solid var(--border); padding: 0.4rem 0.5rem; color: var(--text-main); font-family: inherit; font-size: 0.9rem; }
        input:focus, select:focus { outline: none; border-color: var(--primary); }

        .btn { padding: 0.5rem 1rem; font-size: 0.9rem; cursor: pointer; border: none; background: #333; color: #fff; text-align: center; }
        .btn-primary { background: var(--primary); }
        .btn-primary:hover { background: var(--primary-hover); }
        .btn-danger { background: var(--sell); }
        .btn-danger:hover { background: #dc2626; }
        .btn-small { padding: 0.25rem 0.5rem; font-size: 0.8rem; }

        .table-container { overflow-x: auto; border: 1px solid var(--border); }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.85rem; }
        th, td { padding: 0.5rem; border-bottom: 1px solid var(--border); }
        th { font-weight: bold; background: #000; color: var(--text-muted); }
        tr:hover td { background: #222; }

        .badge-buy { color: var(--buy); font-weight: bold; }
        .badge-sell { color: var(--sell); font-weight: bold; }

        .engine-controls { display: flex; gap: 0.5rem; align-items: center; background: #000; padding: 0.75rem; border: 1px solid var(--border); }

        /* Capacity panel */
        .capacity-panel { background: #000; border: 1px solid var(--border); padding: 0.5rem; font-size: 0.85rem; display: none; flex-direction: column; gap: 0.25rem; }
        .capacity-panel.visible { display: flex; }
        .capacity-row { display: flex; justify-content: space-between; }
        .capacity-label { color: var(--text-muted); }
        .capacity-ok { color: var(--buy); }
        .capacity-warn { color: #f59e0b; }
        .capacity-error { color: var(--sell); }
        .override-check { display: flex; align-items: center; gap: 0.25rem; font-size: 0.8rem; color: #f59e0b; margin-top: 0.25rem; }
        .override-check input { cursor: pointer; }

        /* Guide Tab */
        .guide-content { line-height: 1.5; font-size: 0.9rem; }
        .guide-content h2 { margin-top: 1rem; color: #fff; border-bottom: 1px solid var(--border); padding-bottom: 0.25rem; }
        .guide-content h3 { margin-top: 0.75rem; color: #ccc; font-size: 1rem; }
        .guide-content ul { margin-left: 1.5rem; margin-bottom: 0.5rem; color: var(--text-muted); }
        .guide-content p { margin-bottom: 0.5rem; color: var(--text-muted); }
        .guide-content table { margin-bottom: 1rem; width: auto; color: var(--text-muted); }
    </style>
</head>

<body>

    <header>
        <div class="logo-section">
            <h1>Execute Engine</h1>
            <p>VNSTOCK Trading automation monitor</p>
        </div>
        <div style="display:flex; gap:1rem; align-items:center;">
            <select id="account-selector" onchange="changeAccount()" style="min-width:200px; padding:0.4rem; font-weight:bold;">
                <option value="">-- Chọn Tài khoản --</option>
            </select>
            <div class="status-badge">
                <div id="engine-dot" class="status-dot"></div>
                <span id="engine-status-text">System Idle</span>
            </div>
        </div>
    </header>

    <div class="tabs">
        <button class="tab-btn active" id="btn-tab-dashboard" onclick="switchTab('dashboard')">
            Dashboard <span id="badge-engine" class="tab-badge">OFF</span>
        </button>
        <button class="tab-btn" id="btn-tab-accounts" onclick="switchTab('accounts')">Quản Lý Tài Khoản</button>
        <button class="tab-btn" id="btn-tab-guide" onclick="switchTab('guide')">Hướng dẫn</button>
        <button class="tab-btn" id="btn-tab-desc" onclick="switchTab('desc')">Mô tả Engine <span id="badge-api" class="tab-badge">API?</span></button>
    </div>

    <!-- TÀI KHOẢN TAB -->
    <div class="card" id="accounts-tab" style="display: none; max-width: 800px; margin: 0 auto; width: 100%;">
        <h2>Thêm Tài Khoản DNSE</h2>
        <div class="form-group">
            <label>Tên Gợi Nhớ (VD: TK Chính, Quỹ A)</label>
            <input type="text" id="acc-name" placeholder="...">
        </div>
        <div class="form-group">
            <label>API KEY</label>
            <input type="password" id="acc-api-key" placeholder="Nhập API Key">
        </div>
        <div class="form-group">
            <label>API SECRET</label>
            <input type="password" id="acc-api-secret" placeholder="Nhập API Secret">
        </div>
        <button class="btn btn-primary" id="add-acc-btn" onclick="addAccount()">Thêm Tài Khoản</button>

        <h2 style="margin-top: 2rem;">Danh Sách Tài Khoản</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Tên</th>
                        <th>Account No</th>
                        <th>API Key</th>
                        <th>Thao tác</th>
                    </tr>
                </thead>
                <tbody id="accounts-list-rows">
                </tbody>
            </table>
        </div>
    </div>

    <!-- DASHBOARD TAB -->
    <div class="main-grid" id="dashboard-tab">
        <!-- Left Pane: Add Config -->
        <div class="card">
            <h2>Thêm lệnh mới</h2>

            <div class="form-group">
                <label>Mã Cổ Phiếu</label>
                <input type="text" id="cfg-symbol" placeholder="VND, HPG, SSI...">
            </div>

            <div class="form-group">
                <label>Chế độ</label>
                <select id="cfg-mode" onchange="toggleModeFields()">
                    <option value="NORMAL">Thường (Cần đủ tiền/sức mua)</option>
                    <option value="TPLUS">Đợi T+ (Khớp phiên ATC/ATO)</option>
                </select>
            </div>

            <div class="form-group">
                <label>Loại Lệnh (MUA/BÁN)</label>
                <select id="cfg-side">
                    <option value="BUY">MUA</option>
                    <option value="SELL">BÁN</option>
                </select>
            </div>

            <div class="form-group">
                <label>Loại Khớp Lệnh</label>
                <select id="cfg-order-type">
                    <option value="MTL">MTL (Thị trường)</option>
                    <option value="LO">LO (Lệnh giới hạn)</option>
                </select>
            </div>

            <div class="form-group">
                <label>Khối lượng</label>
                <input type="number" id="cfg-qty" placeholder="Ví dụ: 1000">
            </div>

            <div class="form-group" id="group-price">
                <label>Giá mục tiêu (VND x1000)</label>
                <input type="number" step="0.01" id="cfg-price" placeholder="Ví dụ: 25.5"
                       oninput="resetCapacity()">
            </div>

            <div class="form-group" id="group-threshold">
                <label>Ngưỡng KL kích hoạt</label>
                <input type="number" id="cfg-threshold" placeholder="Ví dụ: 5000">
            </div>

            <!-- Capacity check row -->
            <div id="group-capacity" class="form-group">
                <button type="button" class="btn btn-primary" id="check-capacity-btn"
                        onclick="checkCapacity()" style="width:100%;">
                    🔍 Kiểm tra sức mua / bán
                </button>
                <!-- Result panel -->
                <div class="capacity-panel" id="capacity-panel">
                    <div class="capacity-row">
                        <span class="capacity-label">Max MUA</span>
                        <span class="capacity-value" id="cap-buy">-</span>
                    </div>
                    <div class="capacity-row">
                        <span class="capacity-label">Max BÁN</span>
                        <span class="capacity-value" id="cap-sell">-</span>
                    </div>
                    <div class="capacity-row" style="margin-top: 0.25rem;">
                        <span class="capacity-label">Gói vay:</span>
                        <span class="capacity-value" id="cap-pkg" style="color:#aaa;">-</span>
                    </div>
                    <div class="override-check" id="override-row">
                        <input type="checkbox" id="override-confirm">
                        <label for="override-confirm">Vẫn tiếp tục dù vượt sức mua/bán (Không khuyến nghị)</label>
                    </div>
                </div>
            </div>

            <div class="form-group" id="group-time" style="display: none;">
                <label>Thời gian thực hiện (HH:MM:SS)</label>
                <input type="text" id="cfg-time" placeholder="Ví dụ: 14:30:00">
            </div>

            <div id="cfg-error-msg" style="color: var(--sell); font-size: 0.85rem; display: none; margin-top: 0.5rem; font-weight: bold;"></div>

            <button class="btn btn-primary" id="add-cfg-btn" onclick="addConfigItem()" style="margin-top: 0.5rem;">Thêm Cấu hình</button>
        </div>

        <!-- Right Pane: Tables -->
        <div class="card" style="overflow: hidden;">
            <h2>Điều khiển Engine</h2>
            <div class="engine-controls">
                <input type="text" id="otp-code" placeholder="Mã Smart OTP (6 số)" style="flex: 1;" maxlength="6">
                <button class="btn btn-primary" id="start-engine-btn" onclick="startEngine()">🚀 Chạy Engine</button>
                <button class="btn btn-danger" id="stop-engine-btn" onclick="stopEngine()" style="display: none;">⏹️ Dừng</button>
            </div>

            <h2 style="margin-top: 1rem;">Cấu hình Đã Tạo</h2>
            <div class="table-container" style="max-height: 250px;">
                <table>
                    <thead>
                        <tr>
                            <th>Mã</th>
                            <th>Chế độ</th>
                            <th>Loại</th>
                            <th>Khớp</th>
                            <th>Khối lượng</th>
                            <th>Giá</th>
                            <th>Ngưỡng</th>
                            <th>Thời gian</th>
                            <th>Thao tác</th>
                        </tr>
                    </thead>
                    <tbody id="config-list-rows">
                        <!-- rows injected via JS -->
                    </tbody>
                </table>
            </div>

            <h2 style="margin-top: 1rem;">Bảng Theo Dõi Thời Gian Thực</h2>
            <div class="table-container" style="flex-grow: 1; min-height: 200px;">
                <table>
                    <thead>
                        <tr>
                            <th>Mã</th>
                            <th>Giá mua</th>
                            <th>KL mua</th>
                            <th>Giá bán</th>
                            <th>KL bán</th>
                            <th>T hàng về</th>
                            <th>Lệnh chờ</th>
                            <th>Tín hiệu</th>
                        </tr>
                    </thead>
                    <tbody id="engine-state-rows">
                        <!-- dynamic state rows -->
                    </tbody>
                </table>
            </div>

        </div>

    </div>

    <!-- MÔ TẢ TABS -->
    <div class="card" id="desc-tab" style="display: none;">
        <div class="guide-content">
            <h2>MÔ TẢ LOGIC VÀ QUY ĐỊNH DỮ LIỆU CỦA ENGINE</h2>
            
            <h3>I. LOGIC HOẠT ĐỘNG CỦA ENGINE</h3>
            <p>Engine chạy 2 luồng kiểm tra song song cho 2 chế độ cấu hình:</p>
            
            <h4>1. Chế độ Thường (NORMAL)</h4>
            <ul>
                <li><strong>Theo dõi:</strong> Giá và khối lượng từ WebSocket thời gian thực.</li>
                <li><strong>Kích hoạt MUA:</strong> Giá Bán Rẻ Nhất (Best Offer) &lt;= Giá Mục Tiêu <strong>VÀ</strong> Khối lượng chờ bán ở mức giá đó &lt;= Ngưỡng kích hoạt.</li>
                <li><strong>Kích hoạt BÁN:</strong> Giá Mua Đắt Nhất (Best Bid) &gt;= Giá Mục Tiêu <strong>VÀ</strong> Khối lượng chờ mua ở mức giá đó &lt;= Ngưỡng kích hoạt.</li>
                <li><strong>Thực thi:</strong>
                    <ul>
                        <li><strong>LO:</strong> Gửi lệnh Limit với mức giá bằng Giá Mục Tiêu.</li>
                        <li><strong>MTL:</strong> Gửi lệnh Market (giá = 0), tự động quét thanh khoản.</li>
                    </ul>
                </li>
            </ul>

            <h4>2. Chế độ Đợi T+ (TPLUS)</h4>
            <ul>
                <li><strong>Theo dõi:</strong> Quét thời gian hiện tại mỗi 0.5s so với <code>time_execute</code>.</li>
                <li><strong>Thực thi:</strong> Ngay khi thời gian hiện tại &gt;= Thời gian cài đặt:
                    <ul>
                        <li><strong>09:00 - 09:15:</strong> Đổi thành lệnh ATO (giá = 0).</li>
                        <li><strong>14:30 - 14:45:</strong> Đổi thành lệnh ATC (giá = 0).</li>
                        <li><strong>Ngoài các khung trên:</strong> Dùng đúng Loại lệnh setup. Nếu LO, gửi kèm Giá mục tiêu. Nếu MTL, gửi lệnh Market (giá = 0).</li>
                    </ul>
                </li>
            </ul>

            <h3>II. QUY ĐỊNH NHẬP DỮ LIỆU</h3>
            <ul>
                <li><strong>Khối lượng:</strong> Nhập chính xác (VD: 100, 1000). Nút "Kiểm tra sức mua / bán" tự động đối chiếu với hạn mức DNSE.</li>
                <li><strong>Giá:</strong> <strong>BẮT BUỘC</strong> dùng thang giá "Nghìn VNĐ". VD: Giá 25.500 VND nhập <code>25.5</code>. Code tự động x1000 lúc gửi lệnh.</li>
                <li><strong>Loại Khớp Lệnh:</strong> 
                    <ul>
                        <li><strong>LO:</strong> Yêu cầu nhập Giá mục tiêu.</li>
                        <li><strong>MTL:</strong> Không yêu cầu biến giá (gửi bằng 0).</li>
                    </ul>
                </li>
            </ul>
        </div>
    </div>

    <div class="card" id="guide-tab" style="display: none;">
        <div class="guide-content">
            <h2>HƯỚNG DẪN SỬ DỤNG GIAO DIỆN WEB</h2>
            
            <h3>I. CẤU HÌNH HỆ THỐNG</h3>
            <ul>
                <li><strong>API Credentials:</strong> Thêm tài khoản mới trong tab <strong>Quản Lý Tài Khoản</strong>. Hệ thống sẽ kết nối với DNSE.</li>
                <li><strong>Quản Lý:</strong> Bạn có thể tạo nhiều tài khoản cùng lúc và chạy song song.</li>
            </ul>

            <h3>II. TẠO CẤU HÌNH LỆNH</h3>
            <ul>
                <li><strong>Chế độ NORMAL:</strong> Bắt buộc nhập <em>Giá mục tiêu</em> và <em>Ngưỡng KL kích hoạt</em>. Phải click <strong>Kiểm tra sức mua / bán</strong> (nếu vượt phải tick override).</li>
                <li><strong>Chế độ TPLUS:</strong> Bắt buộc nhập <em>Thời gian thực hiện</em>. Ô nhập Giá chỉ hiện nếu Loại Khớp Lệnh là <strong>LO</strong>.</li>
            </ul>

            <h3>III. VẬN HÀNH ENGINE</h3>
            <ul>
                <li>Chọn tài khoản trên menu thả xuống ở thanh công cụ.</li>
                <li>Nhập Smart OTP -> Click <strong>Chạy Engine</strong>. Giao diện báo RUN.</li>
                <li>Bảng thời gian thực tự động poll dữ liệu 1s/lần, thể hiện giá tốt nhất và countdown T+.</li>
            </ul>

            <h3>IV. XỬ LÝ SỰ CỐ</h3>
            <ul>
                <li><strong>API MISSING:</strong> Chưa thêm tài khoản.</li>
                <li><strong>Engine tắt ngang:</strong> Thường do OTP hết hạn hoặc Web socket đứt kết nối.</li>
                <li><strong>Lệnh bị Rejected:</strong> Do sức mua không đủ lúc trigger, hoặc truyền giá LO nằm ngoài biên độ trần/sàn. Đảm bảo check kỹ sức mua trước đó.</li>
            </ul>
        </div>
    </div>

    <script>
        const API_URL = ""; // localhost backend
        let currentAccountId = "";

        function switchTab(tabId) {
            document.getElementById("dashboard-tab").style.display = (tabId === "dashboard") ? "grid" : "none";
            document.getElementById("accounts-tab").style.display = (tabId === "accounts") ? "block" : "none";
            document.getElementById("guide-tab").style.display = (tabId === "guide") ? "block" : "none";
            document.getElementById("desc-tab").style.display = (tabId === "desc") ? "block" : "none";
            
            document.getElementById("btn-tab-dashboard").className = (tabId === "dashboard") ? "tab-btn active" : "tab-btn";
            document.getElementById("btn-tab-accounts").className = (tabId === "accounts") ? "tab-btn active" : "tab-btn";
            document.getElementById("btn-tab-guide").className = (tabId === "guide") ? "tab-btn active" : "tab-btn";
            document.getElementById("btn-tab-desc").className = (tabId === "desc") ? "tab-btn active" : "tab-btn";
        }

        async function fetchAccounts() {
            try {
                const res = await fetch(`${API_URL}/api/accounts`);
                const accounts = await res.json();
                
                const selector = document.getElementById("account-selector");
                const tbody = document.getElementById("accounts-list-rows");
                
                selector.innerHTML = '<option value="">-- Chọn Tài khoản --</option>';
                tbody.innerHTML = '';

                accounts.forEach(acc => {
                    // Selector
                    const opt = document.createElement("option");
                    opt.value = acc.id;
                    opt.text = `${acc.name} (${acc.account_no})`;
                    if (acc.id === currentAccountId) opt.selected = true;
                    selector.appendChild(opt);

                    // Table
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td><strong>${acc.name}</strong></td>
                        <td>${acc.account_no}</td>
                        <td>${acc.api_key.substring(0, 8)}...</td>
                        <td><button class="btn btn-danger btn-small" onclick="deleteAccount('${acc.id}')">Xoá</button></td>
                    `;
                    tbody.appendChild(tr);
                });

                if (accounts.length > 0 && !currentAccountId) {
                    currentAccountId = accounts[0].id;
                    selector.value = currentAccountId;
                    changeAccount();
                } else if (accounts.length === 0) {
                    currentAccountId = "";
                }
            } catch (e) { console.error(e); }
        }

        function changeAccount() {
            currentAccountId = document.getElementById("account-selector").value;
            fetchStatus();
            loadConfigs();
            resetCapacity();
        }

        async function addAccount() {
            const btn = document.getElementById("add-acc-btn");
            const name = document.getElementById("acc-name").value;
            const apiKey = document.getElementById("acc-api-key").value;
            const apiSecret = document.getElementById("acc-api-secret").value;

            if (!name || !apiKey || !apiSecret) return alert("❌ Điền đủ thông tin");
            btn.innerText = "Đang xử lý...";
            btn.disabled = true;

            try {
                const res = await fetch(`${API_URL}/api/accounts`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, api_key: apiKey, api_secret: apiSecret })
                });
                if (!res.ok) throw new Error((await res.json()).detail);
                
                document.getElementById("acc-name").value = "";
                document.getElementById("acc-api-key").value = "";
                document.getElementById("acc-api-secret").value = "";
                alert("✅ Đã thêm tài khoản thành công!");
                await fetchAccounts();
            } catch (e) {
                alert("❌ Lỗi: " + e.message);
            } finally {
                btn.innerText = "Thêm Tài Khoản";
                btn.disabled = false;
            }
        }

        async function deleteAccount(id) {
            if (!confirm("Xóa tài khoản này?")) return;
            try {
                await fetch(`${API_URL}/api/accounts/${id}`, { method: 'DELETE' });
                if (currentAccountId === id) {
                    currentAccountId = "";
                    document.getElementById("account-selector").value = "";
                }
                await fetchAccounts();
                changeAccount();
            } catch (e) { alert("❌ Lỗi xóa tài khoản"); }
        }

        async function fetchStatus() {
            if (!currentAccountId) {
                document.getElementById("engine-dot").className = "status-dot";
                document.getElementById("engine-status-text").innerText = "Chưa chọn TK";
                document.getElementById("badge-engine").innerText = "OFF";
                document.getElementById("badge-engine").className = "tab-badge";
                document.getElementById("badge-api").innerText = "API MISSING";
                document.getElementById("badge-api").className = "tab-badge warn";
                document.getElementById("start-engine-btn").style.display = "inline-flex";
                document.getElementById("stop-engine-btn").style.display = "none";
                return;
            }

            try {
                const res = await fetch(`${API_URL}/api/status/${currentAccountId}`);
                const data = await res.json();

                const dot = document.getElementById("engine-dot");
                const text = document.getElementById("engine-status-text");
                const startBtn = document.getElementById("start-engine-btn");
                const stopBtn = document.getElementById("stop-engine-btn");
                const badgeEngine = document.getElementById("badge-engine");
                const badgeApi = document.getElementById("badge-api");

                if (data.engine_running) {
                    dot.className = "status-dot active";
                    text.innerText = "Engine is Active";
                    startBtn.style.display = "none";
                    stopBtn.style.display = "inline-flex";
                    badgeEngine.innerText = "RUN";
                    badgeEngine.className = "tab-badge ok";
                } else {
                    dot.className = "status-dot";
                    text.innerText = "System Idle";
                    startBtn.style.display = "inline-flex";
                    stopBtn.style.display = "none";
                    badgeEngine.innerText = "OFF";
                    badgeEngine.className = "tab-badge";
                }

                if (data.api_valid) {
                    badgeApi.innerText = "API OK";
                    badgeApi.className = "tab-badge ok";
                } else {
                    badgeApi.innerText = "API MISSING";
                    badgeApi.className = "tab-badge warn";
                }
            } catch (e) {
                console.error(e);
            }
        }

        function toggleModeFields() {
            const mode = document.getElementById("cfg-mode").value;
            const orderType = document.getElementById("cfg-order-type").value;
            const grpPrice = document.getElementById("group-price");
            const grpThreshold = document.getElementById("group-threshold");
            const grpTime = document.getElementById("group-time");
            const grpCapacity = document.getElementById("group-capacity");

            resetCapacity();

            if (mode === "TPLUS") {
                grpPrice.style.display = (orderType === "LO") ? "flex" : "none";
                grpThreshold.style.display = "none";
                grpTime.style.display = "flex";
                grpCapacity.style.display = "none";
            } else {
                grpPrice.style.display = "flex";
                grpThreshold.style.display = "flex";
                grpTime.style.display = "none";
                grpCapacity.style.display = "flex";
            }
        }
        
        document.getElementById("cfg-order-type").addEventListener("change", toggleModeFields);

        // --- Capacity check state ---
        let _capacityResult = null;

        function resetCapacity() {
            _capacityResult = null;
            const panel = document.getElementById("capacity-panel");
            panel.classList.remove("visible");
            document.getElementById("cap-buy").textContent = "-";
            document.getElementById("cap-sell").textContent = "-";
            document.getElementById("cap-pkg").textContent = "-";
            document.getElementById("override-row").style.display = "none";
            document.getElementById("override-confirm").checked = false;
            ["cap-buy", "cap-sell"].forEach(id => {
                document.getElementById(id).className = "capacity-value";
            });
        }

        async function checkCapacity() {
            if (!currentAccountId) return alert("❌ Hãy chọn Tài khoản trước");
            const errDiv = document.getElementById("cfg-error-msg");
            errDiv.style.display = "none";
            errDiv.innerText = "";

            const symbol = document.getElementById("cfg-symbol").value.trim();
            const priceRaw = document.getElementById("cfg-price").value;
            const side = document.getElementById("cfg-side").value;

            if (!symbol || !priceRaw) {
                errDiv.innerText = "❌ Nhập Mã Cổ Phiếu và Giá mục tiêu trước khi kiểm tra";
                errDiv.style.display = "block";
                return;
            }

            const btn = document.getElementById("check-capacity-btn");
            const origText = btn.innerText;
            btn.innerText = "Đang kiểm tra...";
            btn.disabled = true;
            resetCapacity();

            try {
                const res = await fetch(`${API_URL}/api/capacity`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ account_id: currentAccountId, symbol, price: parseFloat(priceRaw), order_side: side })
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || "Lỗi không xác định");
                }

                const data = await res.json();
                _capacityResult = data;
                const qty = parseInt(document.getElementById("cfg-qty").value) || 0;

                const panel = document.getElementById("capacity-panel");
                panel.classList.add("visible");

                const buyEl  = document.getElementById("cap-buy");
                const sellEl = document.getElementById("cap-sell");

                buyEl.textContent  = data.qmax_buy.toLocaleString();
                sellEl.textContent = data.qmax_sell.toLocaleString();
                document.getElementById("cap-pkg").textContent = data.loan_package_id;

                let overLimit = false;
                if (side === "BUY") {
                    if (qty > 0 && qty > data.qmax_buy) {
                        buyEl.className = "capacity-value capacity-error";
                        overLimit = true;
                    } else {
                        buyEl.className = "capacity-value capacity-ok";
                    }
                    sellEl.className = "capacity-value";
                } else {
                    if (qty > 0 && qty > data.qmax_sell) {
                        sellEl.className = "capacity-value capacity-error";
                        overLimit = true;
                    } else {
                        sellEl.className = "capacity-value capacity-ok";
                    }
                    buyEl.className = "capacity-value";
                }

                const overrideRow = document.getElementById("override-row");
                overrideRow.style.display = overLimit ? "flex" : "none";

                if (!overLimit) {
                    errDiv.style.color = "var(--buy)";
                    errDiv.innerText = "✅ Sức mua/bán hợp lệ — có thể thêm cấu hình";
                    errDiv.style.display = "block";
                    setTimeout(() => { errDiv.style.display = "none"; errDiv.style.color = "var(--sell)"; }, 3000);
                }

            } catch (e) {
                errDiv.style.color = "var(--sell)";
                errDiv.innerText = "❌ " + e.message;
                errDiv.style.display = "block";
            } finally {
                btn.innerText = origText;
                btn.disabled = false;
            }
        }

        async function loadConfigs() {
            const rows = document.getElementById("config-list-rows");
            rows.innerHTML = "";

            if (!currentAccountId) {
                rows.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted);">Hãy chọn Tài khoản</td></tr>`;
                return;
            }

            try {
                const res = await fetch(`${API_URL}/api/config/${currentAccountId}`);
                const data = await res.json();

                if (data.length === 0) {
                    rows.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted);">Chưa có cấu hình nào</td></tr>`;
                    return;
                }

                data.forEach((c, i) => {
                    const tr = document.createElement("tr");
                    const badge = c.order_side === "BUY" ? "badge-buy" : "badge-sell";
                    const sideVn = c.order_side === "BUY" ? "MUA" : "BÁN";

                    tr.innerHTML = `
                        <td><strong>${c.symbol}</strong></td>
                        <td>${c.mode}</td>
                        <td><span class="${badge}">${sideVn}</span></td>
                        <td><small>${c.order_type || 'MTL'}</small></td>
                        <td>${c.quantity}</td>
                        <td>${c.price ? c.price.toFixed(2) : '-'}</td>
                        <td>${c.qty_threshold || '-'}</td>
                        <td>${c.time_execute || '-'}</td>
                        <td><button class="btn btn-danger btn-small" onclick="deleteConfig(${i})">Xoá</button></td>
                    `;
                    rows.appendChild(tr);
                });
            } catch (e) {
                console.error(e);
            }
        }

        async function addConfigItem() {
            if (!currentAccountId) return alert("❌ Hãy chọn Tài khoản trước");
            
            const btn = document.getElementById("add-cfg-btn");
            const errDiv = document.getElementById("cfg-error-msg");
            errDiv.style.display = "none";
            errDiv.innerText = "";
            
            const symbol = document.getElementById("cfg-symbol").value.trim();
            const mode = document.getElementById("cfg-mode").value;
            const side = document.getElementById("cfg-side").value;
            const orderType = document.getElementById("cfg-order-type").value;
            const qty = parseInt(document.getElementById("cfg-qty").value);

            const priceInput = document.getElementById("cfg-price").value;
            const price = priceInput ? parseFloat(priceInput) : null;

            const thresholdInput = document.getElementById("cfg-threshold").value;
            const threshold = thresholdInput ? parseInt(thresholdInput) : null;

            const time = document.getElementById("cfg-time").value.trim();

            if (!symbol || isNaN(qty) || qty <= 0) {
                errDiv.innerText = "❌ Vui lòng điền đúng Mã Cổ Phiếu và Khối lượng (>0)";
                errDiv.style.display = "block";
                return;
            }

            if (mode === "NORMAL") {
                if (price === null || threshold === null) {
                    errDiv.innerText = "❌ Chế độ Thường yêu cầu điền Giá mục tiêu và Ngưỡng KL kích hoạt";
                    errDiv.style.display = "block";
                    return;
                }
                if (!_capacityResult) {
                    errDiv.innerText = "❌ Vui lòng bấm 'Kiểm tra sức mua / bán' trước khi lưu";
                    errDiv.style.display = "block";
                    return;
                }
                const overLimit = side === "BUY"
                    ? qty > _capacityResult.qmax_buy
                    : qty > _capacityResult.qmax_sell;
                if (overLimit && !document.getElementById("override-confirm").checked) {
                    errDiv.innerText = "⚠️ Khối lượng vượt giới hạn — tick xác nhận ở ô bên trên để tiếp tục";
                    errDiv.style.display = "block";
                    return;
                }
            }

            if (orderType === "LO" && price === null) {
                errDiv.innerText = "❌ Lệnh LO yêu cầu phải nhập Giá mục tiêu";
                errDiv.style.display = "block";
                return;
            }

            if (mode === "TPLUS" && !time) {
                errDiv.innerText = "❌ Chế độ T+ yêu cầu điền Thời gian thực hiện (HH:MM:SS)";
                errDiv.style.display = "block";
                return;
            }

            let statusLabel = "✅ Cấu hình hợp lệ";
            if (mode === "TPLUS") {
                statusLabel = "⏳ Chờ T+";
            } else if (_capacityResult) {
                const overLimit = side === "BUY"
                    ? qty > _capacityResult.qmax_buy
                    : qty > _capacityResult.qmax_sell;
                if (overLimit) statusLabel = "⚠️ Vượt giới hạn";
            }

            const payload = {
                account_id: currentAccountId,
                symbol,
                mode,
                order_side: side,
                quantity: qty,
                price: price,
                qty_threshold: threshold,
                order_type: orderType,
                time_execute: time || null,
                loan_package_id: _capacityResult ? _capacityResult.loan_package_id : null,
                status: statusLabel
            };

            const originalText = btn.innerText;
            btn.innerText = "Đang lưu...";
            btn.disabled = true;

            try {
                const res = await fetch(`${API_URL}/api/config`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (!res.ok) {
                    const err = await res.json();
                    let errMsg = err.detail;
                    if (Array.isArray(errMsg)) {
                        errMsg = errMsg.map(e => `${e.loc ? e.loc.join('.') : ''}: ${e.msg}`).join("\\n");
                    }
                    throw new Error(errMsg || "Lỗi không xác định từ Server");
                }
                loadConfigs();
                document.getElementById("cfg-symbol").value = "";
                document.getElementById("cfg-qty").value = "";
                document.getElementById("cfg-price").value = "";
                document.getElementById("cfg-threshold").value = "";
                document.getElementById("cfg-time").value = "";
                resetCapacity();
                errDiv.style.color = "var(--buy)";
                errDiv.innerText = "✅ Thêm thành công!";
                errDiv.style.display = "block";
                setTimeout(() => { errDiv.style.display = "none"; errDiv.style.color = "var(--sell)"; }, 3000);
            } catch (e) {
                errDiv.innerText = "❌ " + e.message;
                errDiv.style.display = "block";
            } finally {
                btn.innerText = originalText;
                btn.disabled = false;
            }
        }

        async function deleteConfig(idx) {
            if (!currentAccountId) return;
            try {
                await fetch(`${API_URL}/api/config/${currentAccountId}/${idx}`, { method: 'DELETE' });
                loadConfigs();
            } catch (e) {
                console.error(e);
            }
        }

        async function startEngine() {
            if (!currentAccountId) return alert("❌ Hãy chọn Tài khoản trước");
            const otp = document.getElementById("otp-code").value.trim();
            if (!otp) return alert("❌ Nhập mã Smart OTP để kích hoạt giao dịch!");

            const btn = document.getElementById("start-engine-btn");
            btn.innerText = "Đang chạy...";
            btn.disabled = true;

            try {
                const res = await fetch(`${API_URL}/api/engine/start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ account_id: currentAccountId, otp })
                });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail);
                }
                document.getElementById("otp-code").value = "";
                fetchStatus();
            } catch (e) {
                alert("❌ Lỗi kích hoạt: " + e.message);
            } finally {
                btn.innerText = "🚀 Chạy Engine";
                btn.disabled = false;
            }
        }

        async function stopEngine() {
            if (!currentAccountId) return;
            try {
                await fetch(`${API_URL}/api/engine/stop`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ account_id: currentAccountId })
                });
                fetchStatus();
            } catch (e) {
                console.error(e);
            }
        }

        async function pollEngineState() {
            const rows = document.getElementById("engine-state-rows");
            if (!currentAccountId) {
                rows.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">Vui lòng chọn tài khoản</td></tr>`;
                return;
            }

            try {
                const res = await fetch(`${API_URL}/api/engine/state/${currentAccountId}`);
                const state = await res.json();

                if (!state.running || state.data.length === 0) {
                    rows.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">Chưa có dữ liệu (Engine đang tắt)</td></tr>`;
                    return;
                }

                rows.innerHTML = "";
                state.data.forEach(d => {
                    const tr = document.createElement("tr");

                    const bid_px = d.bid_px ? parseFloat(d.bid_px).toFixed(2) : '-';
                    const bid_qty = d.bid_qty ? Math.floor(d.bid_qty) : '-';
                    const ask_px = d.ask_px ? parseFloat(d.ask_px).toFixed(2) : '-';
                    const ask_qty = d.ask_qty ? Math.floor(d.ask_qty) : '-';

                    tr.innerHTML = `
                        <td><strong>${d.symbol}</strong></td>
                        <td style="color: var(--buy);">${bid_px}</td>
                        <td style="color: var(--buy);">${bid_qty}</td>
                        <td style="color: var(--sell);">${ask_px}</td>
                        <td style="color: var(--sell);">${ask_qty}</td>
                        <td>${d.tplus}</td>
                        <td>${d.pending}</td>
                        <td>${d.signal}</td>
                    `;
                    rows.appendChild(tr);
                });

            } catch (e) {
                console.error(e);
            }
        }

        // Init
        fetchAccounts();

        // Intervals
        setInterval(fetchStatus, 5000);
        setInterval(pollEngineState, 1000);

    </script>
</body>

</html>
"""

with open("/Users/leoinv/Documents/CODE/Execute_engine_VNSTOCK/static/index.html", "w") as f:
    f.write(html_content)
print("Updated index.html")
