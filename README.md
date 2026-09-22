# AltCode Master (ASCII Sheet) ⌨️✨

> An interactive, clean, and minimalistic browser-based ASCII and Alt Code reference sheet covering all numeric codes from **0 to 9999**. Installable as a Progressive Web App (PWA) on any smartphone with complete offline support.

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![PWA Ready](https://img.shields.io/badge/PWA-Ready-success.svg)
![Codes](https://img.shields.io/badge/Codes-0_to_9999-orange.svg)

---

## 🚀 Features

- **Complete 0 to 9999 Coverage**:
  - Standard ASCII (0–127) with control character badges (`NUL`, `ESC`, `CR`, `LF`) and DOS graphic symbols (`☺`, `☻`, `♥`, `☼`).
  - Extended ANSI / Windows-1252 & OEM CP437 (128–255).
  - Greek alphabet (`µ`, `π`, `Ω`, `α`), mathematical operators (`±`, `÷`, `√`, `∞`), currency symbols (`€`, `$`, `£`, `‰`), arrows (`←`, `↑`, `→`, `↓`), shapes, and dingbats up to 9999 (`✏`).
- **Bidirectional Search & Alt Code Converter**:
  - **Enter Digits → See the Sign**: Type `177` or `0177` to see `±`, `0137` to see `‰`, `0181` to see `µ`, `8364` to see `€`, or `3` to see `♥`.
  - **Enter / Paste Sign → Get Numeric Digits**: Paste any symbol (e.g. `±`, `‰`, `µ`) to reveal its Alt shortcut, decimal code, hex (`U+00B1`), and HTML entity (`&plusmn;`).
  - **Search by Name or Alias**: Type `"plus minus"`, `"mu"`, `"permille"`, `"euro"`, `"degree"`, `"heart"`, or `"arrow"` to find exact characters.
- **⭐ Pinned Favorites Bar**:
  - **Long-Press to Pin**: Touch and hold (mobile) or click and hold (desktop) any sign or table row for 450ms. A visual ring fills, haptic vibration triggers, and the symbol is pinned to the top Favorites bar.
  - **Persistent**: Favorites stay saved across sessions in `localStorage`.
- **Smartphone Installable (PWA)**:
  - Add to Home Screen on Android (via direct prompt) or iOS Safari (via Share $\rightarrow$ Add to Home Screen).
  - Offline-ready with built-in service worker (`sw.js`).
- **High Performance 120 FPS Scrolling**:
  - Virtualized chunk rendering for buttery-smooth scrolling through all 10,000 items.
  - Table View and touch-friendly Grid View toggle.
  - Quick range selector (`0-255`, `256-999`, `1000-1999`, etc.) and instant "Jump to Code #" input.

---

## ⌨️ How Alt Codes Work

On Windows:
1. Ensure **Num Lock** is ON on your numeric keypad.
2. Press and **HOLD** the <kbd>Alt</kbd> key.
3. Type the numeric digits on the **numeric keypad**:
   - `Alt + 0177` $\rightarrow$ **`±`** (Plus-Minus)
   - `Alt + 0137` $\rightarrow$ **`‰`** (Per Mille / Permille)
   - `Alt + 0181` $\rightarrow$ **`µ`** (Micro / Mu)
   - `Alt + 0128` $\rightarrow$ **`€`** (Euro)
   - `Alt + 3` $\rightarrow$ **`♥`** (Heart)
   - `Alt + 1` $\rightarrow$ **`☺`** (Smiley)
4. Release the <kbd>Alt</kbd> key $\rightarrow$ the symbol appears!

---

## 🛠️ Project Structure

```text
├── index.html            # Main UI shell with search station, inspector, and table
├── style.css             # Minimalist styling with light/dark themes & mobile responsiveness
├── app.js                # Core controller: search, converter, long-press, PWA
├── ascii_data.js         # Complete dataset with 10,000 records (0 to 9999)
├── generate_dataset.py   # Python generator for dataset and icons
├── manifest.webmanifest  # PWA manifest for smartphone installation
├── sw.js                 # Service worker for offline caching
└── icons/                # High-res PWA icons and SVG assets
```

---

## 🌐 Deploy to GitHub Pages

To make the app accessible from any smartphone:
1. In your GitHub repository, navigate to **Settings** $\rightarrow$ **Pages** (in the left sidebar).
2. Under **Build and deployment** $\rightarrow$ **Branch**, select `main` and root `/(root)`, then click **Save**.
3. Your app will be live at:
   **`https://andregemeinhardt.github.io/ascii_sheet/`**

---

## 📄 License

MIT License. Free to use, modify, and distribute.
