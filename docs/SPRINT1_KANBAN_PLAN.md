# DEPORTEData · Sprint 1 Kanban Plan (Reto A)

## Contexto operativo
- Proyecto: **DEPORTEData**.
- Reto elegido: **Reto A** (gasto por hogar vs práctica federada por CCAA).
- Duración sprint: **1 semana**.
- Metodología: **Scrum ligero + Kanban operativo**.
- Equipo: frontend, backend, IA y devops.

---

## 1) Estructura de backlog para Sprint 1

### ÉPICA E1 — Definición del problema, hipótesis y KPIs
**Objetivo**: aterrizar el reto A en preguntas analíticas medibles.

Subtareas:
1. Definir pregunta principal y preguntas secundarias.
2. Formular 3–5 hipótesis verificables.
3. Definir KPIs mínimos (gasto hogar, práctica federada, variación interanual, correlación inicial).
4. Establecer glosario de métricas y supuestos.

---

### ÉPICA E2 — Catálogo y trazabilidad de fuentes oficiales
**Objetivo**: identificar y documentar datasets descargables sin scraping.

Subtareas:
1. Selección de fuentes oficiales (INE, CSD, ministerios, portales abiertos).
2. Registro de licencia, periodicidad, granularidad y cobertura.
3. Descarga de datasets en `data/raw/`.
4. Diccionario inicial de campos por fuente.

---

### ÉPICA E3 — Base técnica de ingestión y estructura del repositorio
**Objetivo**: dejar el proyecto listo para desarrollar con flujo reproducible.

Subtareas:
1. Estructura de carpetas (`src/`, `data/`, `notebooks/`, `docs/`, `infra/`).
2. Script de ingestión base y validación de esquema inicial.
3. Versionado de dependencias y `.env.example`.
4. Convenciones de logging y gestión de errores.

---

### ÉPICA E4 — Diseño preliminar del modelo analítico en estrella
**Objetivo**: definir modelo lógico para hechos/dimensiones del reto A.

Subtareas:
1. Definir tabla de hechos `hechos_indicadores`.
2. Definir dimensiones `dim_tiempo`, `dim_geografia`, `dim_indicador`, `dim_fuente`.
3. Proponer claves y reglas de integridad.
4. Entregar diagrama (Mermaid o draw.io exportado).

---

### ÉPICA E5 — Entorno de trabajo, CI mínima y definición de DoD
**Objetivo**: reducir fricción de equipo desde Sprint 1.

Subtareas:
1. Configurar workflow CI básico (lint + tests smoke).
2. Definir Definition of Done para issues.
3. Configurar plantillas de issue/PR.
4. Definir normas de ramas y revisión.

---

## 2) Lista de issues propuestas (épicas y subtareas)

> Formato: **Título · Descripción · Criterios de aceptación · Etiquetas · Responsable sugerido**.

### EPIC-01 · Definición analítica del Reto A
**Descripción**: consolidar alcance analítico de Sprint 1 y documentar hipótesis del equipo.

**Criterios de aceptación**:
- Documento de alcance en `docs/` publicado.
- Pregunta principal + al menos 3 preguntas secundarias.
- 3–5 hipótesis con posible método de validación.

**Etiquetas**: `epic`, `sprint-1`, `analytics`, `reto-a`

**Responsable sugerido**: IA (co-lidera con backend)

#### Subtareas
1. **[S1-A1] Redactar marco de hipótesis iniciales del Reto A**
   - Criterios: hipótesis medibles + variable dependiente/independiente.
   - Etiquetas: `task`, `analytics`, `ia`, `sprint-1`
   - Responsable: IA

2. **[S1-A2] Definir KPIs analíticos mínimos del sprint**
   - Criterios: al menos 4 KPIs con fórmula y fuente.
   - Etiquetas: `task`, `analytics`, `backend`, `sprint-1`
   - Responsable: Backend

---

### EPIC-02 · Catálogo de fuentes y trazabilidad
**Descripción**: construir inventario oficial de fuentes con trazabilidad y metadatos.

