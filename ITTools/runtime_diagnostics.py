"""Read-only runtime smoke test for the actual packaged Windows application."""
import importlib
import json
from pathlib import Path
import sys
import threading
import traceback


def summarize_api_result(value, expected_type, required_keys=()):
    """Validate the response without recording machine or user data."""
    if not isinstance(value, expected_type):
        raise TypeError(f'Expected {expected_type.__name__}, got {type(value).__name__}')
    if isinstance(value, dict):
        if value.get('success') is False:
            raise ValueError(value.get('message', 'API returned failure'))
        missing = set(required_keys) - value.keys()
        if missing:
            raise ValueError('Missing keys: ' + ', '.join(sorted(missing)))
        return 'Response keys verified: ' + ', '.join(sorted(value.keys()))
    return f'{len(value)} items; values omitted'


def run(report_path):
    report = {'executable': sys.executable, 'frozen': bool(getattr(sys, 'frozen', False)),
              'python': sys.version, 'version': importlib.import_module('constants').APP_VERSION, 'runtime_directory': getattr(sys, '_MEIPASS', None), 'checks': {}}

    def check(name, action):
        try:
            result = action()
            report['checks'][name] = {'ok': True, 'detail': str(result)}
        except Exception:
            report['checks'][name] = {'ok': False, 'detail': traceback.format_exc()}

    # Match the application's .NET initialization before lazy API imports.
    check('webview.winforms', lambda: importlib.import_module('webview.platforms.winforms').__file__)

    def worker():
        check('_tkinter', lambda: importlib.import_module('_tkinter').__file__)
        for name in ['computer_info', 'startup_manager', 'uninstall_manager', 'bitlocker',
                     'ip_manager', 'ip_scanner', 'browser_backup', 'boot_manager', 'printer_fix',
                     'auto_shutdown', 'backup_driver', 'currency', 'datetime_tool', 'desktop_icon',
                     'firewall', 'folder_size', 'hosts_editor', 'office_opt', 'other_tools',
                     'sendto_editor', 'server_tools', 'services_manager', 'wincheck', 'win_update',
                     'classic_menu', 'zoom_screen', 'zoom_screen_gui', 'fluent_cleaner']:
            check('modules.' + name, lambda name=name: importlib.import_module('modules.' + name).__file__)
        from web_api import Api
        api = Api()
        for method, expected, keys in [
            ('get_app_info', dict, ('version', 'is_admin')),
            ('get_computer_info', dict, ('cpu', 'os', 'ram_total')),
            ('get_startup_entries', list, ()),
            ('get_installed_apps', dict, ('data',)),
            ('get_printers', list, ()),
            ('get_network_adapters', dict, ('data',)),
            ('get_windows_services', dict, ('services', 'total')),
            ('get_boot_entries', dict, ('entries', 'timeout')),
            ('get_system_drives', list, ()),
            ('get_datetime_info', dict, ('timezone',)),
            ('get_browser_backup_info', dict, ('browsers', 'history')),
        ]:
            check('api.' + method, lambda method=method, expected=expected, keys=keys:
                  summarize_api_result(getattr(api, method)(), expected, keys))
        def cleaner_integrity():
            from modules import fluent_cleaner
            bundle = fluent_cleaner.bundle_directory()
            manifest = json.loads((bundle / 'release-manifest.json').read_text(encoding='utf-8'))
            fluent_cleaner.verify_files(bundle, manifest)
            return f"Verified {len(manifest['files'])} bundled files"
        check('fluentcleaner.integrity', cleaner_integrity)
        def dpapi_roundtrip():
            from security_utils import protect_backup_bytes
            fixture = b'ITTools synthetic release check - no user data'
            encrypted = protect_backup_bytes(fixture)
            if encrypted == fixture or protect_backup_bytes(encrypted, decrypt=True) != fixture:
                raise ValueError('DPAPI roundtrip failed')
            return 'Synthetic backup encryption/decryption verified'
        check('backup.dpapi', dpapi_roundtrip)


    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()

    def tk_window():
        import tkinter
        root = tkinter.Tk()
        root.withdraw()
        try:
            root.update_idletasks()
            return root.tk.call('info', 'patchlevel')
        finally:
            root.destroy()

    check('tkinter.window', tk_window)
    def web_assets():
        from html.parser import HTMLParser
        root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
        class Scripts(HTMLParser):
            def handle_starttag(self, tag, attrs):
                attributes = dict(attrs)
                if tag == 'script' and attributes.get('src'):
                    script = (root / 'web' / attributes['src']).resolve()
                    if not script.is_relative_to(root.resolve()) or not script.is_file():
                        raise FileNotFoundError('Missing or invalid web script: ' + attributes['src'])
        html = (root / 'web/index.html').read_text(encoding='utf-8')
        Scripts().feed(html)
        if not (root / 'web/logo.png').is_file():
            raise FileNotFoundError('Missing application logo')
        return 'HTML, script files and logo verified'
    check('web.assets', web_assets)
    report['ok'] = all(check['ok'] for check in report['checks'].values())
    Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if report['ok'] else 1
