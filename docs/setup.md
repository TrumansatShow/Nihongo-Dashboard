# Setup

## Windows quick install

1. Download the release zip and extract
2. Set up Anki (below)
3. Double-click `Nihongo Dashboard.exe`

Windows might warn about an unrecognized publisher — click **More info → Run anyway**. This is normal for unsigned indie tools.

## Anki setup

The dashboard uses the AnkiConnect add-on to read your decks.

### Install AnkiConnect
- Tools → Add-ons → Get Add-ons
- Code: `2055492159`
- Restart Anki

### Allow CORS
The dashboard runs on port 8080 and AnkiConnect runs on 8765. They need to talk:

- Tools → Add-ons → AnkiConnect → Config
- Find `"webCorsOriginList": ["http://localhost"]`
- Change to `"webCorsOriginList": ["http://localhost", "http://localhost:8080"]`
- OK, then restart Anki

## WaniKani setup

1. Go to [wanikani.com/settings/personal_access_tokens](https://www.wanikani.com/settings/personal_access_tokens)
2. Generate a new token (default permissions are fine)
3. In the dashboard, click the gear icon → paste the token

## BunPro

Their public API isn't released yet, so stats are entered manually in the Grammar tab. Just type your numbers in — they save automatically.

## Game Sentence Miner

GSM doesn't export CSVs directly, but Anki does. Export your mining deck from Anki:

- File → Export
- Format: Notes in Plain Text (.txt)
- Check "Include tags"
- Rename the file to `.csv` if needed
- Drag it onto the Game Miner tab

## Running from source

```bash
git clone https://github.com/YOUR-USERNAME/nihongo-dashboard
cd nihongo-dashboard
python3 server.py
```

Requires Python 3.9+. Standard library only.

## Troubleshooting

**Port 8080 in use**: the launcher tries to free it automatically. If it can't, edit `server.py` and change `PORT = 8080` to something else, then update AnkiConnect's CORS list to match.

**Anki tab can't connect**: check that Anki is open, AnkiConnect is installed, and CORS is configured for `http://localhost:8080`.

**Kanji popup says "(meaning unavailable)"**: the local server proxies Jisho. Make sure the server is running and you have internet.

**Anything else**: open an issue with the browser console output.
