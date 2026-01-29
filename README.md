# Unideck - Remote Control Deck

A remote control deck system using Unihiker M10 as a touch interface to control Mac applications and Spotify playback over WiFi.

## 🚀 Features

- **App Launcher**: Open Spotify, VS Code, Chrome, Terminal on your Mac
- **Media Controls**: Play/pause, next/previous track, volume control
- **Touch Interface**: Custom GUI with app icons and media buttons
- **WiFi Communication**: TCP connection between Unihiker and Mac
- **Customizable**: Easy to add more apps and commands

## 📦 Components

| File | Runs On | Purpose |
|------|---------|---------|
| `unihiker_remote_deck.py` | **Unihiker M10** | Touch interface - sends commands |
| `server_mac.py` | **Mac Laptop** | Receives commands, controls apps & Spotify |

## 🛠️ Quick Setup

### 1. Mac Server Setup
```bash
python3 server_mac.py
```
Note the IP address displayed and keep the server running.

### 2. Unihiker Setup
1. Connect Unihiker to same WiFi network
2. Copy `unihiker_remote_deck.py` to Unihiker
3. Update the IP address in the file (line 32)
4. Install dependencies: `pip3 install customtkinter`
5. Run: `python3 unihiker_remote_deck.py`

## 📋 Requirements

### Mac
- Python 3.x
- macOS with AppleScript support

### Unihiker M10
- Python 3.x
- CustomTkinter library
- WiFi connection

## 🎮 Usage

1. Start the Mac server
2. Launch the Unihiker app
3. Tap app icons to open applications on Mac
4. Use media controls for Spotify playback

## 📖 Documentation

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup instructions, troubleshooting, and customization options.

## 🔧 Customization

Add more apps by editing the `APP_COMMANDS` dictionary in `server_mac.py` and adding corresponding buttons in `unihiker_remote_deck.py`.

## 📄 License

MIT License - feel free to modify and distribute.