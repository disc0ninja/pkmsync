import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from pkmsync.config import PKMSyncConfig
from pkmsync.git_ops import GitOperator
from pkmsync.lock import PKMSyncLock, PKMSyncLockError
# sync(config: PKMSyncConfig), builds GitOperator/PKMSyncLock internally
# Lock contention → caught, logged quietly, return (not an error); everything else propagates
# Flow: acquire lock → clean up stale rebase if found (info log) → status() → stage+commit if dirty → pull → push
# Commit message: "PKMSyncCommit: <device> <date time>", device-local time
# status() == 3 at that point should be unreachable — raise loudly if it happens anyway

logger = logging.getLogger(__name__)

class PKMSyncSyncError(Exception):
    pass

def sync(cfg: PKMSyncConfig):
    try:
        with PKMSyncLock(Path(Path(cfg.log_path).parent / "pkmsync.lock")):
            G = GitOperator(Path(cfg.vault_path), cfg.branch)
            if G.check_for_rebase_in_progress():
                logger.warning("Recovered from a stale rebase left by a previous run")
                G.abort_rebase()
            s = G.status()
            if s == 0:
                pass
            elif s in [1, 2]:
                G.stage()
                G.commit(f"PKMSyncCommit: {cfg.device_id} {datetime.now(ZoneInfo(cfg.timezone)).strftime('%Y-%m-%dT%H:%M:%S%z')}")
            else:
                raise PKMSyncSyncError(f"Encountered unexpected status of repo, status {s}. Please recover repo state manually before retrying sync")
            G.pull()
            G.push()
    except PKMSyncLockError:
        logger.info("Lock held by sync already in progress.")
