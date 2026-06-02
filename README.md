# 🏦 MVP de Inteligencia Competitiva — Asociación Cibao (ACAP)

> Sistema de monitoreo de mercado y soporte a decisiones estratégicas para el mercado financiero dominicano.

---

## 📌 El Problema de Negocio

El **Encargado de Inteligencia Competitiva** de una asociación de ahorros y préstamos enfrenta un desafío cotidiano: asistir al negocio en la toma de decisiones sobre posicionamiento, precios y segmentos de clientes sin una visión consolidada del mercado.

La información existe, pero está dispersa — en reportes de agencias externas (Ipsos, Kantar, Nielsen), publicaciones del Banco Central (BCRD), y datos internos de clientes — y llega de forma inconsistente, a veces con errores críticos.

**Resultado:** decisiones basadas en intuición o información parcial, oportunidades de mercado sin explotar y reacción lenta ante movimientos de competidores.

---

## 💡 La Solución

Este MVP centraliza la inteligencia de mercado en un sistema integrado de monitoreo y reportes que permite:

- **Monitorear** tasas y posicionamiento de los 7 principales competidores del mercado financiero RD con 24 meses de historial
- **Alertar** automáticamente cuando un competidor registra cambios de tasa o eventos competitivos de alto impacto
- **Auditar** la calidad de los reportes de agencias externas antes de usarlos en decisiones
- **Segmentar** la base de clientes para identificar oportunidades de cross-sell y retención
- **Entregar** reportes ejecutivos en Power BI para VP Marketing, Gerencia y fuerza de ventas

---

## 🎯 Contexto Real: Diseñado contra Requerimientos del Puesto

Este MVP no es un ejercicio genérico. Fue construido tomando como base dos fuentes reales:

1. **La descripción oficial del puesto** de Encargado de Inteligencia Competitiva en Asociación Cibao de Ahorros y Préstamos — incluyendo sus responsabilidades clave, el perfil técnico requerido y las competencias esperadas.
2. **El perfil de LinkedIn** de un profesional con un rol equivalente en la misma institución, cuyas responsabilidades documentadas incluyen: liderar iniciativas basadas en datos, gestionar un analista senior, trabajar con agencias de investigación de mercado, producir análisis de tendencias y reportes de inteligencia competitiva, y automatizar reportes para la fuerza de ventas y líderes senior.

Cada componente del MVP está diseñado para responder a una responsabilidad concreta del rol:

| Responsabilidad del puesto | Cómo este MVP la aborda |
|---|---|
| Monitoreo competitivo continuo | Dashboard de Paisaje Competitivo con tasas de 7 instituciones, 24 meses de historial y alertas automáticas |
| Análisis sectorial y económico | Página de Tendencias Macro con indicadores BCRD (tasa de referencia, inflación, tipo de cambio) |
| Reportería estratégica | Reporte Power BI de 5 páginas con hallazgos, riesgos, oportunidades y KPIs para alta dirección |
| Investigación de mercado | Integración de reportes de agencias externas (Ipsos, Kantar, Nielsen) con auditoría de calidad |
| Análisis de datos y segmentación | Inteligencia de clientes con 4 segmentos, perfiles de comportamiento y oportunidades de cross-sell |
| Automatización de reportes | Reporte Power BI diseñado para actualización y distribución periódica; pipeline de datos prototipado como prueba de concepto |
| Desarrollo de estrategias | Hallazgos con recomendaciones concretas de posicionamiento, producto y expansión de cuota |

> El proyecto demuestra que entiendo las responsabilidades del rol, sé traducirlas en requerimientos analíticos y puedo entregar las herramientas que un Encargado de Inteligencia Competitiva necesita para operar.

---

## 👤 Mi Contribución

Este proyecto fue diseñado y liderado por mí como caso de negocio y solución de inteligencia competitiva. Mis responsabilidades:

