# TODO

- [ ] **Failure notifications.** A failed or conflicted sync currently only shows up in the log file. Surface it somewhere visible: on macOS a notification from the launchd job (e.g. `osascript -e 'display notification ...'`), with a plan for Linux and Termux later. Conflicts matter most, since they stop syncing until fixed by hand. See "Notifications" under Future features in the README.
- [ ] **Ruff cleanups.** Work through `ruff check` output.
