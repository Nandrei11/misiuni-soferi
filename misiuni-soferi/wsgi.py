import sys
import os

# Adaugă directorul curent la Python path
sys.path.append(os.path.dirname(__file__))

from main import app

if __name__ == "__main__":
    app.run()
