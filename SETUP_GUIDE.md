# Unihiker Remote Deck - Setup Guide

## 📦 Files Overview

| File | Runs On | Purpose |
|------|---------|---------|
| `unihiker_remote_deck.py` | **Unihiker M10** | Touch interface - sends commands |
| `server_mac.py` | **Mac Laptop** | Receives commands, controls apps & Spotify |

---

## 🖥️ Step 1: Setup Mac Server

### 1.1 Copy server to Mac
Transfer `server_mac.py` to your Mac (via AirDrop, USB, email, etc.)

### 1.2 Run the server
Open Terminal on your Mac and run:
```bash
cd /path/to/folder
python3 server_mac.py
```

You'll see:
```
=======================================================
      REMOTE DECK SERVER - MAC
=======================================================
   Listening on port: 9999
   Your Mac IP: 192.168.1.XXX

   Set this IP in unihiker_remote_deck.py:
   HOST_IP = "192.168.1.XXX"
=======================================================

Supported commands:
  Apps:  OPEN_SPOTIFY, OPEN_VSCODE, OPEN_CHROME, OPEN_TERMINAL
  Media: MEDIA_PLAY_PAUSE, MEDIA_NEXT, MEDIA_PREV
         MEDIA_VOL_UP, MEDIA_VOL_DOWN, MEDIA_MUTE

Waiting for Unihiker connection...
```

**⚠️ Copy your Mac's IP address!**

### 1.3 Allow firewall (if prompted)
If macOS asks to allow incoming connections, click **"Allow"**.

---

## 📱 Step 2: Setup Unihiker M10

### 2.1 Connect Unihiker to same WiFi
Make sure your Unihiker M10 is connected to the **same WiFi network** as your Mac.

### 2.2 Transfer the Python file
Connect Unihiker to your PC via USB and copy `unihiker_remote_deck.py` to the Unihiker.

**Option A - USB File Copy:**
1. Connect Unihiker via USB
2. It appears as a USB drive
3. Copy `unihiker_remote_deck.py` to `/root/`

**Option B - SCP (Terminal):**
```bash
scp unihiker_remote_deck.py root@10.1.2.3:/root/
```
- USB IP: `10.1.2.3`
- Password: `dfrobot`

### 2.3 Update the IP address
Edit `unihiker_remote_deck.py` on the Unihiker and change line 32:
```python
HOST_IP = "192.168.1.XXX"  # Your Mac's IP from Step 1.2
```

### 2.4 Install CustomTkinter on Unihiker
SSH into Unihiker:
```bash
ssh root@10.1.2.3
# Password: dfrobot
```

Install the required library:
```bash
pip3 install customtkinter
```

### 2.5 Run the app
```bash
python3 /root/unihiker_remote_deck.py
```

---

## 🖼️ Enable Fullscreen Mode (Optional)

Edit `unihiker_remote_deck.py` and uncomment these lines (around line 740):
```python
self.attributes('-fullscreen', True)
self.overrideredirect(True)
```

---

## 🔄 Auto-Start on Unihiker Boot (Optional)

Create a startup script:
```bash
nano /root/start_deck.sh
```

Contents:
```bash
#!/bin/bash
sleep 5  # Wait for WiFi
cd /root
python3 unihiker_remote_deck.py
```

Make executable:
```bash
chmod +x /root/start_deck.sh
```

Add to crontab:
```bash
crontab -e
# Add this line:
@reboot /root/start_deck.sh
```

---

## 🧪 Testing

1. **Mac**: Run `python3 server_mac.py` (keep running)
2. **Unihiker**: Run the app, wait for splash screen → connects to Mac
3. **Test apps**: Tap VS Code, Chrome, Terminal - they should open on Mac
4. **Test Spotify**: Tap Spotify → use Play/Pause, Next, Prev buttons

---

## 📐 Network Diagram

```
┌─────────────────┐         WiFi          ┌─────────────────┐
│   UNIHIKER M10  │ ─────────────────────▶│   MAC LAPTOP    │
│   (Linux ARM)   │     TCP Port 9999     │                 │
├─────────────────┤                       ├─────────────────┤
│  Touch Buttons  │     "OPEN_VSCODE"     │  server_mac.py  │
│  - Spotify      │  ──────────────────▶  │                 │
│  - VS Code      │                       │  Opens apps via │
│  - Chrome       │     "MEDIA_NEXT"      │  - open -a      │
│  - Terminal     │  ──────────────────▶  │  - osascript    │
│                 │                       │                 │
│  Media Controls │       "OK"            │  Controls       │
│  - Play/Pause   │  ◀──────────────────  │  Spotify via    │
│  - Next/Prev    │                       │  AppleScript    │
│  - Volume       │                       │                 │
└─────────────────┘                       └─────────────────┘
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection fails | Check IP address in config, ensure Mac server is running |
| Server won't start | Port 9999 in use? Run `lsof -i :9999` and kill the process |
| Apps don't open | Verify app names in server_mac.py match your installed apps |
| Spotify controls don't work | Open Spotify first, then try controls |
| Firewall blocking | System Preferences → Security → Firewall → Allow Python |
| Unihiker display issues | Try running without fullscreen first |

---

## ➕ Adding More Apps

### On Mac (server_mac.py):
```python
APP_COMMANDS = {
    "OPEN_SPOTIFY": "open -a Spotify",
    "OPEN_VSCODE": "open -a 'Visual Studio Code'",
    "OPEN_CHROME": "open -a 'Google Chrome'",
    "OPEN_TERMINAL": "open -a Terminal",
    # Add more:
    "OPEN_SLACK": "open -a Slack",
    "OPEN_DISCORD": "open -a Discord",
    "OPEN_SAFARI": "open -a Safari",
}
```

### On Unihiker (unihiker_remote_deck.py):
In `DeckState.setup_ui()`, add to `self.apps` list:
```python
{"name": "Slack", "icon": "💬", "color": "#4A154B", "command": "OPEN_SLACK"},
```

---

## 🎵 Spotify Commands Reference

| Command | Description |
|---------|-------------|
| `MEDIA_PLAY_PAUSE` | Toggle play/pause |
| `MEDIA_NEXT` | Skip to next track |
| `MEDIA_PREV` | Go to previous track |
| `MEDIA_VOL_UP` | Increase system volume |
| `MEDIA_VOL_DOWN` | Decrease system volume |
| `MEDIA_MUTE` | Toggle mute |
