# log.py
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta

LOG_DIR = "logs"

# Define get_logger first so it's available when _logger_instance is initialized
def get_logger():
    """Returns the configured logger instance."""
    return _logger_instance

def setup_logging():
    """Sets up the logging configuration for the application."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Use only the current date as the log file name (e.g., 2025-07-08.log)
    today_date = datetime.now().strftime("%Y-%m-%d")
    log_file_path = os.path.join(LOG_DIR, f"{today_date}.log")

    logger = logging.getLogger("FuelTankDetectionLogger")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    # Daily rotating handler at midnight
    file_handler = TimedRotatingFileHandler(
        filename=log_file_path,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding='utf-8',
        utc=False
    )
    
    # IMPORTANT CHANGE HERE: Modified formatter string to remove logger name and level
    # and include your desired separator.
    formatter = logging.Formatter('%(asctime)s - ----------------------------------> %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    # Add a header for the current day's log file upon setup/start
    # This specific line will also follow the new formatter.
    logger.info(f"------------------{today_date}---------------------")

    return logger

def clean_old_logs(days_to_keep=7):
    """Deletes log files older than a specified number of days.
    This function explicitly cleans up files based on their date in the filename."""
    cutoff_time = datetime.now() - timedelta(days=days_to_keep)
    current_logger = get_logger()

    for filename in os.listdir(LOG_DIR):
        if filename.endswith(".log") or ".log." in filename:
            filepath = os.path.join(LOG_DIR, filename)
            try:
                base_name = filename.split('.')[0]
                file_date = datetime.strptime(base_name, "%Y-%m-%d")

                if file_date < cutoff_time:
                    os.remove(filepath)
                    current_logger.info(f"Deleted old log file: {filename}")
            except ValueError:
                current_logger.debug(f"Skipping non-date-formatted file in log cleanup: {filename}")
                continue
            except Exception as e:
                current_logger.error(f"Error deleting log file {filename}: {e}")

# Initialize logger and perform cleanup
_logger_instance = setup_logging()
clean_old_logs(days_to_keep=7)