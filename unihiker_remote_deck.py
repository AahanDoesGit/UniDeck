"""
Unihiker M10 Remote Control Deck
A full-screen touch interface application for controlling a host PC.
Screen Resolution: 240x320 (vertical orientation)

Author: Remote Deck System
"""

import customtkinter as ctk
import threading
import socket
import time
from typing import Callable, Optional
from PIL import Image, ImageTk
import os
import glob


# ============================================================================
# CONFIGURATION
# ============================================================================
class Config:
    """Application configuration constants."""
    
    # Demo mode - set to True to skip connection and go straight to deck
    DEMO_MODE = False
    
    # Screen dimensions (Unihiker M10)
    SCREEN_WIDTH = 240
    SCREEN_HEIGHT = 320
    
    # Network settings
    HOST_IP = "192.168.29.69"
    HOST_PORT = 9999
    PING_TIMEOUT = 2
    
    # Colors (Dark Modern Palette)
    BG_PRIMARY = "#1a1a1a"
    BG_SECONDARY = "#2b2b2b"
    BG_TERTIARY = "#3d3d3d"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a0a0a0"
    TEXT_MUTED = "#666666"
    
    # Accent colors for app buttons
    ACCENT_SPOTIFY = "#1DB954"
    ACCENT_VSCODE = "#007ACC"
    ACCENT_CHROME = "#FFC107"
    ACCENT_TERMINAL = "#6B7280"
    
    # UI Settings
    CORNER_RADIUS = 15
    BUTTON_HEIGHT = 70
    SPLASH_DURATION = 2.0  # seconds
    IDLE_TIMEOUT = 15.0 # seconds before screensaver activates
    
    # Animation Settings (Higher FPS)
    TARGET_FPS = 60
    FRAME_TIME = 1000 // TARGET_FPS  # 16ms for 60 FPS
    IDLE_FPS = 30
    IDLE_FRAME_TIME = 1000 // IDLE_FPS  # 33ms for 30 FPS

    

# ============================================================================
# BASE STATE CLASS
# ============================================================================
class BaseState(ctk.CTkFrame):
    """Base class for all application states."""
    
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color=Config.BG_PRIMARY)
        self.app = app_controller
        self.setup_ui()
    
    def setup_ui(self):
        """Override this method to setup the state's UI."""
        raise NotImplementedError("Subclasses must implement setup_ui()")
    
    def on_enter(self):
        """Called when transitioning INTO this state."""
        pass
    
    def on_exit(self):
        """Called when transitioning OUT OF this state."""
        pass


# ============================================================================
# STATE 1: SPLASH SCREEN (BOOT)
# ============================================================================
class SplashState(BaseState):
    """Boot/Splash screen with logo and progress bar."""
    
    def setup_ui(self):
        # Center container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Logo/Title
        self.logo_label = ctk.CTkLabel(
            self.container,
            text="*",
            font=ctk.CTkFont(size=48),
            text_color=Config.TEXT_PRIMARY
        )
        self.logo_label.pack(pady=(0, 10))
        
        self.title_label = ctk.CTkLabel(
            self.container,
            text="UNIHIKER",
            font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
            text_color=Config.TEXT_PRIMARY
        )
        self.title_label.pack(pady=(0, 5))
        
        self.subtitle_label = ctk.CTkLabel(
            self.container,
            text="Remote Deck",
            font=ctk.CTkFont(family="Arial", size=12),
            text_color=Config.TEXT_SECONDARY
        )
        self.subtitle_label.pack(pady=(0, 30))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.container,
            width=180,
            height=6,
            corner_radius=3,
            fg_color=Config.BG_SECONDARY,
            progress_color=Config.ACCENT_SPOTIFY
        )
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar.set(0)
        
        # Status text
        self.status_label = ctk.CTkLabel(
            self.container,
            text="System Initializing...",
            font=ctk.CTkFont(family="Arial", size=10),
            text_color=Config.TEXT_MUTED
        )
        self.status_label.pack()
        
        # Animation variables
        self.progress_value = 0.0
        self.animation_running = False
    
    def on_enter(self):
        """Start the boot animation."""
        self.progress_value = 0.0
        self.progress_bar.set(0)
        self.animation_running = True
        self._animate_progress()
    
    def on_exit(self):
        """Stop the animation."""
        self.animation_running = False
    
    def _animate_progress(self):
        """Animate the progress bar over SPLASH_DURATION seconds."""
        if not self.animation_running:
            return
        
        # Calculate step for 60 FPS
        step = 1.0 / (Config.SPLASH_DURATION * Config.TARGET_FPS)
        self.progress_value += step
        
        if self.progress_value >= 1.0:
            self.progress_bar.set(1.0)
            self.status_label.configure(text="Ready!")
            # Transition to next state after a brief delay
            self.after(200, lambda: self.app.change_state("handshake"))
        else:
            self.progress_bar.set(self.progress_value)
            # Update status text at milestones
            if self.progress_value > 0.7:
                self.status_label.configure(text="Preparing interface...")
            elif self.progress_value > 0.4:
                self.status_label.configure(text="Loading components...")
            
            self.after(Config.FRAME_TIME, self._animate_progress)  # 60 FPS


