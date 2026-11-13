import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

BASE_DIR = Path(__file__).resolve().parent

# ============================================================
# INSTANCIA FASTAPI
# ============================================================
app = FastAPI(
    title="Gimnasio Fitness Pro - API & Dashboard",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Intentar importar pymysql de manera segura
try:
    import pymysql
    from pymysql.cursors import DictCursor
except Exception:
    pymysql = None

MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "bd_gimnasio",
    "connect_timeout": 2
}

def get_db():
    if not pymysql:
        return None
    try:
        return pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
    except Exception:
        return None

# ============================================================
# DATOS DE RESPALDO (DEMO)
# ============================================================
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

def cargar_demo_records():
    for ruta in [BASE_DIR / "cobros_demo.json", BASE_DIR.parent / "cobros_demo.json"]:
        if ruta.exists():
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return []

# ============================================================
# RUTAS HTML
# ============================================================
@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def index_page():
    rutas = [
        BASE_DIR / "index.html",
        BASE_DIR.parent / "index.html",
        BASE_DIR.parent / "dashboard.html"
    ]
    for r in rutas:
        if r.exists():
            try:
                return HTMLResponse(content=r.read_text(encoding="utf-8"))
            except Exception:
                pass
    return HTMLResponse(content="<h2>Fitness Pro Analytics Activo</h2>")

# ============================================================
# ENDPOINTS JSON
# ============================================================
@app.get("/kpis/resumen")
@app.get("/api/kpis/resumen")
def resumen_kpis():
    conn = get_db()
    if not conn:
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
    except Exception:
        return DEMO_KPIS
    finally:
        try:
            conn.close()
        except Exception:
            pass

@app.get("/cobros/powerbi")
@app.get("/api/cobros/powerbi")
def obtener_cobros_powerbi():
    conn = get_db()
    if not conn:
        return cargar_demo_records()
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
    except Exception:
        return cargar_demo_records()
    finally:
        try:
            conn.close()
        except Exception:
            pass

@app.get("/cobros")
@app.get("/api/cobros")
def listar_cobros(
    plan: Optional[str] = Query(None),
    sucursal: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=2000),
    offset: int = Query(0, ge=0)
):
    conn = get_db()
    if not conn:
        registros = cargar_demo_records()
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
    except Exception:
        return cargar_demo_records()
    finally:
        try:
            conn.close()
        except Exception:
            pass
