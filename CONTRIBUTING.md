# Contributing

Issues, bug reports, and PRs are welcome.

## Reporting a bug

Open an issue with:
- What you expected
- What happened instead
- Browser and OS
- Console output if there's an error (F12 → Console)

## Code style

The dashboard is one HTML file with vanilla JS. No build step, no framework. Open `dashboard.html`, edit, refresh. The Python server uses only the standard library.

A few things to keep in mind:
- Vanilla JS only — no frameworks, no bundlers
- Python: stdlib only, no external dependencies
- Match the existing CSS variable system if you add styles (themes need to keep working)
- Test against both themes
- Don't break offline functionality — only Jisho lookups need internet

## Areas that could use help

- Mac/Linux launch scripts
- More entries in the curated kanji database (currently ~120, fallback uses Jisho)
- Mobile/responsive tweaks
- BunPro API support if/when they release one
- Direct GSM SQLite database integration

## License

By contributing you agree your work is licensed under GPL-3.0, same as the project.
