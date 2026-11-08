# gns3-api 操作手册

在仓库根目录运行 `python -m gns3_api <资源> <动作>`。使用 `python -m gns3_api --help` 查看资源列表，或在子命令后加 `--help` 查看参数。

## 环境准备

使用 Python 3.10–3.12。启动 GNS3 服务，在目标服务端注册拓扑需要的模板和镜像，并确保本机可以访问设备的 Telnet 控制台。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install requests
python -m gns3_api --help
```

## 命令速查

| 命令 | 用途 |
| --- | --- |
| `python -m gns3_api topology validate <拓扑>` | 离线检查拓扑和设备配置文件的引用。 |
| `python -m gns3_api topology build <拓扑>` | 创建新工程、节点和链路，并下发配置。 |
| `python -m gns3_api topology configure <拓扑>` | 根据构建状态文件重新配置已有工程。 |
| `python -m gns3_api topology apply [配置清单]` | 向已有工程下发增量配置。省略路径时使用内置清单。 |
| `python -m gns3_api project list` | 列出工程及其 `project_id`。 |
| `python -m gns3_api project stop <项目ID>` | 停止指定工程。 |
| `python -m gns3_api project delete <项目ID>` | 停止并删除指定工程。传入 `--force` 可请求强制删除。 |
| `python -m gns3_api template list` | 列出模板及其 `template_id`。 |

`topology build` 以及 `project`、`template` 下的命令支持 `--server`。默认地址为 `http://127.0.0.1:3080/v2`，自定义地址也应包含 `/v2`。

## 校验、构建和重新配置

`<拓扑>` 接受 `topologies/` 下的目录名、拓扑目录路径或 `topology.json` 路径。以下命令中的路径请替换为实际路径。

```powershell
python -m gns3_api topology validate "path/to/topology.json"
python -m gns3_api topology build "path/to/topology.json"
python -m gns3_api topology configure "path/to/topology.json"
```

- `build` 每次创建新工程。传入 `--no-config` 可暂缓下发设备配置。
- `build_state.json` 默认生成在拓扑文件所在目录。用 `build --state <路径>` 自定义位置后，重新配置时也要通过 `configure --state <路径>` 传入同一文件。
- `configure` 使用状态文件中的服务端地址和节点映射。

## 下发增量配置

```powershell
python -m gns3_api topology apply "path/to/configure.json" --dry-run
python -m gns3_api topology apply "path/to/configure.json"
```

- `--dry-run` 离线检查配置脚本和节点映射，仍需读取构建状态文件。
- `--variant <名称>` 选择清单中的配置，省略时使用清单指定的默认项。
- `--state <路径>` 覆盖清单指定的构建状态文件。
- 下发进度和失败信息记录在清单所在目录的 `apply_state.json`。

## 导出项目和模板

列表命令默认将 JSON 输出到终端。使用 `--output` 可写入文件。

```powershell
python -m gns3_api project list --output local_projects.json
python -m gns3_api template list --output local_templates.json
```
