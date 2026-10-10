import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
dts = root / 'target/linux/mediatek/dts/mt7622-ruijie-rg-ew3200gx-pro.dts'
text = dts.read_text()
layout = [
    ('Preloader', 0x0, 0x20000), ('ATF', 0x20000, 0x10000),
    ('u-boot', 0x30000, 0x50000), ('u-boot-env', 0x80000, 0x10000),
    ('Factory', 0x90000, 0x40000), ('product_info', 0xd0000, 0x10000),
    ('kdump', 0xe0000, 0x10000), ('firmware', 0xf0000, 0xf10000),
]
end = 0
for label, offset, size in layout:
    assert offset == end, f'Gap or overlap at {label}'
    end = offset + size
    pattern = (r'(partition@)[0-9a-fA-F]+(\s*\{\s*'
               r'(?:compatible\s*=\s*"denx,fit";\s*)?'
               r'label\s*=\s*"' + re.escape(label) +
               r'";\s*reg\s*=\s*)<[^>]+>')
    text, count = re.subn(pattern, lambda m: f'{m[1]}{offset:x}{m[2]}<0x{offset:x} 0x{size:x}>', text)
    assert count == 1, f'Unexpected upstream layout: {label}, matches={count}'
assert end == 0x1000000
text = text.replace('model = "Ruijie RG-EW3200GX PRO";', 'model = "Ruijie M32 / X32 (stock 16MiB layout)";')
# Keep the upstream compatible and profile to retain its network/MAC init scripts.
assert 'mediatek,mtd-eeprom = <&factory 0x0>' in text
assert 'mediatek,mtd-eeprom = <&factory 0x5000>' in text
dts.write_text(text)
mk = root / 'target/linux/mediatek/image/mt7622.mk'
source = mk.read_text()
anchor = 'define Device/ruijie_rg-ew3200gx-pro\n'
assert source.count(anchor) == 1
source = source.replace(anchor, anchor + '  IMAGE_SIZE := 15424k\n')
mk.write_text(source)
print('Adapted eight partitions; EEPROM absolute addresses: 0x90000 / 0x95000; firmware limit: 15424 KiB')

# M32 stock environment is 64 KiB; verified against the original backup CRC.
envtools = root / 'package/boot/uboot-tools/uboot-envtools/files/mediatek_mt7622'
source = envtools.read_text()
old_env = 'ubootenv_add_uci_config "/dev/mtd3" "0x0" "0x20000" "0x20000"'
assert source.count(old_env) == 1, 'Unexpected upstream Ruijie environment configuration'
envtools.write_text(source.replace(old_env, 'ubootenv_add_uci_config "/dev/mtd3" "0x0" "0x10000" "0x10000"'))
print('Adapted M32 U-Boot environment size and erase sector to 64 KiB')

# Apply the release overlay and ensure init scripts are executable.
import shutil
overlay = Path(__file__).resolve().parents[1] / 'files'
shutil.copytree(overlay, root / 'files', dirs_exist_ok=True)
for path in (root / 'files/etc/init.d').glob('*'):
    path.chmod(0o755)
for path in (root / 'files/etc/uci-defaults').glob('*'):
    path.chmod(0o755)
