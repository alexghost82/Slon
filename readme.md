# Slon

Slon is a desktop personal AI assistant for Windows, macOS, and Linux. It runs locally on your machine, listens for a wake word, and talks to cloud models you configure yourself—JARVIS-like tone, personal use.

## Quick Start

Use **Python 3.11 or 3.12** (not 3.13+).

```bash
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

Install dependencies for your OS (pick one):

```bash
pip install -r requirements-macos.txt    # macOS
pip install -r requirements-windows.txt  # Windows
pip install -r requirements-linux.txt    # Linux
```

Or let the helper pick the OS file and install Playwright browsers:

```bash
python setup.py
```

If you installed via `pip` only, also run:

```bash
playwright install
```

Start the desktop app:

```bash
python main.py
```

Configure API keys in the UI or via your local config (never commit key files). A Gemini key is required for the default cloud path; OpenRouter is optional.

## Requirements

| Item | Notes |
|---|---|
| OS | Windows, macOS, or Linux |
| Python | 3.11 or 3.12 (`>=3.11,<3.13`) |
| Microphone | Needed for wake-word / voice input |
| Gemini | Primary cloud provider (API key via local config) |
| OpenRouter | Optional alternate / fallback provider |

## Wake word

After launch, say **Slon** (Russian ASR often hears **Слон**) to get the assistant’s attention.

## Language

Slon is Russian-first:

- The desktop UI, the activity log, and the first-run setup overlay are rendered from
  the catalogs in `i18n/`. The active locale comes from `language` in
  `config/settings.json` (`ru` by default, `en` also shipped); an unsupported value
  falls back to Russian.
- The assistant always answers in Russian regardless of the language you speak to it.
  That rule lives in `core/prompt.txt`, so switching `language` to `en` changes the UI
  chrome only, not the replies.
- Speech recognition defaults to Russian (`ru`) and local speech synthesis uses the
  Piper voice `ru_RU-dmitri-medium`.

Tool parameters are still extracted in English (city names, search queries, and so on),
which is required by the tool schemas.

## App icon

`logo.png` in the repository root is the single source of truth.

- Desktop: loaded at startup and set as the Qt window / taskbar icon. On macOS the
  Dock icon still comes from an app bundle, so `python main.py` keeps the
  interpreter icon there.
- iOS (`MarkRemote`): built from the same art into
  `ios/AppProject/Sources/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png`
  (square, opaque — iOS rejects icons with alpha).

After replacing `logo.png`, regenerate the iOS asset:

```bash
python -m tools.make_app_icons
```

## Desktop API (optional)

Loopback-only by default:

```bash
python -m server
```

Binds to `127.0.0.1` unless you explicitly opt into a private LAN address. Do not expose this API to the public internet.

## License

Personal and **non-commercial** use under [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).

This project is **not** commercial-ready and does not grant commercial redistribution rights.

## Attribution

Slon is a personal desktop AI modernization. Third-party package licenses are listed in `THIRD_PARTY_LICENSES.md`. Upstream project names and social handles are intentionally omitted here; keep attribution in that registry and in your own notices if you redistribute under CC BY-NC.
