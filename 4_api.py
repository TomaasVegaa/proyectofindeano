import json
from datetime import date
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import pymysql
from pymysql.cursors import DictCursor
import uvicorn

BASE_DIR = Path(__file__).resolve().parent

# ============================================================
# INSTANCIA DE FASTAPI
# ============================================================
app = FastAPI(
    title="API de Gestión y Analítica - Gimnasio Fitness Pro",
    description="API REST de alto rendimiento para analítica en tiempo real.",
    version="2.0.0"
)

# CORS habilitado para Vercel y clientes externos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración local de MySQL
MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "bd_gimnasio",
    "cursorclass": DictCursor,
    "connect_timeout": 2
}

def get_db_connection():
    try:
        return pymysql.connect(**MYSQL_CONFIG)
    except Exception:
        return None

# Cargar datos de respaldo para cuando esté desplegado en la nube (Vercel)
def get_demo_records():
    demo_file = BASE_DIR / "cobros_demo.json"
    if demo_file.exists():
        with open(demo_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

DEMO_KPIS = {
    "metricas_generales": {
        "total_transacciones": 12000,
        "total_socios_unicos": 3826,
        "facturacion_total": 242002400.0,
        "ticket_promedio": 20166.87,
        "edad_promedio": 41.9
    },
    "recaudacion_por_plan": [
        {"plan_membresia": "Musculación", "total_recaudado": 110500000.0, "cantidad_cobros": 5480, "porcentaje_participacion": 45.67},
        {"plan_membresia": "Pase Libre", "total_recaudado": 72400000.0, "cantidad_cobros": 2896, "porcentaje_participacion": 24.13},
        {"plan_membresia": "CrossFit", "total_recaudado": 38200000.0, "cantidad_cobros": 1736, "porcentaje_participacion": 14.47},
        {"plan_membresia": "Funcional", "total_recaudado": 14100000.0, "cantidad_cobros": 881, "porcentaje_participacion": 7.34},
        {"plan_membresia": "Spinning", "total_recaudado": 6802400.0, "cantidad_cobros": 453, "porcentaje_participacion": 3.78}
    ],
    "recaudacion_por_sucursal": [
        {"sucursal": "Sede Centro", "total_recaudado": 125000000.0, "cantidad_cobros": 6200},
        {"sucursal": "Sede Norte", "total_recaudado": 64000000.0, "cantidad_cobros": 3173},
        {"sucursal": "Sede Sur", "total_recaudado": 37000000.0, "cantidad_cobros": 1834},
        {"sucursal": "Sede Oeste", "total_recaudado": 16002400.0, "cantidad_cobros": 793}
    ],
    "recaudacion_por_medio_pago": [
        {"forma_pago": "Efectivo", "total_recaudado": 105000000.0, "cantidad_cobros": 5206},
        {"forma_pago": "Mercado Pago", "total_recaudado": 89000000.0, "cantidad_cobros": 4413},
        {"forma_pago": "Transferencia", "total_recaudado": 28000000.0, "cantidad_cobros": 1388},
        {"forma_pago": "Tarjeta Débito", "total_recaudado": 12000000.0, "cantidad_cobros": 595},
        {"forma_pago": "Tarjeta Crédito", "total_recaudado": 8002400.0, "cantidad_cobros": 398}
    ]
}

# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/", response_class=HTMLResponse, summary="Dashboard Web Principal")
def ruta_raiz():
    """Entrega el Dashboard web interactivo directamente en la raíz."""
    html_file = BASE_DIR / "index.html"
    if not html_file.exists():
        html_file = BASE_DIR / "dashboard.html"
    if html_file.exists():
        return FileResponse(html_file)
    return HTMLResponse("<h1>Fitness Pro Analytics en línea</h1>")

@app.get("/dashboard", response_class=HTMLResponse, summary="Dashboard Web Analítico")
def ver_dashboard():
    return ruta_raiz()

@app.get("/kpis/resumen", summary="Resumen ejecutivo y KPIs")
def resumen_kpis():
    conn = get_db_connection()
    if not conn:
        # Modo fallback en la nube (Vercel)
        return DEMO_KPIS
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_transacciones,
                    COUNT(DISTINCT dni_socio) as total_socios_unicos,
                    CAST(SUM(monto_pagado) AS DOUBLE) as facturacion_total,
                    CAST(AVG(monto_pagado) AS DOUBLE) as ticket_promedio,
                    AVG(edad) as edad_promedio
                FROM cobros_gimnasio
            """)
            generales = cursor.fetchone()

            cursor.execute("""
                SELECT 
                    plan_membresia,
                    COUNT(*) as cantidad_cobros,
                    CAST(SUM(monto_pagado) AS DOUBLE) as total_recaudado,
                    ROUND((COUNT(*) / 12000.0) * 100, 2) as porcentaje_participacion
                FROM cobros_gimnasio
                GROUP BY plan_membresia
                ORDER BY total_recaudado DESC
            """)
            por_plan = cursor.fetchall()

            cursor.execute("""
                SELECT 
                    sucursal,
                    COUNT(*) as cantidad_cobros,
                    CAST(SUM(monto_pagado) AS DOUBLE) as total_recaudado
                FROM cobros_gimnasio
                GROUP BY sucursal
                ORDER BY total_recaudado DESC
            """)
            por_sucursal = cursor.fetchall()

            cursor.execute("""
                SELECT 
                    forma_pago,
                    COUNT(*) as cantidad_cobros,
                    CAST(SUM(monto_pagado) AS DOUBLE) as total_recaudado
                FROM cobros_gimnasio
                GROUP BY forma_pago
                ORDER BY total_recaudado DESC
            """)
            por_pago = cursor.fetchall()

            return {
                "metricas_generales": generales,
                "recaudacion_por_plan": por_plan,
                "recaudacion_por_sucursal": por_sucursal,
                "recaudacion_por_medio_pago": por_pago
            }
    finally:
        conn.close()

@app.get("/cobros/powerbi", summary="Endpoint para Power BI y analítica")
def obtener_cobros_powerbi():
    conn = get_db_connection()
    if not conn:
        return get_demo_records()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, nro_recibo, fecha_pago, dni_socio, nombre_socio,
                    edad, plan_membresia, sucursal, 
                    CAST(monto_pagado AS DOUBLE) AS monto_pagado,
                    forma_pago, estado_membresia
                FROM cobros_gimnasio
                ORDER BY id ASC
            """)
            return cursor.fetchall()
    finally:
        conn.close()

