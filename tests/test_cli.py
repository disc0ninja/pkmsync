import logging
import os
import pkmsync
import pytest
from argparse import ArgumentParser
from pathlib import Path
from pkmsync.cli import get_config_path
from pkmsync.cli import main as cli
from unittest.mock import patch, Mock

from pkmsync.git_ops import PKMSyncGitOperatorError

def test_get_config_path_returns_passed_config_path_if_passed_config(tmp_path):
    cfg_path = tmp_path / "test_config.toml"
    actual = get_config_path(cfg_path)
    assert actual == cfg_path

def test_get_config_path_returns_defaults_in_expected_order_when_called_with_None(tmp_path, monkeypatch):
    tmp_home = tmp_path
    tmp_xdg_home = tmp_path
    monkeypatch.setenv("HOME", str(tmp_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_xdg_home))
    default_xdg_home = tmp_xdg_home / "pkmsync"
    default_home = tmp_home / ".config"
    default_home_pkmsync = tmp_home / ".config/pkmsync"
    default_xdg_home.mkdir()
    default_home.mkdir()
    default_home_pkmsync.mkdir()
    default_paths = [
            default_xdg_home / "config.toml",
            default_home_pkmsync / "config.toml",
            default_home / "pkmsync.toml",
            tmp_home / ".pkmsync.toml"
        ]
    for p in default_paths[::-1]:
        p.write_text("test")
        assert get_config_path(None) == p

def test_get_config_path_returns_None_when_called_with_None_and_no_default_exists(tmp_path, monkeypatch):
    tmp_home = tmp_path
    tmp_xdg_home = tmp_path
    monkeypatch.setenv("HOME", str(tmp_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_xdg_home))
    default_xdg_home = tmp_xdg_home / "pkmsync"
    default_home = tmp_home / ".config"
    default_home_pkmsync = tmp_home / ".config/pkmsync"
    default_xdg_home.mkdir()
    default_home.mkdir()
    default_home_pkmsync.mkdir()
    default_paths = [
            default_xdg_home / "config.toml",
            default_home_pkmsync / "config.toml",
            default_home / "pkmsync.toml",
            tmp_home / ".pkmsync.toml"
        ]
    for p in default_paths:
        assert not p.exists()
        assert get_config_path(None) == None

@patch("argparse.ArgumentParser")
@patch("pkmsync.cli.get_config_path")
def test_cli_exits_1_when_no_config_found(mock_get_config_path, _mock_argparser, caplog):
    mock_get_config_path.return_value = None
    expected = 1
    with caplog.at_level(logging.ERROR):
        actual = cli()
    assert "Unable to load config from " in caplog.text
    assert actual == expected

@patch("argparse.ArgumentParser")
@patch("pkmsync.cli.get_config_path")
@patch("pkmsync.cli.load_config")
@patch("pkmsync.cli.sync")
def test_cli_exits_1_when_sync_raises(mock_sync, mock_load_config, mock_get_config_path, _mock_argparser, tmp_path, caplog):
    mock_get_config_path.return_value = "test_path"
    mock_load_config.return_value.log_path = tmp_path / "test_logfile"
    mock_sync.side_effect = Exception("test error")
    expected = 1
    with caplog.at_level(logging.ERROR):
        actual = cli()
    assert "Encountered an unexpected exception running sync test error" in caplog.text
    assert actual == expected

@patch("argparse.ArgumentParser")
@patch("pkmsync.cli.get_config_path")
@patch("pkmsync.cli.load_config")
@patch("pkmsync.cli.sync")
def test_cli_exits_0_when_sync_succeeds(mock_sync, mock_load_config, mock_get_config_path, _mock_argparser, tmp_path):
    mock_get_config_path.return_value = "test_path"
    mock_load_config.return_value.log_path = tmp_path / "test_logfile"
    mock_sync.return_value = None
    expected = 0
    actual = cli()
    assert actual == expected

@patch("argparse.ArgumentParser")
@patch("pkmsync.cli.get_config_path")
@patch("pkmsync.cli.load_config")
@patch("pkmsync.cli.sync")
def test_cli_logs_to_file(mock_sync, mock_load_config, mock_get_config_path, _mock_argparser, tmp_path):
    expected = "test logging to file"
    def test_log(_):
        logging.getLogger("pkmsync.sync").warning(expected)

    mock_get_config_path.return_value = "test_path"
    mock_load_config.return_value.log_path = tmp_path / "test_logfile"
    mock_sync.side_effect = test_log
    cli()
    actual = (tmp_path / "test_logfile").read_text()
    assert expected in actual
