import unittest
from unittest.mock import patch
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1] / "ITTools"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from modules import rustdesk_manager


class RustDeskManagerTests(unittest.TestCase):
    def test_validate_mac_valid(self):
        self.assertTrue(rustdesk_manager.validate_mac("00:11:22:33:44:55"))
        self.assertTrue(rustdesk_manager.validate_mac("AA-BB-CC-DD-EE-FF"))
        self.assertTrue(rustdesk_manager.validate_mac("a1:b2:c3:d4:e5:f6"))

    def test_validate_mac_invalid(self):
        self.assertFalse(rustdesk_manager.validate_mac("invalid-mac"))
        self.assertFalse(rustdesk_manager.validate_mac("00:11:22:33:44:55:66"))
        self.assertFalse(rustdesk_manager.validate_mac("00:11:22:33:44; rm -rf"))
        self.assertFalse(rustdesk_manager.validate_mac(""))

    def test_create_magic_packet(self):
        packet = rustdesk_manager.create_magic_packet("00:11:22:33:44:55")
        self.assertEqual(len(packet), 102)
        self.assertEqual(packet[:6], b"\xff" * 6)
        expected_mac_bytes = bytes.fromhex("001122334455")
        self.assertEqual(packet[6:12], expected_mac_bytes)
        self.assertEqual(packet[-6:], expected_mac_bytes)

    def test_send_wake_on_lan_invalid_mac(self):
        res = rustdesk_manager.send_wake_on_lan("invalid-mac")
        self.assertFalse(res.get("success"))
        self.assertIn("không hợp lệ", res.get("message", "").lower())

    def test_send_wake_on_lan_valid_payload(self):
        res = rustdesk_manager.send_wake_on_lan("AA:BB:CC:DD:EE:FF", broadcast_ip="127.0.0.1")
        self.assertTrue(res.get("success"))

    def test_connect_direct_ip_rejects_invalid_ip(self):
        res = rustdesk_manager.connect_direct_ip("999.999.999.999; calc.exe")
        self.assertFalse(res.get("success"))
        self.assertIn("không hợp lệ", res.get("message", "").lower())

    @patch("modules.rustdesk_manager.subprocess.Popen")
    @patch("modules.rustdesk_manager.find_rustdesk_executable", return_value="C:\\fake\\rustdesk.exe")
    def test_connect_direct_ip_passes_connect_flag(self, mock_find, mock_popen):
        res = rustdesk_manager.connect_direct_ip("192.168.102.7:21118", password="secretpassword")
        self.assertTrue(res.get("success"))
        mock_popen.assert_called_once()
        cmd = mock_popen.call_args[0][0]
        self.assertIn("--connect", cmd)
        self.assertIn("192.168.102.7:21118", cmd)
        self.assertIn("--password", cmd)
        self.assertIn("secretpassword", cmd)

    def test_get_rustdesk_info_structure(self):
        info = rustdesk_manager.get_rustdesk_info()
        self.assertIsInstance(info, dict)
        self.assertIn("installed", info)
        self.assertIn("service_status", info)
        self.assertIn("direct_ip_listening", info)
        self.assertIn("local_ips", info)


if __name__ == "__main__":
    unittest.main()
