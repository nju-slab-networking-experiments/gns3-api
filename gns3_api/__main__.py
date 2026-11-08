"""Unified GNS3 command-line entry point."""

import argparse
import json
import sys
from pathlib import Path

from .apply_configs import apply
from .topology_build import (
    DEFAULT_GNS3_SERVER,
    GNS3APIError,
    GNS3Client,
    build_topology,
    configure_existing,
    load_topology,
)
from .utils import RouterConfigError


TOPOLOGIES_DIR = Path(__file__).resolve().parents[1] / "topologies"


def _topology_path(value: Path) -> Path:
    if value.suffix.lower() == ".json":
        return value
    if not value.is_absolute() and len(value.parts) == 1 and not value.is_dir():
        return TOPOLOGIES_DIR / value / "topology.json"
    return value / "topology.json"


def _add_server(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--server", default=DEFAULT_GNS3_SERVER, help="包含 /v2 的 GNS3 API 地址"
    )


def _add_listing(parser: argparse.ArgumentParser) -> None:
    _add_server(parser)
    parser.add_argument("--output", type=Path, help="将 JSON 写入文件，省略时输出到终端")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m gns3_api", description="管理 GNS3 网络实验")
    groups = parser.add_subparsers(dest="group", required=True)

    topology = groups.add_parser("topology", help="校验、构建或配置拓扑")
    topology_commands = topology.add_subparsers(dest="action", required=True)
    for action, help_text in (
        ("validate", "离线校验拓扑和配置文件"),
        ("build", "创建并配置新工程"),
        ("configure", "重新配置已有工程"),
    ):
        command = topology_commands.add_parser(action, help=help_text)
        command.add_argument("topology", type=Path, help="实验目录名或 topology.json 路径")
        if action != "validate":
            command.add_argument("--state", type=Path, help="覆盖 build_state.json 路径")
        if action == "build":
            _add_server(command)
            command.add_argument("--no-config", action="store_true", help="跳过设备配置")
    apply_command = topology_commands.add_parser("apply", help="向已有工程下发增量配置")
    apply_command.add_argument(
        "profile", nargs="?", type=Path, default=TOPOLOGIES_DIR / "lab8" / "configure.json",
        help="配置清单路径，默认使用实验八",
    )
    apply_command.add_argument("--variant", help="清单中的配置套题，默认使用清单指定的套题")
    apply_command.add_argument("--state", type=Path, help="覆盖清单指定的 build_state.json")
    apply_command.add_argument("--dry-run", action="store_true", help="仅离线检查")

    project = groups.add_parser("project", help="列出、停止或删除 GNS3 工程")
    project_commands = project.add_subparsers(dest="action", required=True)
    _add_listing(project_commands.add_parser("list", help="列出工程或导出 JSON"))
    for action, help_text in (("stop", "停止工程"), ("delete", "停止并删除工程")):
        command = project_commands.add_parser(action, help=help_text)
        command.add_argument("project_id", help="GNS3 工程 ID")
        _add_server(command)
        if action == "delete":
            command.add_argument("--force", action="store_true", help="请求 GNS3 强制删除")

    template = groups.add_parser("template", help="查询 GNS3 模板")
    template_commands = template.add_subparsers(dest="action", required=True)
    _add_listing(template_commands.add_parser("list", help="列出模板或导出 JSON"))

    return parser


def _run_topology(args: argparse.Namespace) -> None:
    if args.action == "apply":
        apply(args.profile, variant=args.variant, state_path=args.state, dry_run=args.dry_run)
        return

    topology = _topology_path(args.topology)
    if args.action == "validate":
        path, _ = load_topology(topology)
        print(f"[OK] 拓扑定义校验通过: {path}")
    elif args.action == "build":
        build_topology(
            topology, server=args.server, state_path=args.state,
            apply_config=not args.no_config,
        )
    else:
        configure_existing(topology, state_path=args.state)


def _run_server_command(args: argparse.Namespace) -> None:
    client = GNS3Client(args.server)
    if args.action == "list":
        items = client.list_projects() if args.group == "project" else client.list_templates()
        data = json.dumps(items, ensure_ascii=False, indent=2)
        if args.output is None:
            print(data)
        else:
            args.output.write_text(data + "\n", encoding="utf-8")
            print(f"[OK] 已导出 {len(items)} 条记录：{args.output}")
    elif args.action == "stop":
        client.stop_project(args.project_id)
        print(f"[OK] 已停止工程：{args.project_id}")
    elif args.action == "delete":
        client.remove_project(args.project_id, force=args.force)
        print(f"[OK] 已删除工程：{args.project_id}")


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = _build_parser().parse_args(argv)
    try:
        if args.group == "topology":
            _run_topology(args)
        else:
            _run_server_command(args)
    except (GNS3APIError, RouterConfigError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
