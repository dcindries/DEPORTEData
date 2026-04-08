# Contexto de datos — Empleo vinculado al deporte en España

**Proyecto:** DEPORTEData — Previsión anual de empleo vinculado al deporte  
**Fuente oficial:** INE · Encuesta de Población Activa (EPA) procesada por DEPORTEData  
**Portal de descarga:** [estadisticas.educacion.gob.es — Empleo](https://estadisticas.educacion.gob.es/DeporteDynPx/deportebase/index.htm?type=pcaxis&path=/empleo/&file=pcaxis)  
**Elaborado para:** Sprint 1 — Catálogo de fuentes y trazabilidad  
**Fecha:** Abril 2026

---

## ¿Qué miden estos datos?

Todos los archivos recogen el **empleo vinculado al deporte en España** tal como lo define la EPA del INE: personas ocupadas cuya actividad principal o secundaria está ligada a ocupaciones o actividades deportivas (deportistas, entrenadores, gestores de instalaciones, árbitros, etc.).

El valor de referencia clave es el número de personas en miles. A modo de contexto del sector:

- En **2025** se registraron **270.200 empleos** vinculados al deporte (+6% respecto a 2024 y +15,2% respecto a 2022).
- El sector deportivo generó un **3,3% del PIB** y casi 414.000 puestos de trabajo en 2018.
- El perfil laboral es más joven y con mayor nivel formativo que la media nacional.

---

## Árbol de archivos

```
docs/
├── resources_csv/          ← Archivos RAW descargados del INE (sin procesar)
│   ├── DATOS ANUALES(MEDIAS MÓVILES)_...jornada.csv
│   ├── DATOS ANUALES(MEDIAS MÓVILES)_...perfil.csv
│   ├── DATOS TRIMESTRALES_...jornada.csv
│   ├── DATOS TRIMESTRALES_...perfil.csv
│   ├── MEDIAS ANUALES_...tipo_empleo.csv
│   ├── MEDIAS ANUALES_...demografia.csv
│   └── MEDIAS ANUALES_...jornada_sexo.csv
│
└── clean_data/             ← Archivos procesados y normalizados (listos para análisis)
    ├── anual_mm_jornada.csv
    ├── anual_mm_perfil.csv
    ├── medias_anuales_demografia.csv
    ├── medias_anuales_jornada_sexo.csv
    ├── medias_anuales_tipo_empleo.csv
    ├── trimestral_jornada_laboral.csv
    └── trimestral_perfil_demografico.csv
```

---

## Descripción detallada de cada CSV

### Grupo 1 — Datos anuales con medias móviles

Los datos de medias móviles suavizan la estacionalidad trimestral calculando el promedio de cuatro trimestres consecutivos. Son especialmente útiles para **detectar tendencias de fondo** sin el ruido estacional.

---

#### `anual_mm_jornada.csv` / `resources_csv/DATOS ANUALES(MEDIAS MÓVILES)_...jornada.csv`

| Atributo | Detalle |
|---|---|
| **Cobertura temporal** | Desde el periodo `De 2014-1T hasta 2014-4T` hasta `De 2025-1T hasta 2025-4T` |
| **Filas** | ~1.596 |
| **Columnas** | `indicador`, `situacion_jornada`, `periodo`, `valor` |
| **Segmentación** | Tipo de contrato y jornada |

**¿Qué contiene?** Empleo vinculado al deporte segmentado por situación laboral y tipo de jornada, expresado como media móvil anual de cuatro trimestres. Los valores de `situacion_jornada` son:

- `TOTAL` — todos los ocupados deportivos
- `Situación profesional: Asalariados total` — asalariados en conjunto
- `Situación profesional: Asalariados: Contrato indefinido` — trabajadores con contrato fijo
- `Situación profesional: Asalariados: Contrato temporal` — trabajadores con contrato temporal
- `Situación profesional: No asalariados` — autónomos y empleadores
- `Tipo de jornada: Tiempo completo` — jornada completa
- `Tipo de jornada: Tiempo parcial` — jornada parcial

**¿Por qué importa?** Permite analizar la **calidad del empleo deportivo** a lo largo del tiempo. Si el ratio de contratos temporales crece, señala mayor precariedad. Si el tiempo parcial sube, puede indicar mayor informalidad.

Los indicadores disponibles son cuatro:

1. Valores absolutos en miles (el más usado para forecasting)
2. Distribución porcentual del empleo total
3. Distribución porcentual dentro del empleo vinculado al deporte
4. Porcentaje del empleo deportivo sobre el total nacional

---

#### `anual_mm_perfil.csv` / `resources_csv/DATOS ANUALES(MEDIAS MÓVILES)_...perfil.csv`

| Atributo | Detalle |
|---|---|
| **Cobertura temporal** | Medias móviles de cuatro trimestres desde 2014 hasta 2025 |
| **Filas** | ~2.964 |
| **Columnas** | `indicador`, `sexo_edad_estudios`, `periodo`, `valor` |
| **Segmentación** | Sexo, grupo de edad y nivel de estudios |

**¿Qué contiene?** Empleo deportivo como media móvil desagregado por el perfil sociodemográfico del trabajador. Las categorías de `sexo_edad_estudios` son:

- `TOTAL`
- `Hombres` / `Mujeres`
- `De 16 a 24 años`, `De 25 a 34 años`, `De 35 a 44 años`, `De 45 a 54 años`, `De 55 años en adelante`
- `Primera etapa de educación secundaria e inferior`
- `Segunda etapa de educación secundaria: Total / Orientación general / Orientación profesional`
- `Educación superior o equivalente`

**¿Por qué importa?** Permite estudiar la **brecha de género**, la estructura etaria del empleo deportivo y el nivel educativo predominante. Datos clave para políticas de formación o para proyectar la demanda futura de perfiles específicos.

---

### Grupo 2 — Medias anuales

Las medias anuales son el **agregado consolidado por año completo**, la serie principal para modelado predictivo.

---

#### `medias_anuales_demografia.csv` / `resources_csv/MEDIAS ANUALES_...demografia.csv`

| Atributo | Detalle |
|---|---|
| **Cobertura temporal** | **2011–2025** (serie más larga disponible, 15 años) |
| **Filas** | ~780 |
| **Columnas** | `indicador`, `sexo_edad_estudios`, `periodo`, `valor` |
| **Segmentación** | Mismas categorías de perfil que `anual_mm_perfil` |

**¿Qué contiene?** Es la versión anual consolidada del perfil demográfico. Mismas dimensiones de edad, sexo y nivel educativo, pero expresadas como media del año completo en lugar de media móvil de cuatro trimestres.

**¿Por qué importa?** Es el **dataset principal para la serie histórica larga** (desde 2011). Al cubrir 15 años, permite aplicar modelos de forecasting como ARIMA o Prophet con suficiente histórico para capturar tendencias estructurales.

---

#### `medias_anuales_jornada_sexo.csv` / `resources_csv/MEDIAS ANUALES_...jornada_sexo.csv`

| Atributo | Detalle |
|---|---|
| **Cobertura temporal** | 2011–2025 |
| **Filas** | ~1.260 |
| **Columnas** | `indicador`, `situacion_jornada`, `sexo`, `periodo`, `valor` |
| **Segmentación** | Tipo de contrato/jornada cruzado con sexo |

**¿Qué contiene?** Cruza dos dimensiones a la vez: la **situación laboral** (indefinido, temporal, autónomo, tiempo parcial/completo) y el **sexo** del trabajador. Esto permite responder preguntas como: ¿las mujeres en el sector deportivo tienen más contratos temporales que los hombres?

**¿Por qué importa?** Clave para análisis de **equidad laboral y calidad del empleo por género**. Es el CSV más rico en combinaciones de dimensiones y útil para análisis exploratorio de brechas.

---

#### `medias_anuales_tipo_empleo.csv` / `resources_csv/MEDIAS ANUALES_...tipo_empleo.csv`

| Atributo | Detalle |
|---|---|
| **Cobertura temporal** | **2019–2025** (serie más corta, 7 años) |
| **Filas** | ~189 |
| **Columnas** | `indicador`, `sexo`, `periodo`, `valor` |
| **Segmentación** | Sexo (Hombres / Mujeres / Total) |

**¿Qué contiene?** Es el CSV más específico: distingue entre **empleo principal vinculado al deporte** y **empleo secundario vinculado al deporte**. Los indicadores disponibles son:

1. `Con empleo principal vinculado al deporte` — trabaja principalmente en el sector
2. `Con empleo principal vinculado al deporte y sin empleo secundario` — exclusivamente en deporte
3. `Con empleo principal vinculado al deporte y con empleo secundario` — tiene además otro trabajo
4. `Con empleo principal vinculado al deporte y con empleo secundario vinculado al deporte` — ambos empleos en deporte
5. `Con empleo secundario vinculado al deporte y empleo principal NO vinculado al deporte` — el deporte es actividad complementaria
6. `Porcentaje de empleo principal vinculado al deporte respecto al total de empleo principal`
7. `Porcentaje de empleo secundario vinculado al deporte respecto al total de empleo secundario`

**¿Por qué importa?** Cuantifica cuántas personas viven **del** deporte versus cuántas lo practican como fuente de ingresos secundaria. Es un indicador de la profesionalización real del sector. Limitación: solo disponible desde 2019.

---

### Grupo 3 — Datos trimestrales

Los datos trimestrales tienen mayor granularidad temporal y capturan **estacionalidad** (el empleo deportivo sube en verano por el deporte de temporada).

---

#### `trimestral_jornada_laboral.csv` / `resources_csv/DATOS TRIMESTRALES_...jornada.csv`

| Atributo | Detalle |
|---|---|
| **Cobertura temporal** | **2011-1T hasta 2025-4T** (58 trimestres) |
| **Filas** | ~1.680 |
| **Columnas** | `indicador`, `situacion_jornada`, `periodo`, `valor` |
| **Segmentación** | Tipo de contrato y jornada (mismas categorías que `anual_mm_jornada`) |

**¿Qué contiene?** El empleo deportivo por tipo de contrato y jornada, desagregado trimestre a trimestre desde 2011. El campo `periodo` tiene el formato `YYYY-XT` (ej: `2023-3T` = tercer trimestre de 2023).

**¿Por qué importa?** Permite ver la **estacionalidad real** del empleo deportivo. Hay picos en Q2/Q3 (temporada de verano, competiciones al aire libre) y caídas en Q1. Es el dataset ideal para modelos de forecasting trimestral con componente estacional como Prophet.

---

#### `trimestral_perfil_demografico.csv` / `resources_csv/DATOS TRIMESTRALES_...perfil.csv`

| Atributo | Detalle |
|---|---|
| **Cobertura temporal** | **2011-1T hasta 2025-4T** (58 trimestres) |
| **Filas** | ~3.120 |
| **Columnas** | `indicador`, `sexo_edad_estudios`, `periodo`, `valor` |
| **Segmentación** | Sexo, grupo de edad y nivel educativo |

**¿Qué contiene?** El mayor CSV del proyecto en filas. Combina la granularidad trimestral con la desagregación demográfica completa. Permite rastrear, por ejemplo, cómo evoluciona el empleo de jóvenes de 16–24 años trimestre a trimestre.

**¿Por qué importa?** Es el archivo más detallado para análisis de tendencias por colectivo. Un uso clave es detectar si el crecimiento del empleo deportivo se distribuye de manera homogénea entre grupos o si hay colectivos que quedan rezagados.

---

## Tabla resumen

| Archivo (clean) | Frecuencia | Dimensiones | Rango temporal | Filas | Uso principal |
|---|---|---|---|---|---|
| `anual_mm_jornada` | Medias móviles | Tipo contrato / jornada | 2014–2025 | ~1.596 | Tendencia suavizada por tipo de empleo |
| `anual_mm_perfil` | Medias móviles | Sexo / edad / estudios | 2014–2025 | ~2.964 | Tendencia suavizada por perfil demográfico |
| `medias_anuales_demografia` | Anual | Sexo / edad / estudios | **2011–2025** | ~780 | **Serie larga para forecasting** |
| `medias_anuales_jornada_sexo` | Anual | Jornada × sexo | 2011–2025 | ~1.260 | Análisis de equidad de género |
| `medias_anuales_tipo_empleo` | Anual | Empleo principal/secundario | 2019–2025 | ~189 | Grado de profesionalización |
| `trimestral_jornada_laboral` | Trimestral | Tipo contrato / jornada | **2011-1T – 2025-4T** | ~1.680 | Estacionalidad por tipo de empleo |
| `trimestral_perfil_demografico` | Trimestral | Sexo / edad / estudios | **2011-1T – 2025-4T** | ~3.120 | Estacionalidad por perfil demográfico |

---

## Estructura de los indicadores

Todos los archivos comparten los mismos cuatro tipos de indicador (excepto `medias_anuales_tipo_empleo` que tiene su propio conjunto):

| Indicador | Descripción |
|---|---|
| `EMPLEO VINCULADO AL DEPORTE: Valores absolutos (En miles)` | Número de personas ocupadas. **El indicador principal para predicción.** |
| `EMPLEO VINCULADO AL DEPORTE: Distribución porcentual` | Peso de cada categoría dentro del total de empleo deportivo |
| `EMPLEO VINCULADO AL DEPORTE: En porcentaje del total de empleo` | Peso del empleo deportivo sobre el empleo total nacional |
| `DISTRIBUCIÓN PORCENTUAL DEL EMPLEO TOTAL` | Distribución de referencia del empleo total (no solo deportivo) |

---

## Siguiente paso en el pipeline

Según el diagrama de arquitectura del proyecto, una vez los CSV están en la capa `raw_data` (local) o en el bucket S3 (nube), el flujo continúa así:

```
raw_data / S3  ──►  Procesamiento (ETL)  ──►  Base de datos  ──►  API REST
```

### Capa raw → Procesamiento

El script `clean_csv.py` ya incluido en el repositorio realiza la primera limpieza. Lo que queda para el **Sprint 2** es:

1. **Normalización de tipos** — convertir `valor` a `float`, `periodo` a un tipo fecha estandarizado (para las series anuales un entero `YYYY`, para las trimestrales un `datetime` calculado como primer día del trimestre).
2. **Tratamiento de nulos** — verificar si hay celdas vacías o valores `"."` (convención INE para datos no disponibles) y documentar su tratamiento.
3. **Dataset consolidado** — unir los CSVs relevantes en un único `DataFrame` con columnas: `anio`, `trimestre` (nullable), `segmentacion`, `categoria`, `indicador`, `valor`. Guardar como `data/processed/empleo_deportivo_consolidado.csv`.

### Capa procesada → Base de datos

El dataset consolidado es candidato a cargarse en una tabla relacional con la siguiente estructura mínima:

```sql
CREATE TABLE empleo_deporte (
    id          SERIAL PRIMARY KEY,
    periodo     DATE,          -- primer día del periodo (2023-01-01 para media anual)
    frecuencia  VARCHAR(12),   -- 'anual' | 'trimestral' | 'media_movil'
    dimension   VARCHAR(40),   -- 'jornada' | 'demografia' | 'tipo_empleo'
    categoria   VARCHAR(100),  -- ej. 'Hombres', 'Contrato indefinido'
    indicador   VARCHAR(120),  -- ej. 'Valores absolutos (En miles)'
    valor       FLOAT
);
```

Esta estructura permite consultas directas desde la API sin cargar los CSV en cada petición.

### Capa base de datos → API REST

Con FastAPI y los datos en la base de datos, los endpoints naturales son:

- `GET /empleo/anual` — serie histórica anual del total (para el modelo predictivo)
- `GET /empleo/trimestral` — serie histórica trimestral (para análisis de estacionalidad)
- `GET /empleo/perfil?dimension=sexo` — filtrado por dimensión demográfica
- `GET /prediccion/arima` — resultado del modelo ARIMA entrenado
- `GET /prediccion/prophet` — resultado del modelo Prophet entrenado

---

## Notas de calidad de los datos

- **Fuente única y oficial**: todos los archivos vienen de la misma fuente (EPA/INE vía DEPORTEData), lo que garantiza coherencia metodológica entre ellos.
- **Los totales son consistentes**: el valor `TOTAL` de todos los archivos para el mismo periodo debe coincidir. En 2025 la cifra oficial es 270.200 empleos, verificable en todos los CSVs.
- **Serie larga desde 2011** para medias anuales y trimestrales — suficiente para ARIMA (se recomienda mínimo 30–50 observaciones; aquí hay 15 anuales o 58 trimestrales).
- **`medias_anuales_tipo_empleo`** solo cubre desde 2019 (7 observaciones anuales). No es suficiente para un modelo ARIMA independiente; úsese como variable explicativa complementaria.
- **No existe desagregación geográfica** en estos archivos — los datos son nacionales. Según los objetivos del proyecto, esto está dentro del alcance definido.

---

*Documento generado como parte del Sprint 1 — Catálogo de fuentes y trazabilidad.*
