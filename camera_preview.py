"""
AdaptiBreak Camera Preview Window
Standalone tkinter window showing real-time camera feed with face detection overlay.
Run this alongside the backend for demo purposes.
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
import io
import threading
import time


class CameraPreviewApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AdaptiBreak - Camera Preview")
        self.root.configure(bg='#1a1a2e')
        
        # Window settings
        self.root.geometry("700x580")
        self.root.resizable(True, True)
        
        # API endpoint
        self.api_url = "http://127.0.0.1:8000"
        
        # State
        self.running = True
        self.connected = False
        self.status_data = {}
        
        # Create UI
        self.create_widgets()
        
        # Start update threads
        self.start_updates()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def create_widgets(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_frame = tk.Frame(main_frame, bg='#1a1a2e')
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(
            title_frame, 
            text="AdaptiBreak Camera Preview",
            font=("SF Pro Display", 18, "bold"),
            fg='#ffffff',
            bg='#1a1a2e'
        )
        title_label.pack(side=tk.LEFT)
        
        # Connection status
        self.connection_label = tk.Label(
            title_frame,
            text="● Connecting...",
            font=("SF Pro Display", 11),
            fg='#f59e0b',
            bg='#1a1a2e'
        )
        self.connection_label.pack(side=tk.RIGHT)
        
        # Camera frame container
        camera_container = tk.Frame(main_frame, bg='#0f0f23', relief=tk.FLAT, bd=2)
        camera_container.pack(fill=tk.BOTH, expand=True)
        
        # Camera display label
        self.camera_label = tk.Label(
            camera_container,
            bg='#0f0f23',
            text="Waiting for camera feed...",
            fg='#6b7280',
            font=("SF Pro Display", 14)
        )
        self.camera_label.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Status bar
        status_frame = tk.Frame(main_frame, bg='#16213e', height=80)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        status_frame.pack_propagate(False)
        
        # Status grid
        status_inner = tk.Frame(status_frame, bg='#16213e')
        status_inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Fatigue score
        fatigue_frame = tk.Frame(status_inner, bg='#16213e')
        fatigue_frame.pack(side=tk.LEFT, padx=(0, 30))
        
        tk.Label(
            fatigue_frame,
            text="FATIGUE",
            font=("SF Pro Display", 9),
            fg='#6b7280',
            bg='#16213e'
        ).pack()
        
        self.fatigue_label = tk.Label(
            fatigue_frame,
            text="0.00",
            font=("SF Pro Display", 24, "bold"),
            fg='#10b981',
            bg='#16213e'
        )
        self.fatigue_label.pack()
        
        # Blink rate
        blink_frame = tk.Frame(status_inner, bg='#16213e')
        blink_frame.pack(side=tk.LEFT, padx=30)
        
        tk.Label(
            blink_frame,
            text="BLINK RATE",
            font=("SF Pro Display", 9),
            fg='#6b7280',
            bg='#16213e'
        ).pack()
        
        self.blink_label = tk.Label(
            blink_frame,
            text="0.0/min",
            font=("SF Pro Display", 18, "bold"),
            fg='#8b5cf6',
            bg='#16213e'
        )
        self.blink_label.pack()
        
        # Yawn count
        yawn_frame = tk.Frame(status_inner, bg='#16213e')
        yawn_frame.pack(side=tk.LEFT, padx=30)
        
        tk.Label(
            yawn_frame,
            text="YAWNS",
            font=("SF Pro Display", 9),
            fg='#6b7280',
            bg='#16213e'
        ).pack()
        
        self.yawn_label = tk.Label(
            yawn_frame,
            text="0",
            font=("SF Pro Display", 18, "bold"),
            fg='#f59e0b',
            bg='#16213e'
        )
        self.yawn_label.pack()
        
        # Session duration
        duration_frame = tk.Frame(status_inner, bg='#16213e')
        duration_frame.pack(side=tk.LEFT, padx=30)
        
        tk.Label(
            duration_frame,
            text="DURATION",
            font=("SF Pro Display", 9),
            fg='#6b7280',
            bg='#16213e'
        ).pack()
        
        self.duration_label = tk.Label(
            duration_frame,
            text="00:00",
            font=("SF Pro Display", 18, "bold"),
            fg='#3b82f6',
            bg='#16213e'
        )
        self.duration_label.pack()
        
        # Status message
        status_msg_frame = tk.Frame(status_inner, bg='#16213e')
        status_msg_frame.pack(side=tk.RIGHT)
        
        self.status_message = tk.Label(
            status_msg_frame,
            text="Ready",
            font=("SF Pro Display", 11),
            fg='#6b7280',
            bg='#16213e'
        )
        self.status_message.pack()
        
    def start_updates(self):
        """Start background update threads"""
        # Frame update thread
        self.frame_thread = threading.Thread(target=self.update_frame_loop, daemon=True)
        self.frame_thread.start()
        
        # Status update thread
        self.status_thread = threading.Thread(target=self.update_status_loop, daemon=True)
        self.status_thread.start()
        
    def update_frame_loop(self):
        """Continuously fetch and display frames"""
        while self.running:
            try:
                response = requests.get(
                    f"{self.api_url}/frame",
                    timeout=2
                )
                
                if response.status_code == 200 and response.headers.get('content-type', '').startswith('image'):
                    # Convert to PIL Image
                    image_data = io.BytesIO(response.content)
                    image = Image.open(image_data)
                    
                    # Resize to fit window while maintaining aspect ratio
                    display_width = self.camera_label.winfo_width()
                    display_height = self.camera_label.winfo_height()
                    
                    if display_width > 10 and display_height > 10:
                        # Calculate scaling
                        img_ratio = image.width / image.height
                        display_ratio = display_width / display_height
                        
                        if img_ratio > display_ratio:
                            new_width = display_width
                            new_height = int(display_width / img_ratio)
                        else:
                            new_height = display_height
                            new_width = int(display_height * img_ratio)
                        
                        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Convert to PhotoImage
                    photo = ImageTk.PhotoImage(image)
                    
                    # Update label (thread-safe)
                    self.root.after(0, lambda p=photo: self.update_camera_image(p))
                    
                    if not self.connected:
                        self.connected = True
                        self.root.after(0, self.update_connection_status)
                        
            except requests.exceptions.RequestException:
                if self.connected:
                    self.connected = False
                    self.root.after(0, self.update_connection_status)
                time.sleep(1)
            except Exception as e:
                pass
            
            time.sleep(1/15)  # ~15 FPS
            
    def update_camera_image(self, photo):
        """Update camera image (called from main thread)"""
        self.camera_label.configure(image=photo, text="")
        self.camera_label.image = photo  # Keep reference
        
    def update_status_loop(self):
        """Continuously fetch and display status"""
        while self.running:
            try:
                response = requests.get(
                    f"{self.api_url}/status",
                    timeout=2
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.root.after(0, lambda d=data: self.update_status_display(d))
                    
            except requests.exceptions.RequestException:
                pass
            except Exception as e:
                pass
            
            time.sleep(1)
            
    def update_status_display(self, data):
        """Update status labels (called from main thread)"""
        # Fatigue score
        score = data.get('score', 0.0)
        self.fatigue_label.configure(text=f"{score:.2f}")
        
        # Color based on fatigue level
        if score > 0.6:
            color = '#ef4444'  # Red
        elif score > 0.4:
            color = '#f59e0b'  # Orange
        else:
            color = '#10b981'  # Green
        self.fatigue_label.configure(fg=color)
        
        # Blink rate
        blink_rate = data.get('blink_rate', 0.0)
        self.blink_label.configure(text=f"{blink_rate:.1f}/min")
        
        # Yawn count
        yawn_count = data.get('yawn_count', 0)
        self.yawn_label.configure(text=str(yawn_count))
        
        # Duration
        duration = data.get('session_duration', 0.0)
        mins = int(duration / 60)
        secs = int(duration % 60)
        self.duration_label.configure(text=f"{mins:02d}:{secs:02d}")
        
        # Status message
        is_calibrating = data.get('is_calibrating', False)
        calibration_progress = data.get('calibration_progress', 0.0)
        
        if is_calibrating:
            self.status_message.configure(
                text=f"Calibrating... {int(calibration_progress * 100)}%",
                fg='#f59e0b'
            )
        elif duration > 0:
            self.status_message.configure(
                text="Monitoring Active",
                fg='#10b981'
            )
        else:
            self.status_message.configure(
                text="Session Not Active",
                fg='#6b7280'
            )
            
    def update_connection_status(self):
        """Update connection indicator"""
        if self.connected:
            self.connection_label.configure(
                text="● Connected",
                fg='#10b981'
            )
        else:
            self.connection_label.configure(
                text="● Disconnected",
                fg='#ef4444'
            )
            self.camera_label.configure(
                image='',
                text="Waiting for backend...\n\nMake sure to:\n1. Start the backend (python backend_api.py)\n2. Start a session from the Flutter app"
            )
            
    def on_close(self):
        """Handle window close"""
        self.running = False
        self.root.destroy()
        
    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    print("=" * 50)
    print("🎥 AdaptiBreak Camera Preview")
    print("=" * 50)
    print("This window shows the live camera feed with")
    print("face detection overlay for demo purposes.")
    print("")
    print("Make sure the backend is running first:")
    print("  python backend_api.py")
    print("=" * 50)
    
    app = CameraPreviewApp()
    app.run()


if __name__ == "__main__":
    main()

