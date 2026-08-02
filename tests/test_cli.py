import argparse
import logging
import sys
from pathlib import Path
from pkmsync.config import PKMSyncConfigError, load_config
from pkmsync.sync import sync

def main() -> int:
    parser = argparse.ArgumentParser("pkmsync")
    parser.add_argument("--config", "-c", help="path to toml config that will be used")
    args = parser.parse_args()
    cfg=None
    if args.config is not None:
        cfg=args.config
    else:
        default_config_paths = [
                    Path(os.path.expandvars("$XDG_CONFIG/pkmsync/config.toml")),
                    Path(".config/pkmsync/config.toml"),
                    Path(".config/pkmsync.toml"),
                    Path(os.path.expanduser("~/.pkmsync.toml"))
                ]
        for p in default_config_paths:
            if p.exists():
                cfg=p
                break
    if cfg is None:
        return 1
    c = load_config(cfg)
    sync(c)
    return 0

if __name__ == "__main__":
    sys.exit(main())
