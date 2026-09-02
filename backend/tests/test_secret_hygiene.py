import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_env_is_ignored():
    result = subprocess.run(
        ["git", "check-ignore", "-q", ".env"],
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_env_example_has_placeholders_only():
    values = {}
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        key, value = line.split("=", 1)
        values[key] = value
        assert len(value) <= 40 or not any(
            token in value.lower() for token in ("sk-", "ghp_", "token")
        )
    assert values["POSTGRES_PASSWORD"] == "change_me"
