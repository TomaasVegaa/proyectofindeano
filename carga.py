import time
from pathlib import Path
import pandas as pd
import pymysql

# ============================================================
# CONFIGURACIÓN
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
ARCHIVO_LIMPIO = BASE_DIR / "gimnasio_limpio.xlsx"
HOJA_DATOS = "Cobros_Gimnasio_Limpio"

MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_DATABASE = "bd_gimnasio"
TABLA = "cobros_gimnasio"

print("=" * 65)
print("INICIANDO CARGA DE DATOS A MYSQL (PyMySQL)")
print("=" * 65)

# 1. VERIFICAR Y LEER ARCHIVO LIMPIO
if not ARCHIVO_LIMPIO.exists():
    raise FileNotFoundError(f"No se encontró el archivo limpio: {ARCHIVO_LIMPIO}")

inicio = time.time()
print(f"1. Leyendo datos limpios de '{ARCHIVO_LIMPIO.name}'...")
df = pd.read_excel(ARCHIVO_LIMPIO, sheet_name=HOJA_DATOS)
total_registros = len(df)
print(f"   -> {total_registros:,} registros listos para transferir.")

# 2. CONEXIÓN A MYSQL Y CREACIÓN DE BASE DE DATOS
try:
    print("\n2. Conectando al servidor MySQL...")
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        connect_timeout=5
    )
    cursor = conn.cursor()

    print(f"   -> Creando base de datos `{MYSQL_DATABASE}` si no existe...")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit()
    cursor.close()
    conn.close()

    # 3. CONEXIÓN A LA BASE DE DATOS ESPECÍFICA
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        connect_timeout=5
    )
    cursor = conn.cursor()

    # 4. CREACIÓN DE LA TABLA CON TIPOS DE DATOS E ÍNDICES ÓPTIMOS
    print(f"\n3. Configurando tabla `{TABLA}` con índices de optimización...")
    cursor.execute(f"DROP TABLE IF EXISTS `{TABLA}`;")
    sql_tabla = f"""
    CREATE TABLE `{TABLA}` (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nro_recibo VARCHAR(40) NOT NULL UNIQUE,
        fecha_pago DATE NOT NULL,
        dni_socio VARCHAR(20) NOT NULL,
        nombre_socio VARCHAR(150) NOT NULL,
        edad INT NOT NULL,
        sexo VARCHAR(20) NOT NULL,
        plan_membresia VARCHAR(50) NOT NULL,
        sucursal VARCHAR(50) NOT NULL,
        monto_pagado DECIMAL(10,2) NOT NULL,
        forma_pago VARCHAR(50) NOT NULL,
        estado_membresia VARCHAR(30) NOT NULL,
        INDEX idx_fecha (fecha_pago),
        INDEX idx_plan (plan_membresia),
        INDEX idx_sucursal (sucursal),
        INDEX idx_socio (dni_socio),
        INDEX idx_sexo (sexo)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(sql_tabla)
    conn.commit()
    print(f"   -> Tabla `{TABLA}` verificada e indexada.")

    # 5. PREPARACIÓN DE TUPLAS PARA INSERCIÓN MASIVA
    print("\n4. Preparando lote de registros...")
    
    # Formatear fecha y tipos por seguridad
    df["Fecha_Pago"] = pd.to_datetime(df["Fecha_Pago"]).dt.strftime("%Y-%m-%d")
    df["Edad"] = df["Edad"].astype(int)
    df["Monto_Pagado"] = df["Monto_Pagado"].astype(float)
    df["DNI_Socio"] = df["DNI_Socio"].astype(str)
    df["Nro_Recibo"] = df["Nro_Recibo"].astype(str)
    df["Sexo"] = df["Sexo"].astype(str)

    valores = [
        (
            fila["Nro_Recibo"],
            fila["Fecha_Pago"],
            fila["DNI_Socio"],
            fila["Nombre_Completo"],
            fila["Edad"],
            fila["Sexo"],
            fila["Plan_Membresia"],
            fila["Sucursal"],
            fila["Monto_Pagado"],
            fila["Forma_Pago"],
            fila["Estado_Membresia"]
        )
        for _, fila in df.iterrows()
    ]

    # 6. INSERCIÓN MASIVA EFICIENTE (BATCH INSERT CON ON DUPLICATE KEY UPDATE)
    sql_insert = f"""
    INSERT INTO `{TABLA}` (
        nro_recibo, fecha_pago, dni_socio, nombre_socio, edad, sexo,
        plan_membresia, sucursal, monto_pagado, forma_pago, estado_membresia
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        fecha_pago = VALUES(fecha_pago),
        dni_socio = VALUES(dni_socio),
        nombre_socio = VALUES(nombre_socio),
        edad = VALUES(edad),
        sexo = VALUES(sexo),
        plan_membresia = VALUES(plan_membresia),
        sucursal = VALUES(sucursal),
        monto_pagado = VALUES(monto_pagado),
        forma_pago = VALUES(forma_pago),
        estado_membresia = VALUES(estado_membresia);
    """

    print(f"5. Insertando {len(valores):,} filas en MySQL...")
    cursor.executemany(sql_insert, valores)
    conn.commit()

    # Comprobación de filas en la tabla
    cursor.execute(f"SELECT COUNT(*) FROM `{TABLA}`")
    filas_en_db = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    segundos = round(time.time() - inicio, 2)
    print("\n" + "=" * 65)
    print("¡CARGA A MYSQL COMPLETADA CON ÉXITO!")
    print("=" * 65)
    print(f"Base de datos: `{MYSQL_DATABASE}`")
    print(f"Tabla: `{TABLA}`")
    print(f"Registros confirmados en MySQL: {filas_en_db:,}")
    print(f"Tiempo total de ejecución: {segundos} segundos")
    print("=" * 65)

except pymysql.MySQLError as e:
    print(f"\n[ERROR DE MYSQL]: {e}")
except Exception as e:
    print(f"\n[ERROR GENERAL]: {e}")

