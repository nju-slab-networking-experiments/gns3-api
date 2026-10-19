import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build_api"))
from utils import config_router, RouterConfigError


class ConsoleScriptTests(unittest.TestCase):
    def test_vlan_database_and_configuration_mode_transitions(self):
        commands = ["enable", "vlan database", "vlan 20 name TRUST", "exit",
                    "configure terminal", "hostname HV1", "end", "write memory"]
        outputs = iter([b"Router#", b"Router#", b"Router(vlan)#",
                        b"Router(vlan)#", b"Router#", b"Router(config)#",
                        b"HV1(config)#", b"HV1#", b"HV1#", b"HV1#"])
        telnet = Mock()

        def expect(patterns, timeout):
            output = next(outputs)
            match = patterns[0].search(output)
            self.assertIsNotNone(match, output)
            return 0, match, output

        telnet.expect.side_effect = expect
        with patch("utils._connect_router_console", return_value=telnet), \
                patch("utils.router_initialize", return_value=True), \
                patch("utils.time.sleep"), patch("utils._save_ios_config") as save:
            config_router(5000, commands)
        self.assertEqual([b"\r\n", b"terminal length 0\r\n"] +
                         [c.encode() + b"\r\n" for c in commands] + [b"end\r\n"],
                         [call.args[0] for call in telnet.write.call_args_list])
        save.assert_called_once_with(telnet)
        telnet.close.assert_called_once()

    def test_console_script_rejection_prevents_save(self):
        telnet = Mock()
        telnet.expect.side_effect = [
            (0, None, b"Router#"), (0, None, b"Router#"),
            (0, None, b"% Invalid input detected at '^' marker.\r\nRouter#")]
        with patch("utils._connect_router_console", return_value=telnet), \
                patch("utils.router_initialize", return_value=True), \
                patch("utils.time.sleep"), patch("utils._save_ios_config") as save:
            with self.assertRaises(RouterConfigError):
                config_router(5000, ["enable", "invalid-command"])
        save.assert_not_called()
        telnet.close.assert_called_once()
