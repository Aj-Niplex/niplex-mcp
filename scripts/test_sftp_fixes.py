"""
Offline tests for the HidenCloud SFTP bridge fixes. Uses a fake SFTP client
in memory — no network, no credentials. Covers:

  1. path confinement (_safe_path) still holds
  2. _ensure_dir: no '//' paths, correct mkdir sequence (was a real bug)
  3. read cap: >2 MiB file is refused with a clear message, not OOM'd
  4. stat: missing path says "does not exist"; present path shows type/size
  5. mkdir / rename dispatch through the manager
  6. search: recursive walk, substring match, depth cap
  7. _connect: unset env fails fast with a clear message (timeout wiring)
  8. manager exposes the 8 tools

Run: python scripts/test_sftp_fixes.py
"""
import os
import stat
import sys
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations import hidencloud_sftp as hc  # noqa: E402
from integrations.hidencloud_sftp import HidenCloudSFTPBridge, MAX_READ_BYTES  # noqa: E402
from tools.managers.sftp_manager import SftpManager  # noqa: E402

PASS = 0
FAIL = 0

Attr = namedtuple("Attr", "filename st_mode st_size st_mtime")


def attr(name, is_dir, size=0):
    return Attr(name, stat.S_IFDIR if is_dir else stat.S_IFREG, size, 0)


class FakeFile:
    def __init__(self, data: bytes):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, n=-1):
        if n < 0:
            return self.data
        chunk, self.data = self.data[:n], self.data[n:]
        return chunk

    def write(self, content):
        self.data = content if isinstance(content, bytes) else content.encode("utf-8")
        return len(self.data)


class FakeTransport:
    def close(self):
        pass


class FakeSFTP:
    """In-memory dir tree keyed by absolute path: {'/': {...}}."""

    def __init__(self):
        logs = {"app.log": b"line1\nline2\n"}
        sub = {"bar.md": b"# x", "logs": logs}
        # nested dicts must be SHARED objects between the root and the
        # top-level '/sub' keys, or mutations/stat lookups diverge
        self.tree = {"/": {"foo.txt": b"hello", "sub": sub}, "/sub": sub, "/sub/logs": logs}
        self.stat_calls = []
        self.mkdir_calls = []
        self.renamed = []

    def close(self):
        pass

    def _root(self):
        return self.tree["/"]

    def _norm(self, p):
        p = p.replace("./", "/").replace("//", "/")
        if p == ".":
            return "/"
        if not p.startswith("/"):
            p = "/" + p
        return p

    def listdir_attr(self, p):
        d = self.tree.get(self._norm(p))
        if d is None:
            raise FileNotFoundError(f"no such dir {p}")
        return [attr(name, isinstance(v, dict), len(v) if isinstance(v, bytes) else 0) for name, v in d.items()]

    def stat(self, p):
        self.stat_calls.append(p)
        parts = [x for x in self._norm(p).split("/") if x]
        node = self._root()
        for part in parts:
            if part not in node:
                raise FileNotFoundError(f"no such file {p}")
            node = node[part]
        if isinstance(node, bytes):
            return attr(p, False, len(node))
        return attr(p, True, 0)

    def mkdir(self, p):
        self.mkdir_calls.append(p)
        parts = [x for x in self._norm(p).split("/") if x]
        node = self._root()
        for part in parts[:-1]:
            node = node[part]
        node[parts[-1]] = {}

    def open(self, p, mode="rb"):
        parts = [x for x in self._norm(p).split("/") if x]
        node = self._root()
        for part in parts[:-1]:
            node = node[part]
        if "w" in mode:
            f = FakeFile(b"")
            node[parts[-1]] = f.data
            return f
        data = node.get(parts[-1])
        if data is None:
            raise FileNotFoundError(f"no such file {p}")
        return FakeFile(data if isinstance(data, bytes) else b"")

    def remove(self, p):
        parts = [x for x in self._norm(p).split("/") if x]
        node = self._root()
        for part in parts[:-1]:
            node = node[part]
        if parts[-1] not in node:
            raise FileNotFoundError(f"no such file {p}")
        del node[parts[-1]]

    def rename(self, src, dst):
        self.renamed.append((src, dst))
        parts = [x for x in self._norm(src).split("/") if x]
        node = self._root()
        for part in parts[:-1]:
            node = node[part]
        if parts[-1] not in node:
            raise FileNotFoundError(f"no such file {src}")
        val = node.pop(parts[-1])
        dparts = [x for x in self._norm(dst).split("/") if x]
        dnode = self._root()
        for part in dparts[:-1]:
            if part not in dnode:
                dnode[part] = {}
            dnode = dnode[part]
        dnode[dparts[-1]] = val


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} {detail}")


