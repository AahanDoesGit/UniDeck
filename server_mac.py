"""
Remote Deck Server - Mac Edition
Run this on your Mac laptop to receive commands from Unihiker.

Usage: python3 server_mac.py
"""

import socket
import subprocess
import threading

# ============================================================================
# CONFIGURATION
# ============================================================================
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 9999       # Must match the port in unihiker_remote_deck.py

# App commands for macOS
APP_COMMANDS = {
    "OPEN_SPOTIFY": "open -a Spotify",
    "OPEN_VSCODE": "open -a 'Visual Studio Code'",
    "OPEN_SAFARI": "open -a Safari",
    "OPEN_TERMINAL": "open -a Terminal",
}

# Media commands using AppleScript (controls Spotify directly)
MEDIA_COMMANDS = {
    "MEDIA_PLAY_PAUSE": """osascript -e 'tell application "Spotify" to playpause'""",
    "MEDIA_NEXT": """osascript -e 'tell application "Spotify" to next track'""",
    "MEDIA_PREV": """osascript -e 'tell application "Spotify" to previous track'""",
    "MEDIA_VOL_UP": """osascript -e 'set volume output volume ((output volume of (get volume settings)) + 10)'""",
    "MEDIA_VOL_DOWN": """osascript -e 'set volume output volume ((output volume of (get volume settings)) - 10)'""",
    "MEDIA_MUTE": """osascript -e 'set volume output muted not (output muted of (get volume settings))'""",
}


def get_spotify_track_info():
    """Get current track info from Spotify using AppleScript."""
    script = '''
    tell application "Spotify"
        if player state is playing or player state is paused then
            set trackName to name of current track
            set artistName to artist of current track
            set albumName to album of current track
            set trackDuration to duration of current track
            set playerPos to player position
            set isPlaying to (player state is playing)
            return trackName & "|" & artistName & "|" & albumName & "|" & trackDuration & "|" & playerPos & "|" & isPlaying
        else
            return "NOT_PLAYING"
        end if
    end tell
    '''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            if output == "NOT_PLAYING":
                return "TRACK:||||||false"
            parts = output.split("|")
            if len(parts) >= 6:
                # Format: TRACK:name|artist|album|duration_ms|position_s|is_playing
                return f"TRACK:{output}"
        return "TRACK:||||||false"
    except Exception as e:
        print(f"[!] AppleScript error: {e}")
        return "TRACK:||||||false"


def handle_client(client_socket, address):
    """Handle incoming client commands."""
    print(f"[+] Connection from {address}")
    
    try:
        while True:
            data = client_socket.recv(1024).decode("utf-8").strip()
            if not data:
                break
            
            print(f"[>] Received: {data}")
            
            # Check if it's a track info request
            if data == "GET_TRACK_INFO":
                response = get_spotify_track_info()
                print(f"[♪] Track info: {response}")
            
            # Check if it's an app command
            elif data in APP_COMMANDS:
                try:
                    subprocess.Popen(
                        APP_COMMANDS[data],
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    response = f"OK: Launched {data}"
                    print(f"[✓] {response}")
                except Exception as e:
                    response = f"ERROR: {e}"
                    print(f"[✗] {response}")
            
            # Check if it's a media command
            elif data in MEDIA_COMMANDS:
                try:
                    subprocess.Popen(
                        MEDIA_COMMANDS[data],
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    response = f"OK: {data}"
                    print(f"[✓] Media: {data}")
                except Exception as e:
                    response = f"ERROR: {e}"
                    print(f"[✗] {response}")
            
            else:
                response = f"UNKNOWN: {data}"
                print(f"[?] Unknown command: {data}")
            
            client_socket.send(response.encode("utf-8"))
    
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        client_socket.close()
        print(f"[-] Connection closed: {address}")


def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "Unable to determine"


def main():
    """Start the server."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
        server.listen(5)
        
        local_ip = get_local_ip()
        
        print("=" * 55)
        print("      REMOTE DECK SERVER - MAC")
        print("=" * 55)
        print(f"   Listening on port: {PORT}")
        print(f"   Your Mac IP: {local_ip}")
        print("")
        print("   Set this IP in unihiker_remote_deck.py:")
        print(f'   HOST_IP = "{local_ip}"')
        print("=" * 55)
        print("")
        print("Supported commands:")
        print("  Apps:  OPEN_SPOTIFY, OPEN_VSCODE, OPEN_SAFARI, OPEN_TERMINAL")
        print("  Media: MEDIA_PLAY_PAUSE, MEDIA_NEXT, MEDIA_PREV")
        print("         MEDIA_VOL_UP, MEDIA_VOL_DOWN, MEDIA_MUTE")
        print("  Info:  GET_TRACK_INFO")
        print("")
        print("Waiting for Unihiker connection...")
        print("")
        
        while True:
            client_socket, address = server.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, address),
                daemon=True
            )
            client_thread.start()
    
    except KeyboardInterrupt:
        print("\n[!] Server shutting down...")
    finally:
        server.close()


if __name__ == "__main__":
    main()
