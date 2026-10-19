import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'build_api'))
from lab8 import apply_configs
import utils


class ApplyConfigsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'configA').mkdir()
        self.nodes = {}
        for name in ('ISP-A-BR1', 'TRANSIT-BR1'):
            self.nodes[name] = dict(node_id=name, name=name, node_type='dynamips',
                                    console_type='telnet', console=5000,
                                    console_host='127.0.0.1', status='started')
            (self.root / 'configA' / f'{name}.cfg').write_text(
                '! comment\nenable\nconfigure terminal\nend\nclear ip bgp 1.1.1.1 soft in\n')
        self.state = self.root / 'build_state.json'
        self.state.write_text(json.dumps(dict(project_id='p', project_name='lab7',
                                             server='http://localhost:3080/v2', nodes=self.nodes)))
        self.original = self.state.read_bytes()
        self.profile = self.root / 'configure.json'
        self.profile.write_text(json.dumps(dict(state='build_state.json', default='configA',
            variants={'configA': 'configA'})))
        self.client = Mock()
        self.client._request.side_effect = [Mock(json=lambda: dict(name='lab7', status='opened')),
                                           Mock(json=lambda: list(self.nodes.values()))]

    def test_default_saves_then_stops_without_topology_mutation(self):
        with patch.object(apply_configs, 'GNS3Client', return_value=self.client), \
                patch.object(apply_configs, 'config_router') as configure:
            apply_configs.apply(self.profile)
        self.assertEqual(configure.call_count, 2)
        for call in configure.call_args_list:
            self.assertTrue(call.kwargs['save'])
            self.assertEqual(call.args[1][0], 'enable')
        self.assertEqual([call.args[0] for call in self.client._request.call_args_list], ['GET', 'GET'])
        self.assertEqual(self.client.stop_node.call_count, 2)
        self.client.create_project.assert_not_called()
        self.assertEqual(self.state.read_bytes(), self.original)
        self.assertTrue(json.loads((self.root / 'apply_state.json').read_text())['configured'])

    def test_failure_records_partial_application(self):
        with patch.object(apply_configs, 'GNS3Client', return_value=self.client), \
                patch.object(apply_configs, 'config_router', side_effect=[None, utils.RouterConfigError('bad command')]):
            with self.assertRaises(utils.RouterConfigError):
                apply_configs.apply(self.profile)
        result = json.loads((self.root / 'apply_state.json').read_text())
        self.assertFalse(result['configured'])
        self.assertEqual(result['completed_nodes'], ['ISP-A-BR1'])
        self.assertEqual(result['current_node'], 'TRANSIT-BR1')
        self.assertFalse(result['saved'])
        self.client.stop_node.assert_not_called()

    def test_shutdown_starts_after_all_saves_and_records_failure(self):
        events = []
        def save(*args, **kwargs):
            events.append('save')
        def stop(*args):
            self.assertEqual(events[:2], ['save', 'save'])
            events.append('stop')
            if events.count('stop') == 2:
                raise RuntimeError('stop failed')
        self.client.stop_node.side_effect = stop
        with patch.object(apply_configs, 'GNS3Client', return_value=self.client), \
                patch.object(apply_configs, 'config_router', side_effect=save):
            with self.assertRaisesRegex(RuntimeError, 'stop failed'):
                apply_configs.apply(self.profile)
        result = json.loads((self.root / 'apply_state.json').read_text())
        self.assertTrue(result['saved'])
        self.assertFalse(result['nodes_stopped'])
        self.assertEqual(result['stopped_nodes'], ['ISP-A-BR1'])
        self.assertEqual(result['stopping_node'], 'TRANSIT-BR1')

    def test_dry_run_does_not_connect(self):
        with patch.object(apply_configs, 'GNS3Client') as client:
            apply_configs.apply(self.profile, dry_run=True)
        client.assert_not_called()

    def test_no_save_driver(self):
        tn = Mock()
        with patch.object(utils, '_connect_router_console', return_value=tn), \
                patch.object(utils, 'router_initialize', return_value=True), \
                patch.object(utils, '_send_ios_command'), \
                patch.object(utils.time, 'sleep'), \
                patch.object(utils, '_save_ios_config') as save:
            utils.config_router(5000, ['enable', 'configure terminal', 'end'], save=False)
        save.assert_not_called()
        tn.close.assert_called_once()
