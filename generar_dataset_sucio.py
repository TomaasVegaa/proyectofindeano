import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

# Configuración
BASE_DIR = Path(__file__).resolve().parent
SALIDA_EXCEL = BASE_DIR / "gimnasio_crudo.xlsx"
TOTAL_FILAS_BASE = 12000
CANTIDAD_DUPLICADOS = 500  # Total final ~12.500 filas

random.seed(42)
np.random.seed(42)

print("=" * 60)
print(f"GENERANDO DATASET SUCIO PARA GIMNASIO ({TOTAL_FILAS_BASE + CANTIDAD_DUPLICADOS} REGISTROS)")
print("=" * 60)

nombres = [
    "Juan", "Lucas", "Mateo", "Santiago", "Agustin", "Nicolas", "Federico", "Joaquin",
    "Franco", "Julian", "Tomas", "Martin", "Gonzalo", "Ignacio", "Facundo", "Leandro",
    "Maria", "Sofia", "Camila", "Valentina", "Martina", "Lucia", "Florencia", "Julieta",
    "Paula", "Agustina", "Milagros", "Victoria", "Micaela", "Carolina", "Daniela", "Belen"
]

apellidos = [
    "Gonzalez", "Rodriguez", "Gomez", "Fernandez", "Lopez", "Diaz", "Martinez", "Perez",
    "Romero", "Sanchez", "Alvarez", "Torres", "Ruiz", "Ramirez", "Flores", "Benitez",
    "Acosta", "Medina", "Herrera", "Suarez", "Aguirre", "Gimenez", "Gutierrez", "Pereyra",
    "Molina", "Castro", "Rojas", "Ortiz", "Silva", "Luna", "Juarez", "Cabrera"
]

# Formas con errores y variaciones para simular entrada manual
variaciones_plan = [
    ("Musculación", 0.35),
    ("musculacion", 0.08),
    ("MUSCULACION", 0.05),
    ("Musculacion ", 0.05),
    ("Pase Libre", 0.20),
    ("pase libre", 0.05),
    ("PASE LIBRE", 0.03),
    ("CrossFit", 0.08),
    ("cross fit", 0.03),
    ("crossfit", 0.02),
    ("Funcional", 0.03),
    ("funcional", 0.01),
    ("Spinning", 0.01),
    (np.nan, 0.01)  # Nulos
]

variaciones_sucursal = [
    ("Sede Centro", 0.40),
    ("centro", 0.08),
    ("CENTRO", 0.04),
    ("Sede Norte", 0.20),
    ("norte", 0.05),
    ("NORTE", 0.02),
    ("Sede Sur", 0.12),
    ("sur", 0.03),
    ("Sede Oeste", 0.04),
    (np.nan, 0.02)
]

variaciones_pago = [
    ("Efectivo", 0.30),
    ("efectivo", 0.08),
    ("EFECTIVO", 0.04),
    ("efvo", 0.03),
    ("Mercado Pago", 0.25),
    ("mercado pago", 0.08),
    ("MP", 0.05),
    ("mercadopago", 0.02),
    ("Transferencia", 0.07),
    ("transferencia", 0.02),
    ("Tarjeta Débito", 0.03),
    ("debito", 0.01),
    ("Tarjeta Crédito", 0.01),
    (np.nan, 0.01)
]

variaciones_estado = [
    ("Activo", 0.70),
    ("activo", 0.10),
    ("ACTIVO", 0.05),
    ("Moroso", 0.05),
    ("moroso", 0.03),
    ("Inactivo", 0.04),
    ("baja", 0.02),
    (np.nan, 0.01)
]

def elegir_con_prob(lista_tuplas):
    valores, probs = zip(*lista_tuplas)
    # Normalizar probs
    probs = np.array(probs)
    probs /= probs.sum()
    return np.random.choice(valores, p=probs)

# Precios base por plan
precios_plan = {
    "Musculación": 18000,
    "Pase Libre": 25000,
    "CrossFit": 22000,
    "Funcional": 16000,
    "Spinning": 15000
}

def generar_nombre_sucio(nom, ape):
    tipo = random.random()
    nombre_completo = f"{nom} {ape}"
    if tipo < 0.15:
        # Espacios locos
        return f"  {nombre_completo}   "
    elif tipo < 0.25:
        # Todo mayúsculas
        return nombre_completo.upper()
    elif tipo < 0.35:
        # Todo minúsculas
        return nombre_completo.lower()
    elif tipo < 0.38:
        # Mezcla loca de mayúsculas/minúsculas
        return "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(nombre_completo))
    elif tipo < 0.40:
        return np.nan
    return nombre_completo

def generar_dni_sucio(numero):
    tipo = random.random()
    str_num = str(numero)
    if tipo < 0.15:
        # Con puntos "40.123.456"
        return f"{str_num[:2]}.{str_num[2:5]}.{str_num[5:]}"
    elif tipo < 0.22:
        # Con espacios "40 123 456"
        return f"{str_num[:2]} {str_num[2:5]} {str_num[5:]}"
    elif tipo < 0.27:
        # Con prefijo "DNI 40123456"
        return f"DNI {str_num}"
    elif tipo < 0.29:
        # Muy corto o inválido
        return str_num[:4]
    elif tipo < 0.31:
        return np.nan
    return str_num

