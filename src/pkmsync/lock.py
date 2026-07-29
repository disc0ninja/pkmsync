import fcntl
from pathlib import Path

class PKMSyncLockError(Exception):
    pass

class PKMSyncLock():
    def __init__(self, path: Path):
        self.path = path
        self._fd = None

    def __enter__(self):
        """
        ensure self.path.parent exists
        open self.path, attempt fcntl.flock(..., LOCK_EX | LOCK_NB)
        on BlockingIOError: close whatever you opened, raise PKMSyncLockError
        on success: stash the open file on self, return self
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        f = open(self.path, "w")
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._fd = f
            return self
        except BlockingIOError as e:
            f.close()
            raise PKMSyncLockError(f"Encountered BlockingIOError and failed to acquire lock. Original exception: {e}")

    def __exit__(self, exc_type, exc_value, exc_tb):
        """
        unlock/close
        return None (or False) — do NOT return True here
        """
        if self._fd is not None:
            self._fd.close()
