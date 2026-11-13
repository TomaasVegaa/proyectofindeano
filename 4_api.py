from datetime import date
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
import pymysql
from pymysql.cursors import DictCursor
from pydantic import BaseModel
import uvicorn

# ============================================================
# INSTANCIA DE FASTAPI Y METADATOS
# ============================================================
app = FastAPI(
    title="API de Gestión y Analítica - Gimnasio Fitness Pro",
    description=(
        "API REST de alto rendimiento que conecta la base de datos MySQL "
        "con Power BI y dashboards ejecutivos."
    ),
    version="2.0.0"
)

# Habilitar CORS para permitir consumo desde navegadores o clientes externos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de conexión MySQL
MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "bd_gimnasio",
    "cursorclass": DictCursor,
    "connect_timeout": 5
}

def get_db_connection():
    try:
        return pymysql.connect(**MYSQL_CONFIG)
    except pymysql.MySQLError as e:
        raise HTTPException(status_code=500, detail=f"Error conectando a MySQL: {e}")

# ============================================================
# MODELOS DE RESPUESTA (PYDANTIC)
# ============================================================
class Cobro(BaseModel):
    id: int
    nro_recibo: str
    fecha_pago: date
    dni_socio: str
    nombre_socio: str
    edad: int
    plan_membresia: str
    sucursal: str
    monto_pagado: float
    forma_pago: str
    estado_membresia: str

# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/dashboard", response_class=HTMLResponse, summary="Dashboard Web Analítico")
def ver_dashboard():
    """Sirve el tablero web interactivo completo en el navegador."""
    html_file = Path(__file__).resolve().parent / "dashboard.html"
    if html_file.exists():
        return FileResponse(html_file)
    return HTMLResponse("<h2>Error: No se encontró dashboard.html</h2>", status_code=404)

@app.get("/", summary="Ruta raíz informativa")
def inicio():
    return {
        "sistema": "Gimnasio Fitness Pro - API de Datos",
        "estado": "En línea",
        "tablero_web": "/dashboard",
        "documentacion_swagger": "/docs",
        "endpoint_powerbi": "/cobros/powerbi",
        "endpoint_resumen_kpis": "/kpis/resumen"
    }

@app.get("/cobros/powerbi", summary="Endpoint optimizado para Power BI")
def obtener_cobros_powerbi():
    """
    Retorna la totalidad de los registros limpios en formato JSON plano,
    ideal para ser consumido directamente por Power Query / Power BI Desktop.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    id, nro_recibo, fecha_pago, dni_socio, nombre_socio,
                    edad, plan_membresia, sucursal, 
                    CAST(monto_pagado AS DOUBLE) AS monto_pagado,
                    forma_pago, estado_membresia
                FROM cobros_gimnasio
                ORDER BY id ASC
            """
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conn.close()

@app.get("/cobros", summary="Consultar cobros con filtros y paginación")
def listar_cobros(
    fecha_desde: Optional[date] = Query(None, description="Fecha mínima (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha máxima (YYYY-MM-DD)"),
    plan: Optional[str] = Query(None, description="Filtrar por plan (ej: Musculación)"),
    sucursal: Optional[str] = Query(None, description="Filtrar por sucursal (ej: Sede Centro)"),
    limit: int = Query(100, ge=1, le=2000, description="Límite de registros"),
    offset: int = Query(0, ge=0, description="Desplazamiento / paginación")
):
    """Permite consultas personalizadas con filtros dinámicos."""
    conn = get_db_connection()
    try:
        filtros = []
        parametros = []

        if fecha_desde:
            filtros.append("fecha_pago >= %s")
            parametros.append(fecha_desde)
        if fecha_hasta:
            filtros.append("fecha_pago <= %s")
            parametros.append(fecha_hasta)
        if plan:
            filtros.append("plan_membresia = %s")
            parametros.append(plan)
        if sucursal:
            filtros.append("sucursal = %s")
            parametros.append(sucursal)

        where_clause = " WHERE " + " AND ".join(filtros) if filtros else ""
        sql = f"""
            SELECT 
                id, nro_recibo, fecha_pago, dni_socio, nombre_socio,
                edad, plan_membresia, sucursal,
                CAST(monto_pagado AS DOUBLE) AS monto_pagado,
                forma_pago, estado_membresia
            FROM cobros_gimnasio
            {where_clause}
            ORDER BY id ASC
            LIMIT %s OFFSET %s
        """
        parametros.extend([limit, offset])

        with conn.cursor() as cursor:
            cursor.execute(sql, tuple(parametros))
            return cursor.fetchall()
    finally:
        conn.close()

@app.get("/kpis/resumen", summary="Resumen ejecutivo y KPIs del gimnasio")
def resumen_kpis():
    """Devuelve métricas clave agregadas para toma de decisiones rápidas."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Totales generales
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

            # Desglose por plan
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

            # Desglose por sucursal
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

            # Desglose por forma de pago
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

if __name__ == "__main__":
    print("=" * 65)
    print("INICIANDO SERVIDOR FASTAPI PARA GIMNASIO FITNESS PRO")
    print("=" * 65)
    print("-> API activa en: http://127.0.0.1:8000")
    print("-> Documentación interactiva (Swagger): http://127.0.0.1:8000/docs")
    print("-> Endpoint para Power BI: http://127.0.0.1:8000/cobros/powerbi")
    print("-> Endpoint de KPIs ejecutivos: http://127.0.0.1:8000/kpis/resumen")
    print("=" * 65)
    uvicorn.run(app, host="127.0.0.1", port=8000)

