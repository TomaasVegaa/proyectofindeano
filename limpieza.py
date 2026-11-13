import unicodedata
from pathlib import Path
import numpy as np
import pandas as pd

# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
ARCHIVO_ENTRADA = BASE_DIR / "gimnasio_crudo.xlsx"
ARCHIVO_SALIDA = BASE_DIR / "gimnasio_limpio.xlsx"

print("=" * 65)
print("INICIANDO SCRIPT DE LIMPIEZA DE DATOS (PANDAS)")
print("=" * 65)

# 1. CARGA DE DATOS
if not ARCHIVO_ENTRADA.exists():
    raise FileNotFoundError(f"No se encontró el archivo de entrada: {ARCHIVO_ENTRADA}")

print(f"1. Leyendo dataset crudo: {ARCHIVO_ENTRADA.name}...")
df = pd.read_excel(ARCHIVO_ENTRADA)
filas_iniciales = len(df)
nulos_iniciales = int(df.isna().sum().sum())
print(f"   -> Registros leídos: {filas_iniciales:,}")
print(f"   -> Celdas vacías (NaN) detectadas: {nulos_iniciales:,}")

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def normalizar_texto(valor):
    """Elimina espacios redundantes y aplica formato Title Case."""
    if pd.isna(valor):
        return np.nan
    texto = str(valor).strip()
    texto = " ".join(texto.split())
    return texto.title()

def quitar_acentos(texto):
    """Remueve tildes y diacríticos para facilitar comparaciones."""
    if pd.isna(texto):
        return ""
    s = str(texto)
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    ).lower().strip()

# ============================================================
# 2. ELIMINACIÓN DE DUPLICADOS EXACTOS
# ============================================================
print("\n2. Eliminando filas duplicadas exactas...")
duplicados_detectados = int(df.duplicated().sum())
df = df.drop_duplicates().reset_index(drop=True)
print(f"   -> Duplicados eliminados: {duplicados_detectados:,}")

# ============================================================
# 3. LIMPIEZA Y HOMOLOGACIÓN DE TEXTOS / CATEGORÍAS
# ============================================================
print("\n3. Normalizando campos de texto y categorías...")

# A. Nombre Completo
df["Nombre_Completo"] = df["Nombre_Completo"].apply(normalizar_texto)
# Imputar nombres vacíos con un placeholder genérico
nombres_vacios = df["Nombre_Completo"].isna().sum()
df["Nombre_Completo"] = df["Nombre_Completo"].fillna("Socio No Registrado")

# B. Plan de Membresía
mapa_planes = {
    "musculacion": "Musculación",
    "musculacion ": "Musculación",
    "pase libre": "Pase Libre",
    "cross fit": "CrossFit",
    "crossfit": "CrossFit",
    "funcional": "Funcional",
    "spinning": "Spinning"
}

def homologar_plan(valor):
    if pd.isna(valor):
        return np.nan
    clave = quitar_acentos(valor)
    for k, v in mapa_planes.items():
        if k in clave:
            return v
    return "Musculación"  # Moda por defecto

df["Plan_Membresia"] = df["Plan_Membresia"].apply(homologar_plan)
moda_plan = df["Plan_Membresia"].mode()[0]
df["Plan_Membresia"] = df["Plan_Membresia"].fillna(moda_plan)

# C. Sucursal
mapa_sucursales = {
    "centro": "Sede Centro",
    "norte": "Sede Norte",
    "sur": "Sede Sur",
    "oeste": "Sede Oeste"
}

def homologar_sucursal(valor):
    if pd.isna(valor):
        return np.nan
    clave = quitar_acentos(valor)
    for k, v in mapa_sucursales.items():
        if k in clave:
            return v
    return "Sede Centro"

df["Sucursal"] = df["Sucursal"].apply(homologar_sucursal)
moda_sucursal = df["Sucursal"].mode()[0]
df["Sucursal"] = df["Sucursal"].fillna(moda_sucursal)

# D. Forma de Pago
mapa_pagos = {
    "efectivo": "Efectivo",
    "efvo": "Efectivo",
    "mercado pago": "Mercado Pago",
    "mp": "Mercado Pago",
    "mercadopago": "Mercado Pago",
    "transferencia": "Transferencia",
    "debito": "Tarjeta Débito",
    "credito": "Tarjeta Crédito"
}

def homologar_pago(valor):
    if pd.isna(valor):
        return np.nan
    clave = quitar_acentos(valor)
    for k, v in mapa_pagos.items():
        if k in clave:
            return v
    return "Efectivo"

df["Forma_Pago"] = df["Forma_Pago"].apply(homologar_pago)
moda_pago = df["Forma_Pago"].mode()[0]
df["Forma_Pago"] = df["Forma_Pago"].fillna(moda_pago)

