"""Configuration module for environment variables."""

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI Configuration
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "deepseek-r1-distill-llama-8b")
OPENAI_API_BASE_URL = os.getenv("OPENAI_API_BASE_URL", "http://localhost:1234/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "foobar")
