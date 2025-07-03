"""
Smart logging utility for Hey Chef with concise master log and detailed sub-logs.
Designed to provide Claude Code with essential debugging information without log bloat.
"""
import os
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from collections import deque


class SmartLogManager:
    """Manages master log with intelligent truncation and detailed sub-logs."""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.logs_dir = self.root_dir / "logs"
        self.master_log = self.root_dir / "hey_chef.log"
        
        # In-memory buffers for smart truncation
        self.session_buffer = deque(maxlen=10)
        self.error_buffer = deque(maxlen=20)
        self.audio_buffer = deque(maxlen=15)
        self.state_buffer = deque(maxlen=10)
        
        # Current session info
        self.current_session_id = None
        self.session_start_time = None
        
        self._setup_directories()
        self._setup_loggers()
    
    def _setup_directories(self):
        """Create log directory structure."""
        self.logs_dir.mkdir(exist_ok=True)
        (self.logs_dir / "sessions").mkdir(exist_ok=True)
        (self.logs_dir / "audio").mkdir(exist_ok=True)
        (self.logs_dir / "streamlit").mkdir(exist_ok=True)
        (self.logs_dir / "archived").mkdir(exist_ok=True)
    
    def _setup_loggers(self):
        """Setup logging configuration."""
        # Master logger - writes to master log and buffers
        self.master_logger = logging.getLogger("hey_chef.master")
        self.master_logger.setLevel(logging.INFO)
        
        # Session logger - detailed session logs
        self.session_logger = logging.getLogger("hey_chef.session")
        self.session_logger.setLevel(logging.DEBUG)
        
        # Audio logger - audio operations
        self.audio_logger = logging.getLogger("hey_chef.audio")
        self.audio_logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        for logger in [self.master_logger, self.session_logger, self.audio_logger]:
            logger.handlers.clear()
    
    def start_session(self, mode: str, recipe_type: str, streaming: bool = False):
        """Start a new session with context."""
        self.session_start_time = datetime.now()
        self.current_session_id = self.session_start_time.strftime("%Y%m%d_%H%M%S")
        
        session_msg = f"=== SESSION START {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')} ==="
        context_msg = f"MODE: {mode} | RECIPE: {recipe_type} | STREAMING: {streaming}"
        
        self._add_to_buffer("session", session_msg)
        self._add_to_buffer("session", context_msg)
        
        # Setup session-specific logger
        session_file = self.logs_dir / "sessions" / f"session_{self.current_session_id}.log"
        session_handler = logging.FileHandler(session_file)
        session_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.session_logger.addHandler(session_handler)
        
        self.session_logger.info(session_msg)
        self.session_logger.info(context_msg)
        self._update_master_log()
    
    def end_session(self, success: bool = True, error_msg: str = None):
        """End current session."""
        if not self.session_start_time:
            return
            
        end_time = datetime.now()
        duration = (end_time - self.session_start_time).total_seconds()
        status = "SUCCESS" if success else "FAILED"
        
        end_msg = f"=== SESSION END {end_time.strftime('%H:%M:%S')} ({status}) - Duration: {duration:.1f}s ==="
        
        self._add_to_buffer("session", end_msg)
        if error_msg:
            self._add_to_buffer("error", f"SESSION_ERROR: {error_msg}")
        
        self.session_logger.info(end_msg)
        if error_msg:
            self.session_logger.error(f"Session failed: {error_msg}")
        
        # Clear session handler
        self.session_logger.handlers.clear()
        
        self._update_master_log()
        self._cleanup_old_logs()
    
    def log_audio_event(self, event_type: str, details: str, pid: Optional[int] = None):
        """Log audio-related events."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        pid_str = f" PID:{pid}" if pid else ""
        msg = f"AUDIO_{event_type}: {details}{pid_str} at {timestamp}"
        
        self._add_to_buffer("audio", msg)
        
        # Log to daily audio file
        audio_file = self.logs_dir / "audio" / f"audio_{datetime.now().strftime('%Y%m%d')}.log"
        if not hasattr(self, 'audio_handler') or not audio_file.exists():
            if hasattr(self, 'audio_handler'):
                self.audio_logger.removeHandler(self.audio_handler)
            self.audio_handler = logging.FileHandler(audio_file)
            self.audio_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
            self.audio_logger.addHandler(self.audio_handler)
        
        self.audio_logger.info(f"{event_type}: {details}{pid_str}")
        self._update_master_log()
    
    def log_error(self, error_type: str, error_msg: str, context: str = None):
        """Log errors with context."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        context_str = f" | Context: {context}" if context else ""
        msg = f"ERROR_{error_type}: {error_msg}{context_str} at {timestamp}"
        
        self._add_to_buffer("error", msg)
        
        if self.session_logger.handlers:
            self.session_logger.error(f"{error_type}: {error_msg}{context_str}")
        
        self._update_master_log()
    
    def log_state_change(self, from_state: str, to_state: str, trigger: str = None):
        """Log important state changes."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        trigger_str = f" (trigger: {trigger})" if trigger else ""
        msg = f"STATE: {from_state} -> {to_state}{trigger_str} at {timestamp}"
        
        self._add_to_buffer("state", msg)
        
        if self.session_logger.handlers:
            self.session_logger.info(f"State change: {from_state} -> {to_state}{trigger_str}")
        
        self._update_master_log()
    
    def log_user_action(self, action: str, details: str = None):
        """Log user interactions."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        details_str = f": {details}" if details else ""
        msg = f"USER: {action}{details_str} at {timestamp}"
        
        self._add_to_buffer("state", msg)
        
        if self.session_logger.handlers:
            self.session_logger.info(f"User action: {action}{details_str}")
        
        self._update_master_log()
    
    def _add_to_buffer(self, buffer_type: str, message: str):
        """Add message to appropriate buffer."""
        if buffer_type == "session":
            self.session_buffer.append(message)
        elif buffer_type == "error":
            self.error_buffer.append(message)
        elif buffer_type == "audio":
            self.audio_buffer.append(message)
        elif buffer_type == "state":
            self.state_buffer.append(message)
    
    def _update_master_log(self):
        """Update master log with current buffer contents."""
        lines = []
        
        # Add section headers and content
        if self.session_buffer:
            lines.append("=== RECENT SESSIONS ===")
            lines.extend(self.session_buffer)
            lines.append("")
        
        if self.error_buffer:
            lines.append("=== RECENT ERRORS ===")
            lines.extend(self.error_buffer)
            lines.append("")
        
        if self.audio_buffer:
            lines.append("=== AUDIO EVENTS ===")
            lines.extend(self.audio_buffer)
            lines.append("")
        
        if self.state_buffer:
            lines.append("=== STATE CHANGES ===")
            lines.extend(self.state_buffer)
            lines.append("")
        
        # Add timestamp
        lines.append(f"=== LOG UPDATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
        
        # Write to master log (overwrite each time to keep it concise)
        with open(self.master_log, 'w') as f:
            f.write('\n'.join(lines))
    
    def _cleanup_old_logs(self):
        """Clean up old detailed logs."""
        try:
            # Keep only last 5 session logs
            session_files = sorted((self.logs_dir / "sessions").glob("session_*.log"))
            for old_file in session_files[:-5]:
                old_file.unlink()
            
            # Archive logs older than 7 days
            cutoff_time = time.time() - (7 * 24 * 60 * 60)
            for log_dir in ["audio", "streamlit"]:
                log_path = self.logs_dir / log_dir
                if log_path.exists():
                    for log_file in log_path.glob("*.log"):
                        if log_file.stat().st_mtime < cutoff_time:
                            archive_path = self.logs_dir / "archived" / log_file.name
                            log_file.rename(archive_path)
        except Exception as e:
            pass  # Silent cleanup failure


# Global log manager instance
_log_manager = None


def setup_logging(root_dir: str = ".") -> SmartLogManager:
    """Setup the global logging system."""
    global _log_manager
    _log_manager = SmartLogManager(root_dir)
    return _log_manager


def get_logger() -> SmartLogManager:
    """Get the global log manager."""
    global _log_manager
    if _log_manager is None:
        _log_manager = SmartLogManager()
    return _log_manager