def generar_fecha_sucia(fecha_obj):
    tipo = random.random()
    if tipo < 0.10:
        # Formato DD/MM/YYYY
        return fecha_obj.strftime("%d/%m/%Y")
    elif tipo < 0.18:
        # Formato YYYY/MM/DD con barras
        return fecha_obj.strftime("%Y/%m/%d")
    elif tipo < 0.23:
        # Formato texto
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        return f"{fecha_obj.day} {meses[fecha_obj.month - 1]} {fecha_obj.year}"
    elif tipo < 0.25:
        # Fecha fuera de rango (ej. año 2099 o año 1920)
        return "1920-01-01" if random.random() < 0.5 else "2099-12-31"
    elif tipo < 0.28:
        return np.nan
    # Formato estándar ISO YYYY-MM-DD
    return fecha_obj.strftime("%Y-%m-%d")

def generar_edad_sucia():
    tipo = random.random()
    if tipo < 0.03:
        # Negativa
        return random.randint(-15, -1)
    elif tipo < 0.06:
        # Imposiblemente alta
        return random.randint(125, 999)
    elif tipo < 0.08:
        # Cero
        return 0
    elif tipo < 0.11:
        # Nulo
        return np.nan
    elif tipo < 0.13:
        # En texto
        return random.choice(["veinticinco", "treinta", "18 años", "N/A"])
    # Rango normal: 15 a 65
    return random.randint(16, 68)

def generar_monto_sucio(plan_elegido):
    # Detectar el precio de referencia
    plan_limpio = "Musculación"
    if pd.notna(plan_elegido):
        p_str = str(plan_elegido).lower()
        for k in precios_plan:
            if k.lower() in p_str:
                plan_limpio = k
                break
    precio_base = precios_plan.get(plan_limpio, 18000)

    # Añadir variación de +/- 15% (descuentos, promos)
    monto_real = round(precio_base * random.uniform(0.85, 1.15), -2)

    tipo = random.random()
    if tipo < 0.08:
        # Con signo peso y puntos como texto
        return f"$ {monto_real:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    elif tipo < 0.14:
        # Formato texto "$ 20000"
        return f"$ {int(monto_real)}"
    elif tipo < 0.17:
        # Negativo
        return -monto_real
    elif tipo < 0.20:
        # Cero
        return 0.0
    elif tipo < 0.23:
        # Nulo
        return np.nan
    elif tipo < 0.24:
        # Valor ridículo
        return 9999999.0
    return float(monto_real)

print("1. Creando registros base...")
fecha_inicio = datetime(2024, 1, 1)
registros = []

# Creamos una base fija de ~3000 socios que van pagando mes a mes para que sea súper realista
pool_socios = []
for i in range(3500):
    nom = random.choice(nombres)
    ape = random.choice(apellidos)
    dni_base = random.randint(25000000, 48000000)
    pool_socios.append({
        "nom": nom,
        "ape": ape,
        "dni": dni_base
    })

for i in range(1, TOTAL_FILAS_BASE + 1):
    socio_info = random.choice(pool_socios)
    delta_dias = random.randint(0, 365 + 180)  # ~1.5 años de datos
    fecha_pago = fecha_inicio + timedelta(days=delta_dias)

    plan = elegir_con_prob(variaciones_plan)
    sucursal = elegir_con_prob(variaciones_sucursal)
    forma_pago = elegir_con_prob(variaciones_pago)
    estado = elegir_con_prob(variaciones_estado)
    monto = generar_monto_sucio(plan)
    edad = generar_edad_sucia()
    nombre = generar_nombre_sucio(socio_info["nom"], socio_info["ape"])
    dni = generar_dni_sucio(socio_info["dni"])
    fecha_str = generar_fecha_sucia(fecha_pago)
    nro_factura = f"REC-{2024}-{i:06d}" if random.random() > 0.04 else np.nan

    registros.append({
        "Nro_Recibo": nro_factura,
        "Fecha_Pago": fecha_str,
        "DNI_Socio": dni,
        "Nombre_Completo": nombre,
        "Edad": edad,
        "Plan_Membresia": plan,
        "Sucursal": sucursal,
        "Monto_Pagado": monto,
        "Forma_Pago": forma_pago,
        "Estado_Membresia": estado
    })

df = pd.DataFrame(registros)

# 2. Inyectar duplicados exactos
print(f"2. Inyectando {CANTIDAD_DUPLICADOS} filas duplicadas exactas...")
indices_para_duplicar = np.random.choice(df.index, size=CANTIDAD_DUPLICADOS, replace=False)
duplicados = df.loc[indices_para_duplicar].copy()

df_final = pd.concat([df, duplicados], ignore_index=True)

# Mezclar un poco las filas para que los duplicados no queden todos al final
df_final = df_final.sample(frac=1, random_state=42).reset_index(drop=True)

print(f"3. Guardando archivo Excel en: {SALIDA_EXCEL}")
with pd.ExcelWriter(SALIDA_EXCEL, engine="openpyxl") as writer:
    df_final.to_excel(writer, sheet_name="Cobros_Gimnasio_Crudo", index=False)

print("\n" + "=" * 60)
print("¡DATASET SUCIO GENERADO EXITOSAMENTE!")
print("=" * 60)
print(f"Total de registros generados: {len(df_final)}")
print(f"Duplicados exactos incluidos: {df_final.duplicated().sum()}")
print(f"Celdas vacías totales (NaN): {df_final.isna().sum().sum()}")
print("\nResumen de celdas vacías por columna:")
for col, cant in df_final.isna().sum().items():
    print(f" - {col:20}: {cant} nulos ({cant/len(df_final)*100:.1f}%)")
print("=" * 60)

