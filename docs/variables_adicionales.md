# Variables adicionales para mejorar el modelo

> Respondiendo a: *"qué otros datos o atributos de los clientes, de su comportamiento frente al banco, o de la transacción añadirías al conjunto de datos, para desarrollar un modelo predictivo más efectivo."*

Este documento propone variables nuevas, organizadas por **origen** (interno / externo / scraping) y evaluadas por **factibilidad y costo** según el instructivo.

---

## 1. Marco para evaluar cada variable

Cada variable se evalúa con 4 dimensiones:

| Dimensión | Pregunta |
|---|---|
| **Valor incremental** | ¿Cuánto mejora la priorización A/B/C o el cálculo de τ_c? |
| **Factibilidad** | ¿Existe? ¿Hay maestra de datos? ¿Hay restricciones legales? |
| **Costo** | ¿Es interno (gratis), proveedor (caro), scraping (medio)? |
| **Latencia** | ¿Tiempo entre necesidad y disponibilidad? |

Notación de costo: 🟢 bajo · 🟡 medio · 🔴 alto.

---

## 2. Variables INTERNAS (data warehouse Bancolombia)

### Comportamiento transaccional

| Variable | Por qué importa | Costo | Donde está |
|---|---|---|---|
| **Transacciones / mes (volumen y monto)** | Cliente activo vs pasivo. Activos compran más productos → impacta τ_c real. | 🟢 | Core bancario, tabla de movimientos |
| **Recencia última transacción** | Cliente \"durmiente\" (>90 días sin movimiento) vale menos en valor esperado. | 🟢 | Mismo |
| **Ticket promedio de transacción** | Proxy de capacidad financiera real, mejor que solo segmento. | 🟢 | Mismo |
| **Diversidad de canales usados** | Cliente que usa solo app es más rentable de atender que el que va a oficina. | 🟢 | Logs canales |
| **# productos activos vs contratados** | Refina la fórmula de τ_c (caso "tiene pero no usa"). | 🟢 | `pcac_mac_gpi_tenencia_prod` ya cubre, pero falta granularidad |

### Histórico de campañas

| Variable | Por qué importa | Costo |
|---|---|---|
| **Tasa de respuesta histórica del cliente a ofertas** | Cliente que nunca responde → asignar tiempo allí es desperdicio. | 🟢 |
| **# productos vendidos en últimos 12 meses por ese cliente** | Trayectoria comercial (\"momentum\"). | 🟢 |
| **Última fecha de contacto comercial** | Sobre-contactar deteriora NPS; el modelo debería penalizar saturación. | 🟢 |

### Riesgo y permanencia

| Variable | Por qué importa | Costo |
|---|---|---|
| **Antigüedad del cliente (años)** | Más antiguo → menor riesgo de fuga, mayor LTV. | 🟢 |
| **Score de churn (probabilidad de cancelación a 6 meses)** | Cliente en riesgo de fuga → priorizar **retención** más que venta. | 🟢 si existe modelo, 🟡 si hay que crearlo |
| **Score de cross-sell** | Probabilidad de aceptar un producto nuevo. Si la combinas con τ_c obtienes \"valor esperado por minuto\". | 🟡 |
| **NPS / satisfacción** | Detractores no se les vende, se les retiene. | 🟢 |

### Comportamiento del ejecutivo (el lado de la oferta)

| Variable | Por qué importa | Costo |
|---|---|---|
| **Tasa histórica de cierre del ejecutivo** | Algunos ejecutivos venden más por minuto invertido que otros. Afecta la traducción de τ_c → ventas reales. | 🟢 |
| **Tiempo real medido por actividad (no encuesta)** | Reemplaza el dato auto-reportado, sesgado al alza o a la baja. | 🟢 (existe en CRM) |
| **Antigüedad del ejecutivo en su cargo** | Curva de aprendizaje: nuevo ejecutivo = más lento. | 🟢 |
| **Especialización por producto** | Un ejecutivo experto en renta fija lo vende más rápido. | 🟢 |

---

## 3. Variables EXTERNAS (proveedores comerciales)

### Buró de crédito / información financiera

| Variable | Fuente | Costo | Latencia |
|---|---|---|---|
| **Score DataCrédito / Cifin / TransUnion** | DataCrédito Experian, Cifin (TransUnion Colombia) | 🔴 (~$2-5 USD por consulta) | < 5 s API |
| **Endeudamiento total (sistema financiero)** | Mismo | 🔴 | < 5 s |
| **Reportes negativos** | Mismo | 🟡 | < 5 s |

> **Cómo se compra**: contrato corporativo con DataCrédito o TransUnion. Bancolombia ya debería tenerlo. **Limitación legal**: solo para clientes con autorización de tratamiento (Habeas Data — Ley 1266 de 2008). No usar para perfilamiento sin consentimiento.

### Sociodemográficos enriquecidos

| Variable | Fuente | Costo |
|---|---|---|
| **Estrato socioeconómico** | DANE, vía dirección de residencia | 🟢 |
| **Composición del hogar** | RUE / declaración de renta | 🟡 |
| **Ingresos declarados** | DIAN (con autorización) o RUT | 🟡 |
| **Cargo / industria laboral** | Planilla PILA o LinkedIn | 🟢-🟡 |

### Macro y sectoriales

| Variable | Fuente | Costo |
|---|---|---|
| **Tasa de cambio USD/COP, IBR, DTF** | Banco de la República (API gratis) | 🟢 |
| **Índice de precios al consumidor** | DANE | 🟢 |
| **Sector económico CIIU del cliente** | Ya está en `clientes.cod_ciiu` | 🟢 |
| **Performance del sector** | Asobancaria, Fedesarrollo | 🟡 |

