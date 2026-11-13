# 🏋️‍♂️ Sistema de Datos y Analítica - Gimnasio Fitness Pro
### Pipeline ETL + Base de Datos MySQL + API REST + Dashboard en Power BI

Este proyecto implementa una solución integral de ingeniería y análisis de datos a escala empresarial (**12.000+ registros**) para la gestión de cobros y socios de una cadena de gimnasios con múltiples sedes.

---

## 📐 Arquitectura del Flujo

```
[ .xlsx con ERRORES ]  (12.500 filas sucias)
         │
         ▼
[ 2_limpieza.py ]     (Pandas: normalización, deduplicación e imputación estadística)
         │
         ▼
[ .xlsx LIMPIO ]       (12.000 filas 100% íntegras + Hoja de Auditoría)
         │
         ▼
[ 3_carga_mysql.py ]   (PyMySQL: creación de esquema 'bd_gimnasio', tipos e índices)
         │
         ▼
[ MySQL Database ]     (Tabla indexada: 'cobros_gimnasio')
         │
         ▼
[ 4_api.py ]           (FastAPI: expone JSON en http://127.0.0.1:8000/cobros/powerbi)
         │
         ▼
[ Power BI Desktop ]   (Consumo Web del JSON -> Power Query -> Dashboard interactivo)
```

---

## 📁 Estructura del Proyecto

- `1_generar_dataset_sucio.py`: Generador masivo de 12.500 registros con anomalías deliberadas (espacios, formatos cruzados, nulos, outliers).
- `gimnasio_crudo.xlsx`: Dataset de entrada con los datos desordenados y errores.
- `2_limpieza.py`: Limpia los datos, corrige edades y montos con mediana/media, normaliza textos y DNI, deduplica y genera el reporte de calidad.
- `gimnasio_limpio.xlsx`: Archivo limpio resultante con 2 hojas (`Cobros_Gimnasio_Limpio` y `Auditoria_Limpieza`).
- `3_carga_mysql.py`: Crea la base de datos `bd_gimnasio` y la tabla `cobros_gimnasio` e inserta los datos por lotes en 4 segundos.
- `4_api.py`: Servidor FastAPI con endpoints optimizados para Power BI, filtros dinámicos y KPIs pre-calculados.
- `pipeline_gimnasio.py`: Script maestro que ejecuta los pasos de forma automatizada.

---

## 🚀 Guía de Ejecución Rápida

### Paso 1: Limpieza
```bash
python proyecto_gimnasio/2_limpieza.py
```

### Paso 2: Carga a MySQL
> Asegurate de que **Apache y MySQL** estén iniciados en el panel de **XAMPP**.
```bash
python proyecto_gimnasio/3_carga_mysql.py
```

### Paso 3: Iniciar la API REST
```bash
python proyecto_gimnasio/4_api.py
```
* La API quedará escuchando en `http://127.0.0.1:8000`.
* Documentación interactiva (Swagger): `http://127.0.0.1:8000/docs`.

---

## 📊 Conexión y Armado del Dashboard en Power BI

1. Abrí **Power BI Desktop**.
2. Hacé clic en **Inicio** -> **Obtener datos** -> **Web**.
3. En la ventana emergente, pegá la URL:
   ```text
   http://127.0.0.1:8000/cobros/powerbi
   ```
4. Se abrirá **Power Query Editor** mostrando una lista de registros (`List`).
5. Hacé clic en el botón superior **A la tabla** (To Table) y luego **Aceptar**.
6. En el encabezado de la columna `Column1`, hacé clic en el icono de las **flechas dobles divergentes** (Expandir columnas). Desmarcá la casilla *"Usar el nombre de la columna original como prefijo"* y hacé clic en **Aceptar**.
7. Seleccioná los tipos de datos correctos para cada campo:
   - `fecha_pago` -> **Fecha**
   - `monto_pagado` -> **Número decimal fijo / Moneda**
   - `edad` -> **Número entero**
   - El resto -> **Texto**
8. Hacé clic en **Cerrar y aplicar**.

### Visualizaciones sugeridas para el reporte:
- **Tarjetas KPI:**
  - Facturación Total: `Suma de monto_pagado` (~$242 Millones)
  - Socios Únicos: `Recuento distintivo de dni_socio` (3.826 socios)
  - Ticket Promedio: `Promedio de monto_pagado` (~$20.166)
- **Gráfico de Donut / Torta:** Recaudación por `plan_membresia`.
- **Gráfico de Barras Agrupadas:** Facturación por `sucursal` y por `forma_pago`.
- **Gráfico de Líneas:** Evolución temporal de cobros mes a mes (`fecha_pago`).
- **Tabla de detalle:** Listado con `nro_recibo`, `nombre_socio`, `plan_membresia`, `sucursal`, `monto_pagado` y `estado_membresia`.

