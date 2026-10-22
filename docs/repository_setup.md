# GitHub repository setup — 2026-10-22

Owner authorizes replacing the contents of `main` in
`git@github.com:mhenriquezschott/ErgoTools.git` with the current workspace, including
source, local assets, tools, tests, native/original fixtures and documentation.
The owner has already downloaded a ZIP backup. Existing other branches/tags are
read-only backups for this work; no force push, mirror push or branch deletion is
needed. The replacement is one normal commit parented by existing main, retaining
Git history while removing obsolete files from the current tree.

SSH authenticates as `mhenriquezschott` using the already available agent. No token,
private key, password or global credential/config change is added to the project.
The separate GitHub connector currently reports another account with read-only access;
Git operations therefore use the verified owner SSH connection. Future environments
need that SSH agent/key available. Repository-local author/email reuse the existing
main identity. The remote's default push refspec is main-to-main only.

The owner authorizes routine status/diff/fetch/add/commit/push operations for requested,
reviewed work on main without asking for each command. This does not authorize new
features, modifying other branches, changing repository security settings or writing
the original application/reference environment. Normal code/test/documentation rules
continue. Protected-branch rejection or changed remote main must be resolved without
silently force pushing or disabling rules.

This managed workspace maps filesystem ownership; use a command-scoped exception:

```bash
git -c safe.directory="$PWD" status
git -c safe.directory="$PWD" push origin main:main
```

No global safe.directory exception is installed. On a normally owned checkout, ordinary
Git commands suffice. GitHub SSH authentication itself already works; no gh CLI is
required. The Git config sets the main upstream and a single main push refspec.

Included: current code/assets/guides, the removable external converter, all maintained
tests and frozen fixture support. Frozen `.bak` files inside originals are existing
conversion evidence, not newly generated project backups. Existing NOTICE/third-party
license texts are carried forward, with the license link adjusted to LICENSE.txt.
Excluded: `.venv`, `.python`, caches, `artifacts`, `dist`, personal credentials and
agent-local directories. No runtime data or source is read from the original checkout.

The pre-upload branch/tag tips are in repository_branch_baseline.json. Local upload
inventory/hash and remote verification reports are in ignored artifacts/repository_setup.
Source functional bytes and approved dependencies are unchanged by this repository
operation. Existing validation is reused; no unrelated code repair or new CI/dependency
is introduced. Source archive/build outputs remain generated, not committed.
