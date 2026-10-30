"""reference/local-ci-lock.sh: parallel worktrees queue for fixed ports instead of colliding (backlog 32, 0.5.7)."""

import os
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

LOCK_SCRIPT = Path(__file__).resolve().parents[1] / "reference" / "local-ci-lock.sh"


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@unittest.skipUnless(shutil.which("nc"), "needs nc")
class LocalCiLockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.lock = os.path.join(self.tmp, "ci-local-lock")
        self.port = free_port()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def start(self, body, cwd=None):
        """Run a CI script that sources the lock, takes it, then runs body."""
        script = f'LOCK="{self.lock}"; PORTS="{self.port}"; . "{LOCK_SCRIPT}"; take_lock; echo TOOK; {body}'
        return subprocess.Popen(["sh", "-c", script], cwd=cwd or self.tmp, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def test_takes_and_releases(self):
        proc = self.start(f'readlink "{self.lock}"')
        out, _ = proc.communicate(timeout=20)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("TOOK", out)
        self.assertIn(f":{self.tmp}", out)  # owner recorded as pid:worktree
        self.assertFalse(os.path.lexists(self.lock), "lock left behind after exit")

    def test_second_worktree_waits_for_live_holder(self):
        holder = self.start("sleep 30")
        try:
            deadline = time.time() + 10
            while not os.path.lexists(self.lock) and time.time() < deadline:
                time.sleep(0.1)
            waiter = self.start("true")
            time.sleep(2)
            self.assertIsNone(waiter.poll(), "second run did not wait for the live holder")
            holder.kill()
            holder.wait()
            # The killed holder's symlink is stale: the waiter takes it over on its next 10 s check.
            out, _ = waiter.communicate(timeout=25)
            self.assertIn("waiting for ports", out)
            self.assertIn("TOOK", out)
        finally:
            if holder.poll() is None:
                holder.kill()
            holder.communicate()

    def test_stale_lock_from_dead_process_is_taken_over(self):
        dead = subprocess.Popen(["true"])
        dead.wait()
        os.symlink(f"{dead.pid}:/gone/worktree", self.lock)
        proc = self.start("true")
        out, _ = proc.communicate(timeout=20)
        self.assertEqual(proc.returncode, 0, out)
        self.assertIn("TOOK", out)
        self.assertNotIn("waiting for ports", out)

    def test_port_busy_outside_the_lock_fails_clearly(self):
        with socket.socket() as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", self.port))
            server.listen(64)
            proc = self.start("true")
            out, _ = proc.communicate(timeout=40)
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn(f"port {self.port} is busy outside this lock", out)
        self.assertNotIn("TOOK", out)
        self.assertFalse(os.path.lexists(self.lock), "lock left behind after the port failure")


if __name__ == "__main__":
    unittest.main()
