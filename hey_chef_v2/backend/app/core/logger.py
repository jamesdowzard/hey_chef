"""
Logging utility for Hey Chef v2 backend.
Provides structured logging with multiple handlers and log rotation.
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import json

from .config import Settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 'msecs', 
                          'relativeCreated', 'thread', 'threadName', 'processName', 
                          'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry)


class HeyChefLogger:
    """Centralized logging manager for Hey Chef v2"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Ensure log directories exist
        log_paths = [
            self.settings.logging.logs_directory,
            self.settings.logging.session_logs_directory,
            self.settings.logging.audio_logs_directory,
            self.settings.logging.api_logs_directory,
            self.settings.logging.archived_logs_directory
        ]
        
        for path in log_paths:
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def get_logger(self, name: str, 
                  log_level: Optional[str] = None,
                  add_file_handler: bool = True,
                  add_console_handler: bool = True,
                  json_format: bool = False) -> logging.Logger:
        """Get or create a logger with specified configuration"""
        
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level or self.settings.logging.default_log_level))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler
        if add_console_handler:
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = JSONFormatter() if json_format else logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(logging.DEBUG if self.settings.debug else logging.INFO)
            logger.addHandler(console_handler)
        
        # File handler with rotation
        if add_file_handler:
            log_file = Path(self.settings.logging.logs_directory) / f"{name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_formatter = JSONFormatter() if json_format else logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        self.loggers[name] = logger
        return logger
    
    def get_api_logger(self) -> logging.Logger:
        """Get API-specific logger"""
        return self.get_logger(
            "hey_chef_api",
            log_level=self.settings.logging.api_log_level,
            json_format=self.settings.is_production()
        )
    
    def get_audio_logger(self) -> logging.Logger:
        """Get audio processing logger"""
        return self.get_logger(
            "hey_chef_audio", 
            log_level=self.settings.logging.audio_log_level,
            json_format=False
        )
    
    def get_session_logger(self, session_id: str) -> logging.Logger:
        """Get session-specific logger"""
        logger_name = f"session_{session_id[:8]}"
        logger = self.get_logger(
            logger_name,
            log_level=self.settings.logging.session_log_level,
            add_console_handler=False,
            json_format=True
        )
        
        # Add session-specific file handler
        if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            session_log_file = Path(self.settings.logging.session_logs_directory) / f"session_{session_id[:8]}.log"
            session_handler = logging.handlers.RotatingFileHandler(
                session_log_file,
                maxBytes=5*1024*1024,  # 5MB
                backupCount=2
            )
            session_handler.setFormatter(JSONFormatter())
            logger.addHandler(session_handler)
        
        return logger
    
    def log_audio_event(self, event_type: str, message: str, 
                       session_id: Optional[str] = None, 
                       **kwargs):
        """Log audio processing events"""
        logger = self.get_audio_logger()
        extra = {
            'event_type': event_type,
            'session_id': session_id,
            **kwargs
        }
        logger.info(message, extra=extra)
    
    def log_api_request(self, method: str, path: str, 
                       status_code: int, duration: float,
                       user_agent: Optional[str] = None,
                       client_ip: Optional[str] = None):
        """Log API requests"""
        logger = self.get_api_logger()
        extra = {
            'request_method': method,
            'request_path': path,
            'status_code': status_code,
            'duration': duration,
            'user_agent': user_agent,
            'client_ip': client_ip
        }
        logger.info(f"{method} {path} - {status_code} ({duration:.3f}s)", extra=extra)
    
    def log_websocket_event(self, event_type: str, session_id: str, 
                           message_type: Optional[str] = None,
                           **kwargs):
        """Log WebSocket events"""
        logger = self.get_api_logger()
        extra = {
            'event_type': event_type,
            'session_id': session_id,
            'message_type': message_type,
            **kwargs
        }
        logger.info(f"WebSocket {event_type} for session {session_id[:8]}", extra=extra)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None,
                 logger_name: str = "hey_chef_api"):
        """Log errors with context"""
        logger = self.get_logger(logger_name)
        extra = context or {}
        logger.error(f"Error: {str(error)}", exc_info=True, extra=extra)
    
    def log_performance_metrics(self, operation: str, duration: float,
                              session_id: Optional[str] = None,
                              **metrics):
        """Log performance metrics"""
        logger = self.get_api_logger()
        extra = {
            'operation': operation,
            'duration': duration,
            'session_id': session_id,
            **metrics
        }
        logger.info(f"Performance: {operation} completed in {duration:.3f}s", extra=extra)
    
    def cleanup_old_logs(self, days: int = None):
        """Clean up old log files"""
        days = days or self.settings.logging.log_archive_days
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        log_dirs = [
            self.settings.logging.session_logs_directory,
            self.settings.logging.audio_logs_directory,
            self.settings.logging.api_logs_directory
        ]
        
        archived_count = 0
        for log_dir in log_dirs:
            log_path = Path(log_dir)
            if log_path.exists():
                for log_file in log_path.glob("*.log*"):
                    if log_file.stat().st_mtime < cutoff_time:
                        # Move to archived directory
                        archive_path = Path(self.settings.logging.archived_logs_directory) / log_file.name
                        log_file.rename(archive_path)
                        archived_count += 1
        
        logger = self.get_api_logger()
        logger.info(f"Archived {archived_count} old log files")
        return archived_count


# Global logger instance
_logger_instance: Optional[HeyChefLogger] = None


def setup_logging(settings: Settings) -> HeyChefLogger:
    """Setup global logging instance"""
    global _logger_instance
    _logger_instance = HeyChefLogger(settings)
    return _logger_instance


def get_logger(name: str = "hey_chef") -> logging.Logger:
    """Get logger instance"""
    if _logger_instance is None:
        # Fallback to basic logging if not setup
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(name)
    
    return _logger_instance.get_logger(name)


def get_audio_logger() -> logging.Logger:
    """Get audio processing logger"""
    if _logger_instance is None:
        return get_logger("audio")
    return _logger_instance.get_audio_logger()


def get_api_logger() -> logging.Logger:
    """Get API logger"""
    if _logger_instance is None:
        return get_logger("api")
    return _logger_instance.get_api_logger()


def get_session_logger(session_id: str) -> logging.Logger:
    """Get session-specific logger"""
    if _logger_instance is None:
        return get_logger(f"session_{session_id[:8]}")
    return _logger_instance.get_session_logger(session_id)


def log_audio_event(event_type: str, message: str, **kwargs):
    """Log audio processing events"""
    if _logger_instance:
        _logger_instance.log_audio_event(event_type, message, **kwargs)
    else:
        get_logger("audio").info(f"{event_type}: {message}")


def log_api_request(method: str, path: str, status_code: int, duration: float, **kwargs):
    """Log API requests"""
    if _logger_instance:
        _logger_instance.log_api_request(method, path, status_code, duration, **kwargs)
    else:
        get_logger("api").info(f"{method} {path} - {status_code} ({duration:.3f}s)")