| Área | Rol |
|---|---|
| **Caso de negocio** | Definí el problema, los objetivos y el alcance del MVP |
| **KPIs y requerimientos** | Diseñé los indicadores clave y las preguntas analíticas que el sistema debe responder |
| **Power BI** | Diseñé y desarrollé el modelo de datos, medidas DAX, tema corporativo y las 5 páginas del reporte |
| **Validación** | Verifiqué los hallazgos contra benchmarks del sector financiero dominicano |
| **Backend** | Utilicé herramientas de IA para acelerar el desarrollo de los componentes técnicos (ETL, generación de datos sintéticos, contratos de calidad) |

---

## 📊 Power BI — Reporte Ejecutivo (5 Páginas)

El corazón del MVP es el reporte Power BI, diseñado para responder preguntas estratégicas concretas:

| Página | Pregunta estratégica | Audiencia |
|---|---|---|
| **0 · Portada** | ¿Qué contiene este reporte? | Todos |
| **1 · Paisaje Competitivo** | ¿Dónde está ACAP vs. el mercado de tasas? | VP Marketing, Gerencia |
| **2 · Posición de Mercado** | ¿En qué segmentos tiene ACAP ventaja o riesgo? | VP Marketing, Planificación |
| **3 · Tendencias Macro** | ¿Qué señales del entorno BCRD deben guiar las decisiones estratégicas? | Alta gerencia |
| **4 · Inteligencia de Clientes** | ¿Quiénes son los clientes de ACAP y cuál es su potencial? | Marketing, Ventas |
| **5 · Calidad de Datos** | ¿Podemos confiar en los reportes de agencias? | Analistas, Operaciones |

---

## 🔑 Hallazgos Clave

### Posicionamiento de ACAP en el Mercado

- ACAP mantiene ventaja competitiva en **préstamos comerciales** (−0.71 pp bajo el promedio del mercado)
- En los demás productos está en **paridad** — sin diferenciación de precio
- **Brecha digital crítica:** ACAP tiene un score digital de 18.2 frente a 91.7 de BanReservas — riesgo estratégico de mediano plazo
- **Mayor oportunidad de crecimiento:** segmentos Personal y Comercial (+9% de cuota posible c/u, posición actual 4/7)

### Inteligencia de Clientes

| Segmento | Clientes | % Total | Oportunidad |
|---|---|---|---|
| Digitales — Bajo ingreso | 2,354 | 47.1% | Productos digitales de bajo costo |
| Base — Tradicionales | 1,596 | 31.9% | Migración a canales digitales |
| Digitales — Alta antigüedad | 512 | 10.2% | Retención y fidelización |
| Premium — Potencial cross-sell | 538 | 10.8% | Productos de inversión y crédito |

### Entorno Macroeconómico (BCRD)

- Tasa de referencia BCRD: **7.0%** — estable por 6 meses → ventana favorable para productos de captación
- Tipo de cambio: **60.37 DOP/USD** — presión alcista en 2026
- Inflación: **4.61%** — dentro del rango meta (4% ± 1) → entorno controlado

---

## 🛡 Calidad e Integridad de Datos

Antes de que cualquier reporte de agencia externa alimente el modelo, pasa por un proceso de auditoría automática. En el batch de prueba se detectaron **9 issues críticos** bloqueados antes de llegar al análisis:

| Agencia | Problema detectado | Severidad |
|---|---|---|
| Ipsos RD | Nombre de institución con formato incorrecto | Alta |
| Ipsos RD | Cuota de mercado = 128.5% (imposible) | Media |
| Ipsos RD | Fecha de estudio vacía | Media |
| Kantar BrandZ | NPS = 155 (fuera del rango válido −100 a 100) | Alta |
| Kantar BrandZ | Satisfacción = 102.3% (imposible) | Alta |
| Kantar BrandZ | Fila duplicada por institución/segmento | Alta |
| Nielsen Financial | Tasa = 152.0% (error tipográfico: debía ser 15.2%) | Media |
| Nielsen Financial | Institución vacía | Media |
| Nielsen Financial | Formato de fecha incorrecto (DD/MM/YYYY) | Alta |

