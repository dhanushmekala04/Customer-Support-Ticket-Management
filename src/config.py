"""
Configuration settings for the multi-agent ticket management system.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for the application."""

    # Groq Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL",)
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))

  
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    # Escalation Thresholds
    ESCALATION_KEYWORDS = [
        "lawsuit",
        "lawyer",
        "attorney",
        "sue",
        "legal action",
        "urgent",
        "critical",
        "angry",
        "frustrated",
        "unacceptable",
    ]

    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.7))

    # FAQ Configuration
   # MongoDB Configuration
    MONGO_URI = os.getenv("MONGO_URI")

    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

    FAQ_COLLECTION = os.getenv("FAQ_COLLECTION")
    TICKETS_COLLECTION = os.getenv("TICKETS_COLLECTION")

   
    FAQ_SIMILARITY_THRESHOLD = float(os.getenv("FAQ_SIMILARITY_THRESHOLD", "0.75"))

    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))

    # Ticket Settings
    TICKET_ID_PREFIX = os.getenv("TICKET_ID_PREFIX", "TKT")
    MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "50"))

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required. Please set it in .env file")
        return True


# Create a singleton config instance
config = Config()
