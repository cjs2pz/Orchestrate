"""
Configuration management for the Orchestrate application.

Loads environemnt variables and provides them throughout the application.

"""

import os 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration  from the environemnt variables."""

    #Canvas API
    CANVAS_API_TOKEN = os.getenv("CANVAS_API_TOKEN", "")
    CANVAS_BASE_URL = os.getenv("CANVAS_BASE_URL", "https://canvas.its.virginia.edu")


    @classmethod
    def validate_canvas(cls):
        """Check if Canvas is properly configured.
        Raises:
            ValueError: If required configuration variables are missing.
        """
        if not cls.CANVAS_API_TOKEN:
            raise ValueError(
                "CANVAS_API_TOKEN is not found in .env file! \n"
                "To retreive your Canvas API token, follow these steps:\n"
                "Canvas > Account > Settings > Approved Integrations > New Access Token\n"
            )
        
config = Config()