# ============================================================================
# STATE 2: HANDSHAKE (CONNECTION PHASE)
# ============================================================================
class HandshakeState(BaseState):
    """Connection screen with host discovery."""
    
    def setup_ui(self):
        # Center container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Connection icon (animated)
        self.icon_label = ctk.CTkLabel(
            self.container,
            text="@",
            font=ctk.CTkFont(size=40),
            text_color=Config.TEXT_PRIMARY
        )
        self.icon_label.pack(pady=(0, 20))
        
        # Status text
        self.status_label = ctk.CTkLabel(
            self.container,
            text="Searching for Host PC",
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
            text_color=Config.TEXT_PRIMARY
        )
        self.status_label.pack(pady=(0, 5))
        
        # Animated dots
        self.dots_label = ctk.CTkLabel(
            self.container,
            text="...",
            font=ctk.CTkFont(family="Arial", size=14),
            text_color=Config.TEXT_SECONDARY
        )
        self.dots_label.pack(pady=(0, 20))
        
        # IP address display
        self.ip_label = ctk.CTkLabel(
            self.container,
            text=f"Target: {Config.HOST_IP}",
            font=ctk.CTkFont(family="Arial", size=10),
            text_color=Config.TEXT_MUTED
        )
        self.ip_label.pack(pady=(0, 30))
        
        # Retry button (hidden by default)
        self.retry_button = ctk.CTkButton(
            self.container,
            text="Retry Connection",
            width=160,
            height=40,
            corner_radius=Config.CORNER_RADIUS,
            fg_color=Config.BG_SECONDARY,
            hover_color=Config.BG_TERTIARY,
            text_color=Config.TEXT_PRIMARY,
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
            command=self._retry_connection
        )
        # Button is packed/unpacked based on connection status
        
        # Skip button (for testing without network)
        self.skip_button = ctk.CTkButton(
            self.container,
            text="Skip (Demo Mode)",
            width=120,
            height=30,
            corner_radius=10,
            fg_color="transparent",
            hover_color=Config.BG_SECONDARY,
            text_color=Config.TEXT_MUTED,
            font=ctk.CTkFont(family="Arial", size=10),
            command=lambda: self.app.change_state("deck")
        )
        self.skip_button.pack(pady=(10, 0))
        
        # Animation state
        self.dot_count = 0
        self.animation_running = False
        self.connection_thread: Optional[threading.Thread] = None
    
    def on_enter(self):
        """Start connection attempt."""
        # Demo mode - skip connection and go straight to deck
        if Config.DEMO_MODE:
            self.after(500, lambda: self.app.change_state("deck"))
            return
        
        self.animation_running = True
        self.retry_button.pack_forget()  # Hide retry button
        self.status_label.configure(text="Searching for Host PC")
        self._animate_dots()
        self._start_connection_check()
    
    def on_exit(self):
        """Stop animations."""
        self.animation_running = False
    
    def _animate_dots(self):
        """Animate the loading dots."""
        if not self.animation_running:
            return
        
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * (self.dot_count + 1)
        self.dots_label.configure(text=dots.ljust(3))
        
        self.after(200, self._animate_dots)  # Faster dot animation
    
    def _start_connection_check(self):
        """Start background thread for connection check."""
        self.connection_thread = threading.Thread(target=self._check_connection, daemon=True)
        self.connection_thread.start()
    
    def _check_connection(self):
        """Check if host PC is reachable (runs in background thread)."""
        try:
            # Try to create a socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(Config.PING_TIMEOUT)
            result = sock.connect_ex((Config.HOST_IP, Config.HOST_PORT))
            sock.close()
            
            if result == 0:
                # Connection successful
                self.after(0, self._on_connection_success)
            else:
                # Connection failed
                self.after(0, self._on_connection_failed)
        except Exception as e:
            print(f"Connection error: {e}")
            self.after(0, self._on_connection_failed)
    
    def _on_connection_success(self):
        """Handle successful connection."""
        if not self.animation_running:
            return
        
        self.animation_running = False
        self.status_label.configure(text="Connected!")
        self.dots_label.configure(text="+")
        self.icon_label.configure(text="[OK]")
        
        # Transition to deck after brief delay
        self.after(800, lambda: self.app.change_state("deck"))
    
    def _on_connection_failed(self):
        """Handle failed connection."""
        if not self.animation_running:
            return
        
        self.animation_running = False
        self.status_label.configure(text="Connection Failed")
        self.dots_label.configure(text="")
        self.icon_label.configure(text="[X]")
        
        # Show retry button
        self.retry_button.pack(pady=(0, 0))
    
    def _retry_connection(self):
        """Retry the connection."""
        self.icon_label.configure(text="@")
        self.retry_button.pack_forget()
        self.on_enter()


