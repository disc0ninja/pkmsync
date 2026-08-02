# config.py   - loads per-device TOML (vault_path, remote url/branch, device_id, log_path)
import tomllib
import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import available_timezones

class PKMSyncConfigError(Exception):
    pass

@dataclass
class PKMSyncConfig:
    device_id: str
    remote_url: str
    vault_path: Path | str
    branch: str="main"
    log_path: Path | str="$XDG_STATE_HOME/pkmsync/pkmsync.log"
    timezone: str="America/Chicago"

    def __post_init__(self):
        self.log_path = self._expand(self.log_path)
        self.vault_path = self._expand(self.vault_path)
        self.timezone = self._validate_tz(self.timezone)

    @staticmethod
    def _validate_tz(tz: str)  -> str:
        if tz in available_timezones():
            return tz
        else:
            raise PKMSyncConfigError(f"Encountered error validating timezone in config. {tz} was not found in zoneinfo.available_timezones()")

    @staticmethod
    def _expand(raw: Path | str) -> Path:
        if "$XDG_STATE_HOME" in str(raw) and os.getenv("XDG_STATE_HOME") is None:
            raw = str(raw).replace("$XDG_STATE_HOME", "~/.local/state")
        p = Path(os.path.expanduser(os.path.expandvars(raw)))
        if "$" in str(p):
            raise PKMSyncConfigError(f"Expansion left unresolved environment vars in path {p}")
        return p

def load_config(path: str | Path) ->PKMSyncConfig:
    with open(path, "rb") as f:
        data = tomllib.load(f)

    return PKMSyncConfig(
                data['device_id'],
                data['remote_url'],
                data['vault_path'],
                data.get('branch', 'main'),
                data.get('log_path', '$XDG_STATE_HOME/pkmsync/pkmsync.log'),
                data.get('timezone', "America/Chicago")
            )
