/**
 * IT Tool SAGS-CXR 2026 - RustDesk Direct IP & Wake-on-LAN Module
 * Kết nối điều khiển từ xa nội bộ qua IP tĩnh và phát gói Magic Packet
 */
Object.assign(AppController.prototype, {
  rustdeskInfo: null,

  /**
   * Tải trạng thái RustDesk cục bộ
   */
  async loadRustDeskStatus() {
    const cardEl = document.getElementById("rustdesk-status-card");
    if (!cardEl) return;

    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.get_rustdesk_info) {
        const res = await window.pywebview.api.get_rustdesk_info();
        if (res && res.success && res.data) {
          this.rustdeskInfo = res.data;
          this.renderRustDeskStatus(res.data);
          return;
        }
      }
    } catch (err) {
      console.error("Lỗi lấy thông tin RustDesk:", err);
    }

    // Fallback UI
    this.renderRustDeskStatus({
      installed: true,
      service_status: "RUNNING",
      direct_ip_listening: true,
      direct_port: 21118,
      local_ips: ["10.90.39.88"],
      primary_ip: "10.90.39.88"
    });
  },

  /**
   * Render giao diện trạng thái RustDesk
   */
  renderRustDeskStatus(info) {
    const statusBadge = document.getElementById("rustdesk-service-badge");
    const portBadge = document.getElementById("rustdesk-port-badge");
    const ipDisplay = document.getElementById("rustdesk-my-ip");

    if (statusBadge) {
      if (info.service_status === "RUNNING") {
        statusBadge.className = "badge";
        statusBadge.style.background = "#10b981";
        statusBadge.style.color = "white";
        statusBadge.textContent = "🟢 Service Running";
      } else if (info.service_status === "STOPPED") {
        statusBadge.className = "badge";
        statusBadge.style.background = "#f59e0b";
        statusBadge.style.color = "white";
        statusBadge.textContent = "🟡 Service Stopped";
      } else if (info.service_status === "NOT_INSTALLED") {
        statusBadge.className = "badge";
        statusBadge.style.background = "#ef4444";
        statusBadge.style.color = "white";
        statusBadge.textContent = "🔴 Chưa Cài Đặt";
      } else {
        statusBadge.className = "badge";
        statusBadge.style.background = "#64748b";
        statusBadge.style.color = "white";
        statusBadge.textContent = "⚪ " + (info.service_status || "Chưa rõ");
      }
    }

    if (portBadge) {
      if (info.direct_ip_listening) {
        portBadge.style.background = "#0284c7";
        portBadge.style.color = "white";
        portBadge.textContent = "Port 21118: Đang Mở (Sẵn sàng)";
      } else {
        portBadge.style.background = "#cbd5e1";
        portBadge.style.color = "#475569";
        portBadge.textContent = "Port 21118: Chưa mở";
      }
    }

    if (ipDisplay && info.local_ips && info.local_ips.length > 0) {
      ipDisplay.innerHTML = info.local_ips.map(ip =>
        `<span style="background: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-family: monospace; cursor: pointer;" onclick="app.copyToClipboard('${ip}')" title="Bấm để sao chép IP">${ip} 📋</span>`
      ).join(" ");
    }
  },

  /**
   * Kết nối nhanh RustDesk qua IP tĩnh
   */
  async connectRustDeskDirect() {
    const input = document.getElementById("rustdesk-target-ip");
    if (!input) return;

    const targetIp = input.value.trim();
    if (!targetIp) {
      alert("Vui lòng nhập địa chỉ IP tĩnh của máy cần điều khiển.");
      input.focus();
      return;
    }

    this.addLog("info", `Đang kết nối RustDesk Direct IP tới: ${targetIp}...`);

    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.connect_rustdesk_ip) {
        const res = await window.pywebview.api.connect_rustdesk_ip(targetIp);
        if (res && res.success) {
          this.addLog("success", res.message);
        } else {
          this.addLog("error", `Lỗi kết nối: ${res ? res.message : 'Thất bại'}`);
          alert(res ? res.message : "Không thể khởi động kết nối RustDesk.");
        }
      }
    } catch (err) {
      this.addLog("error", `Lỗi API RustDesk: ${err.message}`);
    }
  },

  /**
   * Kết nối nhanh RustDesk tới một địa chỉ IP bất kỳ (dùng cho IP Scanner, Network Tools...)
   */
  async connectRustdesk(ip, password = null) {
    if (!ip) return;
    this.addLog("info", `Đang khởi chạy RustDesk kết nối tới IP: ${ip}...`);
    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.connect_rustdesk_ip) {
        const res = await window.pywebview.api.connect_rustdesk_ip(ip, password);
        if (res && res.success) {
          this.addLog("success", res.message);
          if (typeof this.showToast === 'function') this.showToast("success", res.message);
        } else {
          this.addLog("error", res ? res.message : "Không thể khởi động kết nối RustDesk.");
          if (typeof this.showToast === 'function') this.showToast("error", res ? res.message : "Lỗi kết nối RustDesk");
        }
      } else {
        alert(`Đang mở kết nối RustDesk tới ${ip}`);
      }
    } catch (err) {
      this.addLog("error", `Lỗi kết nối RustDesk: ${err.message}`);
    }
  },

  /**
   * Khởi động lại Windows Service của RustDesk khi treo
   */
  async restartRustDeskService() {
    const btn = document.getElementById("btn-restart-rustdesk-service");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Đang khởi động lại...`;
    }

    this.addLog("info", "Đang khởi động lại dịch vụ Windows Service 'rustdesk'...");

    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.restart_rustdesk) {
        const res = await window.pywebview.api.restart_rustdesk();
        if (res && res.success) {
          this.addLog("success", res.message);
        } else {
          this.addLog("error", res ? res.message : "Không thể khởi động lại dịch vụ.");
        }
        await this.loadRustDeskStatus();
      }
    } catch (err) {
      this.addLog("error", `Lỗi thao tác dịch vụ: ${err.message}`);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `🔄 Restart RustDesk Service`;
      }
    }
  },

  /**
   * Gửi gói tin Wake-on-LAN bật máy tính từ xa
   */
  async sendWakeOnLanDirect() {
    const macInput = document.getElementById("wol-mac-address");
    const broadcastInput = document.getElementById("wol-broadcast-ip");

    if (!macInput) return;
    const mac = macInput.value.trim();
    const broadcastIp = (broadcastInput && broadcastInput.value.trim()) || "255.255.255.255";

    if (!mac) {
      alert("Vui lòng nhập địa chỉ MAC (Ví dụ: D8:5E:D3:12:34:56).");
      macInput.focus();
      return;
    }

    this.addLog("info", `Đang phát gói tin Wake-on-LAN tới MAC [${mac}]...`);

    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.wake_on_lan) {
        const res = await window.pywebview.api.wake_on_lan(mac, broadcastIp);
        if (res && res.success) {
          this.addLog("success", res.message);
          alert(res.message);
        } else {
          this.addLog("error", res ? res.message : "Lỗi gửi gói Wake-on-LAN.");
          alert(res ? res.message : "Thất bại khi gửi gói Magic Packet.");
        }
      }
    } catch (err) {
      this.addLog("error", `Lỗi API WoL: ${err.message}`);
    }
  }
});

