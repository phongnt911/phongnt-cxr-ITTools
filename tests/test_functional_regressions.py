"""Regression cases for failures found during Windows functional QA. All writes mocked."""
import ast
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ITTools'))
from web_api import Api
from modules import ip_manager as ip, bitlocker as bl, auto_shutdown as power, startup_manager as startup, server_tools, uninstall_manager as uninstall

def result(code=0, out='', err=''):
    return SimpleNamespace(returncode=code, stdout=out, stderr=err)

class FunctionalRegressionTests(unittest.TestCase):
    def test_subnet_boundaries(self):
        for cidr, hosts in [(0, '4,294,967,294'), (24, '254'), (31, '2'), (32, '1')]:
            self.assertEqual(ip.calculate_subnet('192.0.2.130', cidr)['data']['usable_hosts'], hosts)
        self.assertFalse(ip.calculate_subnet('invalid', 24)['success'])
        self.assertFalse(ip.calculate_subnet('192.0.2.1', 33)['success'])

    def test_invalid_ip_never_runs_command(self):
        with patch.object(ip.subprocess, 'run') as run:
            for values in [('Ethernet', 'oops'), ('Ethernet', 'static', '1.2.3.4 & calc'),
                           ('Ethernet', 'static', '192.0.2.1', '255.0.255.0'),
                           ('Ethernet', 'static', '192.0.2.1', '255.255.255.0', '', 'oops')]:
                self.assertFalse(ip.apply_ip_settings(*values)['success'])
            run.assert_not_called()

    def test_dns_failure_is_reported_for_dhcp_and_static(self):
        for mode in ('dhcp', 'static'):
            with patch.object(ip.subprocess, 'run', side_effect=[result(), result(1, err='DNS failed')]) as run:
                self.assertFalse(ip.apply_ip_settings('Ethernet & test', mode, '192.0.2.1', dns1='1.1.1.1')['success'])
                self.assertIsInstance(run.call_args.args[0], list)
                self.assertFalse(run.call_args.kwargs.get('shell', False))

    def test_ipv6_failure_cannot_look_disabled_or_successful(self):
        with patch.object(ip.subprocess, 'run', return_value=result(1, err='Access denied')):
            self.assertFalse(ip.get_ipv6_status()['success'])
            self.assertFalse(ip.set_ipv6_status(True)['success'])

    def test_bitlocker_errors_are_not_success_keywords(self):
        with patch.object(bl.subprocess, 'run', return_value=result(1, 'ERROR: protection encryption password failed')):
            for action in ('enable', 'disable'):
                self.assertFalse(bl.set_bitlocker('C:', action)['success'])

    def test_bitlocker_invalid_drive_does_not_execute(self):
        with patch.object(bl.subprocess, 'run') as run:
            for drive in ('', 'C:; whoami', 'C:\\Windows', None):
                self.assertFalse(bl.set_bitlocker(drive, 'disable')['success'])
                self.assertFalse(bl.get_bitlocker_recovery_key(drive)['success'])
            run.assert_not_called()

    def test_recovery_key_read_never_creates_protector(self):
        with patch.object(bl.subprocess, 'run', return_value=result()) as run:
            self.assertFalse(bl.get_bitlocker_recovery_key('C:')['success'])
            self.assertEqual(run.call_count, 2)
            for call in run.call_args_list:
                self.assertNotIn('-add', call.args[0])
                self.assertNotIn('Add-BitLockerKeyProtector', str(call.args))

    def test_dispatch_requires_explicit_action_and_drive(self):
        api = Api()
        with patch('web_api.subprocess.run') as run:
            for module, action in [('typo', 'open'), ('bitlocker', 'open'), ('bitlocker', 'disable'),
                                   ('firewall', 'typo'), ('win_update', 'open'), ('datetime_tool', 'open')]:
                self.assertFalse(api.run_tool_module(module, action)['success'])
            run.assert_not_called()
        with patch.object(api, 'set_firewall_action', return_value={'success': False}) as setter:
            self.assertFalse(api.run_tool_module('firewall', 'enable')['success'])
            setter.assert_called_once_with('enable_all')

    def test_power_failure_and_hibernate_command(self):
        with patch.object(power.subprocess, 'run', return_value=result(1, err='Power denied')) as run:
            self.assertFalse(power.execute_immediate_power('hibernate')['success'])
            self.assertEqual(run.call_args.args[0], 'shutdown /h')

    def test_invalid_timer_does_not_schedule_shutdown(self):
        with patch.object(power, '_run_ps') as run:
            for action, minutes in [('typo', 1), ('shutdown', 'nan'), ('shutdown', 'inf'), ('shutdown', -1), ('shutdown', 1e30)]:
                self.assertFalse(power.create_quick_timer_task(action, minutes)['success'])
            for changes in [dict(action='typo'), dict(freq='oops'), dict(time_str='23:00";whoami'),
                            dict(days=['Monday;whoami']), dict(date_str='2026-99-99')]:
                args = dict(name='QA', action='shutdown', freq='daily', time_str='23:00') | changes
                self.assertFalse(power.create_scheduled_shutdown_task(**args)['success'])
            for fn in (power.delete_scheduled_shutdown_task, power.run_scheduled_shutdown_task_now):
                self.assertFalse(fn('other-task')['success'])
                self.assertFalse(fn('ITTools_Shutdown_x";whoami')['success'])
            run.assert_not_called()

    def test_hibernate_timer_uses_hibernate(self):
        with patch.object(power, '_run_ps', return_value=result()) as run:
            self.assertTrue(power.create_quick_timer_task('hibernate', 5)['success'])
            script = run.call_args.args[0]
            self.assertIn('shutdown.exe', script)
            self.assertIn("-Argument '/h'", script)

    def test_startup_approval_uses_correct_registry_locations(self):
        self.assertTrue(startup._startup_approval('HKLM\\WOW64Run')[1].endswith('Run32'))
        self.assertTrue(startup._startup_approval('User Startup')[1].endswith('StartupFolder'))
        with patch.object(startup.winreg, 'CreateKey') as create:
            self.assertFalse(startup.toggle_startup_status('QA', 'HKCU\\RunOnce', False)['success'])
            create.assert_not_called()

    def test_startup_failed_save_preserves_old_entry(self):
        with patch.object(startup.winreg, 'CreateKey', side_effect=PermissionError('denied')), patch.object(startup, 'delete_startup_entry') as delete:
            self.assertFalse(startup.save_startup_entry('QAnew', 'QA.exe', old_name='QAold')['success'])
            delete.assert_not_called()

    def test_startup_folder_shortcut_quotes_are_literal(self):
        with patch.object(startup.os, 'makedirs'), patch.object(startup.subprocess, 'run') as run:
            self.assertTrue(startup.save_startup_entry('QA', "C:\\QA's $data.exe", 'User Startup')['success'])
            script = run.call_args.args[0][-1]
            self.assertIn("QA''s $data.exe'", script)
            self.assertTrue(run.call_args.kwargs['check'])

    def test_startup_delete_rejects_path_outside_startup(self):
        with patch.object(startup.os, 'remove') as remove:
            self.assertFalse(startup.delete_startup_entry('QA', 'User Startup', str(ROOT / 'README.md'))['success'])
            remove.assert_not_called()

    def test_iscsi_nonzero_exit_is_failure(self):
        with patch.object(server_tools.subprocess, 'run', return_value=result(1, 'Access denied')):
            self.assertFalse(server_tools.list_iscsi_targets()['success'])

    def test_frontend_api_calls_exist(self):
        import re
        api_methods = set(dir(Api))
        for path in (ROOT / 'ITTools/web').rglob('*.js'):
            for method in re.findall(r'(?:window\.)?pywebview\.api\.(\w+)', path.read_text(encoding='utf-8')):
                self.assertIn(method, api_methods, f'{path.name}: {method}')

    def test_failed_or_cancelled_uninstaller_never_deletes_leftovers(self):
        for exit_code in (1, 1602):
            process = MagicMock()
            process.poll.return_value = exit_code
            with patch.object(uninstall, 'kill_app_processes'), patch.object(uninstall.subprocess, 'Popen', return_value=process), patch.object(uninstall, 'deep_scan_leftover_registry') as registry, patch.object(uninstall, 'deep_scan_leftover_folders') as folders:
                self.assertFalse(uninstall.run_deep_clean_uninstall('QA', 'QA.exe')['success'])
                registry.assert_not_called()
                folders.assert_not_called()

    def test_failed_store_uninstall_never_deletes_data(self):
        with patch.object(uninstall, 'uninstall_store_app', return_value={'success': False, 'message': 'denied'}), patch.object(uninstall, 'deep_scan_leftover_registry') as registry, patch.object(uninstall, 'clean_store_app_leftovers') as folders:
            self.assertFalse(uninstall.run_deep_clean_uninstall('QA', '', is_store=True, package_full_name='QA_1')['success'])
            registry.assert_not_called()
            folders.assert_not_called()

    def test_valid_ip_and_bitlocker_commands_succeed(self):
        with patch.object(ip.subprocess, 'run', return_value=result()) as run:
            self.assertTrue(ip.apply_ip_settings('Ethernet', 'static', '192.0.2.10', '255.255.255.0', '192.0.2.1', '1.1.1.1', '8.8.8.8')['success'])
            self.assertEqual(run.call_count, 3)
        with patch.object(bl.subprocess, 'run', return_value=result()) as run:
            self.assertTrue(bl.set_bitlocker('D:', 'disable')['success'])
            self.assertEqual(run.call_args.args[0], ['manage-bde', '-off', 'D:'])

    def test_successful_uninstall_can_clean_after_confirmation(self):
        process = MagicMock()
        process.poll.return_value = 0
        with patch.object(uninstall, 'kill_app_processes'), patch.object(uninstall.subprocess, 'Popen', return_value=process), patch.object(uninstall.time, 'sleep'), patch.object(uninstall, '_check_reg_key_exists', return_value=False), patch.object(uninstall, 'deep_scan_leftover_registry', return_value=[]) as registry, patch.object(uninstall, 'deep_scan_leftover_folders', return_value=[]) as folders:
            self.assertTrue(uninstall.run_deep_clean_uninstall('QA', 'QA.exe', reg_key_name='QA')['success'])
            registry.assert_called_once()
            folders.assert_called_once()

    def test_no_duplicate_api_methods(self):
        tree = ast.parse((ROOT / 'ITTools/web_api.py').read_text(encoding='utf-8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Api')
        names = [n.name for n in cls.body if isinstance(n, ast.FunctionDef)]
        self.assertEqual(len(names), len(set(names)))
        self.assertIn('is_admin', Api().get_app_info())

if __name__ == '__main__':
    unittest.main()
