from PySide6.QtWidgets import QMessageBox

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIUtils:
    @staticmethod
    def show_not_available(parent):
        QMessageBox.warning(
            parent,
            "OpenAI Not Available",
            "The OpenAI library is not installed. Please run 'pip install openai' to use this feature.",
        )

    @staticmethod
    def is_available():
        return OPENAI_AVAILABLE

    @staticmethod
    def getOpenAI():
        if OPENAI_AVAILABLE:
            return OpenAI(
                api_key="test",
                base_url="http://localhost:17173",
            )
        return None
