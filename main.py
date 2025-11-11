"""
AdaptiBreak: Biometric Feedback for Personalized Study Break Timing
Main application with GUI, study interface, and webcam fatigue detection.

CS 449/549 - Human-Computer Interaction
Sabancı University - Fall 2025
"""

import os
# Suppress macOS Tk deprecation warning
os.environ['TK_SILENCE_DEPRECATION'] = '1'

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import cv2
from PIL import Image, ImageTk
import threading
import time
import json
import random
import os

import config
from fatigue_detector import FatigueDetector
from data_logger import DataLogger
from evaluation import EvaluationSuite, RecallTest


class AdaptiBreakApp:
    """
    Main application for AdaptiBreak study system.
    Manages study sessions, webcam monitoring, and break suggestions.
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(config.WINDOW_TITLE)
        self.root.geometry(f"{config.MAIN_WINDOW_WIDTH}x{config.MAIN_WINDOW_HEIGHT}")
        self.root.configure(bg='#f5f5f5')
        
        # macOS fixes
        self.root.lift()  # Bring window to front
        self.root.attributes('-topmost', True)  # Force to front
        self.root.after(100, lambda: self.root.attributes('-topmost', False))  # Remove topmost after 100ms
        
        # Configure styles
        self.setup_styles()
        
        # Application state
        self.participant_id = None
        self.session_mode = None
        self.fatigue_detector = None
        self.data_logger = None
        self.webcam = None
        self.webcam_thread = None
        self.running = False
        
        # Study state
        self.flashcards = []
        self.current_flashcard_index = 0
        self.session_start_time = None
        self.on_break = False
        self.break_start_time = None
        self.last_biometric_log = 0
        
        # Test results
        self.test_results = None
        self.evaluation_results = None
        
        # Show welcome screen
        self.show_welcome_screen()
        
        # Force initial render (compatible with Tk 8.5)
        try:
            self.root.update_idletasks()
        except:
            pass  # Tk 8.5 may not handle this well
        
    def setup_styles(self):
        """Configure ttk styles for better UI."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Button styles
        style.configure('Accent.TButton', 
                       background='#4287f5',
                       foreground='white',
                       font=('Helvetica', 12, 'bold'),
                       padding=10)
        
        style.configure('TButton',
                       font=('Helvetica', 11),
                       padding=8)
        
        # Label styles
        style.configure('Title.TLabel',
                       font=('Helvetica', 24, 'bold'),
                       background='#f5f5f5')
        
        style.configure('Subtitle.TLabel',
                       font=('Helvetica', 14),
                       background='#f5f5f5')
        
        style.configure('Large.TRadiobutton',
                       font=('Helvetica', 11),
                       background='#f5f5f5')
    
    def clear_window(self):
        """Clear all widgets from the main window."""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    # ==================== WELCOME & CONSENT ====================
    
    def show_welcome_screen(self):
        """Display welcome screen."""
        self.clear_window()
        
        frame = ttk.Frame(self.root, padding=40)
        frame.pack(expand=True, fill='both')
        
        # Title
        title = ttk.Label(frame, text="Welcome to AdaptiBreak", style='Title.TLabel')
        title.pack(pady=20)
        
        # Debug print to confirm this is being called
        print("✓ Welcome screen loaded")
        
        # Description
        desc = ttk.Label(
            frame,
            text=(
                "A research study on personalized study break timing\n"
                "using biometric feedback from webcam monitoring.\n\n"
                "This study is part of CS 449/549 Human-Computer Interaction\n"
                "at Sabancı University, Fall 2025."
            ),
            style='Subtitle.TLabel',
            justify='center'
        )
        desc.pack(pady=20)
        
        # Info box
        info_frame = ttk.LabelFrame(frame, text="Study Information", padding=20)
        info_frame.pack(pady=20, padx=40, fill='x')
        
        info_text = (
            "• Duration: ~60-70 minutes\n"
            "• Activities: Study flashcards, take recall test, complete survey\n"
            "• Webcam: Used for fatigue detection (all processing is local)\n"
            "• Privacy: No images stored, data is anonymous\n"
            "• Voluntary: You can stop at any time"
        )
        
        ttk.Label(info_frame, text=info_text, font=('Helvetica', 11), justify='left').pack()
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Continue to Consent Form", 
                  command=self.show_consent_form,
                  style='Accent.TButton').pack(side='left', padx=10)
        
        ttk.Button(btn_frame, text="Exit",
                  command=self.root.quit).pack(side='left', padx=10)
    
    def show_consent_form(self):
        """Display informed consent form."""
        self.clear_window()
        
        frame = ttk.Frame(self.root, padding=40)
        frame.pack(expand=True, fill='both')
        
        title = ttk.Label(frame, text="Informed Consent", style='Title.TLabel')
        title.pack(pady=10)
        
        # Consent text
        consent_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=20, width=80)
        consent_text.pack(pady=20, fill='both', expand=True)
        
        consent_content = """
INFORMED CONSENT FOR RESEARCH PARTICIPATION

Study Title: AdaptiBreak - Biometric Feedback for Personalized Study Break Timing
Investigators: Bilgekağan Durmaz, Cihat Bera Şimşek, Aynur Aybüke Memiş, 
               Mustafa Mert Yıldızbaş, Bora Urasoğlu
Institution: Sabancı University, CS 449/549 Human-Computer Interaction

PURPOSE:
You are invited to participate in a research study examining adaptive break timing during study sessions using webcam-based fatigue detection. This study compares personalized break suggestions with traditional fixed-timer methods (Pomodoro Technique).

PROCEDURES:
If you agree to participate, you will:
1. Complete a brief demographic questionnaire (5 min)
2. Study vocabulary flashcards while the system monitors fatigue indicators (45 min)
3. Complete a vocabulary recall test (10 min)
4. Fill out usability surveys and provide feedback (10 min)

You will complete this process in two sessions (different days), experiencing both fixed-timer and adaptive break modes. Session order will be randomized.

WEBCAM MONITORING:
• Your laptop's webcam will detect facial landmarks to estimate fatigue
• Monitored indicators: blink frequency, yawning, head posture
• All processing happens locally on your device
• NO images or video are recorded or stored
• NO facial data leaves your computer
• Only aggregated fatigue scores are logged (no identifying features)

RISKS AND BENEFITS:
Risks are minimal. Some participants may feel slight discomfort from webcam monitoring. You may experience normal study-related fatigue. There are no direct benefits to you, but your participation will contribute to understanding how adaptive systems can support learning.

CONFIDENTIALITY:
• All data collected is anonymous
• You will be assigned a participant ID (e.g., "P001")
• No personal identifying information will be stored with study data
• Results will be reported in aggregate form only
• Data will be stored securely and used solely for academic purposes

VOLUNTARY PARTICIPATION:
• Your participation is completely voluntary
• You may withdraw at any time without penalty
• You may decline to answer any question
• Withdrawal will not affect your academic standing

CONTACT INFORMATION:
If you have questions about this study, please contact:
• Instructor: Asst. Prof. Polat Göktaş
• Course: CS 449/549, Sabancı University

CONSENT:
By clicking "I Consent" below, you indicate that:
• You have read and understood this consent form
• You have had the opportunity to ask questions
• You voluntarily agree to participate in this research
• You understand you can withdraw at any time
        """
        
        consent_text.insert('1.0', consent_content)
        consent_text.config(state='disabled')
        
        # Consent checkbox
        self.consent_var = tk.BooleanVar()
        ttk.Checkbutton(
            frame,
            text="I have read and understood the consent form, and I agree to participate",
            variable=self.consent_var,
            style='Large.TRadiobutton'
        ).pack(pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="← Back",
                  command=self.show_welcome_screen).pack(side='left', padx=10)
        
        ttk.Button(btn_frame, text="I Consent →",
                  command=self.process_consent,
                  style='Accent.TButton').pack(side='left', padx=10)
    
    def process_consent(self):
        """Process consent and continue to demographics."""
        if not self.consent_var.get():
            messagebox.showwarning("Consent Required", 
                                  "You must consent to participate in the study.")
            return
        
        self.show_demographics_form()
    
    # ==================== DEMOGRAPHICS ====================
    
    def show_demographics_form(self):
        """Collect participant demographics."""
        self.clear_window()
        
        frame = ttk.Frame(self.root, padding=40)
        frame.pack(expand=True)
        
        title = ttk.Label(frame, text="Participant Information", style='Title.TLabel')
        title.pack(pady=20)
        
        # Form
        form_frame = ttk.Frame(frame)
        form_frame.pack(pady=20)
        
        # Participant ID
        ttk.Label(form_frame, text="Participant ID:", font=('Helvetica', 11)).grid(row=0, column=0, sticky='e', padx=10, pady=10)
        self.pid_entry = ttk.Entry(form_frame, font=('Helvetica', 11), width=20)
        self.pid_entry.grid(row=0, column=1, padx=10, pady=10)
        self.pid_entry.insert(0, f"P{random.randint(100, 999)}")
        
        # Age
        ttk.Label(form_frame, text="Age:", font=('Helvetica', 11)).grid(row=1, column=0, sticky='e', padx=10, pady=10)
        self.age_entry = ttk.Entry(form_frame, font=('Helvetica', 11), width=20)
        self.age_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # Gender
        ttk.Label(form_frame, text="Gender:", font=('Helvetica', 11)).grid(row=2, column=0, sticky='e', padx=10, pady=10)
        self.gender_var = tk.StringVar()
        gender_combo = ttk.Combobox(form_frame, textvariable=self.gender_var, 
                                    values=["Male", "Female", "Non-binary", "Prefer not to say"],
                                    state='readonly', font=('Helvetica', 11), width=18)
        gender_combo.grid(row=2, column=1, padx=10, pady=10)
        
        # Study level
        ttk.Label(form_frame, text="Study Level:", font=('Helvetica', 11)).grid(row=3, column=0, sticky='e', padx=10, pady=10)
        self.level_var = tk.StringVar()
        level_combo = ttk.Combobox(form_frame, textvariable=self.level_var,
                                   values=["Undergraduate", "Graduate", "PhD"],
                                   state='readonly', font=('Helvetica', 11), width=18)
        level_combo.grid(row=3, column=1, padx=10, pady=10)
        
        # Previous study method
        ttk.Label(form_frame, text="Do you use Pomodoro\nor similar techniques?", 
                 font=('Helvetica', 11)).grid(row=4, column=0, sticky='e', padx=10, pady=10)
        self.pomodoro_var = tk.StringVar()
        ttk.Radiobutton(form_frame, text="Yes, regularly", variable=self.pomodoro_var, value="regular").grid(row=4, column=1, sticky='w', padx=10)
        ttk.Radiobutton(form_frame, text="Sometimes", variable=self.pomodoro_var, value="sometimes").grid(row=5, column=1, sticky='w', padx=10)
        ttk.Radiobutton(form_frame, text="Never", variable=self.pomodoro_var, value="never").grid(row=6, column=1, sticky='w', padx=10)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="← Back",
                  command=self.show_consent_form).pack(side='left', padx=10)
        
        ttk.Button(btn_frame, text="Continue →",
                  command=self.process_demographics,
                  style='Accent.TButton').pack(side='left', padx=10)
    
    def process_demographics(self):
        """Validate and save demographics, then proceed to mode selection."""
        # Validate required fields
        if not self.pid_entry.get():
            messagebox.showwarning("Required Field", "Please enter a Participant ID.")
            return
        
        if not self.age_entry.get().isdigit():
            messagebox.showwarning("Invalid Input", "Please enter a valid age.")
            return
        
        if not self.gender_var.get() or not self.level_var.get() or not self.pomodoro_var.get():
            messagebox.showwarning("Required Fields", "Please complete all fields.")
            return
        
        # Save demographics
        self.participant_id = self.pid_entry.get()
        self.demographics = {
            'participant_id': self.participant_id,
            'age': int(self.age_entry.get()),
            'gender': self.gender_var.get(),
            'study_level': self.level_var.get(),
            'pomodoro_experience': self.pomodoro_var.get()
        }
        
        self.show_mode_selection()
    
    # ==================== MODE SELECTION ====================
    
    def show_mode_selection(self):
        """Select study mode (Fixed or Adaptive)."""
        self.clear_window()
        
        frame = ttk.Frame(self.root, padding=40)
        frame.pack(expand=True)
        
        title = ttk.Label(frame, text="Select Study Mode", style='Title.TLabel')
        title.pack(pady=20)
        
        desc = ttk.Label(
            frame,
            text="Please select which mode you will use for this session:",
            font=('Helvetica', 12)
        )
        desc.pack(pady=10)
        
        # Mode descriptions
        modes_frame = ttk.Frame(frame)
        modes_frame.pack(pady=20)
        
        # Fixed mode
        fixed_frame = ttk.LabelFrame(modes_frame, text="Fixed-Timer Mode (Pomodoro)", padding=20)
        fixed_frame.grid(row=0, column=0, padx=20, pady=10)
        
        fixed_desc = (
            "• 25-minute study intervals\n"
            "• 5-minute break intervals\n"
            "• Traditional timer-based approach\n"
            "• Breaks occur at fixed times"
        )
        ttk.Label(fixed_frame, text=fixed_desc, font=('Helvetica', 10), justify='left').pack()
        ttk.Button(fixed_frame, text="Select Fixed Mode",
                  command=lambda: self.start_session('fixed'),
                  style='Accent.TButton').pack(pady=10)
        
        # Adaptive mode
        adaptive_frame = ttk.LabelFrame(modes_frame, text="Adaptive Mode", padding=20)
        adaptive_frame.grid(row=0, column=1, padx=20, pady=10)
        
        adaptive_desc = (
            "• Dynamic break suggestions\n"
            "• Based on detected fatigue\n"
            "• Uses webcam monitoring\n"
            "• Personalized to your state"
        )
        ttk.Label(adaptive_frame, text=adaptive_desc, font=('Helvetica', 10), justify='left').pack()
        ttk.Button(adaptive_frame, text="Select Adaptive Mode",
                  command=lambda: self.start_session('adaptive'),
                  style='Accent.TButton').pack(pady=10)
        
        # Note
        note = ttk.Label(
            frame,
            text="Note: You will complete both modes on different days.\nThe order is randomized for research purposes.",
            font=('Helvetica', 9, 'italic'),
            justify='center'
        )
        note.pack(pady=20)
    
    # ==================== STUDY SESSION ====================
    
    def start_session(self, mode):
        """Initialize and start study session."""
        self.session_mode = mode
        
        # Load flashcards
        try:
            with open('flashcards.json', 'r') as f:
                all_flashcards = json.load(f)
            self.flashcards = random.sample(all_flashcards, 
                                          min(config.FLASHCARDS_PER_SESSION, len(all_flashcards)))
            random.shuffle(self.flashcards)
        except FileNotFoundError:
            messagebox.showerror("Error", "Flashcards file not found!")
            return
        
        # Initialize components
        self.fatigue_detector = FatigueDetector()
        self.data_logger = DataLogger(self.participant_id, mode)
        self.data_logger.log_demographics(self.demographics)
        
        # Initialize webcam
        try:
            self.webcam = cv2.VideoCapture(config.WEBCAM_ID)
            if not self.webcam.isOpened():
                raise Exception("Cannot open webcam")
            
            self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
            self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        except Exception as e:
            messagebox.showerror("Webcam Error", 
                               f"Could not initialize webcam:\n{str(e)}\n\nPlease check camera permissions.")
            return
        
        # Reset state
        self.current_flashcard_index = 0
        self.session_start_time = time.time()
        self.on_break = False
        self.last_biometric_log = time.time()
        self.running = True
        
        # Start webcam thread
        self.webcam_thread = threading.Thread(target=self.webcam_loop, daemon=True)
        self.webcam_thread.start()
        
        # Show study interface
        self.show_study_interface()
    
    def webcam_loop(self):
        """Background thread for webcam processing."""
        while self.running:
            if self.webcam and self.webcam.isOpened():
                ret, frame = self.webcam.read()
                if ret:
                    # Process frame with fatigue detector
                    processed_frame, metrics = self.fatigue_detector.process_frame(frame, draw_landmarks=False)
                    
                    # Log biometric data periodically
                    current_time = time.time()
                    if current_time - self.last_biometric_log >= config.LOG_INTERVAL:
                        self.data_logger.log_biometric_data(metrics)
                        self.last_biometric_log = current_time
                    
                    # Check for break suggestion (adaptive mode only)
                    if self.session_mode == 'adaptive' and not self.on_break:
                        should_break, reason = self.fatigue_detector.should_suggest_break()
                        if should_break:
                            # Check minimum work time
                            time_worked = current_time - self.session_start_time
                            if time_worked >= config.ADAPTIVE_MIN_WORK_TIME:
                                self.root.after(0, self.suggest_break, reason, metrics.get('fatigue_score', 0))
                
            time.sleep(1.0 / config.FPS)
    
    def show_study_interface(self):
        """Display main study interface."""
        self.clear_window()
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True)
        
        # Top bar - Status
        top_bar = ttk.Frame(main_frame, relief='raised', borderwidth=1)
        top_bar.pack(side='top', fill='x', padx=5, pady=5)
        
        mode_text = "Fixed-Timer (Pomodoro)" if self.session_mode == 'fixed' else "Adaptive Mode"
        ttk.Label(top_bar, text=f"Mode: {mode_text}", font=('Helvetica', 11, 'bold')).pack(side='left', padx=10)
        
        self.timer_label = ttk.Label(top_bar, text="Time: 00:00", font=('Helvetica', 11))
        self.timer_label.pack(side='left', padx=20)
        
        self.progress_label = ttk.Label(top_bar, text=f"Progress: 0/{len(self.flashcards)}", font=('Helvetica', 11))
        self.progress_label.pack(side='left', padx=20)
        
        # Center - Flashcard display
        center_frame = ttk.Frame(main_frame)
        center_frame.pack(side='top', fill='both', expand=True, padx=40, pady=20)
        
        # Flashcard container
        self.flashcard_frame = ttk.LabelFrame(center_frame, text="Flashcard", padding=30)
        self.flashcard_frame.pack(fill='both', expand=True)
        
        self.word_label = ttk.Label(self.flashcard_frame, text="", font=('Helvetica', 28, 'bold'))
        self.word_label.pack(pady=20)
        
        self.definition_label = ttk.Label(self.flashcard_frame, text="", font=('Helvetica', 14), wraplength=600)
        self.definition_label.pack(pady=10)
        
        self.example_label = ttk.Label(self.flashcard_frame, text="", font=('Helvetica', 12, 'italic'), 
                                      wraplength=600, foreground='#666')
        self.example_label.pack(pady=10)
        
        # Navigation buttons
        nav_frame = ttk.Frame(center_frame)
        nav_frame.pack(pady=20)
        
        self.prev_btn = ttk.Button(nav_frame, text="← Previous", command=self.previous_flashcard)
        self.prev_btn.pack(side='left', padx=10)
        
        self.next_btn = ttk.Button(nav_frame, text="Next →", command=self.next_flashcard, style='Accent.TButton')
        self.next_btn.pack(side='left', padx=10)
        
        ttk.Button(nav_frame, text="End Session", command=self.confirm_end_session).pack(side='left', padx=30)
        
        # Right sidebar - Stats (for adaptive mode)
        if self.session_mode == 'adaptive':
            sidebar = ttk.LabelFrame(main_frame, text="Fatigue Monitoring", padding=10)
            sidebar.pack(side='right', fill='y', padx=5, pady=5)
            
            ttk.Label(sidebar, text="Status:", font=('Helvetica', 10, 'bold')).pack(pady=5)
            self.status_label = ttk.Label(sidebar, text="Monitoring...", font=('Helvetica', 9))
            self.status_label.pack(pady=5)
            
            ttk.Label(sidebar, text="Blink Rate:", font=('Helvetica', 9)).pack(pady=(10,0))
            self.blink_label = ttk.Label(sidebar, text="0 /min", font=('Helvetica', 9))
            self.blink_label.pack()
            
            ttk.Label(sidebar, text="Yawn Count:", font=('Helvetica', 9)).pack(pady=(10,0))
            self.yawn_label = ttk.Label(sidebar, text="0", font=('Helvetica', 9))
            self.yawn_label.pack()
            
            ttk.Label(sidebar, text="Fatigue Score:", font=('Helvetica', 9)).pack(pady=(10,0))
            self.fatigue_score_label = ttk.Label(sidebar, text="0.0", font=('Helvetica', 9))
            self.fatigue_score_label.pack()
        
        # Start with first flashcard
        self.display_flashcard()
        self.update_timer()
        
        # Schedule fixed breaks if in Pomodoro mode
        if self.session_mode == 'fixed':
            self.schedule_fixed_break()
    
    def display_flashcard(self):
        """Display current flashcard."""
        if self.current_flashcard_index < len(self.flashcards):
            card = self.flashcards[self.current_flashcard_index]
            self.word_label.config(text=card['word'])
            self.definition_label.config(text=card['definition'])
            self.example_label.config(text=f"Example: {card['example']}")
            
            # Log event
            self.data_logger.log_flashcard_event(card['id'], 'viewed')
            
            # Update progress
            self.progress_label.config(text=f"Progress: {self.current_flashcard_index + 1}/{len(self.flashcards)}")
            
            # Update button states
            self.prev_btn.config(state='normal' if self.current_flashcard_index > 0 else 'disabled')
    
    def next_flashcard(self):
        """Move to next flashcard."""
        if self.current_flashcard_index < len(self.flashcards) - 1:
            self.current_flashcard_index += 1
            self.display_flashcard()
        else:
            messagebox.showinfo("Complete", "You've reviewed all flashcards!")
            self.end_session()
    
    def previous_flashcard(self):
        """Move to previous flashcard."""
        if self.current_flashcard_index > 0:
            self.current_flashcard_index -= 1
            self.display_flashcard()
    
    def update_timer(self):
        """Update session timer."""
        if not self.running:
            return
        
        elapsed = time.time() - self.session_start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        self.timer_label.config(text=f"Time: {minutes:02d}:{seconds:02d}")
        
        # Update adaptive mode stats
        if self.session_mode == 'adaptive' and hasattr(self, 'status_label'):
            blink_rate = self.fatigue_detector.get_blink_rate()
            yawn_count = self.fatigue_detector.yawn_counter
            fatigue_score = self.fatigue_detector.calculate_fatigue_score()
            
            self.blink_label.config(text=f"{blink_rate:.1f} /min")
            self.yawn_label.config(text=str(yawn_count))
            self.fatigue_score_label.config(text=f"{fatigue_score:.2f}")
            
            # Update status
            if fatigue_score > config.FATIGUE_SCORE_THRESHOLD:
                self.status_label.config(text="High fatigue detected", foreground='red')
            elif fatigue_score > 0.4:
                self.status_label.config(text="Moderate fatigue", foreground='orange')
            else:
                self.status_label.config(text="Normal state", foreground='green')
        
        # Continue updating
        self.root.after(1000, self.update_timer)
    
    def schedule_fixed_break(self):
        """Schedule next break for fixed-timer mode."""
        if not self.running or self.on_break:
            return
        
        elapsed = time.time() - self.session_start_time
        next_break_time = config.POMODORO_WORK_DURATION
        
        # Find next break interval
        while elapsed >= next_break_time:
            next_break_time += config.POMODORO_WORK_DURATION + config.POMODORO_BREAK_DURATION
        
        time_until_break = (next_break_time - elapsed) * 1000  # Convert to milliseconds
        
        if time_until_break > 0:
            self.root.after(int(time_until_break), lambda: self.suggest_break("Scheduled Pomodoro break", 0))
    
    def suggest_break(self, reason, fatigue_score):
        """Suggest a break to the user."""
        if self.on_break:
            return
        
        # Log break suggestion
        self.data_logger.log_break_event('suggested', fatigue_score=fatigue_score, reason=reason)
        
        # Show notification
        response = messagebox.askyesno(
            "Break Suggestion",
            f"Time for a break!\n\nReason: {reason}\n\nWould you like to take a 5-minute break now?",
            icon='info'
        )
        
        if response:
            self.take_break()
        else:
            self.data_logger.log_break_event('dismissed', fatigue_score=fatigue_score)
            if self.session_mode == 'fixed':
                self.schedule_fixed_break()
    
    def take_break(self):
        """Start break period."""
        self.on_break = True
        self.break_start_time = time.time()
        
        self.data_logger.log_break_event('taken', duration=config.ADAPTIVE_BREAK_DURATION)
        
        # Show break screen
        break_window = tk.Toplevel(self.root)
        break_window.title("Break Time")
        break_window.geometry("400x300")
        break_window.transient(self.root)
        break_window.grab_set()
        
        frame = ttk.Frame(break_window, padding=40)
        frame.pack(expand=True)
        
        ttk.Label(frame, text="Break Time! 😌", font=('Helvetica', 20, 'bold')).pack(pady=20)
        ttk.Label(frame, text="Take a short break to rest your eyes and mind.", 
                 font=('Helvetica', 12)).pack(pady=10)
        
        break_timer = ttk.Label(frame, text="5:00", font=('Helvetica', 24))
        break_timer.pack(pady=20)
        
        def update_break_timer():
            if not self.on_break:
                break_window.destroy()
                return
            
            elapsed = time.time() - self.break_start_time
            remaining = config.ADAPTIVE_BREAK_DURATION - elapsed
            
            if remaining <= 0:
                self.end_break()
                break_window.destroy()
            else:
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                break_timer.config(text=f"{minutes}:{seconds:02d}")
                break_window.after(1000, update_break_timer)
        
        ttk.Button(frame, text="End Break Early", 
                  command=lambda: [self.end_break(), break_window.destroy()]).pack(pady=10)
        
        update_break_timer()
    
    def end_break(self):
        """End break and resume study."""
        self.on_break = False
        
        if self.session_mode == 'fixed':
            self.schedule_fixed_break()
    
    def confirm_end_session(self):
        """Confirm before ending session."""
        response = messagebox.askyesno(
            "End Session",
            "Are you sure you want to end this study session?\n\nYou will proceed to the recall test.",
            icon='question'
        )
        
        if response:
            self.end_session()
    
    def end_session(self):
        """End study session and proceed to testing."""
        self.running = False
        
        # Stop webcam
        if self.webcam:
            self.webcam.release()
        
        # Proceed to recall test
        self.show_recall_test()
    
    # ==================== TESTING & EVALUATION ====================
    
    def show_recall_test(self):
        """Show recall test."""
        self.clear_window()
        
        # Show instructions while test window loads
        frame = ttk.Frame(self.root)
        frame.pack(expand=True)
        ttk.Label(frame, text="Loading recall test...", font=('Helvetica', 14)).pack()
        
        # Create test
        def on_test_complete(results):
            self.test_results = results
            self.data_logger.log_evaluation_data({'test_score': results['score'], 
                                                  'test_correct': results['correct'],
                                                  'test_total': results['total']})
            self.show_evaluation()
        
        RecallTest(self.root, self.flashcards, on_test_complete)
    
    def show_evaluation(self):
        """Show evaluation suite (SUS + feedback)."""
        def on_evaluation_complete(results):
            self.evaluation_results = results
            
            # Combine all evaluation data
            full_evaluation = {
                'test_score': self.test_results['score'],
                'test_correct': self.test_results['correct'],
                'test_total': self.test_results['total'],
                'fatigue_rating': results['fatigue_rating'],
                'concentration_rating': results['concentration_rating'],
                'alertness_rating': results['alertness_rating'],
                'sus_score': results['sus_score'],
                'sus_responses': results['sus_responses'],
                'feedback': results['feedback']
            }
            
            self.data_logger.log_evaluation_data(full_evaluation)
            self.finish_session()
        
        EvaluationSuite(self.root, on_evaluation_complete)
    
    def finish_session(self):
        """Finish session and show summary."""
        # Save all data
        self.data_logger.save_session()
        
        # Show completion screen
        self.clear_window()
        
        frame = ttk.Frame(self.root, padding=40)
        frame.pack(expand=True)
        
        ttk.Label(frame, text="Session Complete! ✓", style='Title.TLabel').pack(pady=20)
        
        # Summary
        summary_frame = ttk.LabelFrame(frame, text="Session Summary", padding=20)
        summary_frame.pack(pady=20)
        
        summary_text = f"""
Mode: {self.session_mode.capitalize()}
Test Score: {self.test_results['correct']}/{self.test_results['total']} ({self.test_results['score']:.1f}%)
SUS Score: {self.evaluation_results['sus_score']:.1f}/100
Fatigue Rating: {self.evaluation_results['fatigue_rating']}/5
        """
        
        ttk.Label(summary_frame, text=summary_text, font=('Helvetica', 12), justify='left').pack()
        
        ttk.Label(frame, text="Thank you for participating!\n\nYour data has been saved anonymously.",
                 font=('Helvetica', 12), justify='center').pack(pady=20)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Start New Session",
                  command=self.show_welcome_screen).pack(side='left', padx=10)
        
        ttk.Button(btn_frame, text="Exit",
                  command=self.root.quit).pack(side='left', padx=10)
    
    def run(self):
        """Start the application."""
        # Start mainloop (removed problematic update() for Tk 8.5 compatibility)
        self.root.mainloop()
        
        # Cleanup on exit
        if self.webcam:
            self.webcam.release()
        cv2.destroyAllWindows()


def main():
    """Main entry point."""
    app = AdaptiBreakApp()
    app.run()


if __name__ == "__main__":
    main()

