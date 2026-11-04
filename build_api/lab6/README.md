# 实验六：TCP 与 UDP Socket Echo

依据《实验六_TCP与UDP_Socket_Echo_GNS3设计方案》生成，使用外层通用构建器，无需实验专用 Python 构建文件。

## 模板、地址和连线

| 节点 | GNS3 模板 name | 镜像 / 地址 |
|---|---|---|
| client | client-lab6-complete | `ghcr.io/myywee/client:lab6-complete`；eth0 `10.10.10.10/24`，网关 `10.10.10.1` |
| Router | Cisco IOSv | Gi0/0 `10.10.10.1/24`，Gi0/1 `10.20.20.1/24` |
| server | server-lab6-complete | `ghcr.io/myywee/server:lab6-complete`；eth0 `10.20.20.20/24`，网关 `10.20.20.1` |

模板名称与镜像对应关系来自项目的 `local_templates.json`。实际构建按 name 查找 GNS3 服务端已注册模板，所有节点使用 `vm` compute。

| 连线 | GNS3 adapter/port |
|---|---|
| client eth0 — Router Gi0/0 | client 0/0 — Router 0/0 |
| Router Gi0/1 — server eth0 | Router 1/0 — server 0/0 |

Client 和 Server 位于不同网段，Router 通过 `configs/router.cfg` 配置并启用两个接口，为两端提供网关。两个网段均为直连网段，无需静态路由或动态路由协议。

## 构建和启动

在项目根目录执行：

```powershell
python build_api/topology_build.py validate build_api/lab6/topology.json
python build_api/topology_build.py build build_api/lab6/topology.json
```

Docker 地址配置写入 Start command，每次启动自动生效；构建器追加交互 Bash 入口。构建成功后关闭三个节点，生成 `build_state.json`。开始实验时在 GNS3 中启动全部节点。

Router 的 GNS3 节点名称为 `Router`，IOS 主机名配置为 `R1-IOSv`。构建器通过 `ios` 驱动下发 `configs/router.cfg`，自动进入配置模式，并在成功后保存到 startup-config。配置文件仅包含配置模式命令，手动粘贴时应先执行 `enable`、`configure terminal`，完成后执行 `end`、`write memory`。

重新应用本目录对应工程的 Client、Router、Server 配置：

```powershell
python build_api/topology_build.py configure build_api/lab6/topology.json
```

设计方案建议复用实验四、五的同一工程。本目录提供独立的实验六构建定义，地址和连线与实验四一致；执行 `build` 会创建新工程，不会迁移已有工程或保留其链路过滤器。若课堂要求连续复用同一工程，应在原工程中准备实验六镜像和程序，不执行这里的 `build`，也不要直接复制其他实验的运行状态文件。

## 链路实验条件

当前构建器不自动设置链路过滤器。实验开始前，在 GNS3 的 **Router—server** 链路设置带宽 20 Mbit/s、单向时延 25 ms、抖动 2 ms、初始丢包率 0%。如环境未提供限速，按方案记录实际条件，并保证实验四、五、六条件一致。

随机丢包环节改为 5%，结束后只将丢包率恢复为 0%，保留时延与抖动。在这条链路抓包，显示过滤器为 `tcp.port == 18080 || udp.port == 18080`。

## 程序和连通性检查

complete 镜像应预置 Python、iproute2、ping、tcpdump 及 `/opt/socket-lab/` 下的实验程序；生成目录时未运行或检查镜像内容。启动全部节点后，在 Router 执行 `show ip interface brief` 和 `show ip route connected`，确认两个接口为 `up/up`，并存在 `10.10.10.0/24`、`10.20.20.0/24` 两条直连路由。随后在 client 检查连通性与程序：

```bash
ping -c 3 10.20.20.20
command -v python3 ip ss ping tcpdump
ls -l /opt/socket-lab/
python3 -m py_compile /opt/socket-lab/tcp_echo_client.py /opt/socket-lab/udp_echo_client.py /opt/socket-lab/udp_peer.py
```

在 server 检查：

```bash
command -v python3 ip ss ping tcpdump
python3 -m py_compile /opt/socket-lab/tcp_echo_server.py /opt/socket-lab/udp_echo_server.py /opt/socket-lab/udp_peer.py
```

TCP/UDP Echo 服务由学生按设计方案第 7.1 节手动启动在后台，同时监听 18080；本目录初始化 Client、Router、Server 网络，服务程序由学生手动启动。UDP 对等通信使用 client 的 19001 和 server 的 19002。程序缺失时按方案在课前准备镜像，后续操作、抓包和记录表沿用原文档。
