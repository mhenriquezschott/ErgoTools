# Installation guide: screenshot maintenance checklist

Companion to the [ErgoTools Software Installation and GitHub Guide](ergotools_installation_and_github_guide.pdf),
6 November 2026 edition (41 pages). Use this list when replacing images after a UI or operating-system update.

## Capture quality

- Keep original PNGs at native resolution. Annotate or crop a copy.
- Keep the selected file or field visible with its context menu. Check numbered
  highlights against the final crop: borders must enclose the intended control,
  and numbers must not cover labels or entered values.
- Include the window title and enough context to identify the action. For small
  controls, capture both the window and a focused detail.
- Record OS/version, architecture, display resolution/scaling, appearance and the
  code commit. Use GitHub Desktop History → Copy SHA, or `git rev-parse HEAD`.
- Hide passwords, tokens, private email, serial numbers and unrelated notifications.
  Use example project data. Review logs for paths and identifiers before sharing.
- Do not manufacture an update or a bug submission to obtain a picture. If no update
  is available, keep the current Fetch view and explain the Pull action in text.

## Windows

| Guide pages | Capture | Important detail |
| --- | --- | --- |
| 5–6 | Clone URL tab, completed clone | Repository address, actual local path, ErgoTools and main |
| 7–9 | uv/Python/environment/library commands | Full command and successful ending; retain output as text too |
| 10 | Desktop shortcut menus and properties | Show more options, Send to Desktop, target remains in tools |
| 11–12 | Main, PLOT and fresh JROT result | Avatar visible; complete window including bottom controls |
| 25, 28 | Fetch/Pull and History → Copy SHA | Crop around relevant action, not unrelated code differences |
| 34 | Diagnostics settings and Explorer log folder | Open report folder and filenames/date modified |

## macOS

| Guide pages | Capture | Important detail |
| --- | --- | --- |
| 13–14 | First open, clone URL, finished clone | Keep account authorization credentials out of the image |
| 15–17 | Terminal installation and Apple tools prompt | Capture successful command ending and any recovery steps |
| 18 | Make Alias and desktop alias | Show original launcher in tools and the separate alias |
| 19 | Main window and readable detail crops | Replace the current native detail images with a full current window when available |
| 20 | Fresh JROT optimization | Show complete result and Keep optimization result action |
| 26, 28 | Fetch/Pull and Copy SHA | Use actual Mac menus; do not substitute Windows/Linux captures |
| 35 | Finder Go to Folder and log directory | `~/Library/Logs/ErgoTools` and report filenames |

## Shared bug-report illustrations

| Guide pages | Capture | Important detail |
| --- | --- | --- |
| 30 | Desktop Repository → Create Issue on GitHub | Replace official reference images with the ErgoTools checkout when convenient |
| 31 | Browser issue draft | Precise title, steps, expected/actual, attachment area; do not submit an example |
| 33 | Screenshot tools | Save location and selected area/window options |
| 38 | ZIP creation and attachment | Review files first: GitHub uploads attachments before issue submission |

Linux instructions are terminal-focused (pages 21–23 and 27); application images
must be native Linux captures. For any replacement, check the printed page number,
caption, annotation position and surrounding explanation together.
