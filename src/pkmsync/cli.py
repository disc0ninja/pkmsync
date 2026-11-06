import argparse
import logging
import os
import sys
from pathlib import Path
from pkmsync.config import load_config
from pkmsync.sync import sync

FORMAT =  "%(asctime)s %(levelname)s %(name)s: %(message)s"
logger = logging.getLogger(__name__)

def get_config_path(cfg: str|Path|None) -> str|Path|None:
        default_config_paths = [
                    Path(os.path.expandvars("$XDG_CONFIG_HOME/pkmsync/config.toml")),
                    Path(os.path.expanduser("~/.config/pkmsync/config.toml")),
                    Path(os.path.expanduser("~/.config/pkmsync.toml")),
                    Path(os.path.expanduser("~/.pkmsync.toml"))
                ]
        if cfg is None:
            for p in default_config_paths:
                if p.exists():
                    return p
        return cfg

def main() -> int:
    logging.basicConfig(format=FORMAT, stream=sys.stderr, level=logging.INFO)
    parser = argparse.ArgumentParser("pkmsync")
    parser.add_argument("--config", "-c", help="path to toml config that will be used")
    args = parser.parse_args()
    cfg = get_config_path(args.config)
    if cfg is None:
        logger.error(f"Unable to load config from {args.config} or default_config_paths.")
        return 1
    c = load_config(cfg)
    log_path = c.log_path
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_path)
    fh.setFormatter(logging.Formatter(FORMAT))
    logging.getLogger("pkmsync").addHandler(fh)

    logger.info(f"Successfully loaded config from {cfg}.")
    logger.info("Starting sync")
    try:
        sync(c)
        logger.info("Finished sync")
        return 0
    except Exception as e:
        logger.exception(f"Encountered an unexpected exception running sync {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