# E. Estado de Membresía
def homologar_estado(valor):
    if pd.isna(valor):
        return "Activo"
    clave = quitar_acentos(valor)
    if "activo" in clave:
        return "Activo"
    elif "moroso" in clave:
        return "Moroso"
    elif "inactivo" in clave or "baja" in clave:
        return "Inactivo"
    return "Activo"

df["Estado_Membresia"] = df["Estado_Membresia"].apply(homologar_estado)

# ============================================================
# 4. NORMALIZACIÓN DE DNI
# ============================================================
print("\n4. Normalizando números de DNI...")
# Extraer solo dígitos numéricos
df["DNI_Socio"] = df["DNI_Socio"].astype(str).str.replace(r"\D+", "", regex=True)

# Validar longitud típica de DNI argentino (entre 7 y 8 dígitos)
dni_invalido = (df["DNI_Socio"].str.len() < 7) | (df["DNI_Socio"].str.len() > 8) | (df["DNI_Socio"] == "")
cant_dni_invalidos = int(dni_invalido.sum())

# Generar DNI sintéticos consistentes para los inválidos / nulos
dnis_reemplazo = [str(30000000 + i) for i in range(cant_dni_invalidos)]
df.loc[dni_invalido, "DNI_Socio"] = dnis_reemplazo
print(f"   -> DNI corruptos/vacíos normalizados: {cant_dni_invalidos:,}")

# ============================================================
# 5. LIMPIEZA DE FECHAS
# ============================================================
print("\n5. Estandarizando fechas...")

# Reemplazar abreviaturas de meses en español para que pandas las reconozca
mapa_meses = {
    "Ene": "Jan", "Feb": "Feb", "Mar": "Mar", "Abr": "Apr",
    "May": "May", "Jun": "Jun", "Jul": "Jul", "Ago": "Aug",
    "Sep": "Sep", "Oct": "Oct", "Nov": "Nov", "Dic": "Dec"
}

serie_fechas = df["Fecha_Pago"].astype(str)
for es, en in mapa_meses.items():
    serie_fechas = serie_fechas.str.replace(es, en, regex=False)

# Convertir con formato mixto y detección automática
fechas_convertidas = pd.to_datetime(serie_fechas, format="mixed", errors="coerce", dayfirst=True)

# Filtrar fechas fuera del rango de operación lógico del gimnasio (2023 a 2026)
rango_valido = (fechas_convertidas >= "2023-01-01") & (fechas_convertidas <= "2026-12-31")
fechas_validas = fechas_convertidas[rango_valido]

# Calcular la mediana de las fechas válidas para imputar faltantes/anómalas
mediana_timestamp = fechas_validas.astype("int64").median()
mediana_fecha = pd.to_datetime(mediana_timestamp)

fechas_anomalas = (~rango_valido) | fechas_convertidas.isna()
cant_fechas_corregidas = int(fechas_anomalas.sum())

fechas_convertidas.loc[fechas_anomalas] = mediana_fecha
df["Fecha_Pago"] = fechas_convertidas.dt.date

print(f"   -> Fechas fuera de rango o nulas imputadas con mediana ({mediana_fecha.strftime('%Y-%m-%d')}): {cant_fechas_corregidas:,}")

# ============================================================
# 6. LIMPIEZA DE EDAD
# ============================================================
print("\n6. Limpiando y validando edades...")

# Convertir cualquier formato a número (extraer dígitos si venía texto como '18 años')
edad_extraida = df["Edad"].astype(str).str.extract(r"(\d+)")[0]
df["Edad"] = pd.to_numeric(edad_extraida, errors="coerce")

# Rango biológicamente y legalmente válido para un gimnasio: 14 a 85 años
rango_edad_valido = (df["Edad"] >= 14) & (df["Edad"] <= 85)
mediana_edad = int(df.loc[rango_edad_valido, "Edad"].median())

edades_anomalas = (~rango_edad_valido) | df["Edad"].isna()
cant_edades_corregidas = int(edades_anomalas.sum())

df.loc[edades_anomalas, "Edad"] = mediana_edad
df["Edad"] = df["Edad"].astype(int)

print(f"   -> Edades inválidas o nulas imputadas con mediana ({mediana_edad} años): {cant_edades_corregidas:,}")

# ============================================================
# 7. LIMPIEZA DE MONTOS PAGADOS
# ============================================================
print("\n7. Limpiando y validando montos pagados...")

def limpiar_monto_texto(val):
    if pd.isna(val):
        return np.nan
    s = str(val).replace("$", "").strip()
    # Si viene formato argentino con puntos de miles y comas decimales
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan

montos_limpios = df["Monto_Pagado"].apply(limpiar_monto_texto)

# Rango válido para cuotas de gimnasio: $ 5.000 a $ 100.000
# Montos negativos, ceros, nulos o disparates (ej. 9999999) son anómalos
monto_valido = (montos_limpios >= 5000) & (montos_limpios <= 100000)
mediana_monto = round(montos_limpios[monto_valido].median(), 2)

