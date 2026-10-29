/**
 * IT Tool LTT 2026 - Hosts File Editor, IP Manager & IP Scanner Module
 */
Object.assign(AppController.prototype, {
  async loadHosts() {
    const txt = document.getElementById("hosts-textarea") || document.getElementById("hosts-textarea-page");
    const infoEl = document.getElementById("hosts-status-info");
    if (!txt) return;

    // Tự động đồng bộ các chỉnh sửa của người dùng vào file tạm
    if (!txt.dataset.tempSyncAttached) {
      txt.dataset.tempSyncAttached = "true";
      let syncTimer = null;
      txt.addEventListener("input", () => {
        clearTimeout(syncTimer);
        syncTimer = setTimeout(async () => {
          if (window.pywebview && window.pywebview.api && window.pywebview.api.update_hosts_temp) {
            try {
              await window.pywebview.api.update_hosts_temp(txt.value);
            } catch (e) {
              console.error("Lỗi đồng bộ file tạm:", e);
            }
          }
        }, 300);
      });
    }

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_hosts_file();
        if (res && res.success) {
          txt.value = res.content || "";
          const lines = (res.content || "").split('\n').length;
          if (infoEl) {
            infoEl.innerHTML = `
              <div style="display: flex; flex-direction: column; gap: 3px;">
                <div>📝 <span style="font-weight:600; color:#0284c7;">File tạm đang sửa:</span> <code style="color: #0284c7; background: #f0f9ff; padding: 2px 6px; border-radius: 4px; border: 1px solid #bae6fd;">${res.temp_path || 'Thư mục tạm'}</code> (${lines} dòng)</div>
                <div style="color: #64748b; font-size: 11px;">📍 Nguồn gốc hệ thống: <code>${res.path || 'C:\\Windows\\System32\\drivers\\etc\\hosts'}</code> <span style="color:#10b981; font-weight:600;">(Đã copy tự động ra file tạm)</span></div>
              </div>
            `;
          }
        } else {
          if (infoEl) infoEl.innerHTML = `<span style="color:#ef4444">❌ Lỗi đọc Hosts: ${res ? res.message : 'Unknown'}</span>`;
        }
      } catch (err) {
        console.error("Lỗi get_hosts_file:", err);
      }
    } else {
      txt.value = "# Copyright (c) 1993-2006 Microsoft Corp.\n127.0.0.1       localhost\n::1             localhost\n# Demo Mock Hosts File\n127.0.0.1       dev.local\n";
      if (infoEl) infoEl.innerHTML = `📍 File tạm: <code>%TEMP%\\IT_Tools_Hosts_Temp\\hosts</code> (MOCK mode)`;
    }
  },

  async saveHosts() {
    const txt = document.getElementById("hosts-textarea") || document.getElementById("hosts-textarea-page");
    if (!txt) return;
    const content = txt.value;
    this.addLog("info", "Đang lưu thay đổi vào File Hosts hệ thống & Flush DNS...");

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.save_hosts_file(content);
        if (res && res.success) {
          this.addLog("success", res.message);
          alert(res.message);
          this.loadHosts();
        } else {
          this.addLog("error", res ? res.message : "Lỗi lưu file Hosts");
          alert(res ? res.message : "Lỗi lưu file Hosts");
        }
      } catch (err) {
        alert(`Lỗi lưu Hosts file: ${err.message}`);
      }
    } else {
      alert("[MOCK] Đã lưu thay đổi vào File Hosts & Flush DNS!");
    }
  },

  async saveHostsAs() {
    const txt = document.getElementById("hosts-textarea") || document.getElementById("hosts-textarea-page");
    if (!txt) return;
    const content = txt.value;

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.save_hosts_as(content);
        if (res && res.success) {
          this.addLog("success", `Đã lưu file hosts ra: ${res.path}`);
          alert(res.message);
        } else if (res && !res.canceled) {
          alert(res.message || "Lỗi khi lưu file!");
        }
      } catch (err) {
        alert(`Lỗi khi lưu file: ${err.message}`);
      }
    } else {
      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "hosts";
      a.click();
      alert("[MOCK] Đã kích hoạt tải file hosts về máy!");
    }
  },

  async loadHostsFromFile() {
    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.load_hosts_from_file();
        if (res && res.success) {
          const txt = document.getElementById("hosts-textarea") || document.getElementById("hosts-textarea-page");
          if (txt) {
            txt.value = res.content || "";
            // Đồng bộ ngay nội dung mới nạp vào file tạm
            if (window.pywebview.api.update_hosts_temp) {
              await window.pywebview.api.update_hosts_temp(txt.value);
            }
            const lines = (res.content || "").split('\n').length;
            const infoEl = document.getElementById("hosts-status-info");
            if (infoEl) infoEl.innerHTML = `📍 Đã nạp từ: <code style="color: #10b981;">${res.path}</code> (${lines} dòng) - Đã đồng bộ sang file tạm`;
            this.addLog("success", `Đã nạp file từ: ${res.path}`);
          }
        }
      } catch (err) {
        console.error("Lỗi nạp file:", err);
      }
    }
  },

  async restoreHosts() {
    if (confirm("Bạn có chắc chắn muốn khôi phục File Hosts về mặc định ban đầu của Windows?\nThao tác này sẽ ghi đè nội dung file hosts gốc bằng mẫu chuẩn của Windows.")) {
      this.addLog("info", "Đang khôi phục File Hosts mặc định...");
      if (window.pywebview && window.pywebview.api) {
        try {
          const res = await window.pywebview.api.restore_hosts_default();
          if (res && res.success) {
            this.addLog("success", res.message);
            alert(res.message);
            this.loadHosts();
          } else {
            this.addLog("error", res ? res.message : "Khôi phục thất bại");
            alert(res ? res.message : "Khôi phục thất bại");
          }
        } catch (err) {
          alert(`Lỗi: ${err.message}`);
        }
      } else {
        alert("[MOCK] Đã khôi phục File Hosts mặc định!");
        this.loadHosts();
      }
    }
  },

  async openHostsFolder() {
    if (window.pywebview && window.pywebview.api) {
      try {
        await window.pywebview.api.open_hosts_folder();
      } catch (err) {
        console.error("Lỗi mở thư mục Hosts gốc:", err);
      }
    }
  },

  async openHostsTempFolder() {
    if (window.pywebview && window.pywebview.api) {
      try {
        await window.pywebview.api.open_hosts_temp_folder();
      } catch (err) {
        console.error("Lỗi mở thư mục tạm Hosts:", err);
      }
    }
  },

  appendHostsPreset(preset) {
    const txt = document.getElementById("hosts-textarea") || document.getElementById("hosts-textarea-page");
    if (!txt) return;

    let textToAdd = "";
    if (preset === 'localhost') {
      textToAdd = "\n# Localhost Mappings\n127.0.0.1       dev.local\n127.0.0.1       test.local\n";
    } else if (preset === 'block_ads') {
      textToAdd = "\n# Block Tracking & Ad Servers\n0.0.0.0         telemetry.microsoft.com\n0.0.0.0         v10.events.data.microsoft.com\n";
    } else if (preset === 'custom') {
      textToAdd = "\n# Custom Domain Block / Mapping\n127.0.0.1       example.com\n127.0.0.1       www.example.com\n";
    }

    if (textToAdd) {
      txt.value = txt.value.trimEnd() + "\n" + textToAdd;
      txt.scrollTop = txt.scrollHeight;
    }
  },

  switchIpSubtab(subtabName, btnEl) {
    if (btnEl && btnEl.parentElement) {
      const btns = btnEl.parentElement.querySelectorAll("button");
      btns.forEach(b => b.className = "btn btn-slate-light btn-sm");
      btnEl.className = "btn btn-primary btn-sm";
    }

    const panes = ["adapters", "edit", "subnet", "ipv6"];
    panes.forEach(p => {
      const pane = document.getElementById(`ip-pane-${p}`);
      if (pane) {
        pane.style.display = (p === subtabName) ? "block" : "none";
      }
    });

    if (subtabName === "adapters" || subtabName === "edit") {
      this.loadNetworkAdapters();
    } else if (subtabName === "ipv6") {
      this.loadIpv6Status();
    }
  },

  generateRandomMac(separator = ":") {
    const hex = "0123456789ABCDEF";
    const bytes = [];
    for (let i = 0; i < 6; i++) {
      let b = "";
      if (i === 0) {
        const secondChar = ["2", "6", "A", "E"][Math.floor(Math.random() * 4)];
        b = hex[Math.floor(Math.random() * 16)] + secondChar;
      } else {
        b = hex[Math.floor(Math.random() * 16)] + hex[Math.floor(Math.random() * 16)];
      }
      bytes.push(b);
    }
    return bytes.join(separator);
  },

  async loadNetworkAdapters() {
    const tbody = document.getElementById("ip-adapters-body");
    const localBadge = document.getElementById("ip-local-badge");
    const extBadge = document.getElementById("ip-ext-badge");
    const selectEl = document.getElementById("ip-edit-adapter-select");

    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">🔄 Đang quét danh sách card mạng hệ thống...</td></tr>`;
    }

    this.addLog("info", "Đang quét danh sách card mạng (Network Adapters)...");

    let data = null;
    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_network_adapters();
        if (res && res.success) {
          data = res.data;
          this.networkAdaptersData = data;
        } else {
          this.addLog("error", "Không thể lấy danh sách card mạng.");
        }
      } catch (err) {
        console.error("Lỗi get_network_adapters:", err);
        this.addLog("error", `Lỗi quét card mạng: ${err.message}`);
      }
    } else {
      data = {
        local_ip: "192.168.1.100",
        external_ip: "203.0.113.1",
        adapters: [
          { name: "Ethernet", ip: "192.168.1.100", prefix: "24", mask: "255.255.255.0", gateway: "192.168.1.1", dns: "8.8.8.8, 8.8.4.4", dns1: "8.8.8.8", dns2: "8.8.4.4", mac: this.generateRandomMac("-"), status: "Up", dhcp: "Enabled" },
          { name: "Wi-Fi", ip: "-", prefix: "-", mask: "255.255.255.0", gateway: "-", dns: "-", dns1: "", dns2: "", mac: this.generateRandomMac("-"), status: "Disconnected", dhcp: "Enabled" }
        ]
      };
      this.networkAdaptersData = data;
    }

    if (!data) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">❌ Không thể nạp thông tin card mạng. Vui lòng bấm nút 🔄 để thử lại.</td></tr>`;
      return;
    }

    if (localBadge) localBadge.innerText = data.local_ip || "N/A";
    if (extBadge) {
      extBadge.innerText = data.external_ip || "Đang lấy...";
      if (!data.external_ip || data.external_ip === "Đang lấy..." || data.external_ip === "N/A") {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.get_external_ip) {
          window.pywebview.api.get_external_ip().then(r => {
            const publicIp = (r && r.ip && typeof r.ip === 'object') ? r.ip.ip : (r ? r.ip : null);
            if (publicIp && publicIp !== "N/A" && publicIp !== "Đang lấy...") {
              extBadge.innerText = publicIp;
              if (this.networkAdaptersData) this.networkAdaptersData.external_ip = publicIp;
            }
          }).catch(e => console.log("Lỗi lấy Public IP:", e));
        }
      }
    }

    const adapters = data.adapters || [];

    if (selectEl) {
      const prevVal = selectEl.value;
      if (adapters.length > 0) {
        selectEl.innerHTML = adapters.map(a => `<option value="${this.escapeHtml(a.name)}">${this.escapeHtml(a.name)} (${this.escapeHtml(a.ip)})</option>`).join("");
        if (prevVal && adapters.some(a => a.name === prevVal)) {
          selectEl.value = prevVal;
        } else {
          // Ưu tiên chọn card mạng đang Active có IP
          const activeAdp = adapters.find(a => (a.status || '').toLowerCase() === 'up' && a.ip && a.ip !== '-');
          if (activeAdp) {
            selectEl.value = activeAdp.name;
          }
        }
      } else {
        selectEl.innerHTML = `<option value="">-- Không tìm thấy card mạng --</option>`;
      }
    }

    this.onAdapterSelectChange();

    if (!tbody) return;

    if (adapters.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Không tìm thấy card mạng nào trong hệ thống.</td></tr>`;
      return;
    }

    tbody.innerHTML = adapters.map(a => {
      const isUp = (a.status || "").toLowerCase() === "up";
      const isDhcp = (a.dhcp || "").toLowerCase() === "enabled";
      const statusBadge = isUp 
        ? `<span class="badge badge-status-enable">🟢 Active ${isDhcp ? '(DHCP)' : '(Static)'}</span>`
        : `<span class="badge badge-status-disabled">⚪ ${this.escapeHtml(a.status)}</span>`;

      return `
        <tr>
          <td style="padding: 10px;">
            <strong style="color: var(--text-main); font-size: 13px;">${this.escapeHtml(a.name)}</strong>
          </td>
          <td style="padding: 10px; font-family: monospace; color: #0284c7; font-weight: 600;">${this.escapeHtml(a.ip)}</td>
          <td style="padding: 10px; text-align: center; color: var(--text-muted);">${this.escapeHtml(a.mask || a.prefix)}</td>
          <td style="padding: 10px; font-family: monospace; color: var(--text-main);">${this.escapeHtml(a.gateway)}</td>
          <td style="padding: 10px; font-family: monospace; color: var(--text-muted); font-size: 12px;">${this.escapeHtml(a.mac)}</td>
          <td style="padding: 10px; text-align: center;">${statusBadge}</td>
          <td style="padding: 10px; text-align: right; white-space: nowrap;">
            <button class="btn btn-slate-light btn-sm" onclick="app.copyToClipboard('${this.escapeHtml(a.ip)}', 'IP')" title="Copy IP" style="padding: 2px 6px; font-size: 11px;">📋 IP</button>
            <button class="btn btn-slate-light btn-sm ml-1" onclick="app.copyToClipboard('${this.escapeHtml(a.mac)}', 'MAC')" title="Copy MAC" style="padding: 2px 6px; font-size: 11px;">📋 MAC</button>
            <button class="btn btn-slate-light btn-sm ml-1" onclick="app.copyToClipboard('${this.escapeHtml(a.name)}', 'Tên Card')" title="Copy Name" style="padding: 2px 6px; font-size: 11px;">📋 Tên</button>
          </td>
        </tr>
      `;
    }).join("");

    this.addLog("success", `Đã hiển thị ${adapters.length} card mạng.`);
  },

  onAdapterSelectChange() {
    const selectEl = document.getElementById("ip-edit-adapter-select");
    if (!selectEl) return;
    const adapterName = selectEl.value;
    if (!adapterName || !this.networkAdaptersData || !this.networkAdaptersData.adapters) return;

    const adapter = this.networkAdaptersData.adapters.find(a => a.name === adapterName);
    if (!adapter) return;

    const isDhcp = (adapter.dhcp || "").toLowerCase() === "enabled";

    const radioDhcp = document.querySelector('input[name="ip-mode-radio"][value="dhcp"]');
    const radioStatic = document.querySelector('input[name="ip-mode-radio"][value="static"]');

    if (isDhcp && radioDhcp) {
      radioDhcp.checked = true;
    } else if (!isDhcp && radioStatic) {
      radioStatic.checked = true;
    }

    this.toggleIpModeForm(isDhcp ? "dhcp" : "static");

    const inputAddr = document.getElementById("ip-input-address");
    const inputMask = document.getElementById("ip-input-mask");
    const inputGw = document.getElementById("ip-input-gateway");
    const inputDns1 = document.getElementById("ip-input-dns1");
    const inputDns2 = document.getElementById("ip-input-dns2");

    if (inputAddr) inputAddr.value = (adapter.ip && adapter.ip !== "-") ? adapter.ip : "";
    if (inputMask) inputMask.value = adapter.mask || (adapter.prefix && adapter.prefix !== "-" ? this.prefixToMask(adapter.prefix) : "255.255.255.0");
    if (inputGw) inputGw.value = (adapter.gateway && adapter.gateway !== "-") ? adapter.gateway : "";

    let d1 = adapter.dns1 || "";
    let d2 = adapter.dns2 || "";
    if (!d1 && adapter.dns && adapter.dns !== "-") {
      const parts = adapter.dns.split(',').map(s => s.trim()).filter(Boolean);
      d1 = parts[0] || "";
      d2 = parts[1] || "";
    }
    if (inputDns1) inputDns1.value = d1;
    if (inputDns2) inputDns2.value = d2;
  },

  prefixToMask(prefix) {
    const p = parseInt(prefix, 10);
    if (isNaN(p) || p < 0 || p > 32) return "255.255.255.0";
    let mask = [];
    for (let i = 0; i < 4; i++) {
      const n = Math.min(Math.max(p - i * 8, 0), 8);
      mask.push(256 - Math.pow(2, 8 - n));
    }
    return mask.join(".");
  },

  copyToClipboard(text, label = "") {
    if (!text || text === "-") return;
    const msg = `Đã sao chép ${label ? label + ': ' : ''}${text}`;
    const copyFallback = () => {
      try {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        this.addLog("info", msg);
        if (typeof this.showToast === "function") this.showToast("info", msg);
      } catch (e) {
        if (typeof this.showToast === "function") this.showToast("error", `Lỗi sao chép: ${e.message}`);
      }
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        this.addLog("info", msg);
        if (typeof this.showToast === "function") this.showToast("info", msg);
      }).catch(() => copyFallback());
    } else {
      copyFallback();
    }
  },

  toggleIpModeForm(mode) {
    const fieldsGroup = document.getElementById("ip-static-fields-group");
    if (fieldsGroup) {
      fieldsGroup.style.opacity = (mode === "dhcp") ? "0.4" : "1.0";
      fieldsGroup.style.pointerEvents = (mode === "dhcp") ? "none" : "auto";
    }
  },

  applyIpPreset(type) {
    const radioStatic = document.querySelector('input[name="ip-mode-radio"][value="static"]');
    if (radioStatic) { radioStatic.checked = true; this.toggleIpModeForm('static'); }

    const inputAddr = document.getElementById("ip-input-address");
    const inputMask = document.getElementById("ip-input-mask");
    const inputGw = document.getElementById("ip-input-gateway");
    const inputDns1 = document.getElementById("ip-input-dns1");
    const inputDns2 = document.getElementById("ip-input-dns2");

    if (type === "home") {
      if (inputAddr && !inputAddr.value) inputAddr.value = "192.168.1.100";
      if (inputMask) inputMask.value = "255.255.255.0";
      if (inputGw) inputGw.value = "192.168.1.1";
      if (inputDns1) inputDns1.value = "8.8.8.8";
      if (inputDns2) inputDns2.value = "8.8.4.4";
    } else if (type === "office") {
      if (inputAddr && !inputAddr.value) inputAddr.value = "192.168.0.100";
      if (inputMask) inputMask.value = "255.255.255.0";
      if (inputGw) inputGw.value = "192.168.0.1";
      if (inputDns1) inputDns1.value = "8.8.8.8";
      if (inputDns2) inputDns2.value = "8.8.4.4";
    } else if (type === "google") {
      if (inputDns1) inputDns1.value = "8.8.8.8";
      if (inputDns2) inputDns2.value = "8.8.4.4";
    } else if (type === "cloudflare") {
      if (inputDns1) inputDns1.value = "1.1.1.1";
      if (inputDns2) inputDns2.value = "1.0.0.1";
    }
  },

  async applyIpSettingsFromForm() {
    const adapterSelect = document.getElementById("ip-edit-adapter-select");
    const adapter = adapterSelect ? adapterSelect.value : "";
    if (!adapter) {
      if (typeof this.showToast === 'function') this.showToast("warning", "Vui lòng chọn Card Mạng (Adapter)!");
      else alert("Vui lòng chọn Card Mạng (Adapter)!");
      return;
    }

    const modeRadio = document.querySelector('input[name="ip-mode-radio"]:checked');
    const mode = modeRadio ? modeRadio.value : "static";

    const ip = document.getElementById("ip-input-address")?.value.trim() || "";
    const mask = document.getElementById("ip-input-mask")?.value.trim() || "255.255.255.0";
    const gw = document.getElementById("ip-input-gateway")?.value.trim() || "";
    const dns1 = document.getElementById("ip-input-dns1")?.value.trim() || "";
    const dns2 = document.getElementById("ip-input-dns2")?.value.trim() || "";

    if (mode === "static" && (!ip || !mask)) {
      if (typeof this.showToast === 'function') this.showToast("warning", "Vui lòng nhập Địa Chỉ IP và Subnet Mask!");
      else alert("Vui lòng nhập Địa Chỉ IP và Subnet Mask!");
      return;
    }

    this.addLog("info", `Đang cài đặt IP cho card mạng '${adapter}'...`);
    if (typeof this.showToast === 'function') this.showToast("info", `Đang áp dụng cấu hình cho '${adapter}'...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.apply_ip_settings(adapter, mode, ip, mask, gw, dns1, dns2);
        this.addLog(res.success ? "success" : "error", res.message);
        if (typeof this.showToast === 'function') this.showToast(res.success ? "success" : "error", res.message);
        else alert(res.message);
        this.loadNetworkAdapters();
      } catch (err) {
        console.error("Lỗi apply_ip_settings:", err);
        if (typeof this.showToast === 'function') this.showToast("error", `Lỗi: ${err.message}`);
        else alert(`Lỗi: ${err.message}`);
      }
    } else {
      if (typeof this.showToast === 'function') this.showToast("info", `[MOCK] Đã áp dụng IP ${ip} cho ${adapter}!`);
      else alert(`[MOCK] Đã áp dụng IP ${ip} cho ${adapter}!`);
    }
  },

  async setDhcpFromForm() {
    const adapterSelect = document.getElementById("ip-edit-adapter-select");
    const adapter = adapterSelect ? adapterSelect.value : "";
    if (!adapter) {
      if (typeof this.showToast === 'function') this.showToast("warning", "Vui lòng chọn Card Mạng (Adapter)!");
      else alert("Vui lòng chọn Card Mạng (Adapter)!");
      return;
    }

    this.addLog("info", `Đang chuyển '${adapter}' sang chế độ DHCP...`);
    if (typeof this.showToast === 'function') this.showToast("info", `Đang cấu hình DHCP cho '${adapter}'...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.apply_ip_settings(adapter, "dhcp");
        this.addLog(res.success ? "success" : "error", res.message);
        if (typeof this.showToast === 'function') this.showToast(res.success ? "success" : "error", res.message);
        else alert(res.message);
        this.loadNetworkAdapters();
      } catch (err) {
        if (typeof this.showToast === 'function') this.showToast("error", `Lỗi: ${err.message}`);
        else alert(`Lỗi: ${err.message}`);
      }
    } else {
      if (typeof this.showToast === 'function') this.showToast("info", `[MOCK] Đã cài DHCP cho ${adapter}!`);
      else alert(`[MOCK] Đã cài DHCP cho ${adapter}!`);
    }
  },

  async runSubnetCalculation() {
    const ipInput = document.getElementById("subnet-input-ip");
    const cidrSelect = document.getElementById("subnet-input-cidr");
    const outputEl = document.getElementById("subnet-result-output");

    const ip = ipInput ? ipInput.value.trim() : "";
    const cidr = cidrSelect ? cidrSelect.value : "24";

    if (!ip) {
      if (typeof this.showToast === 'function') this.showToast("warning", "Vui lòng nhập địa chỉ IP!");
      else alert("Vui lòng nhập địa chỉ IP!");
      return;
    }

    if (outputEl) outputEl.innerHTML = "🔄 Đang tính toán thông số subnet...";

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.calculate_subnet(ip, cidr);
        if (res && res.success && res.data) {
          const d = res.data;
          outputEl.innerHTML = `
            <div>• Network Address   : <strong style="color:#38bdf8">${d.network_address}</strong></div>
            <div>• Broadcast Address : <strong style="color:#f43f5e">${d.broadcast_address}</strong></div>
            <div>• Subnet Mask       : <strong style="color:#34d399">${d.subnet_mask}</strong></div>
            <div>• Wildcard Mask     : <strong style="color:#fbbf24">${d.wildcard_mask}</strong></div>
            <div>• CIDR Notation     : <strong>${d.cidr_notation}</strong></div>
            <div>• Host Đầu (First)  : <strong style="color:#a7f3d0">${d.first_host}</strong></div>
            <div>• Host Cuối (Last)  : <strong style="color:#a7f3d0">${d.last_host}</strong></div>
            <div>• Tổng Số Hosts     : <strong>${d.total_hosts}</strong></div>
            <div>• Usable Hosts      : <strong style="color:#38bdf8">${d.usable_hosts}</strong></div>
            <div>• Lớp IP (Class)    : <strong>${d.ip_class}</strong> (${d.type})</div>
          `;
        } else {
          outputEl.innerHTML = `<span style="color:#f87171">❌ ${res ? res.message : 'Lỗi tính toán'}</span>`;
        }
      } catch (err) {
        outputEl.innerHTML = `<span style="color:#f87171">❌ Lỗi: ${err.message}</span>`;
      }
    } else {
      outputEl.innerHTML = `[MOCK] Subnet result for ${ip}/${cidr}`;
    }
  },

  async loadIpv6Status() {
    const badge = document.getElementById("ipv6-status-badge");
    const btnToggle = document.getElementById("ipv6-btn-toggle");
    if (badge) badge.innerText = "Đang kiểm tra...";

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_ipv6_status();
        this.ipv6Enabled = !!(res && res.enabled);
        if (badge) {
          badge.innerText = res.text || (res.enabled ? "✅ IPv6 Đang Bật" : "🚫 IPv6 Đã Tắt");
          badge.style.color = res.enabled ? "#10b981" : "#ef4444";
        }
        if (btnToggle) {
          btnToggle.disabled = false;
          if (this.ipv6Enabled) {
            btnToggle.className = "btn btn-danger-solid px-4 py-2.5 font-semibold";
            btnToggle.innerHTML = "<span>🚫</span> Tắt IPv6 (Disable)";
            btnToggle.title = "IPv6 đang BẬT. Nhấp để Tắt trên tất cả card mạng";
          } else {
            btnToggle.className = "btn btn-success-solid px-4 py-2.5 font-semibold";
            btnToggle.innerHTML = "<span>✅</span> Bật IPv6 (Enable)";
            btnToggle.title = "IPv6 đang TẮT. Nhấp để Bật trên tất cả card mạng";
          }
        }
      } catch (err) {
        if (badge) badge.innerText = "Lỗi kiểm tra";
      }
    } else {
      this.ipv6Enabled = true;
      if (badge) badge.innerText = "✅ IPv6 Đang Bật (MOCK)";
      if (btnToggle) {
        btnToggle.className = "btn btn-danger-solid px-4 py-2.5 font-semibold";
        btnToggle.innerHTML = "<span>🚫</span> Tắt IPv6 (Disable)";
      }
    }
  },

  async toggleIpv6Status() {
    const isEnabled = (this.ipv6Enabled !== undefined) ? this.ipv6Enabled : true;
    await this.setIpv6Status(!isEnabled);
  },

  async setIpv6Status(enable) {
    const badge = document.getElementById("ipv6-status-badge");
    const btnToggle = document.getElementById("ipv6-btn-toggle");
    if (badge) badge.innerText = `Đang ${enable ? 'bật' : 'tắt'} IPv6...`;
    if (btnToggle) btnToggle.disabled = true;

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.set_ipv6_status(enable);
        this.addLog(res.success ? "success" : "error", res.message);
        if (typeof this.showToast === 'function') this.showToast(res.success ? "success" : "error", res.message);
        else alert(res.message);
        this.loadIpv6Status();
      } catch (err) {
        if (typeof this.showToast === 'function') this.showToast("error", `Lỗi: ${err.message}`);
        else alert(`Lỗi: ${err.message}`);
        if (btnToggle) btnToggle.disabled = false;
      }
    } else {
      if (typeof this.showToast === 'function') this.showToast("info", `[MOCK] Đã ${enable ? 'bật' : 'tắt'} IPv6!`);
      else alert(`[MOCK] Đã ${enable ? 'bật' : 'tắt'} IPv6!`);
      this.ipv6Enabled = enable;
      this.loadIpv6Status();
    }
  },

  parseSmartRangeClient(rawText) {
    const text = (rawText || "").trim();
    if (!text) {
      return { count: 0, desc: "Chưa nhập dải IP", isValid: false, subnet: "", start: "", end: "" };
    }

    // 1. Comma list
    if (text.includes(",")) {
      const parts = text.split(",").map(p => p.trim()).filter(p => /^(\d{1,3}\.){3}\d{1,3}$/.test(p));
      if (parts.length > 0) {
        return {
          count: parts.length,
          desc: `${parts.length} địa chỉ riêng lẻ (${parts.slice(0, 3).join(", ")}${parts.length > 3 ? "..." : ""})`,
          isValid: true,
          subnet: "",
          start: parts[0],
          end: parts[parts.length - 1]
        };
      }
    }

    // 2. Wildcard (e.g. 10.90.39.x or 10.90.39.*)
    const wildMatch = text.match(/^(\d{1,3}\.\d{1,3}\.\d{1,3})\.[xX\*]$/);
    if (wildMatch) {
      const base = wildMatch[1];
      return {
        count: 254,
        desc: `${base}.1 ➔ ${base}.254`,
        isValid: true,
        subnet: `${base}.0/24`,
        start: `${base}.1`,
        end: `${base}.254`
      };
    }

    // 3. CIDR (e.g. 10.90.39.0/24, 192.168.1.0/24)
    if (text.includes("/")) {
      const parts = text.split("/");
      const baseIp = parts[0].trim();
      const mask = parseInt(parts[1]);
      if (!isNaN(mask) && mask >= 16 && mask <= 32) {
        const ipParts = baseIp.split(".");
        if (ipParts.length === 4) {
          const prefix = `${ipParts[0]}.${ipParts[1]}.${ipParts[2]}`;
          if (mask === 24) {
            return {
              count: 254,
              desc: `${prefix}.1 ➔ ${prefix}.254`,
              isValid: true,
              subnet: text,
              start: `${prefix}.1`,
              end: `${prefix}.254`
            };
          } else if (mask === 32) {
            return {
              count: 1,
              desc: `${baseIp} (IP đơn lẻ)`,
              isValid: true,
              subnet: text,
              start: baseIp,
              end: baseIp
            };
          } else {
            const hostCount = Math.max(1, Math.min(1024, Math.pow(2, 32 - mask) - 2));
            return {
              count: hostCount,
              desc: `${hostCount} địa chỉ trong mạng ${text}`,
              isValid: true,
              subnet: text,
              start: `${prefix}.1`,
              end: `${prefix}.${Math.min(254, hostCount)}`
            };
          }
        }
      }
    }

    // 4. Short prefix (e.g. 10.90.39 or 10.90.39.)
    const prefixMatch = text.match(/^(\d{1,3}\.\d{1,3}\.\d{1,3})\.?$/);
    if (prefixMatch) {
      const base = prefixMatch[1];
      return {
        count: 254,
        desc: `${base}.1 ➔ ${base}.254`,
        isValid: true,
        subnet: `${base}.0/24`,
        start: `${base}.1`,
        end: `${base}.254`
      };
    }

    // 5. Hyphen range (e.g. 10.90.39.1-254 or 10.90.39.1 - 10.90.39.50)
    if (text.includes("-")) {
      const parts = text.split("-").map(p => p.trim());
      if (parts.length === 2) {
        const startStr = parts[0];
        let endStr = parts[1];
        if (/^\d{1,3}$/.test(endStr)) {
          const p = startStr.split(".");
          if (p.length === 4) {
            endStr = `${p[0]}.${p[1]}.${p[2]}.${endStr}`;
          }
        }
        const sNums = startStr.split(".").map(n => parseInt(n));
        const eNums = endStr.split(".").map(n => parseInt(n));
        if (sNums.length === 4 && eNums.length === 4 && sNums.every(n => !isNaN(n) && n >= 0 && n <= 255) && eNums.every(n => !isNaN(n) && n >= 0 && n <= 255)) {
          const sInt = (sNums[0] << 24) | (sNums[1] << 16) | (sNums[2] << 8) | sNums[3];
          const eInt = (eNums[0] << 24) | (eNums[1] << 16) | (eNums[2] << 8) | eNums[3];
          const count = eInt - sInt + 1;
          if (count > 0 && count <= 1024) {
            return {
              count: count,
              desc: `${startStr} ➔ ${endStr}`,
              isValid: true,
              subnet: `${sNums[0]}.${sNums[1]}.${sNums[2]}.0/24`,
              start: startStr,
              end: endStr
            };
          }
        }
      }
    }

    // 6. Single IP (e.g. 10.90.39.100)
    if (/^(\d{1,3}\.){3}\d{1,3}$/.test(text)) {
      const nums = text.split(".").map(n => parseInt(n));
      if (nums.every(n => !isNaN(n) && n >= 0 && n <= 255)) {
        return {
          count: 1,
          desc: `${text} (IP đơn lẻ)`,
          isValid: true,
          subnet: `${text}/32`,
          start: text,
          end: text
        };
      }
    }

    return { count: 0, desc: "Định dạng dải IP chưa hợp lệ", isValid: false, subnet: "", start: "", end: "" };
  },

  updateSmartIpPreview(parsed) {
    const banner = document.getElementById("ipscan-scope-banner");
    const textEl = document.getElementById("ipscan-scope-text");
    if (!banner || !textEl) return;

    if (parsed.isValid && parsed.count > 0) {
      textEl.innerHTML = `Sẽ quét <strong style="color: #0284c7;">${parsed.count} địa chỉ</strong>: <span style="font-family: monospace; font-weight: 700; color: #0f172a;">${parsed.desc}</span>`;
      banner.style.background = "#f0f9ff";
      banner.style.borderColor = "#bae6fd";
      banner.style.color = "#0369a1";
    } else {
      textEl.innerHTML = `⚠️ Nhập dải IP (VD: <code style="background:#e2e8f0; padding:1px 4px; border-radius:3px;">10.90.39.x</code> hoặc <code style="background:#e2e8f0; padding:1px 4px; border-radius:3px;">10.90.39.1-254</code>) hoặc bấm <strong>"🎯 Lấy IP Mạng Này"</strong>`;
      banner.style.background = "#fffbeb";
      banner.style.borderColor = "#fde68a";
      banner.style.color = "#92400e";
    }
  },

  onSmartIpInputChanged(val) {
    const parsed = this.parseSmartRangeClient(val);
    this.updateSmartIpPreview(parsed);

    if (parsed.isValid) {
      const subEl = document.getElementById("ipscan-input-subnet");
      const startEl = document.getElementById("ipscan-input-start");
      const endEl = document.getElementById("ipscan-input-end");
      if (subEl && parsed.subnet) subEl.value = parsed.subnet;
      if (startEl && parsed.start) startEl.value = parsed.start;
      if (endEl && parsed.end) endEl.value = parsed.end;
    }
  },

  onClassicIpInputChanged(field) {
    const subEl = document.getElementById("ipscan-input-subnet");
    const startEl = document.getElementById("ipscan-input-start");
    const endEl = document.getElementById("ipscan-input-end");
    const smartEl = document.getElementById("ipscan-smart-input");

    const startVal = startEl ? startEl.value.trim() : "";
    const endVal = endEl ? endEl.value.trim() : "";
    const subVal = subEl ? subEl.value.trim() : "";

    if (smartEl) {
      if (startVal && endVal) {
        smartEl.value = `${startVal} - ${endVal}`;
      } else if (subVal) {
        smartEl.value = subVal;
      }
      const parsed = this.parseSmartRangeClient(smartEl.value);
      this.updateSmartIpPreview(parsed);
    }
  },

  toggleIpScanAdvancedMode() {
    const box = document.getElementById("ipscan-advanced-range-box");
    const btn = document.getElementById("btn-toggle-ip-advanced");
    if (!box) return;

    const isHidden = (box.style.display === "none" || !box.style.display);
    box.style.display = isHidden ? "block" : "none";
    if (btn) {
      btn.innerHTML = isHidden ? "✖ Thu Gọn Phân Đoạn" : "⚙️ Chi Tiết Từ IP - Đến IP";
      btn.className = isHidden ? "btn btn-xs btn-sky-outline" : "btn btn-xs btn-slate-light";
    }
  },

  async loadIpScannerDefaults() {
    const smartEl = document.getElementById("ipscan-smart-input");
    const subEl = document.getElementById("ipscan-input-subnet");
    const startEl = document.getElementById("ipscan-input-start");
    const endEl = document.getElementById("ipscan-input-end");
    const badgeEl = document.getElementById("ipscan-detected-lan-badge");
    const btnLocalPreset = document.getElementById("btn-preset-local");

    let d = null;
    if (window.pywebview && window.pywebview.api) {
      try {
        d = await window.pywebview.api.get_ip_scanner_default_range();
      } catch (err) {
        console.error("Lỗi lấy IP scan defaults:", err);
      }
    }

    if (!d) {
      d = {
        local_ip: "192.168.1.100",
        subnet: "192.168.1.0/24",
        start_ip: "192.168.1.1",
        end_ip: "192.168.1.254",
        wildcard: "192.168.1.x",
        label: "Mạng 192.168.1.x"
      };
    }

    this.detectedLanInfo = d;

    // Auto-fill smart input if empty or fresh
    const defaultVal = d.wildcard || `${d.start_ip} - ${d.end_ip}`;
    if (smartEl && (!smartEl.value || smartEl.value.trim() === "")) {
      smartEl.value = defaultVal;
    }
    if (subEl && !subEl.value) subEl.value = d.subnet || "";
    if (startEl && !startEl.value) startEl.value = d.start_ip || "";
    if (endEl && !endEl.value) endEl.value = d.end_ip || "";

    if (badgeEl) {
      badgeEl.innerHTML = `Mạng máy: <strong>${d.local_ip}</strong> (${d.wildcard || d.subnet})`;
      badgeEl.title = `IP máy hiện tại: ${d.local_ip}\nDải mạng tự động: ${d.subnet}`;
    }
    if (btnLocalPreset) {
      btnLocalPreset.innerHTML = `🏠 Mạng Máy (${d.wildcard || 'LAN'})`;
    }

    if (smartEl) {
      this.onSmartIpInputChanged(smartEl.value);
    }
  },

  applyIpScanPreset(preset) {
    const smartEl = document.getElementById("ipscan-smart-input");
    const subEl = document.getElementById("ipscan-input-subnet");
    const startEl = document.getElementById("ipscan-input-start");
    const endEl = document.getElementById("ipscan-input-end");

    if (preset === 'local') {
      if (this.detectedLanInfo) {
        const d = this.detectedLanInfo;
        const val = d.wildcard || `${d.start_ip} - ${d.end_ip}`;
        if (smartEl) smartEl.value = val;
        if (subEl) subEl.value = d.subnet || "";
        if (startEl) startEl.value = d.start_ip || "";
        if (endEl) endEl.value = d.end_ip || "";
        this.onSmartIpInputChanged(val);
        if (typeof this.showToast === 'function') {
          this.showToast('info', `Đã chọn mạng LAN của máy: ${d.local_ip} (${d.wildcard})`);
        }
      } else {
        if (smartEl) smartEl.value = "";
        this.loadIpScannerDefaults();
      }
    } else if (preset === '192.168.1') {
      const val = "192.168.1.x";
      if (smartEl) smartEl.value = val;
      this.onSmartIpInputChanged(val);
    } else if (preset === '192.168.0') {
      const val = "192.168.0.x";
      if (smartEl) smartEl.value = val;
      this.onSmartIpInputChanged(val);
    } else if (preset === '10.0.0') {
      const val = "10.0.0.x";
      if (smartEl) smartEl.value = val;
      this.onSmartIpInputChanged(val);
    } else if (preset === '172.16.1') {
      const val = "172.16.1.x";
      if (smartEl) smartEl.value = val;
      this.onSmartIpInputChanged(val);
    } else if (preset === '172.16.112') {
      const val = "172.16.112.x";
      if (smartEl) smartEl.value = val;
      this.onSmartIpInputChanged(val);
    } else if (preset === '192.168.102') {
      const val = "192.168.102.x";
      if (smartEl) smartEl.value = val;
      this.onSmartIpInputChanged(val);
    }
  },

  applyPortPreset(type) {
    const portDefs = [
      { id: 'ipscan-chk-port-80', port: 80 },
      { id: 'ipscan-chk-port-443', port: 443 },
      { id: 'ipscan-chk-port-3389', port: 3389 },
      { id: 'ipscan-chk-port-445', port: 445 },
      { id: 'ipscan-chk-port-135', port: 135 },
      { id: 'ipscan-chk-port-1433', port: 1433 },
      { id: 'ipscan-chk-port-389', port: 389 },
      { id: 'ipscan-chk-port-53', port: 53 },
      { id: 'ipscan-chk-port-5985', port: 5985 },
      { id: 'ipscan-chk-port-22', port: 22 },
      { id: 'ipscan-chk-port-88', port: 88 },
      { id: 'ipscan-chk-port-21', port: 21 },
    ];

    let targetPorts = [];
    if (type === 'web') {
      targetPorts = [80, 443];
    } else if (type === 'client') {
      targetPorts = [3389, 445, 135];
    } else if (type === 'server') {
      targetPorts = [445, 3389, 135, 53, 88, 389, 1433, 5985];
    } else if (type === 'db') {
      targetPorts = [1433, 22, 5985];
    } else if (type === 'all') {
      targetPorts = portDefs.map(p => p.port);
    } else if (type === 'none') {
      targetPorts = [];
    }

    portDefs.forEach(p => {
      const el = document.getElementById(p.id);
      if (el) el.checked = targetPorts.includes(p.port);
    });
  },

  async startIpScanner() {
    const smartEl = document.getElementById("ipscan-smart-input");
    const subEl = document.getElementById("ipscan-input-subnet");
    const startEl = document.getElementById("ipscan-input-start");
    const endEl = document.getElementById("ipscan-input-end");
    const threadsEl = document.getElementById("ipscan-input-threads");

    const chkPing = document.getElementById("ipscan-chk-ping");
    const chkHost = document.getElementById("ipscan-chk-hostname");
    const chkMac = document.getElementById("ipscan-chk-mac");

    const btnStart = document.getElementById("ipscan-btn-start");
    const btnExport = document.getElementById("ipscan-btn-export");
    const spinner = document.getElementById("ipscan-spinner");
    const statusText = document.getElementById("ipscan-status-text");
    const badgeCount = document.getElementById("ipscan-count-badge");
    const bodyEl = document.getElementById("ipscan-results-body");

    const smartVal = smartEl ? smartEl.value.trim() : "";
    let subnet_str = subEl ? subEl.value.trim() : "";
    let ip_start = startEl ? startEl.value.trim() : "";
    let ip_end = endEl ? endEl.value.trim() : "";

    // Prioritize smart input value for the backend
    if (smartVal) {
      subnet_str = smartVal;
    }

    const max_threads = threadsEl ? parseInt(threadsEl.value) || 50 : 50;
    const check_ping = chkPing ? chkPing.checked : true;
    const check_hostname = chkHost ? chkHost.checked : true;
    const check_mac = chkMac ? chkMac.checked : true;

    // Collect port list to scan
    const portDefs = [
      { id: 'ipscan-chk-port-80', port: 80 },
      { id: 'ipscan-chk-port-443', port: 443 },
      { id: 'ipscan-chk-port-3389', port: 3389 },
      { id: 'ipscan-chk-port-445', port: 445 },
      { id: 'ipscan-chk-port-135', port: 135 },
      { id: 'ipscan-chk-port-1433', port: 1433 },
      { id: 'ipscan-chk-port-389', port: 389 },
      { id: 'ipscan-chk-port-53', port: 53 },
      { id: 'ipscan-chk-port-5985', port: 5985 },
      { id: 'ipscan-chk-port-22', port: 22 },
      { id: 'ipscan-chk-port-88', port: 88 },
      { id: 'ipscan-chk-port-21', port: 21 },
    ];
    const ports_to_check = [];
    portDefs.forEach(p => {
      const el = document.getElementById(p.id);
      if (el && el.checked) ports_to_check.push(p.port);
    });

    const customPortsEl = document.getElementById('ipscan-input-custom-ports');
    if (customPortsEl && customPortsEl.value) {
      customPortsEl.value.replace(/,/g, ' ').split(/\s+/).forEach(val => {
        const num = parseInt(val.trim());
        if (num > 0 && num <= 65535 && !ports_to_check.includes(num)) {
          ports_to_check.push(num);
        }
      });
    }

    const check_http_port = ports_to_check.includes(80);
    const check_https_port = ports_to_check.includes(443);

    const parsedScope = this.parseSmartRangeClient(smartVal || subnet_str || ip_start);
    const targetLabel = parsedScope.isValid ? `${parsedScope.count} địa chỉ (${parsedScope.desc})` : (smartVal || 'dải mạng LAN');

    if (btnStart) btnStart.disabled = true;
    if (spinner) spinner.style.display = "inline-block";
    if (statusText) statusText.innerText = `Đang quét ${targetLabel} (${max_threads} luồng, ${ports_to_check.length} cổng dịch vụ)... Vui lòng chờ...`;
    if (bodyEl) {
      bodyEl.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-4 text-muted">
            <span class="spinner-border spinner-border-sm text-primary"></span>
            Đang tiến hành quét thiết bị và cổng dịch vụ trong mạng LAN...
          </td>
        </tr>
      `;
    }

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.scan_ip_range(
          subnet_str, ip_start, ip_end, check_ping, check_hostname, check_mac, check_http_port, check_https_port, max_threads, ports_to_check
        );

        if (res && res.success) {
          this.lastScanResults = res.results || [];
          if (badgeCount) badgeCount.innerText = `${res.total} Online`;
          if (statusText) statusText.innerText = `Hoàn tất quét LAN! Tìm thấy ${res.total} thiết bị online.`;
          if (btnExport) btnExport.disabled = (res.total === 0);
          this.renderIpScanResults(res.results || []);
        } else {
          if (statusText) statusText.innerText = `Lỗi quét IP: ${res ? res.message : 'Unknown'}`;
          if (bodyEl) {
            bodyEl.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-danger">Lỗi: ${res ? res.message : 'Không quét được'}</td></tr>`;
          }
        }
      } catch (err) {
        if (statusText) statusText.innerText = `Lỗi ngoại lệ: ${err.message}`;
        if (bodyEl) {
          bodyEl.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-danger">Lỗi kết nối API: ${err.message}</td></tr>`;
        }
      } finally {
        if (btnStart) btnStart.disabled = false;
        if (spinner) spinner.style.display = "none";
      }
    } else {
      setTimeout(() => {
        const mockData = [
          { ip: "192.168.1.1", hostname: "Router-Gateway.home", mac: this.generateRandomMac(":"), vendor: "TP-Link", device_type: "Router", latency_ms: "<1ms", open_ports: [80, 443, 53] },
          { ip: "192.168.1.100", hostname: "PC-DESKTOP-LTT", mac: this.generateRandomMac(":"), vendor: "Realtek", device_type: "PC", latency_ms: "<1ms", open_ports: [445, 135, 3389, 5985] },
          { ip: "192.168.1.200", hostname: "WIN-SERVER-2025", mac: this.generateRandomMac(":"), vendor: "Dell", device_type: "Server", latency_ms: "<1ms", open_ports: [53, 88, 135, 389, 445, 1433, 3389, 5985] },
          { ip: "192.168.1.105", hostname: "iPhone-Guest", mac: this.generateRandomMac(":"), vendor: "Apple", device_type: "iPhone", latency_ms: "12ms", open_ports: [] }
        ];
        this.lastScanResults = mockData;
        if (badgeCount) badgeCount.innerText = "4 Online";
        if (statusText) statusText.innerText = "Hoàn tất quét LAN (MOCK)! Tìm thấy 4 thiết bị online.";
        if (btnExport) btnExport.disabled = false;
        this.renderIpScanResults(mockData);
        if (btnStart) btnStart.disabled = false;
        if (spinner) spinner.style.display = "none";
      }, 800);
    }
  },

  toggleIpScanPortsBox() {
    const box = document.getElementById("ipscan-ports-box");
    const btn = document.getElementById("btn-toggle-ports-box");
    if (!box) return;
    const isHidden = box.style.display === "none";
    box.style.display = isHidden ? "block" : "none";
    if (btn) {
      btn.innerHTML = isHidden ? "🔌 Thu gọn tùy chọn cổng ▲" : "🔌 Tùy chọn cổng (12 Ports) ▼";
    }
  },

  filterIpScanResults() {
    const searchInput = document.getElementById("ipscan-search-input");
    const filterPort = document.getElementById("ipscan-filter-port")?.value || "all";
    const query = (searchInput ? searchInput.value : "").trim().toLowerCase();

    if (!this.lastScanResults || this.lastScanResults.length === 0) {
      const filterInfo = document.getElementById("ipscan-filter-info");
      if (filterInfo) filterInfo.textContent = "0 thiết bị";
      return;
    }

    const filtered = this.lastScanResults.filter(item => {
      const ports = (item.open_ports || []).map(Number);
      if (filterPort === "web" && !ports.includes(80) && !ports.includes(443)) return false;
      if (filterPort === "rdp" && !ports.includes(3389)) return false;
      if (filterPort === "smb" && !ports.includes(445)) return false;

      if (!query) return true;
      const ip = (item.ip || "").toLowerCase();
      const host = (item.hostname || "").toLowerCase();
      const mac = (item.mac || "").toLowerCase();
      const vendor = (item.vendor || item.brand || "").toLowerCase();
      const devType = (item.device_type || "").toLowerCase();
      const portStr = ports.join(" ");

      return ip.includes(query) || host.includes(query) || mac.includes(query) || vendor.includes(query) || devType.includes(query) || portStr.includes(query);
    });

    const filterInfo = document.getElementById("ipscan-filter-info");
    if (filterInfo) {
      if (query || filterPort !== "all") {
        filterInfo.textContent = `Hiển thị ${filtered.length}/${this.lastScanResults.length} thiết bị`;
      } else {
        filterInfo.textContent = `Tổng: ${this.lastScanResults.length} thiết bị`;
      }
    }

    this.renderIpScanResults(filtered, false);
  },

  clearIpScanSearch() {
    const searchInput = document.getElementById("ipscan-search-input");
    if (searchInput) {
      searchInput.value = "";
      searchInput.focus();
    }
    const filterPort = document.getElementById("ipscan-filter-port");
    if (filterPort) filterPort.value = "all";
    this.filterIpScanResults();
  },

  renderIpScanResults(results, updateFilterBadge = true) {
    const body = document.getElementById('ipscan-results-body');
    if (!body) return;
    body.replaceChildren();
    if (updateFilterBadge) {
      const filterInfo = document.getElementById("ipscan-filter-info");
      if (filterInfo) {
        filterInfo.textContent = `${results?.length || 0} thiết bị`;
      }
    }
    if (!results?.length) {
      const cell = body.insertRow().insertCell();
      cell.colSpan = 8;
      cell.textContent = 'Không tìm thấy thiết bị nào phù hợp.';
      return;
    }
    results.forEach((item, index) => {
      const row = body.insertRow();
      row.style.height = "38px";
      row.style.borderBottom = "1px solid #f1f5f9";
      row.style.transition = "background 0.12s";
      row.onmouseover = () => { row.style.background = "#f8fafc"; };
      row.onmouseout = () => { row.style.background = "white"; };

      const ports = (item.open_ports || []).map(Number).filter(p => Number.isInteger(p) && p > 0 && p < 65536);
      const latency = item.latency_ms || item.ping || '<1ms';
      const hostname = item.hostname || 'Không tìm được tên';
      const vendorDev = `${item.vendor || item.brand || 'Unknown'} / ${item.device_type || 'Unknown'}`;
      const portStr = ports.join(', ') || '-';

      // 0: Index
      const cIndex = row.insertCell();
      cIndex.textContent = String(index + 1);
      cIndex.style.cssText = "text-align: center; color: #64748b; font-weight: 600; padding: 6px 4px; font-size: 11.5px;";

      // 1: Status
      const cStatus = row.insertCell();
      cStatus.innerHTML = `<span style="background: #10b981; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10.5px; font-weight: 700;">🟢 Online (${latency})</span>`;
      cStatus.style.cssText = "text-align: center; white-space: nowrap; padding: 6px;";

      // 2: IP
      const cIp = row.insertCell();
      cIp.innerHTML = `<span style="font-family: monospace; font-weight: 700; color: #0284c7; font-size: 12.5px;">${this.escapeHtml(item.ip)}</span>`;
      cIp.style.cssText = "white-space: nowrap; padding: 6px; cursor: pointer;";
      cIp.title = "Bấm để sao chép địa chỉ IP";
      cIp.addEventListener('click', () => this.copyToClipboard(item.ip, 'IP'));

      // 3: Hostname (Compact with Tooltip)
      const cHost = row.insertCell();
      cHost.textContent = hostname;
      cHost.title = hostname;
      cHost.style.cssText = "max-width: 190px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 600; color: #1e293b; padding: 6px; cursor: pointer;";
      cHost.addEventListener('click', () => this.copyToClipboard(hostname, 'Hostname'));

      // 4: MAC
      const cMac = row.insertCell();
      cMac.textContent = item.mac || '-';
      cMac.title = item.mac || '-';
      cMac.style.cssText = "font-family: monospace; font-size: 11.5px; color: #475569; white-space: nowrap; padding: 6px; cursor: pointer;";
      cMac.addEventListener('click', () => this.copyToClipboard(item.mac, 'MAC'));

      // 5: Vendor / Device
      const cVendor = row.insertCell();
      cVendor.textContent = vendorDev;
      cVendor.title = vendorDev;
      cVendor.style.cssText = "max-width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 11.5px; color: #64748b; padding: 6px; cursor: pointer;";
      cVendor.addEventListener('click', () => this.copyToClipboard(vendorDev, 'Nhà sản xuất'));

      // 6: Open Ports (Pill Badges)
      const cPorts = row.insertCell();
      if (ports.length > 0) {
        cPorts.innerHTML = ports.slice(0, 3).map(p =>
          `<span style="background: #f1f5f9; color: #0f172a; border: 1px solid #cbd5e1; padding: 1px 4px; border-radius: 3px; font-size: 10px; font-weight: 600; margin-right: 3px;">${p}</span>`
        ).join('') + (ports.length > 3 ? `<span style="font-size: 10px; color: #64748b;">+${ports.length - 3}</span>` : '');
      } else {
        cPorts.textContent = '-';
        cPorts.style.color = '#94a3b8';
      }
      cPorts.title = `Các cổng mở: ${portStr}`;
      cPorts.style.cssText = "white-space: nowrap; padding: 6px;";

      // 7: Actions (Icon-only buttons with tooltip hover)
      const actions = row.insertCell();
      actions.style.cssText = "text-align: center; white-space: nowrap; padding: 4px 6px;";

      const button = (icon, titleText, callback, extraStyle = '') => {
        const element = document.createElement('button');
        element.type = 'button';
        element.innerHTML = icon;
        element.title = titleText;
        element.style.cssText = `display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; padding: 0; font-size: 13px; margin: 0 1.5px; border-radius: 5px; border: 1px solid #cbd5e1; background: #ffffff; cursor: pointer; transition: all 0.12s; ${extraStyle}`;
        element.addEventListener('click', (e) => {
          e.stopPropagation();
          callback();
        });
        element.onmouseenter = () => { element.style.transform = 'scale(1.1)'; element.style.borderColor = '#0284c7'; };
        element.onmouseleave = () => { element.style.transform = 'scale(1)'; element.style.borderColor = '#cbd5e1'; };
        actions.appendChild(element);
      };

      // 1. RustDesk Direct Remote
      button('🦀', `Kết nối từ xa RustDesk tới ${item.ip}`, () => this.connectRustdesk(item.ip), 'border-color: #fecdd3; background: #fff1f2;');

      // 2. Scan Target Ports
      button('⚡', `Quét chuyên sâu cổng dịch vụ máy ${item.ip}`, () => this.openHostPortScanModal(item.ip));

      // 3. Copy IP
      button('📋', `Sao chép địa chỉ IP (${item.ip})`, () => this.copyToClipboard(item.ip, 'IP'));

      // 4. RDP
      if (ports.includes(3389)) {
        button('🖥️', `Mở Remote Desktop (RDP) tới ${item.ip}`, () => this.connectRdp(item.ip), 'border-color: #bae6fd; background: #f0f9ff;');
      }

      // 5. SMB File/Printer Share
      if (ports.includes(445)) {
        button('📁', `Mở thư mục chia sẻ mạng (SMB) \\\\${item.ip}`, () => this.openSmbShare(item.ip));
      }

      // 6. Web Admin (HTTP/HTTPS)
      if (ports.includes(80) || ports.includes(443)) {
        button('🌐', `Mở giao diện Web quản trị (${ports.includes(443) ? 'https' : 'http'}://${item.ip})`, () => this.openWebBrowser(`${ports.includes(443) ? 'https' : 'http'}://${item.ip}`));
      }

      // 7. WinRM PowerShell
      if (ports.includes(5985) || ports.includes(5986)) {
        button('💻', `Mở phiên PowerShell từ xa (WinRM) tới ${item.ip}`, () => this.openWinRmSession(item.ip));
      }
    });
  },

  exportIpScanCsv() {
    if (!this.lastScanResults || this.lastScanResults.length === 0) {
      if (typeof this.showToast === 'function') this.showToast("warning", "Không có kết quả quét để xuất CSV!");
      else alert("Không có kết quả quét để xuất CSV!");
      return;
    }

    let csvContent = "data:text/csv;charset=utf-8,Index,IP Address,Hostname,MAC Address,Vendor,Device Type,Latency,Open Ports,HTTP (80),HTTPS (443),RDP (3389),SMB (445)\n";
    this.lastScanResults.forEach((row, i) => {
      const vendor = row.vendor || row.brand || '';
      const deviceType = row.device_type || '';
      const latency = row.latency_ms || row.ping || '';
      const openPorts = (row.open_ports || []).join('; ');
      csvContent += `"${i + 1}","${row.ip || ''}","${row.hostname || ''}","${row.mac || ''}","${vendor}","${deviceType}","${latency}","${openPorts}","${row.http ? 'YES' : 'NO'}","${row.https ? 'YES' : 'NO'}","${row.rdp ? 'YES' : 'NO'}","${row.smb ? 'YES' : 'NO'}"\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `lan_ip_scan_results_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },

  exportIpScanResultsCsv() {
    return this.exportIpScanCsv();
  },

  // ── HOST PORT SCANNER MODAL CONTROLLERS ─────────────────────────────────
  openHostPortScanModal(ip = '') {
    const modal = document.getElementById('host-port-scan-modal');
    if (!modal) return;
    modal.style.display = 'flex';
    const ipInput = document.getElementById('hostport-input-ip');
    if (ipInput) {
      if (ip) ipInput.value = ip;
      else if (!ipInput.value) ipInput.value = '127.0.0.1';
    }
    if (ip) {
      this.runHostPortScan();
    }
  },

  closeHostPortScanModal() {
    const modal = document.getElementById('host-port-scan-modal');
    if (modal) modal.style.display = 'none';
  },

  onHostPortProfileChange() {
    const select = document.getElementById('hostport-select-profile');
    const customRow = document.getElementById('hostport-custom-row');
    if (select && customRow) {
      customRow.style.display = (select.value === 'custom') ? 'block' : 'none';
    }
  },

  async runHostPortScan() {
    const ipInput = document.getElementById('hostport-input-ip');
    const target = ipInput ? ipInput.value.trim() : '127.0.0.1';
    if (!target) {
      alert("Vui lòng nhập IP hoặc Hostname mục tiêu cần quét!");
      return;
    }

    const select = document.getElementById('hostport-select-profile');
    const profile = select ? select.value : 'all_windows';

    let ports = null;
    if (profile === 'win_client') {
      ports = [135, 139, 445, 3389, 80, 443];
    } else if (profile === 'win_server') {
      ports = [53, 88, 135, 139, 389, 445, 636, 1433, 3268, 3389, 5985, 5986];
    } else if (profile === 'db_web') {
      ports = [80, 443, 8080, 8443, 1433, 3306, 5432, 22, 21];
    } else if (profile === 'custom') {
      const customInput = document.getElementById('hostport-input-custom-ports');
      if (customInput && customInput.value) {
        ports = customInput.value.replace(/,/g, ' ').split(/\s+/).map(p => parseInt(p)).filter(p => !isNaN(p) && p > 0);
      }
    }

    const btnScan = document.getElementById('hostport-btn-scan');
    const statusText = document.getElementById('hostport-status-text');
    const badgeOpen = document.getElementById('hostport-badge-open');
    const badgeTotal = document.getElementById('hostport-badge-total');
    const btnExport = document.getElementById('hostport-btn-export');
    const bodyEl = document.getElementById('hostport-results-body');

    if (btnScan) btnScan.disabled = true;
    if (statusText) statusText.innerText = `Đang quét cổng dịch vụ trên ${target}... Vui lòng chờ...`;
    if (bodyEl) {
      bodyEl.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-4 text-muted">
            <span class="spinner-border spinner-border-sm text-primary"></span>
            Đang quét các cổng dịch vụ trên máy đích (${target})...
          </td>
        </tr>
      `;
    }

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.scan_single_host_ports(target, ports);
        if (res && res.success) {
          this.lastHostPortResults = res.results || [];
          this.lastHostPortTarget = target;
          if (badgeOpen) badgeOpen.innerText = `${res.open_count} Cổng Mở`;
          if (badgeTotal) badgeTotal.innerText = `${res.total} Tổng Quét`;
          if (statusText) statusText.innerText = `Hoàn tất! Tìm thấy ${res.open_count} cổng MỞ trên ${target}.`;
          if (btnExport) btnExport.disabled = (res.results.length === 0);
          this.renderHostPortScanResults(res.results || [], target);
        } else {
          if (statusText) statusText.innerText = `Lỗi: ${res ? res.message : 'Không quét được'}`;
          if (bodyEl) bodyEl.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-danger">Lỗi: ${res ? res.message : 'Thất bại'}</td></tr>`;
        }
      } catch (e) {
        if (statusText) statusText.innerText = `Lỗi kết nối: ${e.message}`;
        if (bodyEl) bodyEl.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-danger">Lỗi: ${e.message}</td></tr>`;
      } finally {
        if (btnScan) btnScan.disabled = false;
      }
    } else {
      setTimeout(() => {
        const mockPorts = [
          { port: 80, name: "HTTP", desc: "Web Server / Router Web Admin", category: "Web", status: "OPEN", is_open: true, latency_ms: "2ms" },
          { port: 443, name: "HTTPS", desc: "Secure Web / SSL Server", category: "Web", status: "OPEN", is_open: true, latency_ms: "2ms" },
          { port: 3389, name: "RDP", desc: "Remote Desktop Protocol (Điều khiển từ xa)", category: "Windows Client/Server", status: "OPEN", is_open: true, latency_ms: "3ms" },
          { port: 445, name: "SMB", desc: "Server Message Block (Chia sẻ File & Máy in)", category: "Windows File Sharing", status: "OPEN", is_open: true, latency_ms: "1ms" },
          { port: 135, name: "RPC", desc: "RPC Endpoint Mapper & WMI (Quản trị hệ thống)", category: "Windows System", status: "OPEN", is_open: true, latency_ms: "1ms" },
          { port: 1433, name: "MSSQL", desc: "Microsoft SQL Server Database Engine", category: "Database", status: "CLOSED", is_open: false, latency_ms: "4ms" },
          { port: 5985, name: "WinRM HTTP", desc: "Windows Remote Management (PowerShell Remoting)", category: "Remote Admin", status: "OPEN", is_open: true, latency_ms: "2ms" }
        ];
        this.lastHostPortResults = mockPorts;
        this.lastHostPortTarget = target;
        if (badgeOpen) badgeOpen.innerText = "6 Cổng Mở";
        if (badgeTotal) badgeTotal.innerText = "7 Tổng Quét";
        if (statusText) statusText.innerText = `Hoàn tất (MOCK)! Tìm thấy 6 cổng MỞ trên ${target}.`;
        if (btnExport) btnExport.disabled = false;
        this.renderHostPortScanResults(mockPorts, target);
        if (btnScan) btnScan.disabled = false;
      }, 500);
    }
  },

  renderHostPortScanResults(results, target) {
    const body = document.getElementById('hostport-results-body');
    if (!body) return;
    body.replaceChildren();
    (results || []).forEach(item => {
      const row = body.insertRow();
      [item.port, item.name, item.desc, item.category, item.is_open ? '🟢 MỞ' : '🔴 ĐÓNG'].forEach(value => {
        const cell = row.insertCell();
        cell.textContent = String(value ?? '');
        cell.style.padding = '8px';
      });
      const actions = row.insertCell();
      const port = Number(item.port);
      if (!item.is_open || !Number.isInteger(port) || port < 1 || port > 65535) return;
      const button = document.createElement('button');
      button.className = 'btn btn-slate-light btn-sm';
      button.textContent = 'Mở / Sao chép';
      button.addEventListener('click', () => {
        if (port === 3389) this.connectRdp(target);
        else if ([139, 445].includes(port)) this.openSmbShare(target);
        else if ([5985, 5986].includes(port)) this.openWinRmSession(target);
        else if ([80, 8080, 443, 8443].includes(port)) this.openWebBrowser(`${[443, 8443].includes(port) ? 'https' : 'http'}://${target}:${port}`);
        else this.copyToClipboard(`${target}:${port}`, 'Port');
      });
      actions.appendChild(button);
    });
  },

  exportHostPortScanCsv() {
    if (!this.lastHostPortResults || this.lastHostPortResults.length === 0) {
      alert("Không có kết quả quét cổng để xuất CSV!");
      return;
    }
    const target = this.lastHostPortTarget || 'host';
    let csvContent = "data:text/csv;charset=utf-8,Port,Service Name,Description,Category,Status,Latency\n";
    this.lastHostPortResults.forEach(r => {
      csvContent += `"${r.port}","${r.name || ''}","${r.desc || ''}","${r.category || ''}","${r.status || ''}","${r.latency_ms || ''}"\n`;
    });
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `port_scan_${target.replace(/[^a-zA-Z0-9_.-]/g, '_')}_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },

  async connectRdp(ip) {
    if (!ip) return;
    this.addLog("info", `Đang mở kết nối Remote Desktop đến ${ip}...`);
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_rdp_connection === 'function') {
      const res = await window.pywebview.api.open_rdp_connection(ip);
      this.addLog(res.success ? "success" : "error", res.message);
    } else {
      alert(`[MOCK] Mở mstsc.exe /v:${ip}`);
    }
  },

  async openSmbShare(ip) {
    if (!ip) return;
    this.addLog("info", `Đang mở chia sẻ mạng (SMB) \\\\${ip}...`);
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_smb_share === 'function') {
      const res = await window.pywebview.api.open_smb_share(ip);
      this.addLog(res.success ? "success" : "error", res.message);
    } else {
      alert(`[MOCK] Mở explorer.exe \\\\${ip}`);
    }
  },

  async openWinRmSession(ip) {
    if (!ip) return;
    this.addLog("info", `Đang mở phiên PowerShell Remoting (WinRM) đến ${ip}...`);
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_winrm_session === 'function') {
      const res = await window.pywebview.api.open_winrm_session(ip);
      this.addLog(res.success ? "success" : "error", res.message);
    } else {
      alert(`[MOCK] Enter-PSSession -ComputerName ${ip}`);
    }
  },

  openWebBrowser(url) {
    if (!url) return;
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_external_url === 'function') {
      window.pywebview.api.open_external_url(url);
    } else {
      window.open(url, '_blank');
    }
  }
});

