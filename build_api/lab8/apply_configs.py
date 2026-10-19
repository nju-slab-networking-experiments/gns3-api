"""Apply console scripts to an existing project, save them, and stop existing devices without rebuilding."""
import argparse
import json
from pathlib import Path
import sys
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from topology_build import GNS3Client, _write_state, STOPPABLE_NODE_TYPES
from utils import config_router


def apply(profile_path, variant=None, state_path=None, dry_run=False):
    profile_path = Path(profile_path).resolve()
    profile = json.loads(profile_path.read_text(encoding='utf-8-sig'))
    variant = variant or profile['default']
    directory = profile_path.parent / profile['variants'][variant]
    state_path = Path(state_path).resolve() if state_path else (profile_path.parent / profile['state']).resolve()
    state = json.loads(state_path.read_text(encoding='utf-8-sig'))
    project_id = state['project_id']
    scripts = {}
    for path in sorted(directory.glob('*.cfg')):
        commands = [line.strip() for line in path.read_text(encoding='utf-8-sig').splitlines()
                    if line.strip() and not line.lstrip().startswith(('!', '#'))]
        if not commands or commands[0].lower() != 'enable':
            raise ValueError(f'{path}: 必须是以 enable 开始的控制台脚本')
        if any(c.lower().startswith(('write', 'copy', 'reload')) for c in commands):
            raise ValueError(f'{path}: 保存由程序统一执行，配置文件不得包含保存或重启命令')
        if path.stem not in state['nodes']:
            raise ValueError(f'状态文件缺少节点: {path.stem}')
        scripts[path.stem] = commands
    if not scripts:
        raise ValueError(f'配置目录为空: {directory}')
    print(f"工程 {state['project_name']} ({project_id}); {variant}; {len(scripts)} 台设备", flush=True)
    if dry_run:
        print('离线检查通过；未连接 GNS3、未下发配置')
        return
    client = GNS3Client(state['server'])
    project = client._request('GET', f'/projects/{project_id}', expected=(200,)).json()
    if project['name'] != state['project_name']:
        raise ValueError('工程名称与 build_state.json 不一致')
    if project.get('status') == 'closed':
        client._request('POST', f'/projects/{project_id}/open', expected=(200, 201, 204))
    live = client._request('GET', f'/projects/{project_id}/nodes', expected=(200,)).json()
    by_id = {n['node_id']: n for n in live}
    for name, recorded in state['nodes'].items():
        node = by_id.get(recorded['node_id'])
        if node is None or node['name'] != name:
            raise ValueError(f'{name}: 工程节点与 build_state.json 不一致')
    targets = {}
    for name in scripts:
        node = dict(by_id[state['nodes'][name]['node_id']])
        if node['name'] != name or node['node_type'] != 'dynamips' or node.get('console_type') != 'telnet':
            raise ValueError(f'{name}: 现有节点身份或控制台类型不匹配')
        host = node.get('console_host')
        if host in (None, '', '0.0.0.0', '::'):
            host = state['nodes'][name].get('console_host')
        if host in (None, '', '0.0.0.0', '::'):
            host = urlparse(state['server']).hostname
        node['console_host'] = host
        if not isinstance(node.get('console'), int):
            raise ValueError(f'{name}: 无有效 console 端口')
        targets[name] = node
    for recorded in state['nodes'].values():
        node = by_id[recorded['node_id']]
        if node.get('status') != 'started' and node['node_type'] in ('dynamips', 'vpcs'):
            client.start_node(project_id, node['node_id'])
    result_path = profile_path.parent / 'apply_state.json'
    result = {'project_id': project_id, 'source_state': str(state_path), 'variant': variant,
              'configured': False, 'completed_nodes': [], 'saved': False,
              'nodes_stopped': False, 'stopped_nodes': []}
    _write_state(result_path, result)
    try:
        for name, node in targets.items():
            result['current_node'] = name
            _write_state(result_path, result)
            print(f'[APPLY] {name}', flush=True)
            config_router(node['console'], scripts[name], host=node['console_host'], save=True)
            result['completed_nodes'].append(name)
            _write_state(result_path, result)
        result['configured'] = True
        result['saved'] = True
        result.pop('current_node', None)
        _write_state(result_path, result)
        for name, recorded in state['nodes'].items():
            node = by_id[recorded['node_id']]
            if node['node_type'] not in STOPPABLE_NODE_TYPES:
                continue
            result['stopping_node'] = name
            _write_state(result_path, result)
            client.stop_node(project_id, node['node_id'])
            result['stopped_nodes'].append(name)
            result.pop('stopping_node', None)
            _write_state(result_path, result)
        result['nodes_stopped'] = True
    except Exception as exc:
        result['error'] = str(exc)
        raise
    finally:
        _write_state(result_path, result)
    print('[OK] 全部增量配置已应用并保存到 startup-config；所有可关机设备已关闭')


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', nargs='?', default=str(Path(__file__).resolve().parent / 'configure.json'))
    parser.add_argument('--variant', help='配置目录名称，默认使用 profile.default')
    parser.add_argument('--state', help='覆盖已有工程的 build_state.json 路径')
    parser.add_argument('--dry-run', action='store_true', help='仅离线检查，不连接设备')
    args = parser.parse_args()
    try:
        apply(args.profile, args.variant, args.state, args.dry_run)
    except Exception as exc:
        print(f'[ERROR] {exc}', flush=True)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