**Criterios de aceptación**:
- Fichero `docs/sources_catalog.md` creado.
- Cada fuente incluye URL, licencia, rango temporal, cobertura geográfica, formato.
- Datasets descargados a `data/raw/` con naming estándar.

**Etiquetas**: `epic`, `data`, `sprint-1`, `reto-a`

**Responsable sugerido**: Backend

#### Subtareas
1. **[S1-B1] Identificar fuentes oficiales para gasto por hogar**
   - Criterios: mínimo 2 fuentes candidatas con justificación.
   - Etiquetas: `task`, `data`, `backend`, `sprint-1`
   - Responsable: Backend

2. **[S1-B2] Identificar fuentes oficiales de práctica federada por CCAA**
   - Criterios: mínimo 2 fuentes candidatas con detalle territorial.
   - Etiquetas: `task`, `data`, `ia`, `sprint-1`
   - Responsable: IA

3. **[S1-B3] Descargar y versionar dataset raw inicial**
   - Criterios: archivos en `data/raw/` + README de procedencia.
   - Etiquetas: `task`, `data-engineering`, `backend`, `sprint-1`
   - Responsable: Backend

---

### EPIC-03 · Base técnica del repositorio y pipeline de ingestión
**Descripción**: crear base de código para ingestión reproducible y estructura de trabajo.

**Criterios de aceptación**:
- Estructura estándar de directorios creada.
- Script ejecutable de ingestión inicial.
- Dependencias y configuración base documentadas.

**Etiquetas**: `epic`, `backend`, `devops`, `sprint-1`

**Responsable sugerido**: Backend

#### Subtareas
1. **[S1-C1] Crear estructura base del proyecto y convenciones**
   - Criterios: árbol de carpetas + README actualizado.
   - Etiquetas: `task`, `backend`, `documentation`, `sprint-1`
   - Responsable: Backend

2. **[S1-C2] Implementar script `ingest_raw.py` (MVP)**
   - Criterios: descarga/copia raw + validación básica de columnas.
   - Etiquetas: `task`, `data-engineering`, `backend`, `sprint-1`
   - Responsable: Backend

3. **[S1-C3] Definir `.env.example` y parámetros de entorno**
   - Criterios: variables obligatorias documentadas.
   - Etiquetas: `task`, `devops`, `sprint-1`
   - Responsable: DevOps

---

### EPIC-04 · Modelo analítico preliminar en estrella
**Descripción**: definir diseño lógico inicial para hechos y dimensiones del reto.

**Criterios de aceptación**:
- Diagrama del modelo en `docs/`.
- Definición de PK/FK y granularidad.
- Supuestos y riesgos de modelado identificados.

**Etiquetas**: `epic`, `data-model`, `sprint-1`, `reto-a`

**Responsable sugerido**: IA

#### Subtareas
1. **[S1-D1] Diseñar tabla de hechos y granularidad**
   - Criterios: grano explícito (anio-ccaa-indicador-fuente).
   - Etiquetas: `task`, `data-model`, `ia`, `sprint-1`
   - Responsable: IA

2. **[S1-D2] Diseñar dimensiones y diccionario de campos**
   - Criterios: dimensiones mínimas documentadas con tipos.
   - Etiquetas: `task`, `data-model`, `backend`, `sprint-1`
   - Responsable: Backend

---

### EPIC-05 · Operación del equipo: flujo GitHub + CI + calidad
**Descripción**: establecer reglas de colaboración, revisión y despliegue mínimo seguro.

**Criterios de aceptación**:
- Plantillas de issue y PR activas.
- Reglas de ramas y merge documentadas.
- CI básica ejecutándose en PR.

**Etiquetas**: `epic`, `devops`, `governance`, `sprint-1`

**Responsable sugerido**: DevOps

#### Subtareas
1. **[S1-E1] Configurar issue templates (bug/task/epic)**
   - Criterios: plantillas funcionales en `.github/ISSUE_TEMPLATE/`.
   - Etiquetas: `task`, `devops`, `documentation`, `sprint-1`
   - Responsable: DevOps

