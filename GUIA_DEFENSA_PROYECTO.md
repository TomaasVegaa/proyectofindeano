# 🎓 GUÍA DE DEFENSA FINAL: PIPELINE DE DATOS Y ANALÍTICA
## Sistema de Gestión y Cobros - Gimnasio Fitness Pro

Esta guía contiene la explicación paso a paso de cada etapa de tu proyecto para defenderlo con solvencia técnica ante profesores y evaluadores.

---

## 1. El Pitch Inicial (Cómo presentar tu proyecto en 1 minuto)

> *"Buenas tardes. Mi proyecto consiste en un **Pipeline Integral de Ingeniería y Análisis de Datos (ETL + API REST + Dashboard Web)** aplicado a un sistema real de cobros para una cadena de gimnasios llamada **Fitness Pro**.*
>
> *El sistema procesa más de **12.000 registros** a gran escala, toma datos crudos con anomalías del mundo real, aplica un riguroso proceso de limpieza con **Python y Pandas**, almacena la información estructurada e indexada en **MySQL**, expone los datos mediante una **API REST de alto rendimiento con FastAPI**, y finalmente presenta un **Dashboard Analítico interactivo** desplegado en la nube con **Vercel** que permite a la gerencia monitorear ingresos, socios y rendimiento por sucursal en tiempo real."*

---

## 2. Correspondencia con el Pizarrón de Arquitectura

El proyecto sigue con absoluta fidelidad las 5 etapas del diagrama:

| Etapa en Pizarrón | Archivo en el Proyecto | Tecnología | Responsabilidad Principal |
| :--- | :--- | :--- | :--- |
| **1. `.xlsx` ERRORES** | `gimnasio_crudo.xlsx` | Excel / Tabular | Insumo crudo con 12.500 registros y fallas a propósito (duplicados, fechas corruptas, edades negativas, celdas vacías). |
| **2. `.py` Limpieza** | `limpieza.py` | Python (Pandas, NumPy) | Normaliza textos, homologa categorías sin tildes, imputa valores faltantes con estadística descriptiva (mediana y moda) y genera reporte de auditoría. |
| **3. Limpio** | `gimnasio_limpio.xlsx` | Excel (OpenPyXL) | Archivo resultante con 12.000 filas 100% íntegras (0 nulos) y hoja de auditoría de calidad. |
| **4. `.py` Carga** | `carga.py` | Python (PyMySQL) | Conecta a MySQL en XAMPP, crea la base `bd_gimnasio` y la tabla `cobros_gimnasio` con tipos estrictos e índices, e inserta por lotes en 4 segundos. |
| **5. MySQL** | Motor MySQL (3306) | MySQL Server | Almacén persistente estructurado e indexado. |
| **6. `.py` API** | `main.py` / `api.py` | FastAPI + Pydantic | Capa intermedia que desacopla la base de datos, sirve JSON para el frontend y pre-calcula KPIs ejecutivos. |
| **7. Visualización** | `index.html` (Vercel) | HTML5, Tailwind, Chart.js | Tablero analítico web que reemplaza a Power BI: tarjetas de KPIs, gráficos de torta, barras, líneas y tabla interactiva con filtros. |

---

## 3. Explicación Detallada de Cada Etapa

### Paso 1: El Dato Crudo (`gimnasio_crudo.xlsx`)
- **Problema real:** En cualquier negocio donde intervienen recepcionistas o distintas sucursales, los datos ingresados a mano vienen viciados.
- **Anomalías deliberadas presentes:**
  - **Duplicados:** 500 filas repetidas de forma idéntica.
  - **Celdas vacías:** 2.894 valores nulos (`NaN`) distribuidos en recibos, fechas, DNI, nombres, edades y montos.
  - **Fechas multiformato e imposibles:** Formato ISO (`2024-04-19`), argentino (`02/03/2025`), formato texto (`24 Feb 2025`) y fechas fuera de rango histórico (años 1920 y 2099).
  - **Edades anómalas:** Números negativos (`-6`), edades en cero, mayores a 100 años o escritas en palabras (`"veinticinco"`).
  - **Montos corruptos:** Números negativos (`-$18.500`), montos en 0, textos con signos monetarios (`"$ 24.000"`).
  - **DNI sucios:** Con puntos (`"42.404.772"`), espacios (`"39 087 007"`), letras (`"DNI 29237545"`) o vacíos.

---

### Paso 2: Script de Limpieza (`limpieza.py`)
- **Técnicas implementadas:**
  1. `drop_duplicates()`: Elimina las 500 filas repetidas exactas, reduciendo de 12.500 a 12.000 filas.
  2. **Estandarización de Texto:** Función con `unicodedata` para remover tildes y diacríticos, `strip()` para espacios en blanco y `title()` para capitalizar nombres.
  3. **Diccionarios de Homologación:** Unificación de categorías (`musculacion` $\rightarrow$ `Musculación`, `mp` o `efvo` $\rightarrow$ `Mercado Pago` o `Efectivo`).
  4. **Imputación por Moda:** Los campos categóricos faltantes se completan con el valor más frecuente.
  5. **Imputación por Mediana:**
     - Para **fechas anómalas o vacías**: Se imputa la **mediana** de las fechas válidas (`2024-10-01`).
     - Para **edades inválidas**: Se imputa la **mediana** (`42 años`). Se elige la mediana sobre la media porque la mediana es **robusta a valores extremos** (un valor como 999 años distorsionaría la media aritmética).
     - Para **montos inválidos**: Se imputa la mediana de la cuota según el plan (`$19.500`).
  6. **Reporte de Auditoría de Calidad:** Se guarda en la segunda hoja de `gimnasio_limpio.xlsx` documentando cuántos nulos, duplicados y outliers fueron corregidos.

