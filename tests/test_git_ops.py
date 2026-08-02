import pytest
import subprocess
from pathlib import Path
from pkmsync import git_ops
from unittest.mock import patch, MagicMock


class TestGitOperator_status():
    def test_status_raises_on_git_error(self, tmp_path):
        d = tmp_path / "repo"
        d.mkdir()
        G = git_ops.GitOperator(d)
        with pytest.raises(git_ops.PKMSyncGitOperatorError):
            G.status()

    def test_status_returns_0_when_status_reports_clean(self, tmp_path):
        d = tmp_path / "repo"
        d.mkdir()
        _=subprocess.run(["git", "-C", d, "init"])
        G = git_ops.GitOperator(d)
        assert G.status() == 0

    @patch("subprocess.run")
    def test_status_returns_1_when_status_reports_unstaged_changes(self, mock):
        mock.return_value.stdout=" A some_staged_file.txt"
        mock.return_value.returncode=0
        Gadd = git_ops.GitOperator(Path("fake_repo"))
        assert Gadd.status() == 1
        mock.return_value.stdout=" U some_staged_file.txt"
        Gupdate = git_ops.GitOperator(Path("fake_repo"))
        assert Gupdate.status() == 1
        mock.return_value.stdout=" D some_staged_file.txt"
        Gdelete = git_ops.GitOperator(Path("fake_repo"))
        assert Gdelete.status() == 1

    @patch("subprocess.run")
    def test_status_returns_2_when_status_reports_staged_changes(self, mock):
        mock.return_value.stdout="A some_staged_file.txt"
        mock.return_value.returncode=0
        Gadd = git_ops.GitOperator(Path("fake_repo"))
        assert Gadd.status() == 2
        mock.return_value.stdout="MM some_staged_file.txt"
        Gupdate = git_ops.GitOperator(Path("fake_repo"))
        assert Gupdate.status() == 2
        mock.return_value.stdout="D some_staged_file.txt"
        Gdelete = git_ops.GitOperator(Path("fake_repo"))
        assert Gdelete.status() == 2

    @patch("subprocess.run")
    def test_status_returns_3_when_status_reports_rebase_conflict(self, mock):
        mock.return_value.stdout="UU conflicting_file.txt\n"
        mock.return_value.returncode=0
        G = git_ops.GitOperator(Path("fake_repo"))
        assert G.status() == 3


class TestGitOperator_check_for_rebase_in_progress():
    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_check_for_rebase_in_progress_returns_true_if_rebase_in_progress_found(self, mock_path_exists, mock_subprocess_run):
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout=".git"
        mock_path_exists.return_value = True
        G = git_ops.GitOperator(Path("fake_repo"))
        assert G.check_for_rebase_in_progress()

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_check_for_rebase_in_progress_returns_fase_if_no_rebase_in_progress_found(self, mock_path_exists, mock_subprocess_run):
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = ".git\n"
        mock_path_exists.return_value = False
        G = git_ops.GitOperator(Path("fake_repo"))
        assert not G.check_for_rebase_in_progress()