@app.get("/cobros", summary="Listar cobros con filtros")
def listar_cobros(
    plan: Optional[str] = Query(None),
    sucursal: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=2000),
    offset: int = Query(0, ge=0)
):
    conn = get_db_connection()
    if not conn:
        registros = get_demo_records()
        if plan:
            registros = [r for r in registros if r.get("plan_membresia") == plan]
        if sucursal:
            registros = [r for r in registros if r.get("sucursal") == sucursal]
        return registros[offset:offset + limit]

    try:
        filtros = []
        parametros = []
        if plan:
            filtros.append("plan_membresia = %s")
            parametros.append(plan)
        if sucursal:
            filtros.append("sucursal = %s")
            parametros.append(sucursal)

        where = " WHERE " + " AND ".join(filtros) if filtros else ""
        sql = f"""
            SELECT 
                id, nro_recibo, fecha_pago, dni_socio, nombre_socio,
                edad, plan_membresia, sucursal,
                CAST(monto_pagado AS DOUBLE) AS monto_pagado,
                forma_pago, estado_membresia
            FROM cobros_gimnasio
            {where}
            ORDER BY id ASC
            LIMIT %s OFFSET %s
        """
        parametros.extend([limit, offset])
        with conn.cursor() as cursor:
            cursor.execute(sql, tuple(parametros))
            return cursor.fetchall()
    finally:
        conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
