"""Tests for Camera Manager module."""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

# Ensure ITTools directory is in sys.path
BASE_DIR = Path(__file__).resolve().parents[1] / "ITTools"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from modules import camera_manager


class CameraManagerTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "cameras.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_cameras_creates_default_if_missing(self):
        cams = camera_manager.load_cameras(self.config_path)
        self.assertIsInstance(cams, list)
        self.assertGreater(len(cams), 0)
        self.assertTrue(os.path.exists(self.config_path))
        self.assertIn("ip", cams[0])
        self.assertIn("name", cams[0])

    def test_save_and_load_cameras(self):
        sample = [
            {
                "id": "cam-test-1",
                "name": "Camera Quầy Check-in 1",
                "ip": "10.90.39.55",
                "port_web": 80,
                "port_rtsp": 554,
                "location": "Khu A",
                "notes": "Test camera"
            }
        ]
        res = camera_manager.save_cameras(sample, self.config_path)
        self.assertTrue(res.get("success"))
        loaded = camera_manager.load_cameras(self.config_path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["name"], "Camera Quầy Check-in 1")
        self.assertEqual(loaded[0]["ip"], "10.90.39.55")

    def test_save_cameras_rejects_invalid_ip(self):
        invalid_sample = [
            {"id": "cam-bad", "name": "Hacker Cam", "ip": "999.999.999.999; rm -rf /", "port_web": 80}
        ]
        res = camera_manager.save_cameras(invalid_sample, self.config_path)
        self.assertFalse(res.get("success"))

    def test_probe_port_and_check_status_offline(self):
        # Test probing an unreachable local IP / port with quick timeout
        res = camera_manager.check_camera_status(
            {"id": "cam-off", "name": "Offline Cam", "ip": "127.0.0.1", "port_web": 59999, "port_rtsp": 59998},
            timeout=0.1
        )
        self.assertFalse(res["is_online"])
        self.assertFalse(res["rtsp_open"])
        self.assertFalse(res["web_open"])

    def test_ping_all_cameras_concurrent(self):
        cams = [
            {"id": "c1", "name": "Cam 1", "ip": "127.0.0.1", "port_web": 59991, "port_rtsp": 59992},
            {"id": "c2", "name": "Cam 2", "ip": "127.0.0.1", "port_web": 59993, "port_rtsp": 59994},
        ]
        results = camera_manager.ping_all_cameras(cams, timeout=0.1)
        self.assertEqual(len(results), 2)
        self.assertIn("is_online", results[0])
        self.assertIn("is_online", results[1])

    def test_scan_camera_range_invalid_subnet(self):
        res = camera_manager.scan_camera_range("invalid.ip.range", 1, 5)
        self.assertFalse(res.get("success"))


if __name__ == "__main__":
    unittest.main()
