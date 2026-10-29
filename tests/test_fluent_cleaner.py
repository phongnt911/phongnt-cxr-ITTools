import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ITTools'))
from modules import fluent_cleaner as cleaner


class FluentCleanerTests(unittest.TestCase):
    def test_official_bundle_matches_manifest(self):
        bundle = ROOT / 'ITTools' / 'vendor' / 'fluentcleaner'
        manifest = json.loads((bundle / 'release-manifest.json').read_text())
        self.assertEqual(manifest['version'], cleaner.VERSION)
        cleaner.verify_files(bundle, manifest)

    def test_tampering_and_path_escape_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'ITTools' / 'scratch') as path:
            root = Path(path)
            (root / 'app.exe').write_bytes(b'fixture')
            manifest = {'files': {'app.exe': hashlib.sha256(b'fixture').hexdigest()}}
            cleaner.verify_files(root, manifest)
            (root / 'injected.dll').write_bytes(b'unexpected')
            with self.assertRaises(ValueError):
                cleaner.verify_files(root, manifest)
            with self.assertRaises(ValueError):
                cleaner.verify_files(root, {'files': {'../outside.exe': '0' * 64}})
            (root / 'app.exe').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                cleaner.verify_files(root, manifest)

    def test_launch_is_interactive_and_verified_before_execution(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'ITTools' / 'scratch') as path:
            bundle = Path(path) / 'bundle'
            bundle.mkdir()
            (bundle / 'FCleaner.exe').write_bytes(b'fixture')
            manifest = {'files': {'FCleaner.exe': hashlib.sha256(b'fixture').hexdigest()}}
            (bundle / 'release-manifest.json').write_text(json.dumps(manifest))
            process = Mock()
            process.wait.side_effect = subprocess.TimeoutExpired('fixture', 2)
            with patch.object(cleaner, 'bundle_directory', return_value=bundle), \
                 patch.object(cleaner.platform, 'machine', return_value='AMD64'), \
                 patch.dict('os.environ', {'LOCALAPPDATA': str(Path(path) / 'cache'),
                                           'APPDATA': str(Path(path) / 'settings')}), \
                 patch.object(cleaner, '_process', None), \
                 patch.object(cleaner.subprocess, 'Popen', return_value=process) as launch:
                self.assertTrue(cleaner.launch()['success'])
                self.assertEqual(len(launch.call_args.args[0]), 1)
                self.assertFalse(launch.call_args.kwargs['shell'])
                self.assertNotIn('/AUTO', str(launch.call_args))

    def test_cleaner_excludes_runtime_and_preserves_existing_settings(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'ITTools' / 'scratch') as path:
            root = Path(path)
            settings = root / 'roaming' / 'FluentCleaner' / 'settings.json'
            settings.parent.mkdir(parents=True)
            settings.write_text(json.dumps({'GlobalExclusions': ['PATH|C:\\Keep'],
                                            'GlobalExclusionsEnabled': False,
                                            'UnrelatedPreference': 'preserve'}))
            with patch.dict('os.environ', {'APPDATA': str(root / 'roaming'),
                                           'LOCALAPPDATA': str(root / 'local')}), \
                 patch.object(cleaner.sys, 'frozen', True, create=True), \
                 patch.object(cleaner.sys, '_MEIPASS', str(root / 'live-runtime'), create=True):
                cleaner.protect_host_runtime()
                cleaner.protect_host_runtime()
            result = json.loads(settings.read_text(encoding='utf-8'))
            self.assertTrue(result['GlobalExclusionsEnabled'])
            self.assertEqual(result['UnrelatedPreference'], 'preserve')
            self.assertEqual(len(result['GlobalExclusions']), 3)
            self.assertIn('PATH|' + str((root / 'live-runtime').resolve()), result['GlobalExclusions'])


if __name__ == '__main__':
    unittest.main()
