"""Local helpers must fail closed without connecting to remote/application services."""
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location("local_check", Path(__file__).parents[1] / "scripts/check_local.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


@pytest.mark.parametrize("value", [None, "not a URL", "postgresql://role:hidden@remote.invalid/dev", "sqlite://", "postgresql://role@localhost/postgres"])
def test_local_readiness_rejects_missing_remote_or_maintenance_target(value):
    with pytest.raises(ValueError, match="explicit dedicated loopback"):
        check.local_url(value)


def test_readiness_reports_names_without_secret_values(monkeypatch, capsys):
    monkeypatch.setattr(check, "settings", lambda: {"DATABASE_URL":"postgresql://role:private-password@remote.invalid/dev", "SECRET_KEY":"private-secret"})
    assert check.main() == 1
    result = capsys.readouterr().out
    assert "DATABASE_URL" in result and "ALEMBIC_DATABASE_URL" in result
    assert "private-password" not in result and "private-secret" not in result and "remote.invalid" not in result
