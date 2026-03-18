# Bitget BTC Ticker

A lightweight, floating desktop widget that displays the real-time Bitcoin (BTC/USDT) spot price directly fetched from the Bitget API (V2).

The widget runs completely in the background without title bars, sits on top of other windows, and provides an unobtrusive experience for monitoring the BTC price.

## Features

- **Live BTC/USDT Price**, updated automatically based on your polling interval.
- **Floating Overlay** widget that always stays on top of other applications.
- **Customizable Appearance** including transparency (opacity) and overlay position settings.
- **Flexible Polling Interval** adjustable from 30 seconds up to 30 minutes.
- **Visual Direction Indicators**: Colors and arrows adjust dynamically (up=green ▲, down=red ▼).
- **Price Alarms**: Set up to 4 target prices. If the spot price surpasses or drops below a target, you'll hear a system beep sound.
- **System Tray Integration**: Easily access settings or exit the app through a discrete tray icon.

## Requirements

- **Python**: 3.10 or higher
- **OS**: Windows (Recommended for optimal overlay/background execution)

## Installation

```bash
git clone git@github.com:bari-psy77/Bitget-BTC-Ticker.git
cd Bitget-BTC-Ticker
pip install -r requirements.txt
```

*(Dependencies include: `pystray`, `Pillow`, `requests`)*

## Running the Application

Double-click `run.bat` on Windows, or use the following command to start it silently:
```bash
pythonw main.py
```

## How to Use

1. **Reposition Widget**: By default, the widget appears near the bottom-right of your screen. Simply click and drag anywhere on the widget to move it around. Dragging also saves the custom position.
2. **Settings Menu**: Right-click the widget itself, or right-click the Bitget orange logo in your System Tray, and click **Settings**.
3. **Configure Settings**:
   - **Alarms Tab**: Input your target price triggers.
   - **Interval Tab**: Adjust how often it pulls the latest price from Bitget between 30 seconds and 30 minutes.
   - **Display Tab**: Choose the overlay position and use the opacity slider to make the ticker semi-transparent so it does not obstruct your workflow.

## Compiled Windows Executable (.exe)

Don't want to install Python?
A GitHub Actions workflow automatically builds a standalone `Bitget-BTC-Ticker.exe` upon new updates. You can download the latest zipped executable by navigating to the **[Actions]** tab of this repository and finding the latest *Bitget-BTC-Ticker-Windows-Exe* artifact.
