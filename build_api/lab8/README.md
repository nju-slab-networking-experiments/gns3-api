# 实验八：Transit ISP NOC 事故排查

复用实验七现有 GNS3 工程的节点、接口和连线，不创建新拓扑。

## 使用前提

必须先完成实验七的 OSPF、BGP、精确合同过滤、community 来源分类及导出策略，并验证正常。

A/B/C 为独立平行题；切换套题前按实验文档逐项修复并清理上一套全部临时配置，确认回到正常状态。

## 配置目录

| 目录 | 错误通告源端 | 放宽合同的入口 | 异常 Peer 入口 / LOCAL_PREF | 异常 ISP-A 入口 / LOCAL_PREF | 错误备用过滤入口 |
|---|---|---|---|---|---|
| configA | ISP-A-BR1 | TRANSIT-BR1 | TRANSIT-BR2 / 350 | TRANSIT-BR2 / 301 | TRANSIT-BR2 |
| configB | ISP-B-BR1 | TRANSIT-BR2 | TRANSIT-BR1 / 360 | TRANSIT-BR1 / 302 | TRANSIT-BR1 |
| configC | ISP-B-BR2 | TRANSIT-BR3 | TRANSIT-BR2 / 400 | TRANSIT-BR2 / 305 | TRANSIT-BR2 |

每套包含源端和三台 TRANSIT 的四份 `.cfg` 文件。三台 TRANSIT 均包含客户与 Peer 导出模板错误；其余节点继续使用实验七正常配置。

## 自动配置现有工程

在仓库根目录执行，默认应用 configA：

```powershell
python build_api/lab8/apply_configs.py
```

入口默认读取本目录 `configure.json`，自动加载 `../lab7/build_state.json` 中的服务器、工程 ID 和节点 ID，再从 GNS3 获取当前控制台信息。启动已有路由器和 VPCS 后，直接自动下发所选目录的配置，默认实验七已配置成功。不会创建项目、节点或连线，不会覆盖 lab7 的状态文件。

其他用法：

```powershell
# 离线检查文件及节点映射，不连接 GNS3
python build_api/lab8/apply_configs.py --dry-run
# 选择其他套题（须先恢复正常基线）
python build_api/lab8/apply_configs.py --variant configB
python build_api/lab8/apply_configs.py --variant configC
# 使用其他位置的实验七状态文件
python build_api/lab8/apply_configs.py --state "D:/labs/lab7/build_state.json"
```

脚本会逐条等待 IOS 提示符并检查命令错误，包含 EXEC 模式的 soft in/out。每台目标设备配置完成后保存到 startup-config；全部四台保存成功后，关闭工程中的所有可关机设备（包括其他路由器和 VPCS），内置交换机等常驻节点无需关闭。脚本不读取 running-config，不检查实验七策略或上一套 LAB8 残留。

下发状态记录在本目录 `apply_state.json`。失败时立即停止后续下发，保留已完成节点和当前失败节点；已完成节点的故障配置已经保存，当前节点可能部分应用；配置或保存失败时不进入关机阶段。若关闭设备失败，记录已关闭设备和失败位置，不报告全部完成。按实验文档恢复正常配置后再运行，不直接叠加另一套，不自动回滚或重启设备。

初始化会将故障状态写入原工程的 startup-config。初始化前另行保留实验七正常配置备份；build_state.json 只记录工程信息，不是配置备份，重启不能恢复正常基线。

看到 `[OK] 全部增量配置已应用并保存到 startup-config；所有可关机设备已关闭` 后，初始化完成。开始实验时，在 GNS3 启动本工程路由器和 VPCS，等待启动及路由传播；加载已保存配置后，五项故障同时存在。按文档所选套题第 .6 节开始 before 抓包、逐邻居 soft out 和观察；再按第 .7 节以事故 1 → 2 → 3 → 4 → 5 的顺序修复，继续 after、ISP-A 和 DC 备用检查。文件未包含临时断链或修复命令。全部修复、源端清理及接口恢复后才保存正常配置。

已静态核对每套八个设置命令块与实验文档一致，并用模拟测试覆盖自动下发和失败处理；实际 GNS3/C3745 协议行为仍需运行验证。
