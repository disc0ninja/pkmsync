import pytest
from unittest.mock import patch, mock_open

from pkmsync import config
from pathlib import Path

def test_PKMSyncConfig_expand_expands_vars(monkeypatch):
    monkeypatch.setenv("TEST_HOME", "/tmp/fake/home")
    expected = Path("/tmp/fake/home")
    actual = config.PKMSyncConfig._expand("$TEST_HOME")
    assert actual == expected

def test_PKMSyncConfig_expand_expands_tilde_to_home(monkeypatch):
    monkeypatch.setenv("HOME", "/tmp/fake/home")
    expected = Path("/tmp/fake/home/mydir")
    actual = config.PKMSyncConfig._expand("~/mydir")
    assert actual == expected

def test_PKMSyncConfig_expand_expands_to_default_when_XDG_STATE_HOME_is_not_set(monkeypatch):
    monkeypatch.delenv("XDG_STATE_HOME", False)
    monkeypatch.setenv("HOME", "/tmp/fake/home")
    expected = Path("/tmp/fake/home/.local/state/pkmsync/pkmsync.log")
    actual = config.PKMSyncConfig._expand("$XDG_STATE_HOME/pkmsync/pkmsync.log")
    assert actual == expected

def test_PKMSyncConfig_expand_raises_when_unable_to_expand_var(monkeypatch):
    monkeypatch.delenv("UNSET_VAR", False)
    with pytest.raises(config.PKMSyncConfigError):
            config.PKMSyncConfig._expand("$UNSET_VAR/testing")


test_defaults_toml_data = b"""
device_id="testdevice123"
remote_url="ssh://fake.git/testing/test"
vault_path="$TEST_HOME/.pkms-test"
"""

@patch("builtins.open", new_callable=mock_open, read_data=test_defaults_toml_data)
def test_load_config_succeeds_with_default_log_path_and_branch(mock_file, monkeypatch):
    monkeypatch.setenv("TEST_HOME", "/tmp/fake/home")
    monkeypatch.setenv("XDG_STATE_HOME", "/tmp/fake/xdg_home")
    C = config.load_config('test.toml')
    mock_file.assert_called_with('test.toml', 'rb')
    assert C.branch == "main"
    assert C.device_id == "testdevice123"
    assert C.remote_url == "ssh://fake.git/testing/test"
    assert C.vault_path == Path("/tmp/fake/home/.pkms-test")
    assert C.log_path == Path("/tmp/fake/xdg_home/pkmsync/pkmsync.log")

test_complete_toml_data = b"""
device_id="testdevice123"
remote_url="ssh://fake.git/testing/test"
vault_path="$TEST_HOME/.pkms-test"
branch="mybranch"
log_path="mylogs"
"""

@patch("builtins.open", new_callable=mock_open, read_data=test_complete_toml_data)
def test_load_config_succeeds_with_all_settings(mock_file, monkeypatch):
    monkeypatch.setenv("TEST_HOME", "/tmp/fake/home")
    C = config.load_config('test.toml')
    mock_file.assert_called_with('test.toml', 'rb')
    assert C.branch == "mybranch"
    assert C.device_id == "testdevice123"
    assert C.remote_url == "ssh://fake.git/testing/test"
    assert C.vault_path == Path("/tmp/fake/home/.pkms-test")
    assert C.log_path == Path("mylogs")


def test_load_config_reads_real_file(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_HOME", "/tmp/fake/home")
    toml_data = """
    device_id="testdevice123"
    remote_url="ssh://fake.git/testing/test"
    vault_path="$TEST_HOME/.pkms-test"
    branch="mybranch"
    log_path="mylogs"
    """
    d = tmp_path
    p = d / "test_conf.toml"
    p.write_text(toml_data)

    C = config.load_config(p)
    assert C.branch == "mybranch"
    assert C.device_id == "testdevice123"
    assert C.remote_url == "ssh://fake.git/testing/test"
    assert C.vault_path == Path("/tmp/fake/home/.pkms-test")
    assert C.log_path == Path("mylogs")