# ============================================================================
# STATE 3: DECK (APP DASHBOARD)
# ============================================================================
class DeckState(BaseState):
    """Main dashboard with app launcher buttons."""
    
    def setup_ui(self):
        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.header.pack(fill="x", padx=10, pady=(10, 5))
        self.header.pack_propagate(False)
        
        self.header_label = ctk.CTkLabel(
            self.header,
            text="Remote Deck",
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
            text_color=Config.TEXT_PRIMARY
        )
        self.header_label.pack(side="left", pady=5)
        
        # Status indicator
        self.status_dot = ctk.CTkLabel(
            self.header,
            text="●",
            font=ctk.CTkFont(size=10),
            text_color=Config.ACCENT_SPOTIFY
        )
        self.status_dot.pack(side="right", padx=5)
        
        self.status_text = ctk.CTkLabel(
            self.header,
            text="Online",
            font=ctk.CTkFont(family="Arial", size=10),
            text_color=Config.TEXT_SECONDARY
        )
        self.status_text.pack(side="right")
        
        # Button grid container
        self.grid_container = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Configure grid
        self.grid_container.grid_columnconfigure(0, weight=1)
        self.grid_container.grid_columnconfigure(1, weight=1)
        
        # App buttons data - Spotify now navigates to spotify state
        # Using image filenames for icons
        self.apps = [
            {"name": "Spotify", "image": "spotify.png", "color": Config.ACCENT_SPOTIFY, "command": "GOTO_SPOTIFY"},
            {"name": "VS Code", "image": "vscode.png", "color": Config.ACCENT_VSCODE, "command": "OPEN_VSCODE"},
            {"name": "Safari", "image": "saffari.png", "color": "#0A84FF", "command": "OPEN_SAFARI"},
            {"name": "Terminal", "image": "terminal.png", "color": Config.ACCENT_TERMINAL, "command": "OPEN_TERMINAL"},
        ]
        
        # Create buttons
        self._create_app_buttons()
        
        # Footer with disconnect option
        self.footer = ctk.CTkFrame(self, fg_color="transparent", height=35)
        self.footer.pack(fill="x", padx=10, pady=(5, 10))
        self.footer.pack_propagate(False)
        
        self.disconnect_btn = ctk.CTkButton(
            self.footer,
            text="Disconnect",
            width=80,
            height=25,
            corner_radius=8,
            fg_color="transparent",
            hover_color=Config.BG_SECONDARY,
            text_color=Config.TEXT_MUTED,
            font=ctk.CTkFont(family="Arial", size=10),
            command=self._disconnect
        )
        self.disconnect_btn.pack(side="left")
    
    def _create_app_buttons(self):
        """Create the grid of app launcher buttons."""
        for idx, app in enumerate(self.apps):
            row = idx // 2
            col = idx % 2
            
            # Button frame for styling
            btn_frame = ctk.CTkFrame(
                self.grid_container,
                fg_color=Config.BG_SECONDARY,
                corner_radius=Config.CORNER_RADIUS
            )
            btn_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.grid_container.grid_rowconfigure(row, weight=1)
            
            # Inner content
            inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
            inner.place(relx=0.5, rely=0.5, anchor="center")
            
            # Icon with accent color bar
            accent_bar = ctk.CTkFrame(
                btn_frame,
                width=4,
                height=30,
                corner_radius=2,
                fg_color=app["color"]
            )
            accent_bar.place(x=8, rely=0.5, anchor="w")
            
            # Icon
            try:
                # Get absolute path to image
                script_dir = os.path.dirname(os.path.abspath(__file__))
                img_path = os.path.join(script_dir, app["image"])
                
                # Load and resize image
                pil_image = Image.open(img_path)
                
                # Check for custom size (Spotify has a border so we make it slightly smaller)
                icon_size = (48, 48)
                if app["name"] == "Spotify":
                    icon_size = (42, 42)
                
                ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=icon_size)
                
                icon_label = ctk.CTkLabel(
                    inner,
                    text="",
                    image=ctk_image
                )
            except Exception as e:
                print(f"Failed to load image {app.get('image')}: {e}")
                # Fallback to text/initial
                icon_label = ctk.CTkLabel(
                    inner,
                    text=app["name"][:2],
                    font=ctk.CTkFont(size=28),
                    text_color=Config.TEXT_PRIMARY
                )
            
            icon_label.pack(pady=(5, 0))
            
            # App name
            name_label = ctk.CTkLabel(
                inner,
                text=app["name"],
                font=ctk.CTkFont(family="Arial", size=11, weight="bold"),
                text_color=Config.TEXT_PRIMARY
            )
            name_label.pack(pady=(2, 0))
            
            # Make entire frame clickable
            command = app["command"]
            self._make_clickable(btn_frame, command)
            self._make_clickable(inner, command)
            self._make_clickable(icon_label, command)
            self._make_clickable(name_label, command)
    
    def _make_clickable(self, widget, command: str):
        """Make a widget clickable to send a command."""
        widget.bind("<Button-1>", lambda e: self._send_command(command))
        widget.bind("<Enter>", lambda e: widget.configure(cursor="hand2") if hasattr(widget, 'configure') else None)
    
    def _send_command(self, command: str):
        """Send command to Mac host via network socket."""
        print(f"Sending command: {command}")
        
        # Special command to navigate to Spotify player
        if command == "GOTO_SPOTIFY":
            # Send open spotify command, then navigate to player state
            self._send_network_command("OPEN_SPOTIFY")
            self.app.change_state("spotify")
            return
        
        # Send command to Mac server
        self._send_network_command(command)
    
    def _send_network_command(self, command: str):
        """Send command over network to Mac server."""
        def send_in_thread():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((Config.HOST_IP, Config.HOST_PORT))
                sock.send(command.encode("utf-8"))
                response = sock.recv(1024).decode("utf-8")
                print(f"Response: {response}")
                sock.close()
            except Exception as e:
                print(f"Network error: {e}")
        
        threading.Thread(target=send_in_thread, daemon=True).start()
    
    def _disconnect(self):
        """Return to handshake state."""
        self.app.change_state("handshake")


