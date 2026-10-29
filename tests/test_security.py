"""Run: .venv/Scripts/python.exe -m unittest discover -s tests -v"""
import ast
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ITTools'))
from security_utils import validate_host, protect_backup_bytes, require_microsoft_signature
from web_api import Api
from modules import browser_backup, printer_fix, win_update


class SecurityTests(unittest.TestCase):
    def test_host_validation_blocks_script_and_accepts_real_hosts(self):
        for host in ['127.0.0.1', '::1', 'server-01.example.com', 'PRINTER01']:
            self.assertEqual(validate_host(host), host)
        for host in ['', 'x$(Write-Output marker)', 'x";echo marker', 'x & echo marker', 'x\ncommand',
                     'fe80::1%$(echo marker)']:
            with self.assertRaises(ValueError):
                validate_host(host)

    def test_winrm_rejects_injection_before_launch(self):
        with patch('web_api.subprocess.Popen') as launch:
            self.assertFalse(Api().open_winrm_session('127.0.0.1$(echo marker)')['success'])
            launch.assert_not_called()
            self.assertTrue(Api().open_winrm_session('server-01')['success'])
            self.assertIn('Enter-PSSession', launch.call_args.args[0][-1])

    def test_password_is_data_not_a_command(self):
        password = ' x" & echo marker & rem " '
        with patch('web_api.save_windows_credential') as save, patch('web_api.subprocess.run') as run:
            self.assertTrue(Api().save_credential('server', 'user', password)['success'])
            save.assert_called_once_with('server', 'user', password)
            run.assert_not_called()

    def test_printer_user_is_standard_and_never_logs_password(self):
        password = 'synthetic " $() password'
        api = Api()
        with patch('web_api.subprocess.run', return_value=Mock(returncode=0)) as run:
            self.assertTrue(api.create_printer_share_user('print_user', password)['success'])
            self.assertNotIn(password, str(run.call_args.args))
            self.assertNotIn(password, str(api._logs))
            self.assertIn('S-1-5-32-545', run.call_args.args[0][-1])
            self.assertNotIn('S-1-5-32-544', run.call_args.args[0][-1])

    def test_signature_failure_blocks_installer(self):
        with patch('security_utils.subprocess.run', return_value=Mock(returncode=1)):
            with self.assertRaises(ValueError):
                require_microsoft_signature('untrusted.exe')

    def test_no_bulk_unblock_or_protection_disable(self):
        with patch('web_api.subprocess.run') as run:
            self.assertFalse(Api().unblock_files_quick()['success'])
            for action in [win_update.set_defender_status, win_update.set_uac_status, win_update.set_smartscreen_status]:
                self.assertFalse(action(False)['success'])
            run.assert_not_called()

    def test_printer_uses_sfc_and_reports_failure(self):
        progress = Mock()
        with patch('modules.printer_fix.subprocess.run', return_value=Mock(returncode=1)) as run:
            printer_fix.one_click_fix_all_lan_files(progress_cb=progress)
            self.assertEqual(run.call_args.args[0], ['sfc.exe', '/scannow'])
            self.assertFalse(progress.call_args.args[0]['success'])
        self.assertEqual(printer_fix.get_clean_spooler_files(), {})

    @unittest.skipUnless(sys.platform == 'win32', 'Windows DPAPI required')
    def test_backup_encryption_restore_and_tamper_failure(self):
        secret = b'synthetic password fixture - no real browser data'
        encrypted = protect_backup_bytes(secret)
        self.assertNotIn(secret, encrypted)
        self.assertEqual(protect_backup_bytes(encrypted, decrypt=True), secret)
        with tempfile.TemporaryDirectory(dir=ROOT / 'ITTools' / 'scratch') as folder:
            folder = Path(folder)
            source, backup, restored = [folder / name for name in ['source', 'backup', 'restored']]
            source.write_bytes(secret)
            browser_backup._copy_file_safe(str(source), str(backup), protect=True)
            self.assertTrue(backup.read_bytes().startswith(browser_backup.BACKUP_MAGIC))
            self.assertNotIn(secret, backup.read_bytes())
            browser_backup._copy_file_safe(str(backup), str(restored))
            self.assertEqual(restored.read_bytes(), secret)
            backup.write_bytes(browser_backup.BACKUP_MAGIC + b'corrupt')
            with self.assertRaises(RuntimeError):
                browser_backup._copy_file_safe(str(backup), str(restored))
            self.assertEqual(restored.read_bytes(), secret)

    @unittest.skipUnless(sys.platform == 'win32', 'Windows DPAPI and ACL required')
    def test_full_backup_and_restore_synthetic_browser(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'ITTools' / 'scratch') as folder:
            folder = Path(folder)
            profile = folder / 'source' / 'fixture.default'
            profile.mkdir(parents=True)
            secret = b'synthetic sensitive fixture'
            (profile / 'logins.json').write_bytes(secret)
            (profile / 'key4.db').write_bytes(secret)
            definitions = {'Firefox': {'name': 'Firefox', 'type': 'firefox', 'process': [],
                                        'profile_root': str(profile.parent)}}
            with patch.object(browser_backup, 'get_browser_definitions', return_value=definitions), \
                 patch.object(browser_backup, 'close_browser_processes'):
                result = browser_backup.backup_browser_data(['Firefox'], {'passwords': True}, str(folder / 'packages'))
                self.assertTrue(result['success'])
                saved = Path(result['backup_dir']) / 'Firefox' / 'fixture.default' / 'logins.json'
                self.assertNotIn(secret, saved.read_bytes())
                definitions['Firefox']['profile_root'] = str(folder / 'restored')
                restored = browser_backup.restore_browser_data(result['backup_dir'], ['Firefox'])
                self.assertTrue(restored['success'])
                self.assertEqual((folder / 'restored' / 'fixture.default' / 'logins.json').read_bytes(), secret)

    def test_all_python_parses_and_unsafe_printer_settings_removed(self):
        for file in (ROOT / 'ITTools').rglob('*.py'):
            if 'scratch' not in file.parts:
                ast.parse(file.read_text(encoding='utf-8-sig'))
        for name in ['modules/printer_fix.py', 'web_api.py']:
            source = (ROOT / 'ITTools' / name).read_text(encoding='utf-8')
            for value in ['RestrictDriverInstallationToAdministrators /t REG_DWORD /d 0',
                          'NoWarningNoElevationOnInstall /t REG_DWORD /d 1',
                          'AllowInsecureGuestAuth /t REG_DWORD /d 1']:
                self.assertNotIn(value, source)


if __name__ == '__main__':
    unittest.main()