> Este mecanismo protege la integridad de las decisiones tomadas con base en los reportes.

---

## 🗂 Componentes del MVP

### Componentes Centrales

Estos módulos forman el núcleo del producto entregable:

| Componente | Descripción |
|---|---|
| **Power BI (5 páginas)** | Reporte ejecutivo con tema corporativo, DAX avanzado y landing HTML interactiva |
| **KPIs estratégicos** | Métricas de posicionamiento, participación de mercado, score digital y alertas |
| **Monitoreo competitivo** | Seguimiento de tasas de 7 instituciones financieras, 24 meses de historial |
| **Inteligencia de clientes** | Perfiles de segmento para orientar cross-sell y estrategia de producto |
| **Calidad de datos** | Auditoría automática de reportes de agencias externas |
| **Indicadores macro (BCRD)** | Contexto macroeconómico integrado al análisis competitivo |

### Componentes de Aprendizaje y Prototipado

Los siguientes módulos fueron incluidos con fines exploratorios y de aprendizaje técnico. No representan dominio experto en estas tecnologías, sino el resultado de prototipar capacidades avanzadas con apoyo de IA:

| Componente | Tecnología explorada | Estado |
|---|---|---|
| Segmentación K-Means | scikit-learn, clustering | Prototipo funcional |
| Contratos de calidad formales | Great Expectations 1.17 | Prototipo funcional |
| Pipeline ETL automatizado | pandas, SQLAlchemy, SQLite | Prototipo funcional |
| Análisis competitivo automatizado | Python, scipy, statsmodels | Prototipo funcional |

> Estos módulos demuestran capacidad para entender, validar y comunicar soluciones técnicas complejas — no experiencia de desarrollo de software a nivel profesional.

---

## 🗃 Estructura del Repositorio

```
competitive-intelligence-acap/
│
├── docs/
│   └── executive_summary.md         # Resumen ejecutivo para VP Marketing y alta gerencia
│
├── power_bi/
│   ├── ACAP.pbix                    # Reporte Power BI (5 páginas)
│   ├── acap_theme.json              # Tema corporativo ACAP (#1E22AA, #EE2737, #00A566)
│   ├── cover_measure.dax            # Medida DAX para landing page HTML interactiva
│   └── screenshots/                 # Capturas de cada dashboard
│
├── data/
│   ├── processed/                   # Datos listos para Power BI
│   ├── agency/                      # Reportes de agencias externas (Ipsos, Kantar, Nielsen)
│   └── quality_reports/             # Resultados de auditoría de calidad
│
├── src/                             # Backend (prototipado con apoyo de IA)
│   ├── scrapers/                    # Conectores a fuentes de datos
│   ├── etl/                         # Pipeline de integración de datos
│   ├── analytics/                   # Análisis competitivo y segmentación
│   └── quality/                     # Validación y contratos de datos
│
└── sql/
    ├── schema.sql                   # Modelo de datos (6 tablas, 5 vistas analíticas)
    └── procedures/                  # Procedimientos de actualización
```

---

## 📋 Nota sobre los Datos

Los datos son **sintéticos**, generados con valores calibrados a las condiciones reales del mercado financiero dominicano (2024–2026):

- **Tasas de productos:** basadas en rangos publicados por la Superintendencia de Bancos RD
- **Indicadores macro:** calibrados con publicaciones históricas del Banco Central RD
- **Cuotas de mercado:** estimadas a partir de reportes públicos del sector
- **Clientes:** generados con distribuciones realistas para el mercado dominicano

> En producción, el sistema se conectaría a la API del BCRD, al core bancario interno y a los reportes formales de agencias.

---

## 👤 Autor

**Alfred Alonzo**  
[github.com/alfredalonzo03](https://github.com/alfredalonzo03)
