import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "veritabani.db")
SECRET_KEY = os.getenv("SECRET_KEY", "firin-yonetim-gizli-anahtar")
