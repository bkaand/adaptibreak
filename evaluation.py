"""
Evaluation module for AdaptiBreak study.
Includes System Usability Scale (SUS), fatigue ratings, and performance tests.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import random


# System Usability Scale (SUS) Questions
SUS_QUESTIONS = [
    "I think that I would like to use this system frequently.",
    "I found the system unnecessarily complex.",
    "I thought the system was easy to use.",
    "I think that I would need the support of a technical person to be able to use this system.",
    "I found the various functions in this system were well integrated.",
    "I thought there was too much inconsistency in this system.",
    "I would imagine that most people would learn to use this system very quickly.",
    "I found the system very cumbersome to use.",
    "I felt very confident using the system.",
    "I needed to learn a lot of things before I could get going with this system."
]


class EvaluationSuite:
    """
    Complete evaluation suite including SUS, fatigue ratings, and qualitative feedback.
    """
    
    def __init__(self, parent, callback):
        """
        Initialize evaluation suite.
        
        Args:
            parent: Parent tkinter window
            callback: Function to call with evaluation results
        """
        self.parent = parent
        self.callback = callback
        self.results = {}
        
        # Create evaluation window
        self.window = tk.Toplevel(parent)
        self.window.title("Session Evaluation")
        self.window.geometry("800x600")
        self.window.configure(bg='#f5f5f5')
        
        # Make it modal
        self.window.transient(parent)
        self.window.grab_set()
        
        self.current_page = 0
        self.create_pages()
        self.show_page(0)
    
    def create_pages(self):
        """Create all evaluation pages."""
        self.pages = [
            self.create_fatigue_page,
            self.create_sus_page,
            self.create_feedback_page
        ]
    
    def create_fatigue_page(self, container):
        """Create fatigue rating page."""
        frame = ttk.Frame(container)
        
        # Title
        title = ttk.Label(
            frame,
            text="Fatigue Assessment",
            font=('Helvetica', 18, 'bold')
        )
        title.pack(pady=20)
        
        # Instructions
        instructions = ttk.Label(
            frame,
            text="Please rate how tired you felt during this study session:",
            font=('Helvetica', 12)
        )
        instructions.pack(pady=10)
        
        # Fatigue scale
        scale_frame = ttk.Frame(frame)
        scale_frame.pack(pady=20)
        
        self.fatigue_var = tk.IntVar(value=3)
        
        ttk.Label(scale_frame, text="Not tired at all", font=('Helvetica', 10)).grid(row=0, column=0, padx=5)
        
        for i in range(1, 6):
            ttk.Radiobutton(
                scale_frame,
                text=str(i),
                variable=self.fatigue_var,
                value=i
            ).grid(row=0, column=i, padx=10)
        
        ttk.Label(scale_frame, text="Extremely tired", font=('Helvetica', 10)).grid(row=0, column=6, padx=5)
        
        # Additional fatigue questions
        questions_frame = ttk.Frame(frame)
        questions_frame.pack(pady=20, padx=40, fill='both')
        
        self.concentration_var = tk.IntVar(value=3)
        self.alertness_var = tk.IntVar(value=3)
        
        # Concentration question
        ttk.Label(questions_frame, text="How would you rate your concentration level?", 
                 font=('Helvetica', 11)).pack(anchor='w', pady=(10, 5))
        
        conc_scale = ttk.Frame(questions_frame)
        conc_scale.pack(anchor='w', padx=20)
        ttk.Label(conc_scale, text="Poor").grid(row=0, column=0)
        for i in range(1, 6):
            ttk.Radiobutton(conc_scale, text=str(i), variable=self.concentration_var, value=i).grid(row=0, column=i, padx=5)
        ttk.Label(conc_scale, text="Excellent").grid(row=0, column=6)
        
        # Alertness question
        ttk.Label(questions_frame, text="How alert did you feel?", 
                 font=('Helvetica', 11)).pack(anchor='w', pady=(20, 5))
        
        alert_scale = ttk.Frame(questions_frame)
        alert_scale.pack(anchor='w', padx=20)
        ttk.Label(alert_scale, text="Very drowsy").grid(row=0, column=0)
        for i in range(1, 6):
            ttk.Radiobutton(alert_scale, text=str(i), variable=self.alertness_var, value=i).grid(row=0, column=i, padx=5)
        ttk.Label(alert_scale, text="Very alert").grid(row=0, column=6)
        
        return frame
    
    def create_sus_page(self, container):
        """Create System Usability Scale page."""
        frame = ttk.Frame(container)
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(frame, bg='#f5f5f5', highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Title
        title = ttk.Label(
            scrollable_frame,
            text="System Usability Scale (SUS)",
            font=('Helvetica', 18, 'bold')
        )
        title.pack(pady=20)
        
        # Instructions
        instructions = ttk.Label(
            scrollable_frame,
            text="For each statement, please indicate your level of agreement:",
            font=('Helvetica', 12)
        )
        instructions.pack(pady=10)
        
        # SUS questions
        self.sus_vars = []
        
        for i, question in enumerate(SUS_QUESTIONS):
            q_frame = ttk.LabelFrame(scrollable_frame, text=f"Question {i+1}", padding=10)
            q_frame.pack(pady=10, padx=40, fill='x')
            
            ttk.Label(q_frame, text=question, wraplength=600, font=('Helvetica', 10)).pack(anchor='w', pady=5)
            
            var = tk.IntVar(value=3)
            self.sus_vars.append(var)
            
            scale_frame = ttk.Frame(q_frame)
            scale_frame.pack(pady=5)
            
            ttk.Label(scale_frame, text="Strongly Disagree").grid(row=0, column=0, padx=5)
            for j in range(1, 6):
                ttk.Radiobutton(scale_frame, text=str(j), variable=var, value=j).grid(row=0, column=j, padx=5)
            ttk.Label(scale_frame, text="Strongly Agree").grid(row=0, column=6, padx=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return frame
    
    def create_feedback_page(self, container):
        """Create qualitative feedback page."""
        frame = ttk.Frame(container)
        
        # Title
        title = ttk.Label(
            frame,
            text="Your Feedback",
            font=('Helvetica', 18, 'bold')
        )
        title.pack(pady=20)
        
        # Instructions
        instructions = ttk.Label(
            frame,
            text="Please share your thoughts about the system:",
            font=('Helvetica', 12)
        )
        instructions.pack(pady=10)
        
        # Questions with text areas
        questions = [
            "What did you like most about the system?",
            "What did you like least or found most challenging?",
            "How did you feel about the webcam monitoring?",
            "Do you have any suggestions for improvement?"
        ]
        
        self.feedback_texts = []
        
        for question in questions:
            q_frame = ttk.Frame(frame)
            q_frame.pack(pady=10, padx=40, fill='both', expand=True)
            
            ttk.Label(q_frame, text=question, font=('Helvetica', 11, 'bold')).pack(anchor='w', pady=(5, 2))
            
            text_widget = scrolledtext.ScrolledText(q_frame, height=3, width=70, wrap=tk.WORD)
            text_widget.pack(fill='both', expand=True)
            self.feedback_texts.append(text_widget)
        
        return frame
    
    def show_page(self, page_num):
        """Display specific evaluation page."""
        # Clear current content
        for widget in self.window.winfo_children():
            widget.destroy()
        
        # Main container
        container = ttk.Frame(self.window)
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Create and show page
        page_frame = self.pages[page_num](container)
        page_frame.pack(fill='both', expand=True)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.window)
        nav_frame.pack(side='bottom', pady=20)
        
        if page_num > 0:
            ttk.Button(
                nav_frame,
                text="← Previous",
                command=lambda: self.show_page(page_num - 1)
            ).pack(side='left', padx=10)
        
        if page_num < len(self.pages) - 1:
            ttk.Button(
                nav_frame,
                text="Next →",
                command=lambda: self.show_page(page_num + 1)
            ).pack(side='right', padx=10)
        else:
            ttk.Button(
                nav_frame,
                text="Submit",
                command=self.submit_evaluation,
                style='Accent.TButton'
            ).pack(side='right', padx=10)
        
        self.current_page = page_num
    
    def calculate_sus_score(self):
        """Calculate SUS score (0-100)."""
        score = 0
        for i, var in enumerate(self.sus_vars):
            value = var.get()
            # Odd questions (0, 2, 4, 6, 8): subtract 1
            # Even questions (1, 3, 5, 7, 9): 5 minus value
            if i % 2 == 0:
                score += (value - 1)
            else:
                score += (5 - value)
        
        # Multiply by 2.5 to get 0-100 scale
        return score * 2.5
    
    def submit_evaluation(self):
        """Collect and submit evaluation results."""
        self.results = {
            'fatigue_rating': self.fatigue_var.get(),
            'concentration_rating': self.concentration_var.get(),
            'alertness_rating': self.alertness_var.get(),
            'sus_score': self.calculate_sus_score(),
            'sus_responses': [var.get() for var in self.sus_vars],
            'feedback': {
                'liked_most': self.feedback_texts[0].get('1.0', 'end-1c'),
                'liked_least': self.feedback_texts[1].get('1.0', 'end-1c'),
                'webcam_feelings': self.feedback_texts[2].get('1.0', 'end-1c'),
                'suggestions': self.feedback_texts[3].get('1.0', 'end-1c')
            }
        }
        
        self.window.destroy()
        self.callback(self.results)


class RecallTest:
    """
    Vocabulary recall test to measure learning performance.
    """
    
    def __init__(self, parent, flashcards, callback):
        """
        Initialize recall test.
        
        Args:
            parent: Parent tkinter window
            flashcards: List of flashcards that were studied
            callback: Function to call with test results
        """
        self.parent = parent
        self.callback = callback
        
        # Select random subset of flashcards for testing
        self.test_items = random.sample(flashcards, min(20, len(flashcards)))
        self.current_item = 0
        self.responses = []
        self.start_time = None
        
        # Create test window
        self.window = tk.Toplevel(parent)
        self.window.title("Vocabulary Recall Test")
        self.window.geometry("700x500")
        self.window.configure(bg='#f5f5f5')
        
        # Make it modal
        self.window.transient(parent)
        self.window.grab_set()
        
        self.show_instructions()
    
    def show_instructions(self):
        """Show test instructions."""
        # Clear window
        for widget in self.window.winfo_children():
            widget.destroy()
        
        frame = ttk.Frame(self.window)
        frame.pack(expand=True, fill='both', padx=40, pady=40)
        
        title = ttk.Label(
            frame,
            text="Vocabulary Recall Test",
            font=('Helvetica', 20, 'bold')
        )
        title.pack(pady=20)
        
        instructions = ttk.Label(
            frame,
            text=(
                "You will be shown vocabulary words that you studied.\n\n"
                "For each word, select the correct definition from the options provided.\n\n"
                f"There are {len(self.test_items)} questions.\n\n"
                "Click 'Start Test' when you're ready."
            ),
            font=('Helvetica', 12),
            justify='center'
        )
        instructions.pack(pady=20)
        
        ttk.Button(
            frame,
            text="Start Test",
            command=self.start_test,
            style='Accent.TButton'
        ).pack(pady=20)
    
    def start_test(self):
        """Start the recall test."""
        import time
        self.start_time = time.time()
        self.show_question()
    
    def show_question(self):
        """Display current test question."""
        if self.current_item >= len(self.test_items):
            self.show_results()
            return
        
        # Clear window
        for widget in self.window.winfo_children():
            widget.destroy()
        
        frame = ttk.Frame(self.window)
        frame.pack(expand=True, fill='both', padx=40, pady=40)
        
        # Progress
        progress = ttk.Label(
            frame,
            text=f"Question {self.current_item + 1} of {len(self.test_items)}",
            font=('Helvetica', 10)
        )
        progress.pack(pady=10)
        
        # Question
        item = self.test_items[self.current_item]
        question = ttk.Label(
            frame,
            text=f"What is the meaning of:\n\n{item['word']}",
            font=('Helvetica', 16, 'bold'),
            justify='center'
        )
        question.pack(pady=30)
        
        # Generate answer options (correct + 3 random wrong)
        correct_answer = item['definition']
        
        # Get other definitions as distractors
        all_definitions = [fc['definition'] for fc in self.test_items if fc['definition'] != correct_answer]
        distractors = random.sample(all_definitions, min(3, len(all_definitions)))
        
        options = [correct_answer] + distractors
        random.shuffle(options)
        
        # Answer selection variable
        self.answer_var = tk.StringVar()
        
        # Display options
        options_frame = ttk.Frame(frame)
        options_frame.pack(pady=20, fill='both', expand=True)
        
        for option in options:
            ttk.Radiobutton(
                options_frame,
                text=option,
                variable=self.answer_var,
                value=option,
                style='Large.TRadiobutton'
            ).pack(anchor='w', pady=10, padx=20)
        
        # Submit button
        ttk.Button(
            frame,
            text="Submit Answer",
            command=lambda: self.submit_answer(correct_answer),
            style='Accent.TButton'
        ).pack(pady=20)
    
    def submit_answer(self, correct_answer):
        """Submit answer and move to next question."""
        selected = self.answer_var.get()
        
        if not selected:
            return  # No answer selected
        
        is_correct = (selected == correct_answer)
        
        self.responses.append({
            'word': self.test_items[self.current_item]['word'],
            'correct_answer': correct_answer,
            'selected_answer': selected,
            'is_correct': is_correct
        })
        
        self.current_item += 1
        self.show_question()
    
    def show_results(self):
        """Display test results."""
        import time
        end_time = time.time()
        duration = end_time - self.start_time
        
        correct_count = sum(1 for r in self.responses if r['is_correct'])
        total_count = len(self.responses)
        score = (correct_count / total_count * 100) if total_count > 0 else 0
        
        results = {
            'score': score,
            'correct': correct_count,
            'total': total_count,
            'duration': duration,
            'responses': self.responses
        }
        
        # Clear window
        for widget in self.window.winfo_children():
            widget.destroy()
        
        frame = ttk.Frame(self.window)
        frame.pack(expand=True, fill='both', padx=40, pady=40)
        
        title = ttk.Label(
            frame,
            text="Test Complete!",
            font=('Helvetica', 20, 'bold')
        )
        title.pack(pady=20)
        
        score_label = ttk.Label(
            frame,
            text=f"Your Score: {correct_count}/{total_count} ({score:.1f}%)",
            font=('Helvetica', 16)
        )
        score_label.pack(pady=20)
        
        time_label = ttk.Label(
            frame,
            text=f"Time taken: {int(duration//60)}:{int(duration%60):02d}",
            font=('Helvetica', 12)
        )
        time_label.pack(pady=10)
        
        ttk.Button(
            frame,
            text="Continue",
            command=lambda: self.finish(results),
            style='Accent.TButton'
        ).pack(pady=30)
    
    def finish(self, results):
        """Finish test and return results."""
        self.window.destroy()
        self.callback(results)

