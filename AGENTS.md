# AGENTS.md — Reglas operativas del repositorio DEPORTEData

## Objetivo
Este repositorio implementa el proyecto universitario **DEPORTEData** para el **Reto A**.
El objetivo operativo es trabajar con un flujo profesional de planificación, desarrollo y entrega por sprints.

## Metodología y organización
- Marco: **Scrum ligero** con sprints semanales.
- Gestión diaria: tablero **Kanban** en GitHub Projects.
- Equipos/roles: `frontend`, `backend`, `ia`, `devops`.
- Todo el trabajo debe estar trazado mediante **Issue -> PR -> Merge**.

## Estructura de trabajo recomendada
- Épicas para objetivos de alto nivel.
- Subtareas para trabajo ejecutable de corta duración.
- Sprint 1 orientado a:
  1. definición analítica,
  2. catálogo de fuentes,
  3. base de ingestión,
  4. diseño de modelo en estrella,
  5. gobierno técnico (plantillas, CI y flujo Git).

## Flujo de ramas (GitHub Flow simplificado)
- `main`: rama protegida de publicación/estable.
- `develop`: rama de integración del sprint.
- `feature/<area>-<short-name>`: desarrollo por issue.
- `hotfix/<short-name>`: correcciones críticas.

### Reglas de merge
1. No se permite push directo a `main` ni `develop`.
2. Todo cambio debe llegar por PR desde `feature/*` hacia `develop`.
3. `develop` solo pasa a `main` en cierre de sprint/release.
4. Requiere al menos 1 aprobación (2 para infraestructura/seguridad).
5. CI obligatoria en verde para merge.
6. Método preferido: **Squash and merge**.

## Convenciones de issues y PR
- Usar plantillas en `.github/ISSUE_TEMPLATE/`.
- Toda issue debe incluir criterios de aceptación verificables.
- Toda PR debe incluir:
  - resumen,
  - tipo de cambio,
  - checklist DoD,
  - issues relacionados (`Closes #...`),
  - evidencias (logs/capturas/enlaces).

## Definition of Done (DoD)
Una tarea se considera terminada cuando:
1. Cumple criterios de aceptación.
2. Tiene PR mergeada en `develop`.
3. Incluye documentación actualizada cuando aplique.
4. Pasa checks mínimos de calidad.
5. Mantiene trazabilidad completa (issue/PR/evidencia).

## Etiquetas recomendadas
- Tipo: `epic`, `task`, `bug`, `chore`, `docs`.
- Sprint: `sprint-1`, `sprint-2`, etc.
- Dominio: `frontend`, `backend`, `ia`, `devops`, `data-model`, `analytics`, `governance`.
- Prioridad: `priority:high`, `priority:medium`, `priority:low`.

## Kanban recomendado
Columnas:
1. Backlog
2. Ready
3. In Progress
4. In Review
5. Blocked
6. Done (Sprint)

## Calidad y seguridad
- Prohibido subir secretos o credenciales.
- Mantener `.env.example` y usar gestores seguros de configuración.
- Documentar riesgos, supuestos y limitaciones analíticas.
- En análisis: no confundir correlación con causalidad.

## Documentación mínima esperada
- README actualizado.
- Catálogo de fuentes y trazabilidad.
- Diseño del modelo en estrella.
- Evidencias de validación y decisiones técnicas.
