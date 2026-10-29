"""Release regression tests. Windows mutations use mocks; fixtures stay in scratch."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ITTools'))
from web_api import Api
import runtime_diagnostics as diagnostics
from modules import boot_manager as boot, browser_backup as backup, folder_size

def reply(code=0, text=''):
    return SimpleNamespace(returncode=code, stdout=text, stderr='')

class ReleaseTests(unittest.TestCase):
    def test_service_failed_command_not_success_keyword(self):
        service = Mock(); service.status.return_value = 'stopped'
        with patch('web_api.subprocess.run', return_value=reply(1, 'SUCCESS is not guaranteed')) as run, patch('psutil.win_service_get', return_value=service), patch('time.sleep'):
            self.assertFalse(Api().manage_windows_service('QA', 'start')['success'])
            self.assertFalse(Api().set_service_startup_type('QA', 'Automatic')['success'])

    def test_service_transition_must_reach_target(self):
        service = Mock(); service.status.return_value = 'start_pending'
        with patch('web_api.subprocess.run', return_value=reply()), patch('psutil.win_service_get', return_value=service), patch('time.sleep'):
            response = Api().manage_windows_service('QA', 'start')
            self.assertFalse(response['success'])
            self.assertTrue(response.get('pending'))

    def test_service_names_are_arguments_and_restart_waits_for_stop(self):
        service = Mock(); service.status.side_effect = ['stopped', 'running']
        with patch('web_api.subprocess.run', return_value=reply()) as run, patch('psutil.win_service_get', return_value=service), patch('time.sleep'):
            self.assertTrue(Api().manage_windows_service('QA & Literal', 'restart')['success'])
            self.assertEqual([c.args[0] for c in run.call_args_list], [['sc.exe','stop','QA & Literal'], ['sc.exe','start','QA & Literal']])
            self.assertTrue(all(not c.kwargs.get('shell',False) for c in run.call_args_list))

    def test_service_restart_stops_on_stop_failure(self):
        with patch('web_api.subprocess.run', return_value=reply(5, 'Access denied')) as run:
            self.assertFalse(Api().manage_windows_service('QA', 'restart')['success'])
            self.assertEqual(run.call_count, 1)

    def test_service_invalid_type_does_not_enable_automatically(self):
        with patch('web_api.subprocess.run') as run:
            self.assertFalse(Api().set_service_startup_type('QA','typo')['success'])
            self.assertFalse(Api().manage_windows_service('QA','typo')['success'])
            run.assert_not_called()

    def test_service_delayed_auto_is_preserved(self):
        with patch('web_api.subprocess.run', return_value=reply()) as run:
            self.assertTrue(Api().set_service_startup_type('QA', 'Automatic (Delayed)')['success'])
            self.assertEqual(run.call_args.args[0], ['sc.exe','config','QA','start=','delayed-auto'])

    def test_boot_delete_error_is_failure(self):
        with patch.object(boot.subprocess,'run', return_value=reply(1,'not successfully completed')):
            self.assertFalse(boot.delete_boot_entry('{12345678-1234-1234-1234-123456789012}')['success'])

    def test_boot_invalid_input_never_executes(self):
        with patch.object(boot.subprocess,'run') as run:
            self.assertFalse(boot.delete_boot_entry('/all')['success'])
            for timeout in (-1, 1000, 'bad', True, 1.5):
                self.assertFalse(boot.set_boot_timeout(timeout)['success'])
            run.assert_not_called()

    def test_diagnostic_checks_reject_failed_or_incomplete_api_data(self):
        for value in ({'success':False,'message':'denied'}, {'success':True}, []):
            with self.assertRaises((ValueError, TypeError)):
                diagnostics.summarize_api_result(value, dict, ('data',))
        text=diagnostics.summarize_api_result({'success':True, 'data':['private fixture']}, dict, ('data',))
        self.assertNotIn('private fixture', text)

    def test_restore_respects_selected_browser_and_data_categories(self):
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT/'ITTools/scratch') as directory:
            root=Path(directory); source=root/'packages'/'Chrome'/'Default'; source.mkdir(parents=True)
            for file in ('Bookmarks','History','Login Data'): (source/file).write_bytes(b'synthetic')
            definitions={name:dict(name=name,type='chromium',process=[],profile_root=str(root/name)) for name in ('Chrome','Edge')}
            self.assertEqual(backup.resolve_restore_plan(str(source.parent), ['Edge'], definitions), {})
            self.assertEqual(backup.resolve_restore_plan(str(root/'packages'), [], definitions), {})
            with patch.object(backup,'get_browser_definitions',return_value=definitions), patch.object(backup,'close_browser_processes'):
                result=backup.restore_browser_data(str(root/'packages'), ['Chrome'], {'bookmarks':True})
                self.assertTrue(result['success'])
                restored=root/'Chrome'/'Default'
                self.assertTrue((restored/'Bookmarks').exists())
                self.assertFalse((restored/'History').exists())
                self.assertFalse((restored/'Login Data').exists())

    def test_empty_restore_options_cannot_overwrite_profile(self):
        with patch.object(backup,'close_browser_processes') as close:
            self.assertFalse(backup.restore_browser_data(str(ROOT), ['Chrome'], {})['success'])
            close.assert_not_called()

    def test_directory_scan_fixture_matches_total(self):
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT/'ITTools/scratch') as directory:
            root=Path(directory); (root/'nested').mkdir()
            (root/'a.bin').write_bytes(b'a'*7); (root/'nested'/'b.bin').write_bytes(b'b'*11)
            value=folder_size.scan_directory_sizes(str(root))
            self.assertTrue(value['success'])
            self.assertEqual(value['total_bytes'],18)
            self.assertEqual(sum(n['size_bytes'] for n in value['items']),18)
            self.assertFalse(folder_size.scan_directory_sizes(str(root/'missing'))['success'])

if __name__=='__main__': unittest.main()
