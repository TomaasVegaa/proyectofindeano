import sys
from pathlib import Path

# Agregar directorio raíz para importar main.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import app
