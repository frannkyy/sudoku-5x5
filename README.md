# Sudoku 1-5: 100 Levels

A mobile-friendly 5x5 mini Sudoku / Latin-Sudoku app written in Python with Kivy. It has:

- 5x5 grid only
- numbers 1, 2, 3, 4, and 5 only
- row and column rules: each row and each column must contain 1-5 once
- GIF splash screen inside the Kivy app
- PNG Android presplash fallback for the native Android loading screen
- unique-solution puzzle generation
- 100 levels, getting harder by reducing clues
- automatic level unlock after solving
- hints, mistake tracking, restart, new puzzle, previous/next unlocked level
- save/resume progress

## Why row/column rules only?

Classic Sudoku boxes work cleanly for square sizes like 4x4, 6x6, and 9x9 because they can be divided into equal boxes. A 5x5 grid cannot be divided into equal classic Sudoku boxes, so this app uses the common 5x5 mini rule: each row and each column contains 1 through 5 once.

## Run on desktop

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

On Windows, from the project folder you can also run:

```powershell
python main.py
```

## Important: make sure you are running the new file

The correct `main.py` contains these lines near the top:

```python
SIDE = 5
MAX_LEVEL = 100
```

If your app still shows 9x9 or 4x4, you are running an older copy of `main.py`. Unzip this project into a fresh folder and run this copy.

## GIF splash screen on Android

This project includes:

```text
assets/splash.gif
assets/presplash.png
```

The in-app splash screen uses `assets/splash.gif` and appears as soon as Kivy starts.

Buildozer's native Android presplash should stay PNG/JPG, so `buildozer.spec` uses:

```ini
presplash.filename = assets/presplash.png
```

That means Android shows a static first loading image, then the app shows the GIF splash.

## Build for Android APK

Buildozer is usually run on Linux or WSL. From this project folder:

```bash
pip install buildozer
buildozer android debug
```

The debug APK should be created inside the `bin/` folder.

## Files

- `main.py` - the complete 5x5 app
- `assets/splash.gif` - in-app GIF splash screen
- `assets/presplash.png` - Android native presplash fallback
- `requirements.txt` - desktop Python dependencies
- `buildozer.spec` - Android build configuration
