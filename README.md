# Ruijie M32 / X32 experimental OpenWrt

OpenWrt 25.12.5, commit f0a60eee2fe051741c643ea6118718aae1ef17fb.
Adapted from RG-EW3200GX PRO for the user's observed stock 16 MiB SPI-NOR layout.
This is an experimental hardware adaptation, not an official M32 image.

Partition start/size (hex):

| Partition | Start | Size |
|---|---|---|
| Preloader | 0 | 20000 |
| ATF | 20000 | 10000 |
| u-boot | 30000 | 50000 |
| u-boot-env | 80000 | 10000 |
| Factory | 90000 | 40000 |
| product_info | d0000 | 10000 |
| kdump | e0000 | 10000 |
| firmware | f0000 | f10000 |

EEPROM offsets within Factory remain 0 and 5000, following the older X32 adaptation.
Upstream compatible/profile remains ruijie,rg-ew3200gx-pro so its network and MAC setup scripts are retained. The model string and distributed image filenames explicitly identify M32/X32.
No bootloader images are built or flashed by this project.

First test only the initramfs-kernel.bin via U-Boot menu 1 (TFTP to SDRAM).
Check stable uptime, serial console, LAN ports, both Wi-Fi radios and MAC addresses.
The previous unmodified PRO image reset during Wi-Fi initialization; changing partitions is not proof that this reset is fixed.
Before any permanent installation, back up the complete SPI-NOR and Factory data and copy backups off the router. Do not flash this test image through U-Boot menu 2 or use forced upgrades.
The sysupgrade image is provided for later review, not an instruction to flash it immediately.

References:
- https://www.mydigit.cn/thread-439212-1-1.html
- https://github.com/ericvwv/ActionsOpenwrt
- https://github.com/openwrt/openwrt/tree/v25.12.5
