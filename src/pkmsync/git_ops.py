import subprocess
from dataclasses import dataclass
from pathlib import Path
import re


class PKMSyncGitOperatorError(Exception):
    pass


@dataclass
class GitOperator():
    vault_path: Path
    branch: str="main"

    def status(self) -> int:
        """
        Gets the git repo status and returns an integer corresponding to the status.
        0: clean
        1: unstaged changes
        2: uncommitted changes
        3: rebase in progress
        """
        s = subprocess.run(["git", "-C", self.vault_path, "status", "--porcelain"], capture_output=True, text=True)
        if int(s.returncode) != 0:
            raise PKMSyncGitOperatorError(f"Encountered error running git status. Command exited with {s.returncode}\n{s.stderr}")
        lines = s.stdout.split("\n")
        if len(lines) == 1 and lines[0] == '':
            return 0
        if any(re.match(r"(U[ADU]|[AD]U|AA|DD)", line) for line in lines):
            return 3
        if any(re.match(r"[ACDMR]", line) for line in lines):
            return 2
        if any(re.match(r"(\?\?| [ACDMRU])", line) for line in lines):
            return 1
        raise PKMSyncGitOperatorError(f"Unable to determine git status. Command exited with {s.returncode}\n{s.stderr}")

    def check_for_rebase_in_progress(self) -> bool:
        """
        Checks if rebase-merge or rebase-apply directories exist in the git directory.
        """
        s = subprocess.run(["git", "-C", self.vault_path, "rev-parse", "--git-dir"], capture_output=True, text=True)
        g = s.stdout.strip('\n')
        if s.returncode != 0 or g == '':
            raise PKMSyncGitOperatorError(f"Failed to check if rebase is in-progress. Command to get .git direcotory didn't exit cleanly. Command exited with {s.returncode}\n{s.stderr}")
        g_rebase_paths = [Path(f"{g}/rebase-merge"), Path(f"{g}/rebase-apply")]
        if any(p.exists() for p in g_rebase_paths):
            return True
        return False

    def pull(self):
        """
        Attempts to pull and rebase from the remote
        """
        # TODO: Get this setup to back-off retry eventually
        if self.check_for_rebase_in_progress():
            raise PKMSyncGitOperatorError(f"Aborting pull due to finding rebase already in progress")

        s = subprocess.run(["git", "-C", self.vault_path, "pull", "--rebase", "origin", self.branch], capture_output=True, text=True)
        if int(s.returncode) != 0:
            if self.check_for_rebase_in_progress():
                abort = subprocess.run(["git", "-C", self.vault_path, "rebase", "--abort"], capture_output=True, text=True)
                if abort.returncode != 0:
                    raise PKMSyncGitOperatorError(f"Encountered error trying to abort pull and rebase. Command exited with {abort.returncode}\n{abort.stderr}")
            raise PKMSyncGitOperatorError(f"Encountered error trying to pull and rebase. Command exited with {s.returncode}\n{s.stderr}")

    def stage(self):
        """
        Stage uncommitted changes and prepare to make a new commit"
        """
        s = subprocess.run(["git", "-C", self.vault_path, "add", "-A"], capture_output=True, text=True)
        if int(s.returncode) !=0:
            raise PKMSyncGitOperatorError(f"Encountered error trying to stage changes. Command exited with {s.returncode}\n{s.stderr}")

    def commit(self, message: str):
        """
        commit staged changes
        """
        s = subprocess.run(["git", "-C", self.vault_path, "commit", "-m", message], capture_output=True, text=True)
        if int(s.returncode) !=0:
            raise PKMSyncGitOperatorError(f"Encountered error trying to commit. Command exited with {s.returncode}\n{s.stderr}")

    def push(self):
        """
        push update to remote
        """
        s = subprocess.run(["git", "-C", self.vault_path, "push", "origin", self.branch], capture_output=True, text=True)
        if int(s.returncode) !=0:
            raise PKMSyncGitOperatorError(f"Encountered error trying to push. Command exited with {s.returncode}\n{s.stderr}")
