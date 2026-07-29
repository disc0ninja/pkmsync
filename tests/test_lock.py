import pytest
from pkmsync import lock

def test_PKMSyncLock_acquires_and_then_releases_lock(tmp_path):
    d = tmp_path / "pkmsynclock"
    d.mkdir()
    p = d / "pkmsync.lock"
    with lock.PKMSyncLock(p):
        pass
    with lock.PKMSyncLock(p):
        pass


def test_PKMSyncLock_raises_PKMSyncLockError_when_lock_held_by_other_process(tmp_path):
    d = tmp_path / "pkmsynclock"
    d.mkdir()
    p = d / "pkmsync.lock"
    with lock.PKMSyncLock(p):
        with pytest.raises(lock.PKMSyncLockError) as e:
            with lock.PKMSyncLock(p):
                pass
        e.match("Encountered BlockingIOError and failed to acquire lock. Original exception:")

