# Publishing notes

For me — feel free to delete before pushing.

## First release

1. **GitHub Desktop** is the easiest path if you're not used to git.
2. Create a new repo, copy these files in, commit, publish.
3. Run `build.bat` to make `dist/Nihongo Dashboard.exe`.
4. Test the exe in a fresh folder (just the exe + dashboard.html).
5. Zip the working folder, attach it to a GitHub release tagged `v1.0`.

## Sharing

Subreddits that fit:
- r/LearnJapanese (read their self-promo rules first)
- r/WaniKani — likely most receptive
- r/japaneselearningtools

Discord communities to consider: Refold, TheMoeWay.

When posting, lead with what's unique — all-in-one, offline-first, the aesthetic. Don't oversell.

## Versioning

Use [semver](https://semver.org/):
- `1.0.1` — bug fix
- `1.1.0` — new feature, no breaking changes
- `2.0.0` — breaking change (config migration etc.)

## Maintenance

- Acknowledge issues within a week even if you can't fix them
- Keep a CHANGELOG.md once you have multiple versions
- You don't have to merge every PR — your project, your call
