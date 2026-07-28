# pkmsync

A small tool to keep a plain-markdown PKM (personal knowledge management) vault in sync across multiple devices — macOS laptops, a Linux desktop, and an Android/Termux phone — using git as the transport, without having to manually `add`/`commit`/`push`/`pull` every time a note changes.

pkmsync is meant to be triggered periodically (cron, `launchd`, a Termux job, or eventually a lightweight daemon) rather than run interactively. Each run checks the vault for local changes, commits anything found, rebases on top of the remote, and pushes — so that after two devices have each run once, they converge on the same state.

## How it works

On each run, pkmsync:
1. Checks whether a rebase from a previous run was left in progress (e.g. the process was killed or the device slept mid-sync) and cleans it up.
2. Checks the working tree for uncommitted changes and commits them if found.
3. Pulls from the remote with `--rebase`.
4. If the rebase hits a conflict, it aborts the rebase and stops loudly rather than attempting to auto-resolve anything — conflicts require manual attention.
5. Pushes.

Rebase (rather than merge) was chosen deliberately: since each run commits and syncs immediately, there's realistically only ever one local commit to replay, which avoids the usual risks of automating rebase, and keeps history linear.

## Requirements

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)
- `git`
- A private git remote (e.g. a GitHub repo) that the vault will sync through
- Each device must already have the vault **cloned by hand** once, with a remote named `origin` pointing at that repo, before pkmsync runs there for the first time (see [Future features](#future-features))

## Configuration

Each device has its own TOML config file describing that device's setup:

```toml
device_id = "laptop1"
remote_url = "git@github.com:youruser/your-vault.git"
vault_path = "$HOME/notes"
branch = "main"                                          # optional, defaults to "main"
log_path = "$XDG_STATE_HOME/pkmsync/pkmsync.log"          # optional, this is the default
```

`vault_path` and `log_path` support `$VAR`-style environment variable references and `~` expansion. `$XDG_STATE_HOME` falls back to `~/.local/state` if unset (useful since cron/Termux job schedulers often run with a minimal environment). If a referenced variable can't be resolved at all, config loading fails loudly rather than silently producing a broken path.

## Development

```sh
uv sync
uv run pytest
```

### Project layout

- `src/pkmsync/config.py` — loads and validates per-device TOML config (`PKMSyncConfig`)
- `src/pkmsync/git_ops.py` — subprocess-based wrapper around the git operations pkmsync needs (`GitOperator`): status, conflict/rebase detection, pull/rebase, stage, commit, push
- `src/pkmsync/lock.py` — *in progress* — prevents overlapping runs if one invocation is still working when the next is triggered
- `sync.py` / a CLI entry point — *not yet started* — will tie config, locking, and git operations together into the actual run-this-on-a-schedule command

## Current status

This project is under active development and not yet usable end-to-end. Config loading and the git operations layer are implemented and tested; the orchestration layer (locking, the actual `sync()` flow, and the CLI entry point) is still being built.

## Future features

Ideas that are intentionally out of scope for the initial version, but planned or under consideration:

- **Daemon mode**: replace the cron/scheduled-job trigger with a long-running process using filesystem watching (desktop) or a sleep loop (Termux), reusing the same sync logic.
- **Automated clone/remote bootstrap**: currently, cloning the vault and configuring the `origin` remote on a new device is a manual, one-time step. Automating that (so pkmsync could set up a brand-new device itself from just a config file) is a planned addition.
- **Encryption at rest**: since the remote is typically a non-self-hosted git host, encrypting vault contents before they leave the device (likely via git's clean/smudge filter mechanism, similar to `git-crypt`) is under consideration.
- **Notifications**: surfacing sync failures and conflicts somewhere more visible than a log file (desktop notifications, a push notification, etc.).
- **Retry/backoff**: smarter handling of transient failures (e.g. no network) instead of just failing until the next scheduled run.

## AI

Development of this project has involved consulting an AI assistant (Claude) for architecture discussion, design trade-offs, targeted hints when debugging, and code review — but **no code in this repository has been written by AI**. All implementation, including the tests, has been written by hand as a deliberate part of using this project to practice and improve Python skills.
