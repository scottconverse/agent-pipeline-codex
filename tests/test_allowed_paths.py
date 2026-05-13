# SPDX-License-Identifier: Apache-2.0

import subprocess

from scripts import check_allowed_paths
from scripts.check_allowed_paths import _is_under, _load_manifest_lists


def test_manifest_path_lists_keep_hash_inside_quotes(tmp_path) -> None:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        """
pipeline_run:
  allowed_paths:
    - "docs/#archive/"
    - "scripts/" # real comment
  forbidden_paths:
    - "tmp/#scratch/"
""",
        encoding="utf-8",
    )

    allowed, forbidden = _load_manifest_lists(manifest)

    assert allowed == ["docs/#archive/", "scripts/"]
    assert forbidden == ["tmp/#scratch/"]


def test_is_under_matches_prefix_boundaries() -> None:
    assert _is_under("src/auth/login.py", ["src/auth/"])
    assert _is_under("src/auth", ["src/auth/"])
    assert not _is_under("src/authorization.py", ["src/auth/"])


def test_git_changed_files_includes_untracked(monkeypatch) -> None:
    def fake_run(args, **kwargs):
        if args[:3] == ["git", "diff", "--name-only"]:
            return subprocess.CompletedProcess(args, 0, stdout="scripts/a.py\n", stderr="")
        if args[:3] == ["git", "ls-files", "--others"]:
            return subprocess.CompletedProcess(args, 0, stdout="docs/new.md\n", stderr="")
        raise AssertionError(args)

    monkeypatch.setattr(check_allowed_paths.subprocess, "run", fake_run)

    assert check_allowed_paths._git_changed_files() == ["docs/new.md", "scripts/a.py"]

