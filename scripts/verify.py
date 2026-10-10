import struct
import subprocess
import sys
from pathlib import Path
import shutil

root, out = map(Path, sys.argv[1:])
out.mkdir(parents=True, exist_ok=True)
images = root / 'bin/targets/mediatek/mt7622'
for kind in ('initramfs-kernel', 'squashfs-sysupgrade'):
    matches = list(images.glob(f'*ruijie_rg-ew3200gx-pro-{kind}.bin'))
    assert len(matches) == 1, (kind, matches)
    src = matches[0]
    assert src.stat().st_size > 1024 * 1024
    if kind == 'squashfs-sysupgrade':
        assert src.stat().st_size <= 0xf10000, 'Image exceeds actual firmware partition'
    else:
        raw = src.read_bytes()
        assert struct.unpack('>I', raw[:4])[0] == 0xd00dfeed, 'Not a FIT image'
        listing = subprocess.check_output(['fdtget', '-l', str(src), '/images'], text=True)
        fdt_nodes = [n for n in listing.splitlines() if n.startswith('fdt')]
        assert len(fdt_nodes) == 1
        data = subprocess.check_output(['fdtget', '-t', 'bx', str(src), f'/images/{fdt_nodes[0]}', 'data'], text=True)
        dtb = out / 'm32-x32.dtb'
        dtb.write_bytes(bytes(int(x, 16) for x in data.split()))
        def find_parts(path='/'):
            nodes = subprocess.check_output(['fdtget', '-l', str(dtb), path], text=True).splitlines()
            if 'partition@90000' in nodes and 'partition@f0000' in nodes:
                return path
            for child in nodes:
                result = find_parts(path.rstrip('/') + '/' + child)
                if result:
                    return result
            return None
        parts = find_parts()
        assert parts, 'Adapted NOR partitions missing from embedded DTB'
        decompiled = subprocess.check_output(['dtc', '-I', 'dtb', '-O', 'dts', str(dtb)], text=True)
        assert 'Ruijie M32 / X32 (stock 16MiB layout)' in decompiled
        for node, values in [('partition@90000', '90000 40000'), ('partition@f0000', 'f0000 f10000')]:
            actual = subprocess.check_output(['fdtget', '-t', 'x', str(dtb), f'{parts}/{node}', 'reg'], text=True).strip()
            assert actual == values, (node, actual)
        (out / 'compiled-device-tree.dts').write_text(decompiled)
    shutil.copy2(src, out / f'openwrt-25.12.5-ruijie-m32-x32-{kind}.bin')
print('Verified FIT embedded DTB and sysupgrade size. Hardware operation remains untested.')
