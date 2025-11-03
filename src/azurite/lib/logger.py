import logging

class LoggerFormatter(logging.Formatter):

    grey = "\x1b[38;21m"
    green = "\033[92m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

class Logger:
    
    @staticmethod
    def get_logger(logger_name="logging", level=logging.DEBUG, colour_format=True):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(level)
        ch = logging.StreamHandler()
        if colour_format:
            ch.setFormatter(LoggerFormatter())
        else:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)')
            ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger
