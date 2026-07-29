from datetime import datetime


class Logger:

    @staticmethod
    def _log(level: str, message: str):

        now = datetime.now().strftime("%H:%M:%S")

        print(f"[{now}] [{level}] {message}")

    @classmethod
    def info(cls, message: str):
        cls._log("INFO", message)

    @classmethod
    def success(cls, message: str):
        cls._log(" OK ", message)

    @classmethod
    def warning(cls, message: str):
        cls._log("WARN", message)

    @classmethod
    def error(cls, message: str):
        cls._log("FAIL", message)