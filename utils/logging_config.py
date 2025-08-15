"""
Centralized logging configuration for Concatly services.
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path


class ConcatlyLogger:
    """Enhanced logging configuration for Concatly with file and console output."""
    
    def __init__(self, service_name: str = "concatly", log_level: str = "INFO"):
        self.service_name = service_name
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Create logs directory if it doesn't exist
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Set up logger
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(self.log_level)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        self.detailed_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        self.simple_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Set up handlers
        self._setup_file_handler()
        self._setup_console_handler()
        self._setup_error_handler()
        
    def _setup_file_handler(self):
        """Set up rotating file handler for all logs."""
        log_file = self.log_dir / f"{self.service_name}.log"
        
        # Rotating file handler (10MB max, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.detailed_formatter)
        self.logger.addHandler(file_handler)
        
    def _setup_console_handler(self):
        """Set up console handler for INFO and above."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(self.simple_formatter)
        self.logger.addHandler(console_handler)
        
    def _setup_error_handler(self):
        """Set up separate error file handler for ERROR and CRITICAL logs."""
        error_log_file = self.log_dir / f"{self.service_name}_errors.log"
        
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.detailed_formatter)
        self.logger.addHandler(error_handler)
        
    def get_logger(self):
        """Get the configured logger instance."""
        return self.logger
    
    def log_startup(self):
        """Log application startup information."""
        self.logger.info("=" * 80)
        self.logger.info(f"🚀 {self.service_name.upper()} SERVICE STARTING UP")
        self.logger.info(f"📅 Timestamp: {datetime.now().isoformat()}")
        self.logger.info(f"📂 Working Directory: {os.getcwd()}")
        self.logger.info(f"🐍 Python Version: {sys.version}")
        self.logger.info(f"📝 Log Level: {logging.getLevelName(self.log_level)}")
        self.logger.info(f"📄 Log Files: {self.log_dir.absolute()}")
        self.logger.info("=" * 80)
        
    def log_shutdown(self):
        """Log application shutdown information."""
        self.logger.info("=" * 80)
        self.logger.info(f"🛑 {self.service_name.upper()} SERVICE SHUTTING DOWN")
        self.logger.info(f"📅 Timestamp: {datetime.now().isoformat()}")
        self.logger.info("=" * 80)


# Global logger instances
_loggers = {}


def get_logger(service_name: str = "concatly", log_level: str = None) -> logging.Logger:
    """
    Get or create a logger for the specified service.
    
    Args:
        service_name: Name of the service (e.g., "main", "vector_store", "confluence")
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        
    if service_name not in _loggers:
        _loggers[service_name] = ConcatlyLogger(service_name, log_level)
        
    return _loggers[service_name].get_logger()


def log_startup(service_name: str = "concatly"):
    """Log startup information for a service."""
    if service_name in _loggers:
        _loggers[service_name].log_startup()


def log_shutdown(service_name: str = "concatly"):
    """Log shutdown information for a service."""
    if service_name in _loggers:
        _loggers[service_name].log_shutdown()


# Convenience function for API request logging
def log_api_request(logger: logging.Logger, method: str, endpoint: str, 
                   organization_id: str = None, **kwargs):
    """Log API request with consistent formatting."""
    org_info = f" | Org: {organization_id}" if organization_id else ""
    extra_info = " | ".join([f"{k}: {v}" for k, v in kwargs.items()]) if kwargs else ""
    logger.info(f"🌐 API {method} {endpoint}{org_info}{' | ' + extra_info if extra_info else ''}")


def log_api_response(logger: logging.Logger, endpoint: str, status_code: int, 
                    duration_ms: float = None, **kwargs):
    """Log API response with consistent formatting."""
    duration_info = f" | {duration_ms:.1f}ms" if duration_ms else ""
    extra_info = " | ".join([f"{k}: {v}" for k, v in kwargs.items()]) if kwargs else ""
    status_emoji = "✅" if status_code < 400 else "❌"
    logger.info(f"{status_emoji} API {endpoint} → {status_code}{duration_info}{' | ' + extra_info if extra_info else ''}")


def log_error_with_context(logger: logging.Logger, error: Exception, context: str = "", **kwargs):
    """Log error with full context and traceback."""
    import traceback
    
    context_info = f" | Context: {context}" if context else ""
    extra_info = " | ".join([f"{k}: {v}" for k, v in kwargs.items()]) if kwargs else ""
    
    logger.error(f"💥 ERROR: {str(error)}{context_info}{' | ' + extra_info if extra_info else ''}")
    logger.debug(f"🔍 Full traceback:\n{traceback.format_exc()}")
