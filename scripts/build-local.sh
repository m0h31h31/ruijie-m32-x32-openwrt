#!/usr/bin/env bash
set -euo pipefail
umask 022
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
source_dir=/mnt/e/DATA/PycharmProjects/Ruijie_M32_OpenWrt
build_dir=/home/jack/openwrt-m32-25.12.5
mkdir -p "$build_dir"
cd "$build_dir"
exec > >(tee -a local-build.log) 2>&1
echo "Local build started: $(date -Is)"
if [ ! -d openwrt/.git ]; then
  git clone --depth 1 --branch v25.12.5 https://github.com/openwrt/openwrt.git openwrt
fi
test "$(git -C openwrt rev-parse HEAD)" = f0a60eee2fe051741c643ea6118718aae1ef17fb
if [ ! -f adaptation-applied ]; then
  python3 "$source_dir/scripts/adapt.py" openwrt
  touch adaptation-applied
fi
mkdir -p output
git -C openwrt diff > output/m32-adaptation.patch
cp openwrt/target/linux/mediatek/dts/mt7622-ruijie-rg-ew3200gx-pro.dts output/m32-x32.dts
cd openwrt
./scripts/feeds update -a
./scripts/feeds install -a
cp "$source_dir/build.config" .config
make defconfig
grep -q '^CONFIG_TARGET_mediatek_mt7622_DEVICE_ruijie_rg-ew3200gx-pro=y$' .config
cp .config ../output/build.config
./scripts/diffconfig.sh > ../output/diffconfig
git rev-parse HEAD > ../output/source-commit.txt
./scripts/feeds list -s > ../output/feeds.txt
echo 'STAGE: source download'
make download -j8
echo 'STAGE: firmware compilation (12 jobs)'
nice -n 5 make -j12 V=s 2>&1 | tee ../build.log
cd ..
python3 "$source_dir/scripts/verify.py" openwrt output
cp "$source_dir/README.md" output/
(cd output && sha256sum *.bin > SHA256SUMS)
windows_output="$source_dir/local-output"
mkdir -p "$windows_output"
cp -a output/. "$windows_output/"
echo "COMPLETE: $(date -Is); artifacts: $windows_output"