# ============================================================================
# STATE 4: SPOTIFY PLAYER (MUSIC CONTROL) - MODERN UI
# ============================================================================
class SpotifyState(BaseState):
    """Modern Spotify player with progress bar and real-time track info."""
    
    def setup_ui(self):
        # Track state
        self.is_playing = False
        self.track_duration = 0
        self.track_position = 0
        self.update_running = False
        
        # Header with back button
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=35)
        self.header.pack(fill="x", padx=8, pady=(5, 0))
        self.header.pack_propagate(False)
        
        self.back_btn = ctk.CTkButton(
            self.header,
            text="<",
            width=35,
            height=28,
            corner_radius=14,
            fg_color=Config.BG_TERTIARY,
            hover_color="#4a4a4a",
            text_color=Config.TEXT_PRIMARY,
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
            command=self._go_back
        )
        self.back_btn.pack(side="left")
        
        self.header_label = ctk.CTkLabel(
            self.header,
            text="SPOTIFY",
            font=ctk.CTkFont(family="Arial", size=11, weight="bold"),
            text_color=Config.ACCENT_SPOTIFY
        )
        self.header_label.pack(side="right", padx=8)
        
        # Album art container with glow effect (simulated with border)
        self.art_outer = ctk.CTkFrame(
            self,
            width=115,
            height=115,
            corner_radius=16,
            fg_color=Config.ACCENT_SPOTIFY,  # Glow color
            border_width=0
        )
        self.art_outer.pack(pady=(8, 0))
        self.art_outer.pack_propagate(False)
        
        # Inner album art
        self.art_frame = ctk.CTkFrame(
            self.art_outer,
            width=105,
            height=105,
            corner_radius=12,
            fg_color="#1a1a2e"  # Deep purple-black gradient feel
        )
        self.art_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.art_frame.pack_propagate(False)
        
        self.art_icon = ctk.CTkLabel(
            self.art_frame,
            text="♫",
            font=ctk.CTkFont(size=42, weight="bold"),
            text_color=Config.ACCENT_SPOTIFY
        )
        self.art_icon.place(relx=0.5, rely=0.5, anchor="center")
        
        # Track info with scrolling support for long names
        self.track_label = ctk.CTkLabel(
            self,
            text="Not Playing",
            font=ctk.CTkFont(family="Arial", size=13, weight="bold"),
            text_color=Config.TEXT_PRIMARY,
            wraplength=200
        )
        self.track_label.pack(pady=(8, 0))
        
        self.artist_label = ctk.CTkLabel(
            self,
            text="Open Spotify on Mac",
            font=ctk.CTkFont(family="Arial", size=10),
            text_color=Config.TEXT_SECONDARY
        )
        self.artist_label.pack(pady=(0, 6))
        
        # Progress bar section
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent", height=35)
        self.progress_frame.pack(fill="x", padx=15, pady=(0, 5))
        self.progress_frame.pack_propagate(False)
        
        # Time labels
        self.time_left = ctk.CTkLabel(
            self.progress_frame,
            text="0:00",
            font=ctk.CTkFont(family="Arial", size=9),
            text_color=Config.TEXT_MUTED,
            width=30
        )
        self.time_left.pack(side="left")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=140,
            height=6,
            corner_radius=3,
            fg_color=Config.BG_TERTIARY,
            progress_color=Config.ACCENT_SPOTIFY
        )
        self.progress_bar.pack(side="left", padx=5, pady=12)
        self.progress_bar.set(0)
        
        self.time_right = ctk.CTkLabel(
            self.progress_frame,
            text="0:00",
            font=ctk.CTkFont(family="Arial", size=9),
            text_color=Config.TEXT_MUTED,
            width=30
        )
        self.time_right.pack(side="left")
        
        # Main controls (Prev, Play, Next)
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.pack(pady=3)
        
        # Previous button - 3D style
        self.prev_btn = ctk.CTkButton(
            self.controls_frame,
            text="<<",
            width=48,
            height=48,
            corner_radius=24,
            fg_color="#333333",
            hover_color="#444444",
            text_color=Config.TEXT_PRIMARY,
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
            border_width=1,
            border_color="#444444",
            command=self._prev_track
        )
        self.prev_btn.pack(side="left", padx=6)
        
        # Play/Pause button - Large, prominent
        self.play_btn = ctk.CTkButton(
            self.controls_frame,
            text="▶",
            width=60,
            height=60,
            corner_radius=30,
            fg_color=Config.ACCENT_SPOTIFY,
            hover_color="#1ed760",
            text_color="#000000",
            font=ctk.CTkFont(family="Arial", size=22, weight="bold"),
            border_width=2,
            border_color="#1ed760",
            command=self._play_pause
        )
        self.play_btn.pack(side="left", padx=8)
        
        # Next button - 3D style
        self.next_btn = ctk.CTkButton(
            self.controls_frame,
            text=">>",
            width=48,
            height=48,
            corner_radius=24,
            fg_color="#333333",
            hover_color="#444444",
            text_color=Config.TEXT_PRIMARY,
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
            border_width=1,
            border_color="#444444",
            command=self._next_track
        )
        self.next_btn.pack(side="left", padx=6)
        
        # Volume controls - Compact row
        self.volume_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.volume_frame.pack(pady=(8, 3))
        
        self.vol_down_btn = ctk.CTkButton(
            self.volume_frame,
            text="-",
            width=50,
            height=32,
            corner_radius=8,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            text_color=Config.TEXT_PRIMARY,
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
            command=self._volume_down
        )
        self.vol_down_btn.pack(side="left", padx=3)
        
        self.vol_label = ctk.CTkLabel(
            self.volume_frame,
            text="VOL",
            font=ctk.CTkFont(family="Arial", size=9, weight="bold"),
            text_color=Config.TEXT_MUTED,
            width=35
        )
        self.vol_label.pack(side="left")
        
        self.vol_up_btn = ctk.CTkButton(
            self.volume_frame,
            text="+",
            width=50,
            height=32,
            corner_radius=8,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            text_color=Config.TEXT_PRIMARY,
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
            command=self._volume_up
        )
        self.vol_up_btn.pack(side="left", padx=3)
        
        self.mute_btn = ctk.CTkButton(
            self.volume_frame,
            text="X",
            width=40,
            height=32,
            corner_radius=8,
            fg_color="#3d2a2a",
            hover_color="#4d3a3a",
            text_color="#ff6b6b",
            font=ctk.CTkFont(family="Arial", size=11, weight="bold"),
            command=self._mute
        )
        self.mute_btn.pack(side="left", padx=3)
    
    def on_enter(self):
        """Start track info polling."""
        self.update_running = True
        self._poll_track_info()
    
    def on_exit(self):
        """Stop track info polling."""
        self.update_running = False
    
    def _go_back(self):
        """Return to deck."""
        self.update_running = False
        self.app.change_state("deck")
    
    def _format_time(self, seconds):
        """Format seconds as M:SS."""
        if seconds <= 0:
            return "0:00"
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{mins}:{secs:02d}"
    
    def _poll_track_info(self):
        """Poll server for current track info."""
        if not self.update_running:
            return
        
        def fetch():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((Config.HOST_IP, Config.HOST_PORT))
                sock.send("GET_TRACK_INFO".encode("utf-8"))
                response = sock.recv(1024).decode("utf-8")
                sock.close()
                
                if response.startswith("TRACK:"):
                    data = response[6:].split("|")
                    if len(data) >= 6:
                        name, artist, album, duration_ms, position_s, is_playing = data[:6]
                        self._update_ui(name, artist, duration_ms, position_s, is_playing)
            except Exception as e:
                print(f"Track poll error: {e}")
        
        threading.Thread(target=fetch, daemon=True).start()
        
        # Schedule next poll - faster for smoother progress bar
        if self.update_running:
            self.after(1000, self._poll_track_info)  # Poll every 1 second
    
    def _update_ui(self, name, artist, duration_ms, position_s, is_playing):
        """Update UI with track info (called from main thread)."""
        def update():
            if not self.update_running:
                return
            
            # Update track name (truncate if too long)
            display_name = name[:25] + "..." if len(name) > 28 else name
            self.track_label.configure(text=display_name if name else "Not Playing")
            self.artist_label.configure(text=artist if artist else "Unknown Artist")
            
            # Update progress bar
            try:
                duration_sec = float(duration_ms) / 1000 if duration_ms else 0
                position_sec = float(position_s) if position_s else 0
                
                if duration_sec > 0:
                    progress = position_sec / duration_sec
                    self.progress_bar.set(min(progress, 1.0))
                    self.time_left.configure(text=self._format_time(position_sec))
                    self.time_right.configure(text=self._format_time(duration_sec))
            except:
                pass
            
            # Update play button icon
            playing = is_playing.lower() == "true"
            self.is_playing = playing
            self.play_btn.configure(text="||" if playing else "▶")
            
            # Update glow color based on playing state
            glow_color = Config.ACCENT_SPOTIFY if playing else Config.BG_TERTIARY
            self.art_outer.configure(fg_color=glow_color)
        
        self.after(0, update)
    
    def _send_media_command(self, command: str):
        """Send media command to Mac server via network."""
        def send_in_thread():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((Config.HOST_IP, Config.HOST_PORT))
                sock.send(command.encode("utf-8"))
                response = sock.recv(1024).decode("utf-8")
                print(f"Response: {response}")
                sock.close()
            except Exception as e:
                print(f"Network error: {e}")
        
        threading.Thread(target=send_in_thread, daemon=True).start()
    
    def _play_pause(self):
        """Toggle play/pause."""
        print("Media: Play/Pause")
        self._send_media_command("MEDIA_PLAY_PAUSE")
        # Toggle icon immediately for feedback
        self.is_playing = not self.is_playing
        self.play_btn.configure(text="||" if self.is_playing else "▶")
    
    def _next_track(self):
        """Skip to next track."""
        print("Media: Next Track")
        self._send_media_command("MEDIA_NEXT")
    
    def _prev_track(self):
        """Go to previous track."""
        print("Media: Previous Track")
        self._send_media_command("MEDIA_PREV")
    
    def _volume_up(self):
        """Increase volume."""
        print("Media: Volume Up")
        self._send_media_command("MEDIA_VOL_UP")
    
    def _volume_down(self):
        """Decrease volume."""
        print("Media: Volume Down")
        self._send_media_command("MEDIA_VOL_DOWN")
    
    def _mute(self):
        """Toggle mute."""
        print("Media: Mute")
        self._send_media_command("MEDIA_MUTE")


