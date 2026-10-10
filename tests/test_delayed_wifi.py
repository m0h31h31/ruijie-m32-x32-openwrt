"""Check delayed probe ordering and failure handling without router access."""
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "files/etc/init.d/m32-wifi"

class DelayedWifi(unittest.TestCase):
    def run_service(self, probe_status):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = SCRIPT.read_text().replace("/tmp/m32-wifi.log", str(root / "service.log")).replace("/var/run/m32-wifi.pid", str(root / "pid"))
            source += "\nstart\nwait\n"
            mock = """sleep() { echo "sleep $*" >>"$EVENTS"; }
modprobe() { echo "probe $*" >>"$EVENTS"; return "$PROBE_STATUS"; }
ucode() { echo configure >>"$EVENTS"; }
wifi() { echo "wifi $*" >>"$EVENTS"; }
logger() { echo log >>"$EVENTS"; }
"""
            subprocess.run(["sh", "-c", mock + source], env={"EVENTS": str(root / "events"), "PROBE_STATUS": str(probe_status), "PATH": "/usr/bin:/bin"}, check=True)
            return (root / "events").read_text().splitlines()

    def test_delayed_probe_before_configuration(self):
        self.assertEqual(self.run_service(0), ["sleep 20", "probe mt7915e", "sleep 2", "configure", "wifi reload", "log"])

    def test_failed_probe_does_not_reload_wireless(self):
        self.assertEqual(self.run_service(1), ["sleep 20", "probe mt7915e", "log"])

if __name__ == "__main__":
    unittest.main()
