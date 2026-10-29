Object.assign(AppController.prototype, {
  async openFluentCleaner() {
    const button = document.getElementById('fluent-cleaner-open');
    const status = document.getElementById('fluent-cleaner-status');
    if (button) button.disabled = true;
    try {
      if (!window.pywebview?.api?.open_fluent_cleaner) {
        throw new Error('Hãy mở IT Tool trên Windows để sử dụng FluentCleaner.');
      }
      status.textContent = 'Đang kiểm tra bộ FluentCleaner và mở cửa sổ...';
      const result = await window.pywebview.api.open_fluent_cleaner();
      status.textContent = result.message;
      this.addLog(result.success ? 'success' : 'error', result.message);
    } catch (error) {
      status.textContent = error.message;
    } finally {
      if (button) button.disabled = false;
    }
  }
});