# ============================================================================
# MAIN APPLICATION CONTROLLER
# ============================================================================
class RemoteDeckApp(ctk.CTk):
    """Main application controller managing states."""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("Unihiker Remote Deck")
        self.geometry(f"{Config.SCREEN_WIDTH}x{Config.SCREEN_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=Config.BG_PRIMARY)
        
        # Idle/Screensaver functionality
        self.last_interaction = time.time()
        self.idle_active = False
        self.idle_frames = []
        self.current_idle_frame = 0
        self.idle_overlay = None
        self.idle_label = None
        
        # Load idle frames
        self._load_idle_frames()
        
        # Bind global interactions to reset idle timer
        self.bind_all("<Button-1>", self._on_interaction)
        self.bind_all("<Key>", self._on_interaction)
        
        # Full screen setup (comment out for testing on desktop)
        # self.attributes('-fullscreen', True)
        # self.overrideredirect(True)  # Remove window decorations
        
        # Bind escape key to exit fullscreen gracefully
        self.bind("<Escape>", self._on_escape)
        self.bind("<Control-q>", self._on_escape)
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Initialize states
        self.states = {}
        self.current_state: Optional[BaseState] = None
        
        self._init_states()
        
        # Start with splash screen
        self.change_state("splash")
        
        # Start idle check loop
        self.after(1000, self._check_idle)

    def _load_idle_frames(self):
        """Load animation frames for idle screen."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            frames_dir = os.path.join(script_dir, "idle_frames")
            
            # Find all png files
            pattern = os.path.join(frames_dir, "*.png")
            files = sorted(glob.glob(pattern))
            
            if not files:
                return

            for f in files:
                img = Image.open(f)
                # Resize to screen
                img = img.resize((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
                self.idle_frames.append(ctk_img)
                
        except Exception as e:
            print(f"Error loading idle frames: {e}")

    def _on_interaction(self, event):
        """Reset idle timer on any user interaction."""
        self.last_interaction = time.time()
        
        if self.idle_active:
            self._stop_idle_mode()

    def _check_idle(self):
        """Check if idle timeout has passed."""
        if not self.idle_active:
            elapsed = time.time() - self.last_interaction
            if elapsed > Config.IDLE_TIMEOUT:
                self._start_idle_mode()
        
        self.after(1000, self._check_idle)

    def _start_idle_mode(self):
        """Activate screensaver overlay."""
        if not self.idle_frames or self.idle_active:
            return
            
        print("Entering idle mode...")
        self.idle_active = True
        
        # Create overlay if it doesn't exist
        if self.idle_overlay is None:
            self.idle_overlay = ctk.CTkFrame(self, fg_color="black", corner_radius=0)
            self.idle_label = ctk.CTkLabel(self.idle_overlay, text="")
            self.idle_label.pack(fill="both", expand=True)
            # Bind click on overlay to wake up
            self.idle_label.bind("<Button-1>", self._on_interaction)
        
        # Show overlay on top of everything
        self.idle_overlay.place(x=0, y=0, relwidth=1, relheight=1)
        self.idle_overlay.lift()
        
        # Start animation
        self.current_idle_frame = 0
        self._animate_idle()

    def _animate_idle(self):
        """Cycle through idle frames."""
        if not self.idle_active:
            return
            
        # Update frame
        frame = self.idle_frames[self.current_idle_frame]
        self.idle_label.configure(image=frame)
        
        self.current_idle_frame = (self.current_idle_frame + 1) % len(self.idle_frames)
        
        # Schedule next frame at 30 FPS for smoother idle animation
        self.after(Config.IDLE_FRAME_TIME, self._animate_idle)

    def _stop_idle_mode(self):
        """Dismiss screensaver."""
        if not self.idle_active:
            return
            
        print("Waking up!")
        self.idle_active = False
        if self.idle_overlay:
            self.idle_overlay.place_forget()
    
    def _init_states(self):
        """Initialize all application states."""
        self.states = {
            "splash": SplashState(self, self),
            "handshake": HandshakeState(self, self),
            "deck": DeckState(self, self),
            "spotify": SpotifyState(self, self),
        }
    
    def change_state(self, state_name: str):
        """Transition to a new state."""
        if state_name not in self.states:
            print(f"Error: Unknown state '{state_name}'")
            return
        
        # Exit current state
        if self.current_state:
            self.current_state.on_exit()
            self.current_state.place_forget()
        
        # Enter new state
        self.current_state = self.states[state_name]
        self.current_state.place(x=0, y=0, relwidth=1, relheight=1)
        self.current_state.on_enter()
        
        print(f"State changed to: {state_name}")
    
    def _on_escape(self, event=None):
        """Handle escape key - exit fullscreen or close app."""
        self._on_close()
    
    def _on_close(self):
        """Graceful shutdown."""
        print("Shutting down Remote Deck...")
        
        # Exit current state
        if self.current_state:
            self.current_state.on_exit()
        
        self.destroy()


# ============================================================================
# ENTRY POINT
# ============================================================================
def main():
    """Application entry point."""
    # CustomTkinter appearance
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    
    # Create and run application
    app = RemoteDeckApp()
    app.mainloop()


if __name__ == "__main__":
    main()