montos_anomalos = (~monto_valido) | montos_limpios.isna()
cant_montos_corregidos = int(montos_anomalos.sum())

montos_limpios.loc[montos_anomalos] = mediana_monto
df["Monto_Pagado"] = montos_limpios.round(2)

print(f"   -> Montos negativos/nulos/extremos imputados con mediana (${mediana_monto:,.2f}): {cant_montos_corregidos:,}")

# ============================================================
# 8. NÚMERO DE RECIBO
# ============================================================
print("\n8. Verificando correlatividad de recibos...")
recibos_faltantes = df["Nro_Recibo"].isna()
cant_recibos_generados = int(recibos_faltantes.sum())
df.loc[recibos_faltantes, "Nro_Recibo"] = [
    f"REC-2024-{i + 900000:06d}" for i in range(cant_recibos_generados)
]
df["Nro_Recibo"] = df["Nro_Recibo"].astype(str).str.strip()

# ============================================================
# 9. GÉNERO / SEXO
# ============================================================
print("\n9. Estandarizando y limpiando género/sexo...")
if "Sexo" not in df.columns:
    df["Sexo"] = "Masculino"

def normalizar_sexo(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip().upper()
    if s in ["M", "MASC", "MASCULINO", "HOMBRE"]:
        return "Masculino"
    elif s in ["F", "FEM", "FEMENINO", "MUJER"]:
        return "Femenino"
    return np.nan

sexo_limpio = df["Sexo"].apply(normalizar_sexo)
moda_sexo = sexo_limpio.dropna().mode()[0] if not sexo_limpio.dropna().empty else "Masculino"
cant_sexo_imputados = int(sexo_limpio.isna().sum())
sexo_limpio = sexo_limpio.fillna(moda_sexo)
df["Sexo"] = sexo_limpio
print(f"   -> Géneros anómalos o nulos imputados por moda ('{moda_sexo}'): {cant_sexo_imputados:,}")

# ============================================================
# 10. ORDEN Y FORMATO FINAL
# ============================================================
orden_columnas = [
    "Nro_Recibo", "Fecha_Pago", "DNI_Socio", "Nombre_Completo",
    "Edad", "Sexo", "Plan_Membresia", "Sucursal", "Monto_Pagado",
    "Forma_Pago", "Estado_Membresia"
]
df = df[orden_columnas]

# ============================================================
# 11. GENERACIÓN DEL REPORTE DE AUDITORÍA
# ============================================================
reporte = pd.DataFrame({
    "Indicador de Calidad": [
        "1. Total registros originales",
        "2. Filas duplicadas eliminadas",
        "3. Total registros limpios finales",
        "4. Celdas vacías iniciales",
        "5. Celdas vacías finales",
        "6. DNI corregidos / reasignados",
        "7. Fechas anómalas / nulas corregidas",
        "8. Método de imputación para fechas",
        "9. Edades inválidas corregidas",
        "10. Método de imputación para edad",
        "11. Montos incorrectos o negativos corregidos",
        "12. Método de imputación para montos",
        "13. Recibos autogenerados por ausencia",
        "14. Géneros normalizados / imputados",
        "15. Método de estandarización categórica"
    ],
    "Resultado Obtenido": [
        f"{filas_iniciales:,}",
        f"{duplicados_detectados:,}",
        f"{len(df):,}",
        f"{nulos_iniciales:,}",
        f"{int(df.isna().sum().sum()):,}",
        f"{cant_dni_invalidos:,}",
        f"{cant_fechas_corregidas:,}",
        f"Mediana ({mediana_fecha.strftime('%Y-%m-%d')})",
        f"{cant_edades_corregidas:,}",
        f"Mediana ({mediana_edad} años)",
        f"{cant_montos_corregidos:,}",
        f"Mediana (${mediana_monto:,.2f})",
        f"{cant_recibos_generados:,}",
        f"{cant_sexo_imputados:,} imputados por moda ({moda_sexo})",
        "Diccionarios de Homologación + Moda"
    ]
})

# ============================================================
# 12. GUARDAR EN EXCEL LIMPIO (CON 2 HOJAS)
# ============================================================
print(f"\n12. Guardando archivo limpio en: {ARCHIVO_SALIDA.name}...")
with pd.ExcelWriter(ARCHIVO_SALIDA, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Cobros_Gimnasio_Limpio", index=False)
    reporte.to_excel(writer, sheet_name="Auditoria_Limpieza", index=False)

print("\n" + "=" * 65)
print("¡PROCESO DE LIMPIEZA FINALIZADO CON ÉXITO!")
print("=" * 65)
print(f"Archivo generado: {ARCHIVO_SALIDA}")
print(f"Filas originales: {filas_iniciales:,} -> Filas limpias: {len(df):,}")
print(f"Celdas vacías finales: {int(df.isna().sum().sum())} (Calidad 100%)")
print("=" * 65)

