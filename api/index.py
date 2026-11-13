import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Fitness Pro API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    demo_file = BASE_DIR / "cobros_demo.json"
    if demo_file.exists():
        try:
            with open(demo_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

@app.get("/api/kpis/resumen")
@app.get("/kpis/resumen")
def resumen_kpis():
    return DEMO_KPIS

@app.get("/api/cobros")
@app.get("/cobros")
def listar_cobros(
    plan: Optional[str] = Query(None),
    sucursal: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=2000),
    offset: int = Query(0, ge=0)
):
    registros = cargar_demo_records()
    if plan:
        registros = [r for r in registros if r.get("plan_membresia") == plan]
    if sucursal:
        registros = [r for r in registros if r.get("sucursal") == sucursal]
    return registros[offset:offset + limit]

@app.get("/api/cobros/powerbi")
@app.get("/cobros/powerbi")
def obtener_cobros_powerbi():
    return cargar_demo_records()