---

## 4. Variables vía SCRAPING / web público

### LinkedIn (perfiles públicos)

**Qué obtener**:
- Cargo actual y empresa.
- Antigüedad en la empresa actual.
- Educación formal (universidad, postgrado).
- Cambio de cargos en últimos 5 años (carrera ascendente vs estancada).

**Cómo**:
- API oficial de LinkedIn Sales Navigator (corporativo, $$$ pero limpio).
- Scraping con `Playwright` + rotación de user agents + proxies residenciales (más barato pero **viola TOS de LinkedIn**).
- **Recomendado**: Sales Navigator o un proveedor third-party con licencia (Apollo, ZoomInfo).

**Costo**: 🟡 ($100-500 USD/mes para Sales Navigator por usuario).
**Riesgo legal**: scraping directo viola TOS; usar API o proveedor.

### Redes sociales (Twitter/X, Instagram)

**Qué obtener**:
- Engagement con marcas financieras (señal de interés en productos).
- Eventos de vida públicos (boda, nacimiento, mudanza) → triggers de venta.

**Cómo**: API oficial X (caro), o proveedores como Brand24, Meltwater.
**Costo**: 🔴.
**Caveat**: privacidad y representatividad (no todos están en redes).

### Bienes raíces y patrimonio visible

| Fuente | Cómo |
|---|---|
| Catastro distrital (Bogotá, Medellín) — APIs públicas | Inmuebles registrados por NIT/CC |
| Registraduría / SIIF | Vehículos, propiedades |
| Notarías (escrituras públicas) | Compras grandes (señal de liquidez) |

**Costo**: 🟢-🟡.
**Latencia**: medio (catastro mensual; notarías diaria con scraping).

### Actividad empresarial (para clientes con empresa)

| Fuente | Cómo |
|---|---|
| Cámara de Comercio (RUES) | Estado de la matrícula, capital, representante legal |
| SECOP | Contratación pública |
| EMIS / Compustat | Estados financieros |
| Confecámaras | Renovación mercantil |

**Costo**: 🟢 (RUES gratis vía API), 🔴 (EMIS).

---

## 5. Variables COMPORTAMENTALES de productos

| Variable | Por qué importa | Origen |
|---|---|---|
| **Volatilidad mensual del saldo en cuentas** | Cliente con flujos altos = candidato natural a inversión. | Core |
| **Saldo promedio últimos 12 meses** | Capacidad de inversión real. | Core |
| **Concentración de patrimonio en Bancolombia** | Si tiene 80% en Bcolombia → priorizar retención y diversificación. | Core + buró |
| **Histórico de uso de productos de inversión** | Mejor predictor de aceptación que la categoría A/B/C. | Core |
| **Reacción a tasas (re-balanceo de portafolio)** | Cliente sofisticado = candidato a productos estructurados. | Core |

---

## 6. Variables de RED y RELACIONES

| Variable | Por qué importa | Cómo |
|---|---|---|
| **Grafo de transacciones del cliente** | Detecta clientes \"hub\" (mueven dinero entre cuentas de su grupo familiar / empresa). | Core, requiere processing en grafo (Neo4j, NetworkX) |
| **Cliente vs cliente: similaridad de comportamiento** | Recomendaciones tipo \"clientes como tú compraron X\". | Embeddings (cosine similarity sobre transacciones). |
| **Influencia social (likes a marca Bancolombia, etc.)** | Marketing micro-targeted. | Scraping + ML. |

---

## 7. Priorización (qué pediría YO con presupuesto limitado)

Si tuviera **3 meses y $50k USD** para mejorar el modelo:

### Mes 1 — gana con datos internos (costo cero o bajo)
1. Histórico de respuesta a campañas por cliente.
2. Antigüedad del cliente, tasa de cierre del ejecutivo.
3. Saldos promedio y volatilidad.
4. Reconciliar 633 huérfanos en `ecas` (proyecto de gobernanza).

> Esperado: subir métrica del techo 40.8% → 53.4% con C1 mitigado y reordenar prioridades dentro de A/B con datos comportamentales.

### Mes 2 — externos seguros
1. Score DataCrédito (acceso ya existente en banco).
2. Estrato + sector económico enriquecido.

> Esperado: refinar `score_modelo` upstream y mejorar identificación de clientes A "verdaderos" vs ruido.

### Mes 3 — telemetría
1. Tiempo real medido por actividad (instrumentación de CRM).
2. Reemplazar `pcac_encuesta` con datos observados.

> Esperado: τ_c con error <10% (vs >50% probable hoy con encuesta auto-reportada).

### NO priorizaría todavía (mes 6+)
- Scraping de redes sociales: alto costo legal/operativo, valor incremental incierto.
- Embeddings de transacciones: alto costo de implementación, esperar a tener pipeline estable.

---

## 8. Resumen ejecutivo del documento

| Categoría | # variables propuestas | Costo medio | Tiempo a producción |
|---|---|---|---|
| Internas (core + CRM) | 18 | 🟢 | 1-2 sprints |
| Externas (buró, DANE) | 7 | 🟡 | 2-3 sprints |
| Scraping (LinkedIn, RUES) | 5 | 🟡-🔴 | 3-6 sprints |
| Red/grafo | 3 | 🔴 | 6+ meses |

**Recomendación**: empezar por las internas — el ROI es inmediato y el costo es marginal. Las externas y scraping solo después de que el pipeline esté estable y la métrica del modelo plateé.

> El mensaje central: **antes de buscar más datos afuera, hay que aprovechar bien los que ya hay adentro**. Reconciliar los 633 huérfanos vale más que cualquier scraping.
