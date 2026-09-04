# Bad Apple Stock Chart

An HTS-style terminal visualizer that renders **Bad Apple!!** as candlesticks. Asset prices fluctuate dynamically based on the ratio of green (bull) to red (bear) pixels per frame.

## 🍎 Features

- **Pixel Sentiment Engine**: Converts frames into ANSI stock candles (`█`, `│`). The net balance between green and red pixels directly drives price momentum ($\Delta P$).
- **HTS-Style Terminal UI**: Full-screen blessed UI featuring real-time price quotes, percentage change, frame counters, dynamic Y-axis price ladders, and trade tick feeds.
- **Whale Trade Alerts**: Emphasizes institutional-sized simulated trades (`★` for high turnover, `⚡` for volume spikes).
- **A/V Sync**: Synchronized playback via frame-skipping and optional macOS native audio (`afplay`).

---

## 🛠 Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (Fast Python package installer and resolver)
- macOS (recommended for native `afplay` audio sync) or Linux/Windows

---

## 🚀 Quick Start

1. **Clone & Install Dependencies**
```bash
git clone https://github.com/hyotaime/bad-apple-stock-chart.git
cd bad-apple-stock-chart
uv sync
```

2. **Run**
```bash
# Place your video file (bad_apple.mp4) in the root directory
uv run python main.py -f bad_apple.mp4
```

> **Controls**: Press Ctrl+C to quit. Terminal automatically adapts to window resize.

---

## ⚙️ How It Works

Each frame is converted to grayscale, downsampled, and evaluated across brightness thresholds:

$$\text{Net Sentiment} = \frac{\text{Green Px} - \text{Red Px}}{\text{Total Px}}$$


* Green ($> 140$): Bullish pressure; pushes current price upward (capped at $\pm 0.3$ per tick).
* Red ($< 90$): Bearish pressure; drives prices down.
* Mid-tones ($90 \sim 140$): Neutral order-book spread.

---

## 📜 License
MIT License. Bad Apple!! originates from Touhou Project by Team Shanghai Alice.

