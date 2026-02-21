import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MAX_ATTEMPTS = 6
WORD_LENGTH = 6
