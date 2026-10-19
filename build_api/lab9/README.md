# Lab9 企业二层网络拓扑

根据用户最新截图调整完整骨架，共 24 个节点、44 条物理链路。ISP 位于顶部，ER、CORE、FW、AGG 逐层向下，左侧为四台 LB 测试 PC，右侧为 ADMIN/OFFICE，底部为 HV 和两个迁移交换机；坐标适当横向拉宽、纵向压缩。拓扑保留完整骨架；`configs/` 提供实验九文档模块一的基础配置命令，覆盖 AGG1/2、TRUST-SW1/2、DMZ-SW1/2、OFFICE-PC 和 ADMIN-PC。这些文件是可在设备控制台依次执行的命令，不是完整的 running-config/startup-config。已有命令文件的 18 台节点已声明 `config`，构建时会启动并配置这些节点，完成后关闭。

ADMIN-PC 按用户指定连接 TRUST-SW2 FastEthernet1/5，OFFICE-PC 连接 TRUST-SW1 FastEthernet1/5。LB1/2 分别拆成 DMZ-PC 和 MGMT-PC，连接对应 DMZ-SW 的 FastEthernet1/5 和 FastEthernet1/6。HV1/2/3 按新图改为 C3745 路由器；其他设备之间的连接关系沿用原拓扑。

AGG 使用用户指定的 Cisco IOSvL2 模板（ID：`fdcbf3bb-549c-4a2f-931f-c85b39205c67`，镜像：`vios_l2-adventerprisek9-m.ssa.high_iron_20200929.qcow2`）；其他模板名称取自仓库的 `local_templates.json`：

| 节点 | 模板 | 接口设置 |
|---|---|---|
| ISP、FW1/2 | c3745 | 板载两个 FE 口 |
| ER1/2、CORE1/2 | c3745 | Slot1 NM-1FE-TX |
| DMZ-SW1/2、TRUST-SW1/2 | c3745 | Slot1 NM-16ESW |
| AGG1/2 | Cisco IOSvL2 | 16 个适配器，Gi0/0～Gi3/3 |
| HV1/2/3 | c3745 | Slot0 GT96100-FE、Slot1 NM-16ESW，Slot2～4 留空，与 DMZ/TRUST 交换机一致 |
| LB1-DMZ-PC、LB1-MGMT-PC、LB2-DMZ-PC、LB2-MGMT-PC | VPCS | Ethernet0 |
| VMOTION-SW1/2 | Ethernet switch | 各 3 个独立交换端口 |
| OFFICE-PC、ADMIN-PC | VPCS | Ethernet0 |

IOSvL2 的 Gi0/0～Gi0/3 对应 adapter 0～3，Gi1/0～Gi1/3 对应 adapter 4～7，port 均为 0。C3745 的 fX/Y 对应 adapter X、port Y；内置交换机 eX 对应 adapter 0、port X。

每台 HV 的端口连接如下：

| HV 接口 | 对端（HV1/2/3 对应端口依次列出） | 后续配置用途 |
|---|---|---|
| f1/0 | DMZ-SW1 f1/2、f1/3、f1/4 | access VLAN30，PVST+ 冗余 |
| f1/1 | DMZ-SW2 f1/2、f1/3、f1/4 | access VLAN30，PVST+ 冗余 |
| f1/2 | TRUST-SW1 f1/2、f1/3、f1/4 | trunk VLAN20/40，PVST+ 冗余 |
| f1/3 | TRUST-SW2 f1/2、f1/3、f1/4 | trunk VLAN20/40，PVST+ 冗余 |
| f0/0 | VMOTION-SW1 e0、e1、e2 | 迁移平面 A，VRF VMA |
| f0/1 | VMOTION-SW2 e0、e1、e2 | 迁移平面 B，VRF VMB |

HV 当前仅落实模块和物理接线；表中的 HV VLAN、PVST+ 与 VRF 功能待后续配置。

新图的 HV 路由器及独立 LB VPCS 替代了原文档中的 Linux 主机，后续配置需要按此结构重新编写，不能直接使用原 Linux bonding/namespace 脚本。LB 的 DMZ 与 MGMT 接口后续分别配置为 VLAN30、VLAN40 的 access 口。

在仓库根目录执行：

```powershell
python build_api/topology_build.py validate build_api/lab9/topology.json
python build_api/topology_build.py build build_api/lab9/topology.json
```

本次仅完成离线拓扑校验，未在 GNS3 创建或启动项目。

## 模块一基础命令

`configs/<设备名>.cfg` 与实验文档模块一对应设备的代码块一致，包含进入配置模式与保存命令。交换机预置主机名、VLAN、物理 access/trunk、管理地址及基础 STP 设置；两台 PC 分别使用 10.10.10.101/24、10.10.10.102/24，无网关。

六台交换机业务 VLAN 优先级均为 32768；AGG 的 Gi0/1、Gi0/2 保持 shutdown。不包含模块二的 LACP、Port-channel1、根桥优先级调整或上联 10/100 开销。

仅用于新建、无旧业务配置的工程，不用于将完成态回退到初始态。操作时仅启动上述 8 台设备，FW、HV、LB 及其他扩展节点保持关闭；完成并保存后另存为 L2-START。

已有配置文件的 16 台 Cisco 节点使用 ios 驱动，两台 OFFICE/ADMIN PC 使用 vpcs 驱动。IOS 驱动支持以 enable 开头的控制台命令文件及 vlan database 模式切换。build 会自动下发并保存配置；已有工程可使用 configure 子命令及对应 build_state.json 下发，避免重复创建工程。四台 LB PC 和两台 VMOTION 交换机尚无配置声明。本次仅离线校验，未向实际设备下发配置。