def make_bridge(fake=None):
    b = HidenCloudSFTPBridge()
    b.host, b.user, b.password = "h", "u", "p"
    if fake is not None:
        b._connect = lambda: ((fake, FakeTransport()), None)
    return b


def test_safe_path():
    b = make_bridge()
    safe, err = b._safe_path("a/b/../c.txt")
    check("safe_path normalizes", safe == "/a/c.txt" and err is None, f"{safe} {err}")
    safe, err = b._safe_path("../../etc/passwd")
    check("safe_path traversal stays under root", err is None and safe.startswith("/"), f"{safe} {err}")
    check("safe_path rejects bad types", b._safe_path(None)[0] == "/", "None -> root")


def test_ensure_dir_no_double_slash():
    fake = FakeSFTP()
    b = make_bridge(fake)
    b._ensure_dir(fake, "/new/deep/path")
    check("ensure_dir creates each level", fake.mkdir_calls == ["/new", "/new/deep", "/new/deep/path"], f"{fake.mkdir_calls}")
    check("ensure_dir never emits '//'", all("//" not in p for p in fake.mkdir_calls), f"{fake.mkdir_calls}")
    # idempotent: existing dirs are skipped
    fake.mkdir_calls.clear()
    b._ensure_dir(fake, "/sub/logs/again")
    check("ensure_dir idempotent on existing", fake.mkdir_calls == ["/sub/logs/again"], f"{fake.mkdir_calls}")


def test_read_cap():
    fake = FakeSFTP()
    fake.tree["/"]["big.bin"] = b"x" * (MAX_READ_BYTES + 1)
    b = make_bridge(fake)
    out = b.read_file("/big.bin")
    check("read cap refuses oversized file", "read cap" in out and "Error" in out, out[:80])
    out = b.read_file("/foo.txt")
    check("small file reads fine", out == "hello", repr(out))
    out = b.read_file("/missing.txt")
    check("missing file clear error", "does not exist" in out, out[:80])


def test_stat():
    fake = FakeSFTP()
    b = make_bridge(fake)
    out = b.stat("/foo.txt")
    check("stat shows FILE + size", "FILE" in out and "5 bytes" in out, out)
    out = b.stat("/sub")
    check("stat shows DIR", "DIR" in out, out)
    out = b.stat("/nope")
    check("stat missing path", "does not exist" in out, out)


def test_mkdir_rename():
    fake = FakeSFTP()
    b = make_bridge(fake)
    out = b.mkdir("/brand/new/dir")
    check("mkdir creates parents", "Directory ready" in out and "/brand/new/dir" in fake.mkdir_calls, out)
    out = b.rename("/foo.txt", "/moved.txt")
    check("rename works", "Renamed/moved" in out, out)
    out = b.rename("/ghost.txt", "/x.txt")
    check("rename missing source", "does not exist" in out, out)


def test_search():
    fake = FakeSFTP()
    b = make_bridge(fake)
    out = b.search("/", "log")
    check("search finds by substring", "app.log" in out and "/sub/logs/app.log" in out, out)
    out = b.search("/", "")
    check("search empty pattern lists all", "foo.txt" in out and "bar.md" in out, out)
    # depth 0 = list the start dir's own entries but never recurse into subdirs
    out = b.search("/sub", "", max_depth=0)
    check("search depth cap: own entries listed", "bar.md" in out, out)
    check("search depth cap: no recursion", "app.log" not in out, out)


def test_connect_fail_fast():
    b = HidenCloudSFTPBridge()
    b.host = b.user = b.password = None
    out = b.list_files("/")
    check("connect fails fast w/o env", "not fully configured" in out, out)
    b2 = HidenCloudSFTPBridge()
    b2.host, b2.user, b2.password = "1.2.3.4", "u", "p"
    b2.timeout = 5
    out = b2.list_files("/")
    check("connect error names timeout", "SFTP connection failed" in out and "5s" in out, out)


def test_manager_tools():
    mgr = SftpManager()
    tools = mgr.describe()["tools"]
    for t in ("list_files", "read_file", "write_file", "delete_file", "stat", "mkdir", "rename", "search"):
        check(f"manager has tool {t}", t in tools)
    check("unknown tool handled", "Unknown sftp tool" in mgr.call("nope"))
    fake = FakeSFTP()
    mgr.hidencloud = make_bridge(fake)
    out = mgr.call("stat", path="/foo.txt")
    check("manager dispatches stat", "FILE" in out, out)
    out = mgr.call("search", path="/", pattern="log")
    check("manager dispatches search", "app.log" in out, out)


def main():
    print("== HidenCloud SFTP fixes test ==")
    test_safe_path()
    test_ensure_dir_no_double_slash()
    test_read_cap()
    test_stat()
    test_mkdir_rename()
    test_search()
    test_connect_fail_fast()
    test_manager_tools()
    print(f"\n{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
