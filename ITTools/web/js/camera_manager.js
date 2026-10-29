/**
 * IT Tool SAGS-CXR 2026 - Camera IP Manager Module
 * Quản lý, giám sát và chẩn đoán Camera IP trong mạng LAN
 */
Object.assign(AppController.prototype, {
  currentCameras: [],
  cameraScanResults: [],

  /**
   * Tải danh sách Camera từ cấu hình
   */
  async loadCameraList() {
    const tbody = document.getElementById("camera-table-body");
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted"><span class="spinner-border spinner-border-sm"></span> Đang nạp danh sách Camera IP...</td></tr>`;

    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.get_camera_list) {
        const res = await window.pywebview.api.get_camera_list();
        if (res && res.success && Array.isArray(res.cameras)) {
          this.currentCameras = res.cameras;
          this.renderCameraTable(this.currentCameras);
          this.updateCameraSummary();
          return;
        }
      }
    } catch (err) {
      console.error("Lỗi nạp danh sách camera:", err);
    }

    // Mock data fallback
    this.currentCameras = [
      { id: "cam-01", name: "Khu Vực Soi Chiếu An Ninh A", ip: "10.90.39.201", port_web: 80, port_rtsp: 554, location: "Tầng 1 - Ga Đi Quốc Nội", notes: "Hikvision 4MP" },
      { id: "cam-02", name: "Băng Chuyền Trả Hành Lý 1", ip: "10.90.39.202", port_web: 80, port_rtsp: 554, location: "Tầng Trệt - Ga Đến", notes: "Dahua IR" },
      { id: "cam-03", name: "Cửa Ra Tàu Bay (Gate 1)", ip: "10.90.39.203", port_web: 80, port_rtsp: 554, location: "Phòng Chờ Cách Ly", notes: "Uniview Dome" }
    ];
    this.renderCameraTable(this.currentCameras);
    this.updateCameraSummary();
  },

  /**
   * Render bảng danh sách Camera
   */
  renderCameraTable(cameras) {
    const tbody = document.getElementById("camera-table-body");
    if (!tbody) return;

    if (!cameras || cameras.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Chưa có camera nào trong danh sách. Bấm <strong>"➕ Thêm Camera"</strong> hoặc <strong>"🔍 Dò Tìm Camera LAN"</strong> để thêm mới.</td></tr>`;
      return;
    }

    tbody.innerHTML = cameras.map((cam, idx) => {
      const statusBadge = cam.checked
        ? (cam.is_online
            ? `<span class="badge" style="background: #10b981; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">🟢 Online (${cam.latency_ms} ms)</span>`
            : `<span class="badge" style="background: #ef4444; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">🔴 Mất Tín Hiệu</span>`)
        : `<span class="badge" style="background: #94a3b8; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">⚪ Chưa kiểm tra</span>`;

      const rtspBadge = cam.checked && cam.rtsp_open
        ? `<span title="Port RTSP 554 mở" style="color: #0284c7; font-weight: 600; font-size: 11px;">RTSP: 554 ✓</span>`
        : `<span style="color: #64748b; font-size: 11px;">RTSP: ${cam.port_rtsp || 554}</span>`;

      return `
        <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.15s;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='white'">
          <td class="text-center" style="padding: 10px; font-weight: 600; color: #64748b;">${idx + 1}</td>
          <td style="padding: 10px;">
            <div style="font-weight: 700; color: #1e293b; font-size: 13px;">${this.escapeHtml(cam.name)}</div>
            <div style="font-size: 11px; color: #64748b;">📍 ${this.escapeHtml(cam.location || 'Chưa đặt vị trí')} ${cam.notes ? `• ${this.escapeHtml(cam.notes)}` : ''}</div>
          </td>
          <td style="padding: 10px; font-family: monospace; font-weight: 700; color: #0284c7; font-size: 13px;">
            ${this.escapeHtml(cam.ip)}
          </td>
          <td style="padding: 10px;">
            <div>Web: <code style="background:#e2e8f0; padding:1px 4px; border-radius:3px;">${cam.port_web || 80}</code></div>
            <div>${rtspBadge}</div>
          </td>
          <td style="padding: 10px;">
            ${statusBadge}
          </td>
          <td style="padding: 10px; text-align: right; white-space: nowrap;">
            <button class="btn btn-sm btn-sky-outline" style="padding: 3px 8px; font-size: 12px; margin-right: 4px;" onclick="app.openCameraWeb('${cam.ip}', ${cam.port_web || 80})" title="Mở trang Web Admin">
              🌐 Web
            </button>
            <button class="btn btn-sm btn-slate-light" style="padding: 3px 8px; font-size: 12px; margin-right: 4px;" onclick="app.editCameraModal('${cam.id}')" title="Sửa thông tin">
              ✏️
            </button>
            <button class="btn btn-sm btn-rose-outline" style="padding: 3px 8px; font-size: 12px;" onclick="app.deleteCamera('${cam.id}')" title="Xóa camera">
              🗑️
            </button>
          </td>
        </tr>
      `;
    }).join("");
  },

  /**
   * Cập nhật thông số tóm tắt camera
   */
  updateCameraSummary() {
    const totalEl = document.getElementById("camera-count-total");
    const onlineEl = document.getElementById("camera-count-online");
    const offlineEl = document.getElementById("camera-count-offline");

    const total = this.currentCameras.length;
    let online = 0;
    let offline = 0;

    this.currentCameras.forEach(c => {
      if (c.checked) {
        if (c.is_online) online++;
        else offline++;
      }
    });

    if (totalEl) totalEl.textContent = total;
    if (onlineEl) onlineEl.textContent = online;
    if (offlineEl) offlineEl.textContent = offline;
  },

  /**
   * Ping kiểm tra trực tiếp toàn bộ Camera
   */
  async pingAllCameras() {
    const btn = document.getElementById("btn-ping-all-cameras");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Đang kiểm tra...`;
    }
    this.addLog("info", "Đang kiểm tra kết nối hàng loạt toàn bộ Camera IP...");

    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.ping_cameras) {
        const res = await window.pywebview.api.ping_cameras();
        if (res && res.success && Array.isArray(res.results)) {
          const resMap = {};
          res.results.forEach(r => { resMap[r.id] = r; });

          this.currentCameras = this.currentCameras.map(cam => {
            const check = resMap[cam.id];
            if (check) {
              return { ...cam, checked: true, is_online: check.is_online, latency_ms: check.latency_ms, rtsp_open: check.rtsp_open, web_open: check.web_open };
            }
            return cam;
          });

          this.renderCameraTable(this.currentCameras);
          this.updateCameraSummary();
          this.addLog("success", `Hoàn tất kiểm tra: ${res.results.filter(r=>r.is_online).length}/${res.results.length} camera đang hoạt động bình thường.`);
        }
      }
    } catch (err) {
      this.addLog("error", `Lỗi ping camera: ${err.message}`);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `⚡ Kiểm Tra Tất Cả (Ping All)`;
      }
    }
  },

  /**
   * Mở giao diện Web quản trị Camera
   */
  async openCameraWeb(ip, port) {
    this.addLog("info", `Mở giao diện Web camera: http://${ip}:${port}`);
    if (window.pywebview && window.pywebview.api && window.pywebview.api.open_camera_web) {
      await window.pywebview.api.open_camera_web(ip, port);
    } else {
      window.open(`http://${ip}:${port}`, "_blank");
    }
  },

  /**
   * Mở Modal thêm Camera mới
   */
  showAddCameraModal() {
    document.getElementById("modal-camera-id").value = "";
    document.getElementById("modal-camera-name").value = "";
    document.getElementById("modal-camera-ip").value = "";
    document.getElementById("modal-camera-port-web").value = "80";
    document.getElementById("modal-camera-port-rtsp").value = "554";
    document.getElementById("modal-camera-location").value = "";
    document.getElementById("modal-camera-notes").value = "";
    document.getElementById("modal-camera-title").textContent = "➕ Thêm Camera IP Mới";

    const modal = document.getElementById("modal-camera-form");
    if (modal) modal.style.display = "flex";
  },

  /**
   * Mở Modal sửa Camera
   */
  editCameraModal(id) {
    const cam = this.currentCameras.find(c => c.id === id);
    if (!cam) return;

    document.getElementById("modal-camera-id").value = cam.id;
    document.getElementById("modal-camera-name").value = cam.name || "";
    document.getElementById("modal-camera-ip").value = cam.ip || "";
    document.getElementById("modal-camera-port-web").value = cam.port_web || 80;
    document.getElementById("modal-camera-port-rtsp").value = cam.port_rtsp || 554;
    document.getElementById("modal-camera-location").value = cam.location || "";
    document.getElementById("modal-camera-notes").value = cam.notes || "";
    document.getElementById("modal-camera-title").textContent = "✏️ Chỉnh Sửa Thông Tin Camera";

    const modal = document.getElementById("modal-camera-form");
    if (modal) modal.style.display = "flex";
  },

  /**
   * Đóng Modal Camera
   */
  closeCameraModal() {
    const modal = document.getElementById("modal-camera-form");
    if (modal) modal.style.display = "none";
  },

  /**
   * Lưu dữ liệu từ Modal Camera
   */
  async saveCameraFromModal() {
    const id = document.getElementById("modal-camera-id").value.trim();
    const name = document.getElementById("modal-camera-name").value.trim();
    const ip = document.getElementById("modal-camera-ip").value.trim();
    const port_web = parseInt(document.getElementById("modal-camera-port-web").value) || 80;
    const port_rtsp = parseInt(document.getElementById("modal-camera-port-rtsp").value) || 554;
    const location = document.getElementById("modal-camera-location").value.trim();
    const notes = document.getElementById("modal-camera-notes").value.trim();

    if (!name || !ip) {
      alert("Vui lòng nhập Tên Camera và Địa chỉ IP.");
      return;
    }

    if (id) {
      // Edit
      const idx = this.currentCameras.findIndex(c => c.id === id);
      if (idx !== -1) {
        this.currentCameras[idx] = { ...this.currentCameras[idx], name, ip, port_web, port_rtsp, location, notes };
      }
    } else {
      // Add new
      const newId = `cam-${Date.now().toString().slice(-4)}`;
      this.currentCameras.push({ id: newId, name, ip, port_web, port_rtsp, location, notes });
    }

    this.closeCameraModal();
    this.renderCameraTable(this.currentCameras);
    this.updateCameraSummary();

    // Lưu vào file JSON cấu hình
    if (window.pywebview && window.pywebview.api && window.pywebview.api.save_camera_list) {
      const res = await window.pywebview.api.save_camera_list(this.currentCameras);
      if (res && res.success) {
        this.addLog("success", `Đã lưu danh sách camera thành công.`);
      } else {
        this.addLog("error", `Lỗi lưu camera: ${res ? res.message : ''}`);
      }
    }
  },

  /**
   * Xóa một camera khỏi danh sách
   */
  async deleteCamera(id) {
    const cam = this.currentCameras.find(c => c.id === id);
    if (!cam) return;

    if (!confirm(`Bạn có chắc chắn muốn xóa camera "${cam.name}" (${cam.ip})?`)) {
      return;
    }

    this.currentCameras = this.currentCameras.filter(c => c.id !== id);
    this.renderCameraTable(this.currentCameras);
    this.updateCameraSummary();

    if (window.pywebview && window.pywebview.api && window.pywebview.api.save_camera_list) {
      await window.pywebview.api.save_camera_list(this.currentCameras);
      this.addLog("info", `Đã xóa camera: ${cam.name}`);
    }
  },

  /**
   * Dò tìm Camera mới trong dải mạng
   */
  async scanCameraRange() {
    const subnetInput = document.getElementById("camera-scan-subnet");
    const startInput = document.getElementById("camera-scan-start");
    const endInput = document.getElementById("camera-scan-end");
    const resultsContainer = document.getElementById("camera-scan-results");

    if (!subnetInput || !resultsContainer) return;

    const subnet = subnetInput.value.trim() || "10.90.39";
    const start = parseInt(startInput.value) || 1;
    const end = parseInt(endInput.value) || 50;

    const btn = document.getElementById("btn-start-camera-scan");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Đang dò tìm camera...`;
    }

    resultsContainer.innerHTML = `<div class="text-center py-3 text-muted"><span class="spinner-border spinner-border-sm"></span> Đang quét các cổng RTSP 554, Web 80, SDK 8000 trong dải ${subnet}.${start}-${end}...</div>`;
    this.addLog("info", `Bắt đầu quét dải camera IP: ${subnet}.${start} - ${subnet}.${end}`);

    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.scan_cameras_lan) {
        const res = await window.pywebview.api.scan_cameras_lan(subnet, start, end);
        if (res && res.success) {
          this.cameraScanResults = res.devices || [];
          this.renderCameraScanResults(this.cameraScanResults);
          this.addLog("success", `Dò tìm hoàn tất: Tìm thấy ${res.count} thiết bị có dịch vụ camera.`);
        } else {
          resultsContainer.innerHTML = `<div class="text-danger py-2">Lỗi: ${res ? res.message : 'Không quét được'}</div>`;
        }
      }
    } catch (err) {
      resultsContainer.innerHTML = `<div class="text-danger py-2">Lỗi kết nối: ${err.message}</div>`;
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `🔍 Bắt Đầu Quét Camera`;
      }
    }
  },

  /**
   * Render kết quả dò tìm camera
   */
  renderCameraScanResults(devices) {
    const container = document.getElementById("camera-scan-results");
    if (!container) return;

    if (!devices || devices.length === 0) {
      container.innerHTML = `<div class="text-muted py-3 text-center">Không tìm thấy thiết bị mở cổng camera nào trong dải IP này.</div>`;
      return;
    }

    container.innerHTML = `
      <div style="font-weight: 700; color: #0284c7; margin-bottom: 8px;">Tìm thấy ${devices.length} Camera IP tiềm năng:</div>
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px;">
        ${devices.map(d => `
          <div style="background: white; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px; display: flex; justify-content: space-between; align-items: center;">
            <div>
              <div style="font-weight: 700; color: #0f172a; font-family: monospace;">${d.ip}</div>
              <div style="font-size: 11px; color: #475569;">${this.escapeHtml(d.vendor_guess)}</div>
              <div style="font-size: 10px; color: #64748b;">Ports mở: ${d.ports.join(", ")}</div>
            </div>
            <button class="btn btn-sm btn-emerald-solid" style="padding: 3px 8px; font-size: 11px;" onclick="app.addScannedCamera('${d.ip}', '${this.escapeHtml(d.vendor_guess)}')">
              ➕ Thêm
            </button>
          </div>
        `).join("")}
      </div>
    `;
  },

  /**
   * Thêm camera phát hiện được vào danh sách chính
   */
  async addScannedCamera(ip, vendor) {
    const exists = this.currentCameras.some(c => c.ip === ip);
    if (exists) {
      alert(`Camera IP ${ip} đã có sẵn trong danh sách.`);
      return;
    }

    const newCam = {
      id: `cam-${Date.now().toString().slice(-4)}`,
      name: `${vendor} (${ip})`,
      ip: ip,
      port_web: 80,
      port_rtsp: 554,
      location: "Phát hiện qua quét LAN",
      notes: vendor
    };

    this.currentCameras.push(newCam);
    this.renderCameraTable(this.currentCameras);
    this.updateCameraSummary();

    if (window.pywebview && window.pywebview.api && window.pywebview.api.save_camera_list) {
      await window.pywebview.api.save_camera_list(this.currentCameras);
      this.addLog("success", `Đã thêm camera mới: ${ip}`);
    }
  }
});
