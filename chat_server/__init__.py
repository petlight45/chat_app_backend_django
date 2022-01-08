import os
from pathlib import Path
from dotenv import load_dotenv

print(os.getcwd())
# raise ZeroDivisionError
load_dotenv(os.path.join(os.getcwd(), "env", ".env"))