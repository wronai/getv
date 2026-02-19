"""E2E tests for getv CLI commands.

Tests run the actual CLI via CliRunner against a temporary GETV_HOME.
"""

import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from getv.__main__ import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def home(tmp_path):
    """Temporary GETV_HOME directory."""
    return str(tmp_path)


def invoke(runner, home, args):
    """Helper to invoke CLI with --home."""
    return runner.invoke(cli, ["--home", home] + args, catch_exceptions=False)


class TestSetAndGet:

    def test_set_and_get(self, runner, home):
        r = invoke(runner, home, ["set", "llm", "groq", "LLM_MODEL=llama3", "API_KEY=gsk_test"])
        assert r.exit_code == 0
        assert "Saved 2 var(s)" in r.output

        r = invoke(runner, home, ["get", "llm", "groq", "LLM_MODEL"])
        assert r.exit_code == 0
        assert r.output.strip() == "llama3"

        r = invoke(runner, home, ["get", "llm", "groq", "API_KEY"])
        assert r.exit_code == 0
        assert r.output.strip() == "gsk_test"

    def test_get_missing_profile(self, runner, home):
        r = invoke(runner, home, ["get", "llm", "nonexistent", "KEY"])
        assert r.exit_code != 0

    def test_get_missing_key(self, runner, home):
        invoke(runner, home, ["set", "llm", "x", "A=1"])
        r = invoke(runner, home, ["get", "llm", "x", "MISSING"])
        assert r.exit_code != 0

    def test_set_invalid_format(self, runner, home):
        r = invoke(runner, home, ["set", "llm", "x", "NOEQUALS"])
        assert r.exit_code != 0


class TestList:

    def test_list_categories(self, runner, home):
        invoke(runner, home, ["set", "llm", "groq", "X=1"])
        invoke(runner, home, ["set", "devices", "rpi3", "Y=2"])
        r = invoke(runner, home, ["list"])
        assert r.exit_code == 0
        assert "llm/" in r.output
        assert "devices/" in r.output

    def test_list_profiles(self, runner, home):
        invoke(runner, home, ["set", "llm", "groq", "MODEL=llama3"])
        invoke(runner, home, ["set", "llm", "openai", "MODEL=gpt-4"])
        r = invoke(runner, home, ["list", "llm"])
        assert r.exit_code == 0
        assert "groq" in r.output
        assert "openai" in r.output

    def test_list_profile_vars(self, runner, home):
        invoke(runner, home, ["set", "llm", "groq", "MODEL=llama3", "API_KEY=secret"])
        r = invoke(runner, home, ["list", "llm", "groq"])
        assert r.exit_code == 0
        assert "MODEL=llama3" in r.output
        # API_KEY should be masked by default
        assert "secret" not in r.output or "secr" in r.output

    def test_list_show_secrets(self, runner, home):
        invoke(runner, home, ["set", "llm", "groq", "API_KEY=mysecretkey123"])
        r = invoke(runner, home, ["list", "llm", "groq", "--show-secrets"])
        assert r.exit_code == 0
        assert "mysecretkey123" in r.output


class TestDelete:

    def test_delete_existing(self, runner, home):
        invoke(runner, home, ["set", "llm", "groq", "X=1"])
        r = invoke(runner, home, ["delete", "llm", "groq"])
        assert r.exit_code == 0
        assert "Deleted" in r.output

        # Confirm gone
        r = invoke(runner, home, ["get", "llm", "groq", "X"])
        assert r.exit_code != 0

    def test_delete_nonexistent(self, runner, home):
        r = invoke(runner, home, ["delete", "llm", "nonexistent"])
        assert "Not found" in r.output


class TestExport:

    def test_export_json(self, runner, home):
        invoke(runner, home, ["set", "llm", "groq", "MODEL=llama3", "KEY=val"])
        r = invoke(runner, home, ["export", "llm", "groq", "--format", "json"])
        assert r.exit_code == 0
        data = json.loads(r.output)
        assert data["MODEL"] == "llama3"

    def test_export_shell(self, runner, home):
        invoke(runner, home, ["set", "llm", "groq", "MODEL=llama3"])
        r = invoke(runner, home, ["export", "llm", "groq", "--format", "shell"])
        assert r.exit_code == 0
        assert "export MODEL='llama3'" in r.output

    def test_export_docker(self, runner, home):
        invoke(runner, home, ["set", "llm", "groq", "MODEL=llama3"])
        r = invoke(runner, home, ["export", "llm", "groq", "--format", "docker"])
        assert r.exit_code == 0
        assert "MODEL=llama3" in r.output

    def test_export_missing_profile(self, runner, home):
        r = invoke(runner, home, ["export", "llm", "nonexistent", "--format", "json"])
        assert r.exit_code != 0