---

### Paso 3: Carga en Base de Datos (`carga.py` $\rightarrow$ MySQL)
- **Diseño Relacional y Tipado Estricto:**
  - `nro_recibo`: `VARCHAR(40) UNIQUE` (impide duplicados a nivel de motor).
  - `fecha_pago`: `DATE NOT NULL` (permite agrupaciones temporales nativas en SQL).
  - `monto_pagado`: `DECIMAL(10,2)` (nunca float en bases financieras para evitar errores de redondeo binario).
  - `INDEX` en `fecha_pago`, `plan_membresia`, `sucursal` y `dni_socio`: Acelera las consultas analíticas de la API cuando el volumen de datos crece.
- **Inserción Masiva (Batch Insert):** Uso de `executemany` con cláusula `ON DUPLICATE KEY UPDATE`. Logra insertar los 12.000 registros en apenas **4 segundos**.

---

### Paso 4: API REST con FastAPI (`main.py` / `api.py`)
- **¿Por qué colocar una API en el medio y no conectar el Dashboard directo a MySQL?**
  1. **Seguridad:** La base de datos nunca debe exponerse a internet ni al navegador cliente (evita inyecciones SQL y exposición de credenciales).
  2. **Desacoplamiento:** El frontend solo consume un contrato JSON; si mañana cambiás MySQL por PostgreSQL, el dashboard ni se entera.
  3. **Rendimiento:** La API pre-calcula los KPIs agregados (`/kpis/resumen`) en el servidor, evitando que el navegador del usuario tenga que descargar y procesar miles de filas en memoria.
- **Documentación automática:** Al estar construida con FastAPI, genera la documentación interactiva Swagger en `/docs`.

---

### Paso 5: Dashboard Analítico Web (`index.html` en Vercel)
- **¿Por qué un Dashboard Web en lugar de Power BI Desktop?**
  1. **Acceso universal:** Funciona en cualquier navegador sin necesidad de licencias ni de instalar software pesado en Windows.
  2. **Tecnologías estándar:** Desarrollado con **Tailwind CSS** (estilos modernos en modo oscuro), **Chart.js** (gráficos interactivos vectoriales) y **Lucide Icons**.
  3. **Despliegue en la nube:** Aloja la aplicación en **Vercel** (`https://proyectofindeano-r71z.vercel.app`), accesible para cualquier persona con un enlace público.
  4. **Modo Respaldo Inteligente:** Si se ejecuta en internet sin conexión directa a la base local de XAMPP, el dashboard conmuta automáticamente a sus datos pre-almacenados (`cobros_demo.json`), garantizando disponibilidad del 100%.

---

## 4. Preguntas Frecuentes de Evaluadores y Cómo Responderlas

#### P: ¿Por qué usaste la Mediana y no la Media para corregir los números atípicos?
> **R:** *"La media aritmética es muy sensible a los valores atípicos (outliers). Si un usuario ingresó una edad errónea de 999 años o un monto de $99.000.000, la media se desviaría por completo. La mediana, en cambio, representa el valor del percentil 50 y es estadísticamente robusta frente a anomalías extremas."*

#### P: ¿Cómo garantizás que si ejecutás la carga dos veces no se dupliquen las 12.000 filas?
> **R:** *"En MySQL definí una restricción de unicidad (`UNIQUE KEY`) sobre `nro_recibo` y en la sentencia SQL apliqué `ON DUPLICATE KEY UPDATE`. Esto hace que el proceso sea **idempotente**: si un recibo ya existe en la base de datos, actualiza sus campos en lugar de crear una fila duplicada."*

#### P: ¿Qué ventaja tiene usar tipos `DECIMAL` en vez de `FLOAT` en la base de datos?
> **R:** *"En sistemas de facturación y cobros nunca se debe usar `FLOAT` o `DOUBLE` porque representan números con coma flotante binaria y generan errores de redondeo por precisión (por ejemplo $0.1 + 0.2 = 0.30000000000000004$). `DECIMAL(10,2)` almacena los valores como números exactos en base 10 con dos posiciones decimales fijas."*

#### P: ¿Por qué agregaste índices (`INDEX`) en la tabla de cobros?
> **R:** *"Con 12.000 registros, una consulta que filtre por sucursal o rango de fechas sin índices haría un escaneo completo de la tabla (Full Table Scan). Al indexar `fecha_pago`, `sucursal` y `plan_membresia`, el motor B-Tree de MySQL localiza los registros en tiempo logarítmico $O(\log n)$, respondiendo en milisegundos."*

---

## 5. Resumen de Métricas Clave del Gimnasio para Mencionar

- **Volumen procesado:** 12.500 registros crudos $\rightarrow$ 12.000 registros limpios deduplicados.
- **Calidad de datos lograda:** 0 celdas vacías (100% completitud).
- **Facturación Total consolidada:** **$ 242.002.400**
- **Socios Únicos activos:** **3.826 socios**
- **Ticket Promedio:** **$ 20.166,87**
- **Plan líder en recaudación:** **Musculación** (representa más del 45% de los ingresos).
- **Sucursal con mayor facturación:** **Sede Centro**, seguida por Sede Norte.
- **Medio de pago principal:** **Efectivo** (43%) y **Mercado Pago** (37%).