class TestGitOperator_pull():
    @patch("subprocess.run")
    @patch("pkmsync.git_ops.GitOperator.check_for_rebase_in_progress")
    def test_pull_raises_on_git_error(self, mock_check_for_rebase_in_progress, mock_subprocess_run):
        mock_check_for_rebase_in_progress.return_value = False
        mock_subprocess_run.return_value.returncode=128
        G = git_ops.GitOperator(Path("fake_repo"))
        with pytest.raises(git_ops.PKMSyncGitOperatorError) as e:
            G.pull()
        e.match("Encountered error trying to pull and rebase. Command exited with")

    @patch("subprocess.run")
    def test_pull_returns_None_on_success(self, mock):
        mock.return_value.returncode=0
        G = git_ops.GitOperator(Path("fake_repo"))
        assert G.pull() is None

    @patch("subprocess.run")
    @patch("pkmsync.git_ops.GitOperator.check_for_rebase_in_progress")
    def test_pull_aborts_pull_if_rebase_in_progress(self, mock_check_for_rebase_in_progress, mock_subprocess_run):
        mock_subprocess_run.return_value.returncode=0
        mock_check_for_rebase_in_progress.return_value = True
        G = git_ops.GitOperator(Path("fake_repo"))
        with pytest.raises(git_ops.PKMSyncGitOperatorError) as e:
            G.pull()
        assert e.match("Aborting pull due to finding rebase already in progress")

    @patch("subprocess.run")
    @patch("pkmsync.git_ops.GitOperator.check_for_rebase_in_progress")
    @patch("pkmsync.git_ops.GitOperator.abort_rebase")
    def test_pull_aborts_pull_if_rebase_finds_conflicts(self, mock_abort_rebase, mock_check_for_rebase_in_progress, mock_subprocess_run):
        mock_subprocess_run.return_value.returncode=1
        mock_check_for_rebase_in_progress.side_effect = [False, True]
        G = git_ops.GitOperator(Path("fake_repo"))
        with pytest.raises(git_ops.PKMSyncGitOperatorError) as e:
            G.pull()
        e.match("Encountered error trying to pull and rebase.")
        mock_abort_rebase.assert_called_once()

    @patch("subprocess.run")
    def test_pull_aborts_pull_if_rebase_finds_conflicts_and_raises_if_abort_fails(self, mock_subprocess_run):
            mock_subprocess_run.return_value.returncode= 1
            with patch('pkmsync.git_ops.GitOperator.check_for_rebase_in_progress') as mock_check_for_rebase_in_progress:
                mock_check_for_rebase_in_progress.side_effect = [False,True]
                G = git_ops.GitOperator(Path("fake_repo"))
                with pytest.raises(git_ops.PKMSyncGitOperatorError) as e:
                    G.pull()
                assert e.match("Encountered error trying to abort rebase. Command exited with")

class TestGitOperator_abort():
    @patch("subprocess.run")
    def test_git_abort_rebase_raises_on_error(self, mock):
        mock.return_value.returncode=128
        G = git_ops.GitOperator(Path("fake_repo"))
        with pytest.raises(git_ops.PKMSyncGitOperatorError) as e:
            G.abort_rebase()
        assert e.match("Encountered error trying to abort rebase. Command exited with")

    @patch("subprocess.run")
    def test_git_abort_rebase_calls_rebase_abort(self, mock):
        mock.return_value.returncode=0
        G = git_ops.GitOperator(Path("fake_repo"))
        G.abort_rebase()
        mock.assert_called_once()
        mock.assert_called_with(["git", "-C", Path("fake_repo"), "rebase", "--abort"], capture_output=True, text=True)


class TestGitOperator_commit():
    @patch("subprocess.run")
    def test_commit_raises_on_failure(self, mock):
        mock.return_value.returncode=128
        G = git_ops.GitOperator(Path("fake_repo"))
        with pytest.raises(git_ops.PKMSyncGitOperatorError) as e:
            G.commit("failing to commit")
        assert e.match("Encountered error trying to commit. Command exited with")

    @patch("subprocess.run")
    def test_commit_returns_none_on_success(self, mock):
        mock.return_value.returncode=0
        G = git_ops.GitOperator(Path("fake_repo"))
        assert G.commit("should return None") is None
        mock.assert_called_with(["git", "-C", Path("fake_repo"), "commit", "-m", "should return None"], capture_output=True, text=True)


class TestGitOperator_push():
    @patch("subprocess.run")
    def test_push_raises_on_failure(self, mock):
        mock.return_value.returncode=128
        G = git_ops.GitOperator(Path("fake_repo"))
        with pytest.raises(git_ops.PKMSyncGitOperatorError) as e:
            G.push()
        assert e.match("Encountered error trying to push. Command exited with")

    @patch("subprocess.run")
    def test_push_returns_none_on_success(self, mock):
        mock.return_value.returncode=0
        G = git_ops.GitOperator(Path("fake_repo"))
        assert G.push() is None
        mock.assert_called_once()
        mock.assert_called_with(["git", "-C", Path("fake_repo"), "push", "origin", "main"], capture_output=True, text=True)
