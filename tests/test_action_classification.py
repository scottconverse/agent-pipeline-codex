# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTION_CLASSIFICATION = ROOT / "pipelines" / "action-classification.yaml"


MATCH_CASES = {
    r"rm\s+-rf": "rm -rf build",
    r"rm\s+-r\s": "rm -r build",
    r"\bshred\b": "shred secret.txt",
    r"git\s+push\b.*\bmain\b": "git push origin main",
    r"git\s+push\b.*\bmaster\b": "git push origin master",
    r"git\s+push\b.*--force\b": "git push --force origin feature",
    r"git\s+tag\b.*-d\b": "git tag -d v1.0.0",
    r"git\s+branch\b.*-D\b": "git branch -D old-branch",
    r"\bnpm\s+publish\b": "npm publish",
    r"\btwine\s+upload\b": "twine upload dist/*",
    r"\bcargo\s+publish\b": "cargo publish",
    r"\bchmod\b": "chmod 777 file",
    r"\bchown\b": "chown user file",
    r"\bssh-keygen\b": "ssh-keygen -t ed25519",
    r"\bDROP\s+TABLE\b": "psql -c 'DROP TABLE users'",
    r"\bDROP\s+DATABASE\b": "psql -c 'DROP DATABASE civic'",
    r"\bTRUNCATE\b": "psql -c 'TRUNCATE users'",
    r"\bDELETE\s+FROM\b": "psql -c 'DELETE FROM users'",
    r"export\s+\w*KEY=": "export API_KEY=abc",
    r"export\s+\w*SECRET=": "export CLIENT_SECRET=abc",
    r"export\s+\w*TOKEN=": "export ACCESS_TOKEN=abc",
    r"export\s+\w*PASSWORD=": "export DB_PASSWORD=abc",
    r"\bnpm\s+install\b.*--global\b": "npm install typescript --global",
    r"\bnpm\s+install\s+-g\b": "npm install -g typescript",
    r"\bsudo\b": "sudo apt update",
    r"\bgit\s+commit\b.*BREAKING": "git commit -m 'feat!: BREAKING change'",
    r"git\s+push\b(?!.*\b(main|master)\b)(?!.*--force\b)": "git push origin feature",
    r"\bgh\s+pr\s+create\b": "gh pr create --fill",
    r"\bgh\s+issue\s+create\b": "gh issue create --title bug",
    r"\bgh\s+release\s+create\b": "gh release create v1.0.0",
    r"curl\b.*-X\s+POST": "curl https://example.com -X POST",
    r"curl\b.*-X\s+PUT": "curl https://example.com -X PUT",
    r"curl\b.*-X\s+PATCH": "curl https://example.com -X PATCH",
    r"curl\b.*-X\s+DELETE": "curl https://example.com -X DELETE",
    r"curl\b.*--data\b": "curl https://example.com --data '{}'",
    r"wget\b.*--post": "wget https://example.com --post-data=x",
    r"\bsendmail\b": "sendmail user@example.com",
    r"\bslack-cli\b": "slack-cli send hello",
    r"\bdocker\s+push\b": "docker push image:tag",
    r"\bkubectl\s+apply\b": "kubectl apply -f deploy.yaml",
    r"\bkubectl\s+delete\b": "kubectl delete pod civic",
    r"\s>\s": "echo hi > file.txt",
    r"\s>>\s": "echo hi >> file.txt",
    r"\btee\b": "echo hi | tee file.txt",
    r"\bcp\s": "cp a b",
    r"\bmv\s": "mv a b",
    r"\bmkdir\b": "mkdir build",
    r"\brm\s(?!-r)(?!-rf)": "rm file.txt",
    r"\bgit\s+add\b": "git add file.txt",
    r"\bgit\s+commit\b": "git commit -m update",
    r"\bgit\s+stash\b": "git stash",
    r"\bgit\s+checkout\b": "git checkout feature",
    r"\bgit\s+branch\s(?!.*-D\b)(?!.*-d\b)": "git branch feature",
    r"\bpip\s+install\b": "pip install pytest",
    r"\bnpm\s+install\b(?!\s+--global\b)": "npm install",
    r"^cat\s": "cat README.md",
    r"^less\s": "less README.md",
    r"^head\s": "head README.md",
    r"^tail\s": "tail README.md",
    r"\bgrep\b": "grep -R thing .",
    r"^find\s": "find . -name README.md",
    r"^ls\b": "ls -la",
    r"^wc\s": "wc -l README.md",
    r"^diff\s": "diff a b",
    r"\bgit\s+log\b": "git log --oneline",
    r"\bgit\s+diff\b": "git diff",
    r"\bgit\s+status\b": "git status",
    r"\bgit\s+show\b": "git show HEAD",
    r"python\s+-c\b": "python -c \"print(1)\"",
    r"\bpytest\b": "pytest -q",
    r"\bruff\s+check\b": "ruff check .",
    r"\bmypy\b": "mypy src",
}


def _patterns() -> list[str]:
    patterns: list[str] = []
    for raw in ACTION_CLASSIFICATION.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if stripped.startswith("- pattern: "):
            _, value = stripped.split(":", 1)
            patterns.append(value.strip().strip("'\""))
    return patterns


def test_every_action_classification_regex_compiles_and_has_a_fixture() -> None:
    patterns = _patterns()

    assert patterns
    assert set(patterns) == set(MATCH_CASES)
    for pattern in patterns:
        re.compile(pattern)


def test_every_action_classification_regex_matches_its_fixture_only() -> None:
    safe_noop = "echo agent pipeline safe noop"

    for pattern in _patterns():
        compiled = re.compile(pattern)
        assert compiled.search(MATCH_CASES[pattern]), pattern
        assert not compiled.search(safe_noop), pattern


def test_feature_branch_push_rule_does_not_capture_read_only_or_force_push_commands() -> None:
    pattern = re.compile(r"git\s+push\b(?!.*\b(main|master)\b)(?!.*--force\b)")

    assert pattern.search("git push origin feature")
    assert not pattern.search("git push --force origin feature")
    assert not pattern.search("git push origin main")
    assert not pattern.search("git log --oneline")
    assert not pattern.search("git status")
    assert not pattern.search("git diff")


def test_force_push_rule_catches_common_force_forms() -> None:
    force_long = re.compile(r"git\s+push\b.*--force\b")

    assert force_long.search("git push --force origin feature")
    assert force_long.search("git push origin feature --force")
    assert not force_long.search("git push origin feature")
