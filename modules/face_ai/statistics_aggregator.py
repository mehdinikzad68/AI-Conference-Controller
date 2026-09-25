"""
Statistics Aggregator Module

Aggregates face analysis results over time and generates statistics and charts.
"""

import numpy as np
from typing import List, Dict
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class StatisticsAggregator:
    """
    Aggregates face analysis results and generates statistics.
    
    Tracks:
    - Number of faces detected over time
    - Attention levels (focused/distracted)
    - Emotion distribution
    - Head pose directions
    - Session duration
    """
    
    def __init__(self):
        """Initialize statistics aggregator."""
        self._session_start = None
        self._frames_processed = 0
        self._total_faces_detected = 0
        
        # Tracking dictionaries
        self._attention_counts = defaultdict(int)  # focused, distracted, left, right, etc.
        self._emotion_counts = defaultdict(int)  # happy, sad, neutral, etc.
        self._gender_counts = defaultdict(int)
        self._age_samples = []  # For calculating average age
        
        # Time series data
        self._timeline_attention = []  # List of attention levels over time
        self._timeline_face_count = []  # Number of faces per frame
        
        # Focused vs distracted tracking
        self._focused_count = 0
        self._distracted_count = 0
        self._smiling_count = 0
    
    def start_session(self):
        """Start a new analysis session."""
        self._session_start = datetime.now()
        self._frames_processed = 0
        self._total_faces_detected = 0
        self._attention_counts.clear()
        self._emotion_counts.clear()
        self._gender_counts.clear()
        self._age_samples.clear()
        self._timeline_attention.clear()
        self._timeline_face_count.clear()
        self._focused_count = 0
        self._distracted_count = 0
        self._smiling_count = 0
    
    def add_frame_results(self, faces: List[Dict], head_poses: List[Dict]):
        """
        Add analysis results from a single frame.
        
        Args:
            faces: List of face analysis results from FaceAnalyzer
            head_poses: List of head pose results (matched to faces)
        """
        self._frames_processed += 1
        num_faces = len(faces)
        self._total_faces_detected += num_faces
        self._timeline_face_count.append(num_faces)
        
        # Aggregate attention and emotions
        frame_attention_sum = 0.0
        frame_focused = 0
        frame_distracted = 0
        
        for i, face in enumerate(faces):
            # Emotion tracking
            emotion = face.get('emotion', 'neutral').lower()
            self._emotion_counts[emotion] += 1
            
            # Positive emotions (smiling indicators)
            if emotion in ['happy', 'surprise', 'fear']:  # Fear might be false positive
                if emotion in ['happy', 'surprise']:
                    self._smiling_count += 1
            
            # Age tracking
            if 'age' in face:
                self._age_samples.append(face['age'])
            
            # Gender tracking
            gender = face.get('gender', 'unknown').lower()
            self._gender_counts[gender] += 1
            
            # Head pose and attention
            if i < len(head_poses) and head_poses[i] is not None:
                pose = head_poses[i]
                direction = pose.get('attention_direction', 'unknown')
                self._attention_counts[direction] += 1
                
                if direction == 'focused':
                    frame_focused += 1
                    frame_attention_sum += 1.0
                elif direction == 'distracted':
                    frame_distracted += 1
                    frame_attention_sum += 0.0
                else:
                    # Partial attention
                    frame_attention_sum += 0.5
        
        # Track focused vs distracted
        self._focused_count += frame_focused
        self._distracted_count += frame_distracted
        
        # Calculate average attention for this frame
        if num_faces > 0:
            avg_attention = frame_attention_sum / num_faces
        else:
            avg_attention = 0.0
        
        self._timeline_attention.append(avg_attention)
    
    def get_statistics(self) -> Dict:
        """
        Get aggregated statistics.
        
        Returns:
            Dictionary with comprehensive statistics
        """
        session_duration = 0
        if self._session_start:
            session_duration = (datetime.now() - self._session_start).total_seconds()
        
        # Calculate average attention
        avg_attention = 0.0
        if self._timeline_attention:
            avg_attention = np.mean(self._timeline_attention)
        
        # Calculate average face count
        avg_face_count = 0.0
        if self._timeline_face_count:
            avg_face_count = np.mean(self._timeline_face_count)
        
        # Calculate average age
        avg_age = 0.0
        if self._age_samples:
            avg_age = np.mean(self._age_samples)
        
        # Focused vs distracted ratio
        total_attention_events = self._focused_count + self._distracted_count
        focused_ratio = 0.0
        if total_attention_events > 0:
            focused_ratio = self._focused_count / total_attention_events
        
        return {
            'session_duration_seconds': session_duration,
            'frames_processed': self._frames_processed,
            'total_faces_detected': self._total_faces_detected,
            'average_attention': float(avg_attention),
            'average_face_count': float(avg_face_count),
            'focused_count': self._focused_count,
            'distracted_count': self._distracted_count,
            'focused_ratio': float(focused_ratio),
            'smiling_count': self._smiling_count,
            'average_age': float(avg_age),
            'attention_distribution': dict(self._attention_counts),
            'emotion_distribution': dict(self._emotion_counts),
            'gender_distribution': dict(self._gender_counts),
        }
    
    def generate_charts(self, output_dir: str = "assets/reports") -> List[str]:
        """
        Generate visualization charts for analysis results.
        
        Args:
            output_dir: Directory to save chart images
            
        Returns:
            List of paths to generated chart files
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        stats = self.get_statistics()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_paths = []
        
        try:
            # 1. Emotion Distribution Pie Chart
            if stats['emotion_distribution']:
                fig, ax = plt.subplots(figsize=(8, 6))
                emotions = list(stats['emotion_distribution'].keys())
                counts = list(stats['emotion_distribution'].values())
                colors = plt.cm.Set3(np.linspace(0, 1, len(emotions)))
                
                ax.pie(counts, labels=emotions, autopct='%1.1f%%', colors=colors, startangle=90)
                ax.set_title('Emotion Distribution', fontsize=14, fontweight='bold')
                
                chart_path = f"{output_dir}/emotion_distribution_{timestamp}.png"
                plt.savefig(chart_path, dpi=150, bbox_inches='tight')
                plt.close()
                chart_paths.append(chart_path)
            
            # 2. Attention Direction Bar Chart
            if stats['attention_distribution']:
                fig, ax = plt.subplots(figsize=(10, 6))
                directions = list(stats['attention_distribution'].keys())
                counts = list(stats['attention_distribution'].values())
                colors = ['green' if d == 'focused' else 'orange' if d == 'distracted' else 'gray' 
                         for d in directions]
                
                bars = ax.bar(directions, counts, color=colors)
                ax.set_xlabel('Attention Direction', fontsize=12)
                ax.set_ylabel('Count', fontsize=12)
                ax.set_title('Head Pose / Attention Distribution', fontsize=14, fontweight='bold')
                ax.tick_params(axis='x', rotation=45)
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}', ha='center', va='bottom')
                
                chart_path = f"{output_dir}/attention_distribution_{timestamp}.png"
                plt.savefig(chart_path, dpi=150, bbox_inches='tight')
                plt.close()
                chart_paths.append(chart_path)
            
            # 3. Attention Over Time Line Chart
            if self._timeline_attention:
                fig, ax = plt.subplots(figsize=(12, 6))
                frames = range(len(self._timeline_attention))
                ax.plot(frames, self._timeline_attention, linewidth=2, color='blue', alpha=0.7)
                ax.axhline(y=stats['average_attention'], color='red', linestyle='--', 
                          label=f"Average: {stats['average_attention']:.2f}")
                ax.fill_between(frames, self._timeline_attention, alpha=0.3, color='blue')
                ax.set_xlabel('Frame Number', fontsize=12)
                ax.set_ylabel('Average Attention Level', fontsize=12)
                ax.set_title('Attention Level Over Time', fontsize=14, fontweight='bold')
                ax.set_ylim(0, 1)
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                chart_path = f"{output_dir}/attention_timeline_{timestamp}.png"
                plt.savefig(chart_path, dpi=150, bbox_inches='tight')
                plt.close()
                chart_paths.append(chart_path)
            
            # 4. Face Count Over Time
            if self._timeline_face_count:
                fig, ax = plt.subplots(figsize=(12, 6))
                frames = range(len(self._timeline_face_count))
                ax.plot(frames, self._timeline_face_count, linewidth=2, color='green', alpha=0.7)
                ax.axhline(y=stats['average_face_count'], color='red', linestyle='--',
                          label=f"Average: {stats['average_face_count']:.2f}")
                ax.fill_between(frames, self._timeline_face_count, alpha=0.3, color='green')
                ax.set_xlabel('Frame Number', fontsize=12)
                ax.set_ylabel('Number of Faces', fontsize=12)
                ax.set_title('Faces Detected Over Time', fontsize=14, fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                chart_path = f"{output_dir}/face_count_timeline_{timestamp}.png"
                plt.savefig(chart_path, dpi=150, bbox_inches='tight')
                plt.close()
                chart_paths.append(chart_path)
            
            # 5. Summary Statistics Text Chart
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.axis('off')
            
            summary_text = f"""
Session Statistics Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

SESSION OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Duration:              {stats['session_duration_seconds']:.1f} seconds
Frames Processed:      {stats['frames_processed']}
Total Faces Detected:   {stats['total_faces_detected']}

ATTENTION METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Average Attention:     {stats['average_attention']:.2%}
Focused Count:          {stats['focused_count']}
Distracted Count:       {stats['distracted_count']}
Focused Ratio:          {stats['focused_ratio']:.2%}

AUDIENCE COMPOSITION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Average Face Count:     {stats['average_face_count']:.2f}
Average Age:            {stats['average_age']:.1f} years
Smiling Events:         {stats['smiling_count']}

GENDER DISTRIBUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{chr(10).join(f"{k.capitalize():<20} {v}" for k, v in stats['gender_distribution'].items())}
"""
            
            ax.text(0.1, 0.9, summary_text, transform=ax.transAxes,
                   fontsize=11, verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            chart_path = f"{output_dir}/summary_report_{timestamp}.png"
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            chart_paths.append(chart_path)
            
            logger.info(f"Generated {len(chart_paths)} charts in {output_dir}")
            
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
        
        return chart_paths

