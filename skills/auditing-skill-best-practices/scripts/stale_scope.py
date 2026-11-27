#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Print a compact Git stale-scope card: stale_scope.py <target> <previous.json>."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath


def git(cwd: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "--no-pager", *args], cwd=cwd,
                            capture_output=True, check=False)
    if result.returncode not in ((0, 1) if "--no-index" in args else (0,)):
        raise ValueError("Git could not bound the target changes")
    return result.stdout


def snapshot(target: Path) -> dict:
    repo = Path(os.fsdecode(git(target, "rev-parse", "--show-toplevel")).strip()).resolve()
    prefix = target.relative_to(repo).as_posix()
    names = git(repo, "ls-files", "--cached", "--others", "-z", "--", prefix)
    files = {}
    for raw in set(names.split(b"\0")) - {b""}:
        path = repo / os.fsdecode(raw)
        relative = path.relative_to(target).as_posix()
        if path.is_symlink():
            files[relative] = {"link": os.readlink(path)}
        elif path.is_file():
            files[relative] = {"bytes": base64.b64encode(path.read_bytes()).decode("ascii"),
                               "executable": bool(path.stat().st_mode & 0o111)}
        elif path.exists():
            raise ValueError("target inventory contains an unsupported entry")
    return {"target": str(target), "repo": str(repo), "files": files}


def baseline_path(findings: Path) -> Path:
    return findings.with_suffix(".scope.json")


def save_baseline(target: Path, findings: Path) -> None:
    """Called by the renderer; an unavailable baseline selects full audit later."""
    path = baseline_path(findings)
    if path.exists():
        return  # Rendering a historical snapshot again must not move its audit boundary.
    try:
        data = snapshot(target)
        data["findings_sha256"] = hashlib.sha256(findings.read_bytes()).hexdigest()
        path.write_text(json.dumps(data), encoding="utf-8")
    except (OSError, ValueError):
        return


def materialize(folder: Path, files: dict) -> None:
    folder.mkdir()
    for name, entry in files.items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("invalid baseline path")
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if "link" in entry:
            path.symlink_to(entry["link"])
        else:
            path.write_bytes(base64.b64decode(entry["bytes"], validate=True))
            path.chmod(0o755 if entry["executable"] else 0o644)


PATH_TOKEN = re.compile(r"(?<![\w:/\\.-])(?:[\w.-]+[/\\])*[\w-]+\.[a-zA-Z][\w.-]*")


def cited_paths(text: str, origin: str, known: set[str]) -> set[str]:
    text = text.replace("\\", "/")
    result = set()
    # Inventory matching also handles names containing spaces.
    for name in known:
        if re.search(r"(?<![\w/.-])" + re.escape(name) + r"(?![\w/.-])", text):
            result.add(name)
    for match in PATH_TOKEN.finditer(text):
        token = match[0].rstrip(".")
        if token.startswith(("http", "www.")) or "://" in text[max(0, match.start() - 8):match.end()]:
            continue
        local = os.path.normpath(str(PurePosixPath(origin).parent / token))
        path = token if token in known else local
        if path != ".." and not path.startswith(("../", "/")):
            result.add(path)
    return result


def card(target: Path, findings: Path) -> dict:
    prior = json.loads(findings.read_text(encoding="utf-8"))
    before = json.loads(baseline_path(findings).read_text(encoding="utf-8"))
    if Path(prior["target"]).resolve() != target or before["target"] != str(target):
        raise ValueError("prior audit target differs")
    if before["findings_sha256"] != hashlib.sha256(findings.read_bytes()).hexdigest():
        raise ValueError("prior findings changed after baseline capture")
    after = snapshot(target)
    if before["repo"] != after["repo"]:
        raise ValueError("Git repository identity differs")
    result = {"changed": [], "added": [], "deleted": [], "renamed": []}
    cited = set()
    known = set(before["files"]) | set(after["files"])
    with tempfile.TemporaryDirectory(prefix="audit-scope-") as directory:
        root = Path(directory)
        materialize(root / "before", before["files"])
        materialize(root / "after", after["files"])
        common = ("diff", "--no-index", "--no-ext-diff", "--no-textconv", "--find-renames")
        rows = iter(git(root, *common, "--name-status", "-z", "--", "before", "after").split(b"\0"))
        for status in rows:
            if not status:
                continue
            name = os.fsdecode(next(rows)).split("/", 1)[1]
            if status.startswith(b"R"):
                new = os.fsdecode(next(rows)).split("/", 1)[1]
                result["renamed"].append({"from": name, "to": new})
            else:
                result[{b"M": "changed", b"T": "changed", b"A": "added", b"D": "deleted"}[status]].append(name)
        # Per-file hunks avoid parsing Git's quoted diff headers as target paths.
        for name in sorted(known):
            old, new = before["files"].get(name), after["files"].get(name)
            if old == new:
                continue
            diff = git(root, "diff", "--no-index", "--no-ext-diff", "--no-textconv",
                       "--no-color", "--unified=0", "--", str(root / "before" / name) if old else os.devnull,
                       str(root / "after" / name) if new else os.devnull).decode("utf-8", errors="replace")
            for line in diff.splitlines():
                if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
                    cited.update(cited_paths(line[1:], name, known))
    paths = set(result["changed"] + result["added"] + result["deleted"]) | cited
    for rename in result["renamed"]:
        paths.update((rename["from"], rename["to"]))
    result["cited"] = sorted(cited)
    result["rules"] = [rule["id"] for rule in prior["rules"]
                       if cited_paths(rule["evidence"], "", known) & paths]
    result["read"] = sorted(paths & set(after["files"]))
    return result


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(json.dumps({"fallback": "full", "reason": "expected <target> <previous.json>"}))
        return 2
    try:
        result = card(Path(argv[1]).expanduser().resolve(), Path(argv[2]).expanduser().resolve())
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as error:
        result = {"fallback": "full", "reason": str(error)}
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
