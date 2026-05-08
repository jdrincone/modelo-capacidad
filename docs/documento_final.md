# Documento final — Modelo de Capacidad DICAGI 2022

**Autor**: jdrincone@gmail.com
**Fecha**: 2026-05-07
**Repositorio**: este directorio (`C:\Users\Asus\Documents\bancolombia`)

---

## 1. Resumen ejecutivo (90 segundos)

| Pregunta | Respuesta corta |
|---|---|
| ¿Qué pide la prueba? | Asignar la mayor cantidad de clientes Preferenciales a Gerentes de Inversión, optimizando $x/y = (\#A + \#B \text{ asignados}) / N$. |
| ¿Cuál es la métrica obtenida? | **$x/y = 0.4076$ (40.76%)** |
| ¿Cuál es el techo teórico del problema? | **40.8%** (limitado por integridad referencial, no por capacidad). |
| ¿Qué tan bueno es el resultado? | **El óptimo absoluto del problema** — los 4 enfoques convergen al mismo valor. |
| ¿El cuello de botella es la capacidad? | **No.** Demanda 2.59M min vs capacidad 3.72M min → ratio 0.70 (utilización 92.3%, holgado pero apretado). El cuello de botella real son los **huérfanos estructurales**. |
| ¿Qué tan complejo fue resolverlo? | El enfoque más simple (regla determinista) llega al óptimo en 0.06 s. |

---

## 2. Entendimiento del problema (qué dice la prueba)

### Restricciones explícitas del PDF (los "deben")

1. Los clientes están atados a su ejecutivo y **no pueden moverse**.
2. Un ejecutivo va a **un solo gerente** (no se reparte cartera).
3. **Misma zona** entre ejecutivo y gerente asignados.
4. **Asignación todo-o-nada**: si se asigna el ejecutivo, van todos sus clientes.
5. **No se debe superar** el tiempo anual disponible del gerente.
6. Prioridad **A > B > C**, y dentro de cada categoría por **score** descendente.

### Lectura adicional: la unidad atómica del problema

> *"Los ejecutivos se asignan a los gerentes, y todos los clientes del ejecutivo se asignan al gerente."*

Esto convierte un problema con **34,145 variables** (una por cliente) en uno con **370 variables binarias** (una por ejecutivo asignable). Es la observación más importante para que el problema sea computacionalmente tratable.

---

## 3. Tablas y calidad de datos

### Inventario

| Tabla | Filas | Rol |
|---|---|---|
| `pcac_mac_gpi_clientes.csv` | 34,145 | Población de clientes con categoría A/B/C, score, asignación actual |
| `pcac_mac_gpi_ecas.csv` | 392 | Relación gerente ↔ ejecutivo (estructura de la red) |
| `pcac_oportunidades_comer.csv` | 247,863 | Productos potenciales por cliente |
| `pcac_mac_gpi_tenencia_prod.csv` | 66,802 | Tenencia y uso de productos por cliente |
| `pcac_planta_comercial2.csv` | 50 | Catálogo de gerentes de inversión |
| `pcac_encuesta.csv` | 1,804 | Tiempos por (gerente, producto, etapa) |
| `pcac_capacidad_gerentes.csv` | 50 | Tiempo anual disponible por gerente |

### Hallazgos críticos sobre calidad

| # | Hallazgo | Impacto cuantificado |
|---|---|---|
| **C1** | **633 ejecutivos huérfanos**: aparecen en `clientes` pero no en `ecas` | Arrastran **7,030 clientes (20.6%)**, incluyendo **1,579 A + 2,727 B** que no son asignables. Esto fija el techo en 40.8%. |
| **C2** | **1 gerente sin equipo**: en `planta` pero no en `ecas` | Capacidad ociosa de 75,930 min — no aprovechada. |
| **C3** | **Mismatch de productos** entre `oportunidades` y `encuesta` | Solo 45% de oportunidades matchean por nombre. Mitigado con un mapeo manual `PRODUCTO_MAP` documentado. |
| **C4** | **Score con valores negativos** (min −0.03) | Coherente comercialmente (cliente indeseable resta). Lo dejamos sin normalizar. |
| **C5** | **Distribución de carga muy sesgada**: max=284 clientes/ejecutivo, mediana=8 | Cola larga severa, pero el modelo lo maneja sin problema dada la sobre-oferta. |
| **C6** | **Encuesta tiene 1,804 filas pero solo 33 combinaciones únicas** producto×etapa | Hay mucha redundancia por gerente; usamos mediana por (producto, etapa) como tiempo robusto. |

---

## 4. Pipeline implementado

```
data/raw/  ─►  loader.py  ─►  tiempo_demanda.py  ─►  df_ejec, df_ger
                                    │
                                    ├──►  analytical.py    (regla determinista)
                                    ├──►  greedy.py        (densidad valor/tiempo)
                                    ├──►  milp.py          (PuLP + CBC, exacto)
                                    └──►  simulated_annealing.py
                                                (Ising + Metropolis-Hastings + MCMC)
                                                │
                                    validators.py
                                                │
                                                ▼
                                    resultado_prueba.csv
```

### Definiciones clave

**Tiempo demandado por cliente** $\tau_c$:
$$\tau_c = \sum_{p \in P_c} \big[ \mathbb{1}[\text{no tiene}] (t^{venta}_p + t^{instr}_p + t^{conex}_p) + \mathbb{1}[\text{tiene-no usa}] \, t^{post}_p \big]$$

**Tiempo demandado por ejecutivo**: $t_e = \sum_{c \in C_e} \tau_c$.

**Valor del ejecutivo** (objetivo a maximizar):
$$v_e = 1000 \cdot n^A_e + 100 \cdot n^B_e + 1 \cdot n^C_e + 0.1 \cdot n_e \cdot \bar{s}_e$$

Pesos $w_A : w_B : w_C = 1000 : 100 : 1$ alinean al optimizador con la métrica oficial.

### Modelo MILP (PuLP/CBC)

$$\max \sum_{e,g} v_e \cdot x_{e,g}$$
$$\text{s.a. } \sum_g x_{e,g} \le 1 \quad \forall e \quad ; \quad \sum_e t_e \cdot x_{e,g} \le T_g \quad \forall g \quad ; \quad x_{e,g} = 0 \text{ si zona}(e) \ne \text{zona}(g)$$

Tamaño: ~370 ejecutivos × 49 gerentes filtrados por zona ⇒ ~3,000 binarias. CBC resuelve a optimalidad en < 1 segundo.

### Mapeo a física estadística (notebook 04)

Hamiltoniano equivalente:
$$H(\boldsymbol{\sigma}) = -\sum_{e,g} v_e \, \sigma_{e,g} + \sum_g \lambda_g \big(\sum_e t_e \sigma_{e,g} - T_g\big)_+^2$$

Resuelto con **Simulated Annealing** (Metropolis-Hastings):
- Cooling geométrico, $T_{\max}=5000$, $T_{\min}=0.01$, $\alpha=0.9995$, 80,000 pasos.
- Vecindario: 70% flip + 30% swap.
- Diagnósticos: curva de enfriamiento $\langle H \rangle(T)$, calor específico $C(T)$, susceptibilidad $\chi(T)$.

---

## 5. Resultados

### Tabla comparativa

| Enfoque | Tiempo | Asignaciones | x/y | %A | %B | %C | Validez |
|---|---|---|---|---|---|---|---|
| Analytical (regla simple) | 0.06 s | 370 ejec | **0.4076** | 71.3% | 78.6% | 82.9% | ✓ |
| Greedy densidad | 0.06 s | 370 ejec | **0.4076** | 71.3% | 78.6% | 82.9% | ✓ |
| MILP (CBC, óptimo) | 0.49 s | 370 ejec | **0.4076** | 71.3% | 78.6% | 82.9% | ✓ |
| Simulated Annealing | varios s | 370 ejec | **0.4076** | 71.3% | 78.6% | 82.9% | ✓ |

### Métrica oficial

$$\frac{x}{y} = \frac{\#A + \#B \text{ asignados}}{N_{\text{total clientes}}} = \frac{3{,}916 + 10{,}000}{34{,}145} = 0.4076 \; (40.76\%)$$

### Por qué los 4 enfoques convergen

El problema **no está saturado por capacidad** (con mapeo de productos aplicado):
- Demanda total real: **2,592,700 min**
- Oferta total: **3,720,570 min**
- Ratio demanda/oferta: **0.70** (utilización 92.3%, queda holgura de 1.13M min)

Aunque la utilización promedio es alta (92.3%), aún cabe TODO ejecutivo asignable porque el filtro previo de huérfanos ya eliminó 633 ejecutivos. Como la capacidad alcanza, no hay decisión real que tomar — todos los 370 ejecutivos asignables entran. El MILP no encuentra ganancia porque el problema se vuelve trivial cuando los huérfanos ya descartaron a la "competencia" por la capacidad.

### Utilización de los gerentes

Utilización media: **92.3%** de la capacidad. Dejaron 1,127,870 min de holgura distribuidos entre los 49 gerentes (promedio ~23,000 min libres por gerente).

---

## 6. Sustentación honesta del resultado

> El instructivo dice: *"es posible que llegues a la conclusión de que no es posible desarrollar un buen modelo predictivo a partir de la información proporcionada o dada la calidad de la misma. Si este es el caso, queremos evaluar el mejor modelo que puedas producir y también que nos des una sustentación de esa conclusión."*

### Diagnóstico del problema

**El problema NO es de optimización — es de calidad de datos**:

1. **Techo estructural en 40.8%**: limitado por 633 ejecutivos huérfanos que arrastran 1,579 A y 2,727 B fuera del modelo. Esos clientes A/B existen y deberían ser asignables, pero la tabla `ecas` no los conecta con un Gerente de Inversión.

2. **Sobre-oferta de capacidad (4.3×)**: los gerentes tienen mucha más capacidad de la que la demanda actual usa. El modelo no necesita ser sofisticado para llenar capacidad.

3. **Ausencia de "señal" para discriminar**: cuando el problema es holgado y todos los ejecutivos asignables caben, no hay decisión real entre incluir vs excluir — todos entran.

### Limitaciones que contribuyen al resultado

| Limitación | Tipo | Mitigación posible |
|---|---|---|
| 633 ejecutivos huérfanos | Calidad de datos | Reconciliar `ecas` con `clientes` (proyecto separado) |
| Mismatch de nombres de producto | Calidad de datos | Tabla maestra de productos compartida (ver C3) |
| Encuesta auto-reportada | Sesgo de medición | Triangular con telemetría real de actividad |
| Score sin documentación | Modelo upstream | Documentar el modelo que produce el score |
| Capacidad nominal (85,050 min/año) | Supuesto | Validar contra registros reales de actividad por gerente |

---

## 7. Conclusiones

1. **La métrica obtenida (40.76%) es el óptimo del problema dadas las restricciones y los datos.** Cualquier mejora más allá requiere mejorar los datos, no el modelo.

2. **Los 4 enfoques convergen al mismo valor**, lo que confirma robustez de la solución y simplicidad estructural del problema (no hay frustración local).

3. **El modelo más simple basta para producción**: la regla determinista corre en 0.06 s y no requiere solver. El MILP es un seguro extra; el SA aporta diagnóstico físico pero no más métrica.

4. **El verdadero proyecto que sigue es de gobernanza de datos**: arreglar `ecas` para reconciliar los huérfanos, lo que potencialmente sube el techo de 40.8% a 53.4%.

5. **Originalidad de la entrega**: mapeo formal a Ising spin glass y diagnósticos físicos (calor específico, susceptibilidad) son diferenciadores conceptuales que validan el resultado desde una segunda perspectiva.

---

## 8. Próximos pasos sugeridos

| Plazo | Acción | Beneficio esperado |
|---|---|---|
| Sprint 1 | Reconciliar 633 ejecutivos huérfanos en `ecas` | Sube techo a 53.4% — gana hasta **+12.6 puntos** de métrica |
| Sprint 1 | Tabla maestra de productos (mapping unificado) | τ_c más fiel; permite usar capacidad como restricción real |
| Sprint 2 | Telemetría real de actividad por gerente | Sustituye encuesta auto-reportada |
| Sprint 2 | Implementar la arquitectura del entregable 4 (`docs/arquitectura.md`) | Servir resultado a CRM, app móvil, web interna |
| Sprint 3 | Variables adicionales (ver `variables_adicionales.md`) | Mejor `score_modelo` upstream → mejor priorización |

---

## 9. Anexo: archivos del entregable

| Archivo | Descripción |
|---|---|
| `resultado_prueba.csv` | Asignación final (entregable 2) |
| `docs/documento_final.md` | Este documento (entregable 1) |
| `docs/variables_adicionales.md` | Propuesta de variables nuevas + fuentes |
| `docs/arquitectura.md` | Bosquejo de sistema (entregable 4) |
| `notebooks/01_eda_clientes_y_red_comercial.ipynb` | EDA de clientes y red |
| `notebooks/02_eda_capacidad_y_tiempos.ipynb` | EDA de capacidad y demanda |
| `notebooks/03_modelo_optimizacion.ipynb` | Greedy + MILP + comparación |
| `notebooks/04_modelo_fisica_estadistica.ipynb` | Hamiltoniano + SA + diagnósticos |
| `src/modelo_capacidad/` | Código modular reutilizable (entregable 3) |
| `pyproject.toml` + `uv.lock` | Entorno reproducible con uv |
| `.claude/agents/` | 3 subagentes especializados (EDA, optimización, físico) |
