import logging
import pytest
from unittest.mock import ANY, call, patch, Mock
from pathlib import Path
from pkmsync import sync
from pkmsync.lock import PKMSyncLockError

import pkmsync
# sync(config: PKMSyncConfig), builds GitOperator/PKMSyncLock internally
# Lock contention → caught, logged quietly, return (not an error); everything else propagates
# Flow: acquire lock → clean up stale rebase if found (info log) → status() → stage+commit if dirty → pull → push
# Commit message: "PKMSyncCommit: <device> <date time>", device-local time
# status() == 3 at that point should be unreachable — raise loudly if it happens anyway

@patch("pkmsync.sync.PKMSyncLock")
@patch("pkmsync.sync.GitOperator")
def test_sync_aquires_lock_on_repo_with_unstaged_changes_makes_commit_pulls_and_pushes(mock_GitOperator, mock_PKMSyncLock):
    mock_conf = Mock()
    mock_conf.device_id = "testid1"
    mock_conf.remote_url = "ssh://fake.git/fake/repo"
    mock_conf.vault_path = Path("fake_repo")
    mock_conf.log_path = Path("fake_logs")
    mock_conf.timezone = "America/Chicago"
    manager = Mock()
    manager.attach_mock(mock_PKMSyncLock.return_value.__enter__, "lock")
    manager.attach_mock(mock_GitOperator.return_value.check_for_rebase_in_progress, "check_for_rebase_in_progress")
    manager.attach_mock(mock_GitOperator.return_value.status, "status")
    manager.attach_mock(mock_GitOperator.return_value.stage, "stage")
    manager.attach_mock(mock_GitOperator.return_value.commit, "commit")
    manager.attach_mock(mock_GitOperator.return_value.pull, "pull")
    manager.attach_mock(mock_GitOperator.return_value.push, "push")
    manager.attach_mock(mock_PKMSyncLock.return_value.__exit__, "unlock")

    mock_GitOperator.return_value.check_for_rebase_in_progress.return_value=False
    mock_GitOperator.return_value.status.return_value=1

    sync.sync(mock_conf)

    assert manager.mock_calls == [
        call.lock(),
        call.check_for_rebase_in_progress(),
        call.status(),
        call.stage(),
        call.commit(ANY),   # the commit message has a live timestamp in it, so match loosely with unittest.mock.ANY
        call.pull(),
        call.push(),
        call.unlock(None, None, None),  # __exit__ always receives (exc_type, exc_value, traceback), None/None/None on success
    ]


@patch("pkmsync.sync.PKMSyncLock")
@patch("pkmsync.sync.GitOperator")
def test_sync_catches_and_logs_when_PKMSyncLockError_is_rasied_before_lock_can_be_acquired(mock_GitOperator, mock_PKMSyncLock, caplog):
    mock = Mock()
    mock.lock, mock.check_for_rebase_in_progress, mock.status, mock.stage, mock.commit, mock.pull, mock.push, mock.unlock = (
                mock_PKMSyncLock.return_value.__enter__,
                mock_GitOperator.return_value.check_for_rebase_in_progress,
                mock_GitOperator.return_value.status,
                mock_GitOperator.return_value.stage,
                mock_GitOperator.return_value.commit,
                mock_GitOperator.return_value.pull,
                mock_GitOperator.return_value.push,
                mock_PKMSyncLock.return_value.__exit__
            )
    mock_conf = Mock()
    mock_conf.device_id = "testid1"
    mock_conf.remote_url = "ssh://fake.git/fake/repo"
    mock_conf.vault_path = Path("fake_repo")
    mock_conf.log_path = Path("fake_logs")
    mock_conf.timezone = "America/Chicago"
    mock.lock.side_effect=PKMSyncLockError("test error")

    with caplog.at_level(logging.INFO):
        sync.sync(mock_conf)
    assert "Lock held by sync already in progress" in caplog.text
    mock.lock.assert_called_once()
    mock.check_for_rebase_in_progress.assert_not_called()
    mock.status.assert_not_called()
    mock.stage.assert_not_called()
    mock.commit.assert_not_called()
    mock.pull.assert_not_called()
    mock.push.assert_not_called()

@patch("pkmsync.sync.PKMSyncLock")
@patch("pkmsync.sync.GitOperator")
def test_sync_raises_if_git_status_not_in_0_1_2(mock_GitOperator, mock_PKMSyncLock):
    mock = Mock()
    mock.lock, mock.check_for_rebase_in_progress, mock.status, mock.stage, mock.commit, mock.pull, mock.push, mock.unlock = (
                mock_PKMSyncLock.return_value.__enter__,
                mock_GitOperator.return_value.check_for_rebase_in_progress,
                mock_GitOperator.return_value.status,
                mock_GitOperator.return_value.stage,
                mock_GitOperator.return_value.commit,
                mock_GitOperator.return_value.pull,
                mock_GitOperator.return_value.push,
                mock_PKMSyncLock.return_value.__exit__
            )
    mock_conf = Mock()
    mock_conf.device_id = "testid1"
    mock_conf.remote_url = "ssh://fake.git/fake/repo"
    mock_conf.vault_path = Path("fake_repo")
    mock_conf.log_path = Path("fake_logs")
    mock_conf.timezone = "America/Chicago"
    mock.check_for_rebase_in_progress.return_value=False
    mock.status.return_value=3

    with pytest.raises(sync.PKMSyncSyncError) as e:
        sync.sync(mock_conf)
    e.match("Encountered unexpected status of repo, status 3. Please recover repo state manually before retrying sync")
    mock.lock.assert_called_once()
    mock.unlock.assert_called_once()
