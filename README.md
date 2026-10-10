# 锐捷 M32 / X32 OpenWrt

基于 OpenWrt **25.12.5** 的非官方适配，面向原厂 **16 MiB SPI-NOR** 分区布局。以 RG-EW3200GX PRO 的上游设备支持为基础；M32 已有实机记录，其他型号仅在分区和硬件一致时适用，不承诺通刷。

## 下载与选择

在 [Releases](https://github.com/m0h31h31/ruijie-m32-x32-openwrt/releases) 下载固件并核对 SHA256SUMS。

- `initramfs-kernel.bin`：U-Boot 菜单 **1 / SDRAM via TFTP** 临时内存启动，用于首次安装前检查。
- `squashfs-sysupgrade.bin`：在匹配分区的 OpenWrt 中升级或从临时系统安装。

不要用 U-Boot 菜单 2 直接写入 initramfs。先备份全部原厂分区并将备份保存到电脑，尤其是 Factory 校准数据。永久安装前执行 `sysupgrade -T /tmp/firmware.bin`；首次安装使用 `sysupgrade -n /tmp/firmware.bin`。不要强制跳过兼容检查。升级过程中保持供电。

## 适配内容

- firmware 位于 `0xf0000`，大小 `0xf10000`，镜像上限 15424 KiB。
- Factory 位于 `0x90000`；两块无线 EEPROM 在该分区内的偏移分别为 `0` 和 `0x5000`。
- U-Boot 环境分区只有 **64 KiB**，修正 PRO 配置原先使用的 128 KiB 读取参数。
- 保留上游 compatible 和网络/MAC 初始化，模型名称明确标为 M32 / X32。
- **5GHz 使用延迟加载**：早期模块加载时暂不加载 `mt7915e`，正常启动服务阶段再等待 20 秒加载并生成缺失的无线配置，随后重新加载无线。保留已有无线名称、密码和禁用设置。

无线默认沿用 OpenWrt 的禁用策略，请在 LuCI 中设置地区、SSID 和密码后启用。新安装时 5GHz radio 可能在开机后约 40 秒才出现。驱动没有被删除，也不需要另外下载内核模块。

## 验证范围

此前构建已实机验证从闪存启动、SquashFS/JFFS2、LAN 和配置持久化。用户提供的后续排障记录验证了延迟加载后的重启、2.4GHz 与 5GHz AP（信道 36 / HE80）。**本 Release 将该办法由 rc.local 整理为独立服务；发布构建未另行刷机测试，客户端吞吐及长期稳定性尚未验证。** 临时系统中曾发生早期 MT7915 初始化卡死；不能将所有刷机报错都归因于它。

状态检查：

```sh
cat /tmp/m32-wifi.log
logread -e m32-wifi
iw dev
ubus call network.wireless status
```

可用 `/etc/init.d/m32-wifi disable` 关闭延迟启动。升级时保留的旧 `/etc/modules.d/mt7915e` 或 rc.local 自定义可能影响新服务，应检查并避免重复加载；从本项目早期测试版升级推荐不保留设置并先导出配置备份。

## 构建

上游固定为 `v25.12.5`，提交 `f0a60eee2fe051741c643ea6118718aae1ef17fb`。GitHub Actions 支持手动运行；本地 Ubuntu/WSL 安装编译依赖后：

```sh
BUILD_DIR=$HOME/openwrt-m32-25.12.5 bash scripts/build-local.sh
```

`adapt.py` 修改分区和环境配置并复制 overlay；`verify.py` 从 FIT 中检查实际 DTB 和固件大小。Release 同时提供构建配置、上游补丁和包源提交清单。已有构建目录若保留旧诊断 overlay，需移除 `files/bin/board_detect` 和 `files/lib/preinit/81_m32_debug`。

## 原厂布局

| 分区 | 起点 | 大小 |
|---|---|---|
| Preloader | 0x0 | 0x20000 |
| ATF | 0x20000 | 0x10000 |
| u-boot | 0x30000 | 0x50000 |
| u-boot-env | 0x80000 | 0x10000 |
| Factory | 0x90000 | 0x40000 |
| product_info | 0xd0000 | 0x10000 |
| kdump | 0xe0000 | 0x10000 |
| firmware | 0xf0000 | 0xf10000 |

## 开源与致谢

本项目的适配脚本、overlay 按 GPL-2.0-only 发布；上游固件中的组件遵循各自许可证。原厂备份、校准数据、密码、MAC/SSH 信息及串口日志均不发布。

感谢 OpenWrt、Langhua Ye 对 RG-EW3200GX PRO 的支持，以及 [X32 适配讨论](https://www.mydigit.cn/thread-439212-1-1.html) 和 [ActionsOpenwrt](https://github.com/ericvwv/ActionsOpenwrt)。
