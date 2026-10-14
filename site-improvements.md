# Luck Ledger site improvements

| Date (Stockholm) | Change | Screenshots |
|---|---|---|
| 2026-10-13 | Merged homepage-v2 to main: skip link, clearer Sunday signup copy, scroll-reveal motion (respects reduced motion), CTA pulse, data-driven issues via `tools/build.py` + `data/issues.json`, 33-moves strip, pack footer link. Issue #1 stays a "First issue · Sunday 18 Oct" teaser until Kit broadcast (`public: false`); Sunday site update flips it live. | `screenshots/2026-10-13-desktop.png`, `screenshots/2026-10-13-mobile.png` (also `-bottom` for below-fold) |
| 2026-10-13 | The Ledger v1: 33 move pages (moves/N.html) built from data/stories.json (New stories from Notion story bank only; unreleased issue stories held back). Tiles link to them. | - |
| 2026-10-14 | Moves strip now shows which moves already have a true story in the Ledger: those tiles get a green border and dark number, and the note reads "4 of 33 moves already have a true, sourced story" instead of "0 of 33 covered in issues so far". Once issues go out, issue-covered moves stay solid green and the note adds a count. Change in `tools/build.py` + one CSS rule; move pages unchanged. | `screenshots/2026-10-14-desktop.png`, `screenshots/2026-10-14-mobile.png`, `screenshots/2026-10-14-moves-crop.png` |
