import subprocess
import sys
import time
from pathlib import Path
import uvicorn
import importlib

BASE_DIR = Path(__file__).resolve().parent

def ejecutar_script(script_path):
    print(f"\n>>> Ejecutando {script_path.name}...")
    resultado = subprocess.run([sys.executable, str(script_path)], capture_output=False)
    if resultado.returncode != 0:
        print(f"Error al ejecutar {script_path.name}")
        sys.exit(1)

def main():
    print("=" * 70)
    print("          SISTEMA DE DATOS Y ANALÍTICA - GIMNASIO FITNESS PRO")
    print("=" * 70)
    
    # 1. Limpieza
    ejecutar_script(BASE_DIR / "2_limpieza.py")
    
    # 2. Carga a MySQL
    ejecutar_script(BASE_DIR / "3_carga_mysql.py")
    
    # 3. Levantar API FastAPI
    print("\n" + "=" * 70)
    print("3. LEVANTANDO SERVIDOR API (FASTAPI + UVICORN)")
    print("=" * 70)
    print("API lista para conectar con Power BI en:")
    print("  -> http://127.0.0.1:8000/cobros/powerbi")
    print("\nDocumentación interactiva disponible en:")
    print("  -> http://127.0.0.1:8000/docs")
    print("\nPresiona CTRL + C para detener el servidor cuando termines.\n")

    sys.path.append(str(BASE_DIR))
    api_module = importlib.import_module("4_api")
    uvicorn.run(api_module.app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()