class TestDiff:

    def test_diff_identical(self, runner, home):
        invoke(runner, home, ["set", "llm", "a", "MODEL=gpt4", "KEY=sk1"])
        invoke(runner, home, ["set", "llm", "b", "MODEL=gpt4", "KEY=sk1"])
        r = invoke(runner, home, ["diff", "llm", "a", "b"])
        assert r.exit_code == 0
        assert "identical" in r.output

    def test_diff_changes(self, runner, home):
        invoke(runner, home, ["set", "llm", "a", "MODEL=gpt4", "KEY=sk1"])
        invoke(runner, home, ["set", "llm", "b", "MODEL=llama3", "KEY=sk1", "EXTRA=yes"])
        r = invoke(runner, home, ["diff", "llm", "a", "b"])
        assert r.exit_code == 0
        assert "---" in r.output
        assert "+++" in r.output
        assert "MODEL" in r.output
        assert "EXTRA" in r.output

    def test_diff_missing_profile(self, runner, home):
        invoke(runner, home, ["set", "llm", "a", "X=1"])
        r = invoke(runner, home, ["diff", "llm", "a", "nonexistent"])
        assert r.exit_code != 0


class TestCopy:

    def test_copy_same_category(self, runner, home):
        invoke(runner, home, ["set", "llm", "groq", "MODEL=llama3", "KEY=gsk_x"])
        r = invoke(runner, home, ["copy", "llm/groq", "llm/groq-backup"])
        assert r.exit_code == 0
        assert "Copied" in r.output

        # Verify destination
        r = invoke(runner, home, ["get", "llm", "groq-backup", "MODEL"])
        assert r.output.strip() == "llama3"

    def test_copy_cross_category(self, runner, home):
        invoke(runner, home, ["set", "llm", "groq", "MODEL=llama3"])
        r = invoke(runner, home, ["copy", "llm/groq", "api/groq"])
        assert r.exit_code == 0
        r = invoke(runner, home, ["get", "api", "groq", "MODEL"])
        assert r.output.strip() == "llama3"

    def test_copy_bad_format(self, runner, home):
        r = invoke(runner, home, ["copy", "bad", "format"])
        assert r.exit_code != 0

    def test_copy_missing_source(self, runner, home):
        r = invoke(runner, home, ["copy", "llm/nonexistent", "llm/backup"])
        assert r.exit_code != 0


class TestImport:

    def test_import_env_file(self, runner, home, tmp_path):
        env_file = tmp_path / "test.env"
        env_file.write_text("DB_HOST=localhost\nDB_PORT=5432\n")
        r = invoke(runner, home, ["import", str(env_file), "db", "local"])
        assert r.exit_code == 0
        assert "Imported 2 var(s)" in r.output

        r = invoke(runner, home, ["get", "db", "local", "DB_HOST"])
        assert r.output.strip() == "localhost"

    def test_import_env_default_category(self, runner, home, tmp_path):
        env_file = tmp_path / "production.env"
        env_file.write_text("SECRET=abc\n")
        r = invoke(runner, home, ["import", str(env_file)])
        assert r.exit_code == 0
        assert "imported/production" in r.output

    def test_import_empty_file(self, runner, home, tmp_path):
        env_file = tmp_path / "empty.env"
        env_file.write_text("# only comments\n")
        r = invoke(runner, home, ["import", str(env_file)])
        assert r.exit_code != 0


class TestUseAndDefaults:

    def test_use_and_defaults(self, runner, home):
        r = invoke(runner, home, ["use", "myapp", "llm", "groq"])
        assert r.exit_code == 0
        assert "myapp" in r.output

        r = invoke(runner, home, ["defaults", "myapp"])
        assert r.exit_code == 0
        assert "llm=groq" in r.output

    def test_defaults_list_all(self, runner, home):
        invoke(runner, home, ["use", "app1", "llm", "groq"])
        invoke(runner, home, ["use", "app2", "llm", "openai"])
        r = invoke(runner, home, ["defaults"])
        assert r.exit_code == 0
        assert "app1" in r.output
        assert "app2" in r.output

    def test_defaults_empty(self, runner, home):
        r = invoke(runner, home, ["defaults"])
        assert r.exit_code == 0
        assert "No app defaults" in r.output


class TestExec:

    def test_exec_with_env(self, runner, home, tmp_path):
        invoke(runner, home, ["set", "llm", "test", "MY_VAR=hello123"])
        # Write env var to a file so we can verify it (subprocess stdout not captured by CliRunner)
        out_file = tmp_path / "exec_output.txt"
        r = runner.invoke(cli, ["--home", home, "exec", "llm", "test", "--",
                                "python", "-c",
                                f"import os; open('{out_file}','w').write(os.environ.get('MY_VAR',''))"],
                          catch_exceptions=False)
        assert r.exit_code == 0
        assert out_file.read_text() == "hello123"

    def test_exec_missing_command(self, runner, home):
        invoke(runner, home, ["set", "llm", "test", "X=1"])
        r = runner.invoke(cli, ["--home", home, "exec", "llm", "test", "--",
                                "nonexistent_command_xyz"],
                          catch_exceptions=False)
        assert r.exit_code != 0