2. **[S1-E2] Crear plantilla de Pull Request**
   - Criterios: checklist DoD + impacto + evidencias.
   - Etiquetas: `task`, `devops`, `documentation`, `sprint-1`
   - Responsable: DevOps

3. **[S1-E3] Definir branch policy y estrategia de merge**
   - Criterios: documento publicado y compartido al equipo.
   - Etiquetas: `task`, `governance`, `devops`, `sprint-1`
   - Responsable: DevOps

---

## 3) Separación épicas vs subtareas

- Las **épicas** agrupan resultados de negocio/técnicos de alto nivel para Sprint 1.
- Las **subtareas** son unidades ejecutables de 0.5 a 1.5 días, asignables a una persona.
- Regla: una subtarea no debe mezclar dos dominios (ej. ingestión + dashboard).

---

## 4) Columnas propuestas del Kanban (GitHub Projects)

1. **Backlog**: todo lo no comprometido.
2. **Ready**: issue refinado con criterios y responsable.
3. **In Progress**: trabajo activo (WIP limitado por rol).
4. **In Review**: PR abierto con reviewer asignado.
5. **Blocked**: dependencia externa o impedimento.
6. **Done (Sprint)**: mergeado y validado en `develop`.

Sugerencia WIP:
- Frontend: 2
- Backend: 3
- IA: 2
- DevOps: 2

---

## 5) Plantillas propuestas

### 5.1 Plantilla de Issue (Task)
```md
## Contexto
Describe el problema o necesidad.

## Objetivo
Resultado concreto esperado.

## Alcance
- Incluye:
- No incluye:

## Criterios de aceptación
- [ ] Criterio 1
- [ ] Criterio 2
- [ ] Criterio 3

## Dependencias
Issues o PRs relacionados.

## Evidencias esperadas
Capturas, logs, notebook, outputs, etc.
```

### 5.2 Plantilla de Pull Request
```md
## Resumen
Qué cambia y por qué.

## Tipo de cambio
- [ ] feature
- [ ] fix
- [ ] refactor
- [ ] docs
- [ ] chore

## Evidencias
- Capturas / outputs / enlaces.

## Checklist DoD
- [ ] Cumple criterios de aceptación del issue.
- [ ] Tests/checks ejecutados localmente.
- [ ] Documentación actualizada.
- [ ] Sin secretos ni credenciales.
- [ ] Reviewer asignado.

## Issues relacionados
Closes #...
```

---

## 6) Normas de ramas y merges (GitHub Flow simplificado)

### Ramas
- `main`: protegida, solo producción estable.
- `develop`: integración del sprint.
- `feature/<area>-<short-name>`: trabajo de cada issue.
- `hotfix/<short-name>`: correcciones urgentes.

### Reglas de merge
1. Nunca push directo a `main` ni `develop`.
2. Todo cambio entra por PR desde `feature/*` -> `develop`.
3. `develop` -> `main` solo en cierre de sprint/release.
4. Mínimo 1 aprobación de reviewer (2 si toca infra/seguridad).
5. CI en verde obligatoria antes de merge.
6. Merge preferido: **Squash and merge** para mantener historial limpio.
7. Commits con convención sugerida: `feat:`, `fix:`, `docs:`, `chore:`.

---

## 7) Definition of Done (DoD) para Sprint 1

Una issue se considera terminada cuando:
1. Cumple todos sus criterios de aceptación.
2. Tiene PR mergeada en `develop`.
3. Incluye actualización documental si aplica.
4. Pasa checks automáticos mínimos.
5. Queda trazabilidad (issue + PR + evidencia).

---

## Recomendación de arranque del Sprint 1 (día 1)
1. Crear proyecto Kanban en GitHub con columnas propuestas.
2. Cargar las 5 épicas y sus subtareas.
3. Etiquetar por rol (`frontend`, `backend`, `ia`, `devops`).
4. Asignar responsables y estimación rápida (S/M/L).
5. Arrancar con EPIC-02 y EPIC-03 en paralelo.
