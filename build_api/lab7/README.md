# 实验七：Transit ISP 的 BGP 策略与多边界故障切换

依据《实验七_Transit_ISP_BGP策略与故障切换》学生操作手册第 3 部分生成基础配置，仅包含设备名称、接口 IP、Loopback、转发功能、交换机 VLAN 和 VPCS 地址/网关。OSPF、BGP、静态路由和路由策略由学生按后续阶段配置。

共 17 个节点、18 条链路：14 台 C3745、1 台内置 Ethernet switch、2 台 VPCS。企业、校园、DC 的每对边界之间均不连线。

## 构建

在仓库根目录执行：

```powershell
python build_api/topology_build.py validate build_api/lab7/topology.json
python build_api/topology_build.py build build_api/lab7/topology.json
```

使用 `vm` compute 上的 `c3745`、`Ethernet switch` 和 `VPCS` 模板；名称依据仓库的 `local_templates.json`。目标 GNS3 实例须已有这些模板和对应 IOS 镜像；实际名称或 compute 不同时修改 `templates`。成功构建后节点会停止，进入实验时启动所需节点。

## 接口与配置

- C3745 的 FastEthernetS/P 对应 `adapter=S, port=P`；交换机和 VPCS 的 eN 对应 `adapter=0, port=N`。
- `properties` 显式设置 C3745 插槽：TRANSIT-BR2 使用三块 NM-1FE-TX，ISP-A/B 和 TRANSIT-BR1/3 各一块，其余路由器仅使用板载接口。
- PUBLIC-SW 的 e0/e1/e2 为 access VLAN 100，其余端口为 access VLAN 999，不接线。内置交换机无控制台，配置直接保存在拓扑的 `properties.ports_mapping` 中。
- `configs` 含 14 份 IOS 配置和 2 份 VPCS 配置。IOS 文件仅保留学生操作手册第 3.1 节基础配置，去掉最外层 `enable`、`configure terminal`、`end`、`write memory`；这些操作由 `ios` 驱动统一执行。文件用于构建器，不应直接作为 startup-config 导入。
- VPCS 仅自动配置第 3.2 节的 IP、默认网关并保存；`show ip` 和 `ping` 由学生手工执行。

已进行离线结构与配置一致性检查；未在实际 GNS3/IOS 环境验证。启动节点后按学生操作手册第 3.3 节检查直连网络，再继续第 4 节及后续阶段。
