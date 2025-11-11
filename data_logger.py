"""
Data Logger for AdaptiBreak study sessions.
Logs biometric data, session events, and evaluation metrics.
"""

import json
import os
import time
from datetime import datetime
import pandas as pd
import config


class DataLogger:
    """
    Logs study session data including biometric metrics, breaks, and performance.
    Ensures privacy by only storing aggregated/anonymized data.
    """
    
    def __init__(self, participant_id, session_mode):
        """
        Initialize logger for a study session.
        
        Args:
            participant_id: Anonymous participant identifier (e.g., "P001")
            session_mode: "fixed" for Pomodoro or "adaptive" for adaptive breaks
        """
        self.participant_id = participant_id
        self.session_mode = session_mode
        self.session_start_time = time.time()
        self.session_id = f"{participant_id}_{session_mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create log directory
        if not os.path.exists(config.LOG_DIRECTORY):
            os.makedirs(config.LOG_DIRECTORY)
        
        # Log files
        self.log_dir = os.path.join(config.LOG_DIRECTORY, self.session_id)
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Data storage
        self.biometric_data = []
        self.break_events = []
        self.flashcard_events = []
        self.session_metadata = {
            'participant_id': participant_id,
            'session_mode': session_mode,
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'total_duration': None
        }
        
    def log_biometric_data(self, metrics):
        """
        Log biometric data point (fatigue indicators).
        
        Args:
            metrics: Dictionary with biometric measurements
        """
        if not config.LOG_BIOMETRIC_DATA:
            return
        
        data_point = {
            'timestamp': time.time() - self.session_start_time,
            'datetime': datetime.now().isoformat(),
            'face_detected': metrics.get('face_detected', False),
            'blink_rate': metrics.get('blink_rate', 0),
            'yawn_count': metrics.get('yawn_count', 0),
            'fatigue_score': metrics.get('fatigue_score', 0),
            'ear': metrics.get('ear', 0),
            'mar': metrics.get('mar', 0),
            'head_tilt': metrics.get('head_tilt', 0),
            'head_forward': metrics.get('head_forward', 0)
        }
        
        self.biometric_data.append(data_point)
    
    def log_break_event(self, break_type, duration=None, fatigue_score=None, reason=None):
        """
        Log a break event.
        
        Args:
            break_type: "suggested", "taken", "dismissed", "scheduled"
            duration: Break duration in seconds (if taken)
            fatigue_score: Fatigue score at break suggestion
            reason: Reason for break suggestion
        """
        event = {
            'timestamp': time.time() - self.session_start_time,
            'datetime': datetime.now().isoformat(),
            'break_type': break_type,
            'duration': duration,
            'fatigue_score': fatigue_score,
            'reason': reason
        }
        
        self.break_events.append(event)
    
    def log_flashcard_event(self, flashcard_id, event_type, response_time=None, correct=None):
        """
        Log flashcard interaction.
        
        Args:
            flashcard_id: Unique flashcard identifier
            event_type: "viewed", "answered", "skipped"
            response_time: Time taken to respond (seconds)
            correct: Whether answer was correct (for testing)
        """
        event = {
            'timestamp': time.time() - self.session_start_time,
            'datetime': datetime.now().isoformat(),
            'flashcard_id': flashcard_id,
            'event_type': event_type,
            'response_time': response_time,
            'correct': correct
        }
        
        self.flashcard_events.append(event)
    
    def log_evaluation_data(self, evaluation_data):
        """
        Log evaluation metrics (test scores, fatigue ratings, SUS).
        
        Args:
            evaluation_data: Dictionary with evaluation metrics
        """
        eval_file = os.path.join(self.log_dir, 'evaluation.json')
        
        with open(eval_file, 'w') as f:
            json.dump(evaluation_data, f, indent=2)
    
    def log_demographics(self, demographics):
        """
        Log participant demographics (anonymous).
        
        Args:
            demographics: Dictionary with demographic info
        """
        demo_file = os.path.join(self.log_dir, 'demographics.json')
        
        # Ensure anonymization
        if config.ANONYMIZE_PARTICIPANT_DATA:
            demographics = demographics.copy()
            demographics.pop('name', None)
            demographics.pop('email', None)
        
        with open(demo_file, 'w') as f:
            json.dump(demographics, f, indent=2)
    
    def save_session(self):
        """Save all session data to files."""
        # Update metadata
        self.session_metadata['end_time'] = datetime.now().isoformat()
        self.session_metadata['total_duration'] = time.time() - self.session_start_time
        
        # Save metadata
        metadata_file = os.path.join(self.log_dir, 'session_metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(self.session_metadata, f, indent=2)
        
        # Save biometric data as CSV
        if self.biometric_data:
            biometric_file = os.path.join(self.log_dir, 'biometric_data.csv')
            df = pd.DataFrame(self.biometric_data)
            df.to_csv(biometric_file, index=False)
        
        # Save break events
        if self.break_events:
            breaks_file = os.path.join(self.log_dir, 'break_events.json')
            with open(breaks_file, 'w') as f:
                json.dump(self.break_events, f, indent=2)
        
        # Save flashcard events
        if self.flashcard_events:
            flashcards_file = os.path.join(self.log_dir, 'flashcard_events.json')
            with open(flashcards_file, 'w') as f:
                json.dump(self.flashcard_events, f, indent=2)
        
        print(f"✓ Session data saved to: {self.log_dir}")
    
    def get_session_summary(self):
        """Get summary statistics for the session."""
        summary = {
            'session_id': self.session_id,
            'duration_minutes': (time.time() - self.session_start_time) / 60,
            'biometric_data_points': len(self.biometric_data),
            'total_breaks': len([b for b in self.break_events if b['break_type'] == 'taken']),
            'breaks_suggested': len([b for b in self.break_events if b['break_type'] == 'suggested']),
            'breaks_dismissed': len([b for b in self.break_events if b['break_type'] == 'dismissed']),
            'flashcards_viewed': len([f for f in self.flashcard_events if f['event_type'] == 'viewed']),
        }
        
        # Average fatigue score
        if self.biometric_data:
            fatigue_scores = [d['fatigue_score'] for d in self.biometric_data if d['face_detected']]
            if fatigue_scores:
                summary['avg_fatigue_score'] = sum(fatigue_scores) / len(fatigue_scores)
                summary['max_fatigue_score'] = max(fatigue_scores)
        
        return summary


class AggregateAnalyzer:
    """
    Analyzes aggregated data across multiple sessions for research insights.
    """
    
    @staticmethod
    def load_all_sessions():
        """Load all session data from log directory."""
        sessions = []
        
        if not os.path.exists(config.LOG_DIRECTORY):
            return sessions
        
        for session_dir in os.listdir(config.LOG_DIRECTORY):
            session_path = os.path.join(config.LOG_DIRECTORY, session_dir)
            if not os.path.isdir(session_path):
                continue
            
            metadata_file = os.path.join(session_path, 'session_metadata.json')
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Load evaluation if exists
                eval_file = os.path.join(session_path, 'evaluation.json')
                if os.path.exists(eval_file):
                    with open(eval_file, 'r') as f:
                        metadata['evaluation'] = json.load(f)
                
                # Load biometric summary
                biometric_file = os.path.join(session_path, 'biometric_data.csv')
                if os.path.exists(biometric_file):
                    df = pd.read_csv(biometric_file)
                    metadata['avg_fatigue'] = df['fatigue_score'].mean()
                    metadata['max_fatigue'] = df['fatigue_score'].max()
                
                sessions.append(metadata)
        
        return sessions
    
    @staticmethod
    def compare_conditions():
        """Compare fixed vs adaptive conditions across participants."""
        sessions = AggregateAnalyzer.load_all_sessions()
        
        fixed_sessions = [s for s in sessions if s['session_mode'] == 'fixed']
        adaptive_sessions = [s for s in sessions if s['session_mode'] == 'adaptive']
        
        comparison = {
            'fixed': {
                'n': len(fixed_sessions),
                'avg_test_score': None,
                'avg_fatigue_rating': None,
                'avg_sus_score': None
            },
            'adaptive': {
                'n': len(adaptive_sessions),
                'avg_test_score': None,
                'avg_fatigue_rating': None,
                'avg_sus_score': None
            }
        }
        
        # Calculate averages for fixed condition
        if fixed_sessions:
            test_scores = [s['evaluation']['test_score'] for s in fixed_sessions 
                          if 'evaluation' in s and 'test_score' in s['evaluation']]
            if test_scores:
                comparison['fixed']['avg_test_score'] = sum(test_scores) / len(test_scores)
            
            fatigue_ratings = [s['evaluation']['fatigue_rating'] for s in fixed_sessions 
                              if 'evaluation' in s and 'fatigue_rating' in s['evaluation']]
            if fatigue_ratings:
                comparison['fixed']['avg_fatigue_rating'] = sum(fatigue_ratings) / len(fatigue_ratings)
            
            sus_scores = [s['evaluation']['sus_score'] for s in fixed_sessions 
                         if 'evaluation' in s and 'sus_score' in s['evaluation']]
            if sus_scores:
                comparison['fixed']['avg_sus_score'] = sum(sus_scores) / len(sus_scores)
        
        # Calculate averages for adaptive condition
        if adaptive_sessions:
            test_scores = [s['evaluation']['test_score'] for s in adaptive_sessions 
                          if 'evaluation' in s and 'test_score' in s['evaluation']]
            if test_scores:
                comparison['adaptive']['avg_test_score'] = sum(test_scores) / len(test_scores)
            
            fatigue_ratings = [s['evaluation']['fatigue_rating'] for s in adaptive_sessions 
                              if 'evaluation' in s and 'fatigue_rating' in s['evaluation']]
            if fatigue_ratings:
                comparison['adaptive']['avg_fatigue_rating'] = sum(fatigue_ratings) / len(fatigue_ratings)
            
            sus_scores = [s['evaluation']['sus_score'] for s in adaptive_sessions 
                         if 'evaluation' in s and 'sus_score' in s['evaluation']]
            if sus_scores:
                comparison['adaptive']['avg_sus_score'] = sum(sus_scores) / len(sus_scores)
        
        return comparison
    
    @staticmethod
    def export_for_analysis(output_file='analysis_data.csv'):
        """Export all session data in format suitable for statistical analysis."""
        sessions = AggregateAnalyzer.load_all_sessions()
        
        rows = []
        for session in sessions:
            if 'evaluation' not in session:
                continue
            
            row = {
                'participant_id': session['participant_id'],
                'session_mode': session['session_mode'],
                'test_score': session['evaluation'].get('test_score'),
                'fatigue_rating': session['evaluation'].get('fatigue_rating'),
                'sus_score': session['evaluation'].get('sus_score'),
                'avg_fatigue_detected': session.get('avg_fatigue'),
                'max_fatigue_detected': session.get('max_fatigue'),
                'duration_minutes': session.get('total_duration', 0) / 60
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        output_path = os.path.join(config.LOG_DIRECTORY, output_file)
        df.to_csv(output_path, index=False)
        print(f"✓ Analysis data exported to: {output_path}")
        
        return df

