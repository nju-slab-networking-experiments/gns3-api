# gns3-api

通过 GNS3 REST API 自动创建和配置网络实验环境的 Python 工具集。项目以 `topology.json` 描述节点、模板、链路和设备配置，由统一构建器完成项目创建、节点连接及配置下发。

## 主要功能

- 离线校验拓扑定义及其引用的配置文件。
- 根据 GNS3 服务端已注册的模板创建节点并连接端口。
- 支持 IOS、VPCS、通用 Telnet 命令和 Docker Start command 配置方式。
- 保存项目 ID、节点 ID、console 信息及配置结果，支持对已有项目重新应用配置。
- 提供项目列表导出、模板列表导出和交互式项目管理脚本。

## 目录说明

```text
gns3-api/
├── README.md
├── build_api/
│   ├── topology_build.py       # 通用拓扑构建命令行入口
│   ├── utils.py                # GNS3 API 与设备配置辅助逻辑
│   ├── README.md               # 拓扑字段和配置机制说明
│   └── lab*/                  # 各实验目录
│       ├── topology.json      # 拓扑定义
│       ├── configs/           # 设备配置文件
│       └── README.md          # 实验说明
├── tests/
│   └── test_topology_build.py  # 构建器与设备配置单元测试
├── list_projects.py           # 导出服务端项目列表
├── list_templates.py          # 导出服务端模板列表
├── manage_projects.py         # 交互式停止、删除项目
├── auto_lab.py                # 按可用模板创建示例节点
├── local_projects.json        # 项目列表快照
└── local_templates.json       # 模板列表快照
```

### 已有实验

| 实验 | 初始态 | 完成态 / 实验目录 |
| --- | --- | --- |
| 实验一：Web 与 DNS 基础 | [lab1-start](build_api/lab1-start/README.md) | [lab1-complete](build_api/lab1-complete/README.md) |
| 实验二：HTTPS | [lab2-start](build_api/lab2-start/README.md) | [lab2-complete](build_api/lab2-complete/README.md) |
| 实验三：XSS 与 CSRF | [lab3-start](build_api/lab3-start/README.md) | [lab3-complete](build_api/lab3-complete/README.md) |
| 实验四：CUBIC 与 BBR 拥塞控制对比 | — | [lab4](build_api/lab4/README.md) |
| 实验六：TCP 与 UDP Socket Echo | — | [lab6](build_api/lab6/README.md) |

各实验的模板名称、节点地址和配置范围以对应目录说明为准。实验四和实验六的 Router 当前不下发设备配置，构建后仍需按实验要求配置路由器。

## 环境准备

1. 使用 Python 3.10–3.12。当前设备配置模块直接依赖标准库 `telnetlib`，环境中需要能导入该模块。
2. 启动可访问的 GNS3 服务端，默认 API 地址为 `http://127.0.0.1:3080/v2`。
3. 在 GNS3 中准备实验所需的模板及对应镜像，并确保拓扑指定的 compute 可用。现有实验使用 `vm` compute，需要准备 GNS3 VM。
4. 使用 Telnet 下发配置时，运行脚本的主机需要能访问节点的 console 地址及端口。

在项目根目录创建虚拟环境并安装依赖，以下命令适用于 PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install requests
```

若已有符合要求的虚拟环境，可直接使用。仓库中的 JSON 快照仅供查看，构建器实际从 GNS3 服务端解析模板，不会自动导入模板或制作实验镜像。

## 快速开始

以下命令均在项目根目录执行，以实验一初始态为例。

### 1. 离线校验

```powershell
python build_api/topology_build.py validate build_api/lab1-start/topology.json
```

该命令检查拓扑结构和配置文件，无需连接 GNS3；模板是否存在及镜像能否启动，需要在实际构建时确认。

### 2. 构建实验

```powershell
python build_api/topology_build.py build build_api/lab1-start/topology.json
```

构建器创建项目、节点和链路，并按拓扑设置启动节点、应用配置。默认在构建完成后关闭可关机节点；NAT 和内置 Ethernet switch 等常驻节点没有独立关机状态。进入实验时，在 GNS3 中打开生成的项目并启动所需节点。

使用其他服务端时，通过 `--server` 指定包含 `/v2` 的完整 API 地址：

```powershell
python build_api/topology_build.py build build_api/lab1-start/topology.json --server http://192.168.1.100:3080/v2
```

运行状态默认写入实验目录的 `build_state.json`，不会写回 `topology.json`。每次执行 `build` 都会尝试新建项目；修改配置后应使用 `configure` 对已有项目重新配置。

### 3. 暂缓配置或重新配置

```powershell
python build_api/topology_build.py build build_api/lab1-start/topology.json --no-config
python build_api/topology_build.py configure build_api/lab1-start/topology.json
```

`configure` 从状态文件读取服务端地址和节点信息，启动待配置节点并重新下发配置，完成后遵循 `project.stop_after_build` 设置。IOS 配置会检查命令错误并保存到 startup-config；Docker 配置写入节点实例的 Start command。

`build` 和 `configure` 均支持 `--state <路径>` 指定状态文件。使用自定义路径构建后，重新配置时应传入同一路径。

若配置阶段失败，构建器会保留项目供修正后重试。可查看命令输出和状态文件中的配置结果，再运行 `configure`。

## 辅助脚本

```powershell
python list_projects.py
python list_templates.py
python manage_projects.py
```

- `list_projects.py` 将服务端项目列表写入根目录 `local_projects.json`。
- `list_templates.py` 将服务端模板列表写入根目录 `local_templates.json`。
- `manage_projects.py` 先输入项目编号，再输入 `s` 停止或 `d` 删除项目；删除操作会实际删除服务端项目。

以上脚本的服务器地址由各文件中的 `GNS3_SERVER` 常量指定。

`auto_lab.py` 是示例脚本，需要可用的 VPCS 模板，并根据服务端已有模板尝试创建其他类型节点。它没有创建链路或下发实验配置，正式实验使用 `build_api/topology_build.py`。

## 新增实验与验证

新增实验时，在 `build_api/` 下创建实验目录，添加 `topology.json`、`configs/` 和实验说明，再用通用构建器校验。拓扑字段、模板解析与配置驱动说明见 [构建器文档](build_api/README.md)。

运行现有单元测试：

```powershell
python -m unittest discover -s tests -v
```

单元测试使用模拟客户端验证构建与配置逻辑，实际镜像、compute 和网络连通性仍需在 GNS3 环境中验证。
