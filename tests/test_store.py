"""Tests for getv.store.EnvStore."""

import pytest
from pathlib import Path
from getv.store import EnvStore


@pytest.fixture
def tmp_env(tmp_path):
    """Create a temporary .env file."""
    env_file = tmp_path / "test.env"
    env_file.write_text(
        "# Database config\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_PASSWORD=secret123\n"
        "\n"
        "# App\n"
        "APP_NAME=myapp\n"
    )
    return env_file


def test_load_and_get(tmp_env):
    store = EnvStore(tmp_env)
    assert store.get("DB_HOST") == "localhost"
    assert store.get("DB_PORT") == "5432"
    assert store.get("DB_PASSWORD") == "secret123"
    assert store.get("APP_NAME") == "myapp"
    assert store.get("MISSING") is None
    assert store.get("MISSING", "default") == "default"


def test_getitem(tmp_env):
    store = EnvStore(tmp_env)
    assert store["DB_HOST"] == "localhost"
    with pytest.raises(KeyError):
        _ = store["NONEXISTENT"]


def test_contains(tmp_env):
    store = EnvStore(tmp_env)
    assert "DB_HOST" in store
    assert "MISSING" not in store


def test_len_and_iter(tmp_env):
    store = EnvStore(tmp_env)
    assert len(store) == 4
    assert set(store) == {"DB_HOST", "DB_PORT", "DB_PASSWORD", "APP_NAME"}


def test_set_and_save(tmp_env):
    store = EnvStore(tmp_env)
    store.set("NEW_KEY", "new_value")
    store.set("DB_HOST", "10.0.0.1")
    store.save()

    # Re-read
    store2 = EnvStore(tmp_env)
    assert store2.get("NEW_KEY") == "new_value"
    assert store2.get("DB_HOST") == "10.0.0.1"
    assert store2.get("DB_PORT") == "5432"  # unchanged


def test_save_preserves_comments(tmp_env):
    store = EnvStore(tmp_env)
    store.set("DB_HOST", "10.0.0.1")
    store.save()

    content = tmp_env.read_text()
    assert "# Database config" in content
    assert "# App" in content


def test_delete(tmp_env):
    store = EnvStore(tmp_env)
    store.delete("DB_PASSWORD")
    store.save()

    store2 = EnvStore(tmp_env)
    assert "DB_PASSWORD" not in store2
    assert len(store2) == 3


def test_update(tmp_env):
    store = EnvStore(tmp_env)
    store.update({"DB_HOST": "newhost", "EXTRA": "val"})
    assert store.get("DB_HOST") == "newhost"
    assert store.get("EXTRA") == "val"


def test_as_dict(tmp_env):
    store = EnvStore(tmp_env)
    d = store.as_dict()
    assert isinstance(d, dict)
    assert d["DB_HOST"] == "localhost"
    assert len(d) == 4


def test_merge_file(tmp_path):
    base = tmp_path / "base.env"
    base.write_text("A=1\nB=2\n")
    overlay = tmp_path / "overlay.env"
    overlay.write_text("B=overridden\nC=3\n")

    store = EnvStore(base)
    store.merge_file(overlay)
    assert store.get("A") == "1"
    assert store.get("B") == "overridden"
    assert store.get("C") == "3"


def test_to_shell_export(tmp_env):
    store = EnvStore(tmp_env)
    shell = store.to_shell_export()
    assert "export APP_NAME='myapp'" in shell
    assert "export DB_HOST='localhost'" in shell


def test_to_json(tmp_env):
    import json
    store = EnvStore(tmp_env)
    data = json.loads(store.to_json())
    assert data["DB_HOST"] == "localhost"


def test_auto_create(tmp_path):
    new_file = tmp_path / "subdir" / "new.env"
    store = EnvStore(new_file)
    store.set("KEY", "VAL")
    store.save()
    assert new_file.exists()
    assert EnvStore(new_file).get("KEY") == "VAL"


def test_quoted_values(tmp_path):
    env_file = tmp_path / "quoted.env"
    env_file.write_text('KEY1="hello world"\nKEY2=\'single quoted\'\nKEY3=no quotes\n')
    store = EnvStore(env_file)
    assert store.get("KEY1") == "hello world"
    assert store.get("KEY2") == "single quoted"
    assert store.get("KEY3") == "no quotes"


def test_reload(tmp_env):
    store = EnvStore(tmp_env)
    assert store.get("DB_HOST") == "localhost"
    # External change
    tmp_env.write_text("DB_HOST=changed\n")
    store.reload()
    assert store.get("DB_HOST") == "changed"
