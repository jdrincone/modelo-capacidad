# Arquitectura para servir el modelo (entregable 4)

> Bosquejo conceptual — **no se implementa**. El PDF aclara que desarrollar la aplicación no suma puntos.

## Diagrama lógico

```
                         ┌─────────────────────────┐
                         │   Orquestador batch     │
                         │   (Airflow / Step Func) │
                         └──────────┬──────────────┘
                                    │ trigger mensual / on-demand
                                    ▼
   ┌──────────┐    ┌───────────────────────────────┐    ┌──────────────┐
   │  CSV /   │───▶│  Job de modelado (Spark/      │───▶│ Tabla        │
   │  Lake    │    │  Python uv-venv)              │    │ asignaciones │
   │  raw     │    │  - load_all() → features      │    │ (Snowflake / │
   └──────────┘    │  - greedy + MILP + SA         │    │  BigQuery)   │
                   │  - validators                 │    └──────┬───────┘
                   │  - métricas (x/y, %A, %B)     │           │
                   └───────────────┬───────────────┘           │
                                   │ logs + métricas            │
                                   ▼                            │
                         ┌─────────────────┐                    │
                         │  Observabilidad │                    │
                         │  (CloudWatch /  │                    │
                         │   Datadog)      │                    │
                         └─────────────────┘                    │
                                                                │
   ┌─────────────────┐                                          │
   │  API REST       │◀─────────── consulta ───────────────────┘
   │  (FastAPI +     │
   │   Pydantic)     │
   └────────┬────────┘
            │
   ┌────────┴───────────────────┬──────────────────┐
   ▼                            ▼                  ▼
 Web interna              App móvil gerentes      CRM Salesforce
```

## Componentes

### 1. Capa batch (cómputo del modelo)

- **Trigger**: scheduled (mensual, primer día hábil) y/o manual.
- **Runtime**: contenedor Docker con `uv` y el código del repo. La misma imagen se usa en dev y prod.
- **Inputs**: snapshots de las 7 tablas en S3/ADLS o consulta directa al data warehouse.
- **Outputs**:
  - Tabla `dicagi.asignaciones_modelo_capacidad` con columnas del entregable + `run_id`, `fecha_corrida`, `version_modelo`.
  - Métricas por corrida: x/y, % A asignados, % B asignados, # ejecutivos sin asignar, tiempo de cómputo.
  - Artefactos del modelo (modelo MILP serializado, configuración SA) en S3 con versionado.

### 2. Capa de servicio (API)

- **Stack**: FastAPI + Pydantic + uvicorn detrás de un API Gateway autenticado (mTLS / OAuth2).
- **Endpoints clave**:
  - `GET /asignacion/cliente/{num_doc_cli}` → gerente y ejecutivo asignados, score, prioridad.
  - `GET /asignacion/gerente/{cod_gte_inv}` → lista de clientes asignados, carga acumulada de tiempo.
  - `GET /asignacion/ejecutivo/{cod_ejec_bco}` → reporte del ejecutivo.
  - `GET /metricas/run/{run_id}` → KPIs de la corrida.
- **Respuesta**: JSON, idempotente, con `Last-Modified` y `ETag` para cache HTTP.

### 3. Cache

- Redis para latencias < 50 ms en consultas frecuentes (look-up por cliente).
- Invalidación: cada vez que el batch publica un nuevo `run_id`, se hace flush selectivo.

### 4. Capa de datos

- Tabla principal en data warehouse columnar (Snowflake / BigQuery / Redshift) particionada por `fecha_corrida`.
- Histórico completo (no se sobrescribe), permite trazabilidad y análisis de evolución.
- Vista materializada `asignacion_vigente` con la última corrida.

## Calidad y MLOps

- **Tests**: unitarios (pytest), integración (datos sintéticos pequeños), validación post-corrida (todos los `validators.py` deben pasar antes de publicar).
- **Versionado**: el modelo (greedy / MILP / SA + sus pesos) se versiona con SemVer + tag git. La metadata de la corrida guarda la versión.
- **Reproducibilidad**: `uv.lock` congela dependencias; seeds fijos para SA. Cada corrida es reproducible bit-a-bit dado el mismo input.
- **Monitoreo de drift**: alerta si la distribución A/B/C, la capacidad agregada o el ratio demanda/capacidad cambia > 15% mes a mes.
- **A/B testing**: posibilidad de correr dos versiones del modelo en paralelo y comparar la métrica x/y.

## Seguridad

- Datos PII (números de documento) cifrados en tránsito (TLS 1.3) y en reposo (KMS).
- Tokens en tablas → en producción se hashean antes de exponer en API pública.
- Logs no contienen documentos completos (solo tokens parciales).
- Acceso a la API por roles (gerente, regional, supervisor).

## Costos esperados (orden de magnitud)

| Componente | Tipo | Costo aprox. mensual |
|---|---|---|
| Job batch (1 corrida/mes, ~10 min en máquina mediana) | EC2 / Cloud Run | < 5 USD |
| Almacenamiento warehouse (histórico de asignaciones) | columnar | < 20 USD |
| API (1k requests/día) | FastAPI sobre Cloud Run | < 30 USD |
| Cache Redis | t3.micro | ~15 USD |
| **Total estimado** | | **< 100 USD/mes** |

## Roadmap evolutivo

1. **v1** — entregable batch + tabla en warehouse + Power BI conectado.
2. **v2** — API REST con autenticación.
3. **v3** — re-run interactivo: el gerente puede simular asignaciones (what-if) cambiando capacidad o pesos.
4. **v4** — integración con CRM (Salesforce) y push a app móvil de gerentes.
5. **v5** — modelo en streaming si la red comercial cambia rápido (alta/baja de ejecutivos).
