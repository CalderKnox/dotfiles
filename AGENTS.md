# Repository Guidelines

## Project Structure & Organization

This repository is a chezmoi source directory for a macOS development environment. `dot_config/` contains Fish, Zsh, Neovim, terminal, and mise configuration; `dot_pi/` holds selected agent settings. Root `dot_*` files configure Git and tmux, and `private_dot_ssh/` manages SSH configuration. Documentation is in `docs/`; offline validation scripts are in `docs/validation/`. See `docs/layout.md` for source-to-target mappings.

## Development & Validation Commands

- `chezmoi diff` previews changes to the target home directory; review it before `chezmoi apply`.
- `chezmoi managed` and `chezmoi ignored` inspect deployment and exclusion boundaries.
- `python3 docs/validation/check.py --strict` runs the main syntax, configuration, behavior, and deployment-boundary checks; missing dependencies and skips fail strict validation.
- `python3 docs/validation/fzf_runtime.py` checks real fzf behavior using a temporary terminal.
- `actionlint` checks GitHub Actions workflows, as in CI.

See `docs/validation/README.md` for dependencies and optional terminal, tmux, and regression checks. Validation uses temporary isolated environments; it does not apply the configuration to your home directory.

## Style & Naming

Follow the surrounding file's style. Neovim Lua uses two spaces and a 120-column limit, configured in `dot_config/nvim/stylua.toml`. Fish autoload files must define a function matching their filename, and completion files must target the corresponding command. Keep numbered Fish `conf.d/` files ordered by initialization phase.

Respect chezmoi naming: `dot_` represents a leading dot, `private_` restricts permissions on that item, and `symlink_` declares a link. Templates use `.tmpl`. Update `docs/layout.md` when adding managed configuration and the README index when adding documentation.

## Testing & Contributions

Add or extend focused checks in `docs/validation/` when changing behavior or deployment boundaries. Run the strict suite and relevant specialized checks; report unavailable dependencies or skips in the pull request. CI runs the strict suite, fzf checks, and actionlint on macOS. No coverage percentage is specified.

Recent commits use Conventional Commit subjects, often with a scope, such as `feat(shell): add directory creation shortcuts`. Keep pull requests focused and describe the change, validation performed, and any relevant issue or visual evidence.

## Security & Configuration

Do not commit credentials, SSH keys, or machine-generated authentication files. Review both `.gitignore` and `.chezmoiignore`: Git exclusion and deployment exclusion are separate. Check `git diff` for personal paths and identity details before sharing changes.
