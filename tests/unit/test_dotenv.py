import os

from config.settings import apply_env_file


def test_apply_env_file_sets_unset_keys(tmp_path, monkeypatch):
    monkeypatch.delenv("CSCN_TEST_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text(
        '# comment\nCSCN_TEST_KEY = "hello world"\n\nBLANKLINE\n', encoding="utf-8")
    apply_env_file(env)
    assert os.environ.get("CSCN_TEST_KEY") == "hello world"


def test_apply_env_file_does_not_override_existing(tmp_path, monkeypatch):
    monkeypatch.setenv("CSCN_TEST_KEY2", "original")
    env = tmp_path / ".env"
    env.write_text("CSCN_TEST_KEY2=changed\n", encoding="utf-8")
    apply_env_file(env)
    assert os.environ.get("CSCN_TEST_KEY2") == "original"
