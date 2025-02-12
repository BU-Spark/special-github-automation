import logging
import sys
from typing import Optional

class SparkLogger:
    _loggers = {}

    def __init__(self, name: str, level: int = logging.DEBUG, output: bool = True, persist: bool = False):
        """
        Initialize the SparkLogger.

        Args:
            name (str): The name of the logger.
            level (int, optional): The minimum log level. Defaults to logging.DEBUG.
            output (bool, optional): Whether to log to the console. Defaults to True.
            persist (bool, optional): Whether to log to a file. Defaults to False.
        """
        self.name = name

        if name in SparkLogger._loggers:
            self.logger = SparkLogger._loggers[name]
            self.logger.setLevel(level)
        else:
            self.logger = logging.getLogger(name)
            self.logger.setLevel(level)

            
            lfmt = f'[{name.upper()}][%(asctime)s][%(levelname)s] --- %(message)s'
            dfmt = '%Y-%m-%d %H:%M:%S'
            formatter = logging.Formatter(fmt=lfmt, datefmt=dfmt)

            if output:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(level)
                console_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)

            if persist:
                file_handler = logging.FileHandler(f"./logs/{name}.log")
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

            self.logger.propagate = False

            SparkLogger._loggers[name] = self.logger

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def critical(self, message: str):
        self.logger.critical(message)

    def change(self, level: int):
        """
        Set a new log level for the logger and all its handlers.

        Args:
            level (int): The new logging level (e.g., logging.INFO).
        """
        self.logger.setLevel(level)
        for handler in self.logger.handlers: handler.setLevel(level)
