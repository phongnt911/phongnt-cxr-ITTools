"""Read-only Windows API checks; never dispatch arbitrary/mutating API methods."""
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / 'ITTools' / 'scratch' / 'qa-results'
CASES = {
    'external_ip': ('get_external_ip', []), 'license_audit': ('get_wincheck_audit', []),
    'winget_session': ('check_bg_winget_session', []), 'app': ('get_app_info', []), 'autostart': ('get_autostart_status', []),
    'printers': ('get_printers', []), 'credentials': ('get_credentials', []),
    'local_users': ('get_local_groups_and_users', []),
    'computer': ('get_computer_info', []), 'monitoring': ('get_realtime_stats', []),
    'missing_drivers': ('check_missing_drivers', []),
    'desktop_icons': ('get_desktop_icon_settings', []), 'startup': ('get_startup_entries', []),
    'drives': ('get_system_drives', []), 'windows_security': ('get_win_update_status', []),
    'uninstall': ('get_installed_apps', []), 'bitlocker': ('get_bitlocker_drives', []),
    'currency': ('get_currency_rates', []), 'firewall': ('get_firewall_status', []),
    'firewall_rules': ('get_firewall_rules_detail', []),
    'network': ('get_network_adapters', []), 'subnet': ('calculate_subnet', ['192.0.2.130', 24]),
    'ipv6': ('get_ipv6_status', []), 'sendto': ('get_sendto_entries', []),
    'datetime': ('get_datetime_info', []), 'browser_backup': ('get_browser_backup_info', []),
    'shutdown_tasks': ('get_scheduled_shutdown_tasks', []),
    'shutdown_logs': ('get_shutdown_event_logs', [5]), 'hosts': ('get_hosts_file', []),
    'office_status': ('get_office_install_progress', []), 'system_tweaks': ('get_system_tweaks_status', []),
    'software_catalog': ('get_software_catalog', []), 'winget_status': ('get_winget_install_status', []),
    'scan_defaults': ('get_ip_scanner_default_range', []),
    'port_definitions': ('get_port_definitions', []),
    'classic_menu': ('get_classic_menu_status', []), 'drivers': ('get_installed_drivers', []),
    'services': ('get_windows_services', []), 'nic_teams': ('get_nic_teams', []),
    'ad_domain': ('get_ad_domain_info', []), 'iscsi': ('list_iscsi_targets', []),
    'boot': ('get_boot_entries', []), 'partitions': ('get_available_partitions', []),
    'zoom': ('get_zoom_screen_status', []),
}


def worker(name):
    sys.path.insert(0, str(ROOT / 'ITTools'))
    from web_api import Api
    api = Api()
    method, args = CASES[name]
    started = time.monotonic()
    try:
        value = getattr(api, method)(*args)
        # Raw data stays local in ignored scratch for UI replay, never stdout.
        (SCRATCH / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, default=str), encoding='utf-8')
        errors = [entry['message'] for entry in api._logs if entry['level'] == 'ERROR']
        failed = isinstance(value, dict) and value.get('success') is False
        summary = {'case': name, 'method': method, 'status': 'FAIL' if failed or errors else 'PASS',
                   'type': type(value).__name__, 'seconds': round(time.monotonic() - started, 2),
                   'keys': sorted(value) if isinstance(value, dict) else [],
                   'items': len(value) if isinstance(value, list) else None,
                   'errors': errors or ([value.get('message', '')] if failed else [])}
    except Exception as error:
        summary = {'case': name, 'method': method, 'status': 'ERROR', 'error': str(error)}
    (SCRATCH / (name + '.summary.json')).write_text(json.dumps(summary, ensure_ascii=False), encoding='utf-8')


def run_case(name):
    try:
        result = subprocess.run([sys.executable, '-X', 'utf8', __file__, '--case', name],
                                cwd=ROOT, capture_output=True, timeout=120)
        file = SCRATCH / (name + '.summary.json')
        if result.returncode or not file.exists():
            return {'case': name, 'status': 'ERROR', 'error': result.stderr.decode('utf-8', errors='replace')[-1500:]}
        return json.loads(file.read_text(encoding='utf-8'))
    except subprocess.TimeoutExpired:
        return {'case': name, 'status': 'TIMEOUT'}


if __name__ == '__main__':
    SCRATCH.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) == 3 and sys.argv[1] == '--case':
        worker(sys.argv[2])
    else:
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for future in concurrent.futures.as_completed([pool.submit(run_case, name) for name in CASES]):
                result = future.result()
                results.append(result)
                print(result['case'], result['status'], flush=True)
        (ROOT / 'security-review' / 'qa-windows.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
