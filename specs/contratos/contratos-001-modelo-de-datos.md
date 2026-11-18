# SPEC contratos-001 — Modelo de datos de Contratistas: contratos, requerimientos, documentos, cumplimiento y sesiones

> **Status:** Borrador
> **Depends on:** SPEC empresa-001, SPEC relaciones-001
> **Date:** 2026-11-18
> **Objective:** Definir el contrato y sus recursos, el catálogo de servicios/perfiles/equipos, los requerimientos, los documentos con versiones y aprobaciones, el cumplimiento por periodo que alimenta las matrices, y las sesiones de capacitación.

---

## Por qué existe esta spec

Es la parte más grande de F0-01: casi todas las pantallas del plan (Mi Empresa, contratos, matrices, configuración) leen estas entidades. Fijar aquí los estados y las reglas que el diseño deja abiertas evita que cada tarea las invente distinto. Las convenciones comunes (formas en la cuenta del cliente, catálogos, folios, estatus calculados) están en SPEC empresa-001.

## Alcance

**Dentro:**

- **Contratos de servicio** con servicios, perfiles y equipos con cantidad, ubicaciones, empleados ligados, recurrencia y subcontratación.
- **Historial de contratos** (modificatorios).
- **Recursos de contrato**: servicios, perfiles y equipos en una sola forma.
- **Requerimientos de cumplimiento**.
- **Documentos de cumplimiento** con versiones, comentarios y aprobaciones por cliente; los acuses de ME-07 son documentos.
- **Cumplimiento de requerimientos**: una fila por sujeto × requerimiento × periodo, que alimenta las cuatro matrices.
- **Sesiones de capacitación** con temario y participantes.
- Reglas de estatus que el diseño deja abiertas, y tipos TypeScript para F0-08.

**Fuera de alcance:**

- Rutas de Sanic: ME-14 (contratos), ME-15 (motor de cumplimiento), CF-01/02/03 (configuración), F0-11 (OCR).
- Banco de preguntas de exámenes y catálogo de inspecciones: sin diseño. Aquí solo se guarda la configuración del examen.
- Catálogo maestro y mapeo: ME-13. Activos (equipos reales con placa o serie): ME-08. Sanciones e incidencias: R-07.

## Modelo de datos

### Recurrencia (estructura común)

Tanto contratos como requerimientos (examen e inspección) y sesiones usan el mismo grupo no repetible `recurrencia`. Lo captura el selector de F0-14:

| Clave | Tipo | Notas |
| --- | --- | --- |
| `tipo` | select | `Por día` \| `Semanal` \| `Mensual` \| `Configurable` |
| `dias_semana` | select múltiple | lun…dom (Por día y Semanal) |
| `cada_horas` | número | Por día: frecuencia en horas, opcional |
| `semanas_mes` | select múltiple | 1–5 (Semanal) |
| `mensual_modo` | select | `dia` (día N) \| `ordinal` (p. ej. 2.º martes) |
| `mensual_dia` / `mensual_ordinal` / `mensual_dia_semana` | número / select / select | |
| `meses` | select múltiple | ene…dic; vacío = cada `cada_n` meses |
| `cada_n` / `unidad` | número / select | Configurable: `día` \| `semana` \| `mes` \| `año` |
| `hora_desde` / `hora_hasta` | hora | default 07:00–16:00 |

### Forma **Recursos de contrato** (catálogo `recursos_de_contrato`)

Una sola forma para los tres catálogos de CF-02.

| Clave | Tipo | Notas |
| --- | --- | --- |
| `tipo` | select | `Servicio` \| `Perfil` \| `Equipo` |
| `nombre` | texto | único por `tipo` |
| `descripcion` | texto largo | |
| `categoria` | select | categorías de servicio o de equipo según `tipo`; vacío en Perfil |
| `clase` | select | solo Equipo: `Equipo` \| `Vehículo` \| `Herramienta` |
| `requerimientos` | catálogo `requerimientos_de_cumplimiento`, múltiple | Perfil solo acepta ámbito `Persona`; Equipo solo `Equipo`; Servicio cualquiera |
| `estatus` | select | `Activo` \| `Inactivo` |

### Forma **Requerimientos de cumplimiento** (catálogo `requerimientos_de_cumplimiento`)

| Clave | Tipo | Notas |
| --- | --- | --- |
| `nombre` | texto | requerido |
| `descripcion` | texto largo | |
| `tipo` | select | `Documento` \| `Examen` \| `Inspección` |
| `ambito` | select | `Empresa` \| `Persona` \| `Equipo` |
| `plataforma` | select | `Sin plataforma` \| `SAT` \| `IMSS` \| `INFONAVIT` \| `STPS` \| `Registro Público de Comercio` \| `INE` \| `Otra` |
| `plataforma_url` | texto | |
| `vigencia_modo` | select | `vigencia` (dura N desde su emisión) \| `periodo` (se entrega cada periodo) |
| `vigencia_n` / `vigencia_unidad` | número / select | modo vigencia: `días` \| `meses` \| `años`; vacío = permanente |
| `periodicidad` | select | modo periodo: `Única` \| `Mensual` \| `Bimestral` \| `Trimestral` \| `Cuatrimestral` \| `Semestral` \| `Anual` \| `Cada 3 años` \| `Cada 10 años` |
| `meses_periodo` | select múltiple | meses en que vence, si no son parejos (p. ej. ICSOE: ene, may, sep) |
| `dia_limite` | número | día del mes en que vence el periodo; default 17 |
| `recurrencia` | grupo `recurrencia` | solo Examen e Inspección: cuándo se aplica |
| `tolerancia_dias` | número | Examen e Inspección |
| `aviso_activo` / `aviso_n` / `aviso_unidad` / `aviso_repetir` | casilla / número / select / casilla | aviso antes de vencer |
| `requiere_acuse` | casilla | el periodo se cumple con un acuse (ME-07) |
| `limitante` | casilla | si no se cumple, el contrato queda En documentación y el sujeto no puede operar |
| `criterios` | grupo repetible | `texto` (qué revisa quien aprueba) |
| `documento_ejemplo` | archivo | |
| `examen` | grupo (no repetible) | `modalidad` (`fisico` \| `digital`), `intentos` (1–10), `calificacion_minima` (default 80), `preguntas_aleatorias`, `respuestas_aleatorias`, `vigencia_resultado_n`, `vigencia_resultado_unidad` |
| `inspeccion` | texto | qué inspección aplica; el catálogo de inspecciones queda para CF-01 |
| `estatus` | select | `Activo` \| `Inactivo` |

Las obligaciones de ME-07 (SAT 32-D, IMSS, INFONAVIT, CFDI de nómina, DIOT, ICSOE, SISUB) son requerimientos de ámbito Empresa, modo periodo, con `requiere_acuse`. Se cargan como datos iniciales en F0-02, no son una forma aparte.

### Forma **Contratos de servicio** (catálogo `contratos_de_servicio`)

| Clave | Tipo | Notas |
| --- | --- | --- |
| `folio` | texto | `C-0001`, lo pone el back |
| `numero_contrato` | texto | el folio propio del documento firmado (p. ej. `CPS/2026/014`), opcional |
| `relacion` | catálogo `relaciones_entre_empresas` | requerido; de ahí salen beneficiario (`cliente`) y contratista |
| `objeto` | texto | requerido |
| `descripcion` | texto largo | |
| `monto` | número | |
| `inicio` / `fin` | fecha | requeridas, `fin` ≥ `inicio` |
| `responsable` | catálogo de usuarios | quien administra el contrato del lado del cliente |
| `contrato_firmado` | archivo | PDF/JPG/PNG; lo lee F0-11 |
| `permite_subcontratacion` | casilla | |
| `servicios` | grupo repetible | `servicio` (recurso `Servicio`) |
| `perfiles` | grupo repetible | `perfil` (recurso `Perfil`), `cantidad`, `requerimientos_excluidos` (catálogo múltiple) |
| `equipos` | grupo repetible | `equipo` (recurso `Equipo`), `cantidad`, `requerimientos_excluidos` |
| `ubicaciones` | grupo repetible | `ubicacion` (catálogo de Ubicaciones existente), `estatus` (`Activa` \| `En apertura` \| `Inactiva`) |
| `empleados` | grupo repetible | `empleado` (catálogo Empleados), `perfil` (recurso `Perfil`), `ubicacion`, `fecha_alta` |
| `recurrencia` | grupo `recurrencia` | cuándo se presta el servicio |
| `estatus_manual` | select | vacío \| `Pausado` \| `Cancelado` |
| `motivo_estatus` | texto | requerido si hay `estatus_manual` |
| `estatus` | select, calculado | `Activo` \| `Por vencer` \| `En documentación` \| `Vencido` \| `Pausado` \| `Cancelado` |
| `cumplimiento_pct` | número, calculado | global del contrato |
| `cumplimiento_contrato_pct` / `cumplimiento_empleados_pct` / `cumplimiento_periodicos_pct` | número, calculado | los tres anillos del detalle |

**Estatus del contrato** (lo calcula el back al guardar, al cambiar el cumplimiento y una vez al día), en este orden; gana el primero que aplique:
1. `Cancelado` / `Pausado` si así está `estatus_manual`.
2. `Vencido` si `fin` < hoy.
3. `En documentación` si algún requerimiento `limitante` del contrato no está `Cumplido`. Es el estatus inicial de un contrato nuevo.
4. `Por vencer` si faltan 30 días o menos para `fin`.
5. `Activo`.

**Requerimientos que exige un contrato** = los de sus servicios + los de sus perfiles + los de sus equipos, menos los `requerimientos_excluidos` de cada renglón, más los requerimientos de empresa asignados a la relación (`requerimientos_asignados` en SPEC relaciones-001). Los de ámbito Persona aplican a cada empleado según el perfil con el que está ligado; los de ámbito Equipo, a cada equipo; los de ámbito Empresa, al contratista.

### Forma **Historial de contratos**

Un registro por cambio del contrato (lo escribe el back, no se captura):

| Clave | Tipo | Notas |
| --- | --- | --- |
| `contrato` | catálogo `contratos_de_servicio` | |
| `evento` | select | `Creación` \| `Ubicaciones` \| `Perfiles` \| `Equipos` \| `Servicios` \| `Empleados` \| `Monto` \| `Vigencia` \| `Estatus` \| `Pausa` \| `Reanudación` \| `Cancelación` \| `Modificatorio` |
| `detalle` | texto | resumen legible ("Monto: 120,000 → 150,000") |
| `antes` / `despues` | texto (JSON) | valores de los campos que cambiaron |
| `documento` | archivo | convenio modificatorio, si lo hay |
| `autor` / `fecha` | usuario / fecha y hora | |

### Forma **Documentos de cumplimiento**

| Clave | Tipo | Notas |
| --- | --- | --- |
| `folio` | texto | `D-0001` |
| `nombre` | texto | |
| `categoria` | select | categorías de documento de ME-06 |
| `requerimiento` | catálogo `requerimientos_de_cumplimiento` | el requerimiento que cumple; vacío = documento suelto sin mapear |
| `dueno_tipo` | select | `Empresa` \| `Persona` \| `Equipo` (igual que `ambito`) |
| `dueno_empresa` | catálogo `empresas` | siempre: la empresa dueña del documento (o la del empleado o equipo) |
| `dueno_empleado` | catálogo Empleados | si `dueno_tipo = Persona` |
| `dueno_equipo` | texto (id) | si `dueno_tipo = Equipo`; apunta al activo de ME-08 |
| `periodo` | grupo (no repetible) | `clave` (`2026-05`, `2026-C2`…), `inicio`, `fin`; solo si el requerimiento es por periodo |
| `en_ceros` | casilla | acuse de declaración en ceros (ME-07) |
| `vigencia_inicio` / `vigencia_fin` | fecha | `vigencia_fin` vacía = permanente |
| `archivo` | archivo | la versión actual |
| `estatus` | select, calculado | `Por revisar` \| `Aceptado` \| `Rechazado` \| `Vencido` |
| `compartido_con` | catálogo `empresas`, múltiple | clientes que pueden verlo y aprobarlo |
| `contratos` | catálogo `contratos_de_servicio`, múltiple | contratos a los que se ligó |
| `origen` | select | `Carga` \| `Carga masiva` \| `Sesión` (otorgado al aprobar una capacitación) |
| `lectura_ia` | texto (JSON) | resultado de F0-11: confianza por campo, propietario y requerimiento sugeridos, conflictos |
| `versiones` | grupo repetible | `numero`, `archivo`, `estatus`, `subido_por`, `fecha`, `motivo_rechazo` |
| `comentarios` | grupo repetible | `autor`, `fecha`, `texto` |
| `aprobaciones` | grupo repetible | `cliente` (empresa), `decision` (`Pendiente` \| `Aprobado` \| `Rechazado`), `revisor`, `fecha`, `motivo` |

Reglas:
- **Reemplazar** un documento agrega una versión y regresa todas las `aprobaciones` a `Pendiente`. **Conservar ambos** crea otro documento.
- Rechazar exige `motivo` (F0-13).
- **Estatus del documento** con varios clientes (regla que faltaba en MX-02): `Rechazado` si algún cliente rechazó; `Aceptado` si todos los clientes de `compartido_con` que lo exigen aprobaron; si no, `Por revisar`. `Vencido` gana sobre `Aceptado` cuando `vigencia_fin` < hoy. Cada cliente ve en su matriz **su propia** decisión, no el estatus global.

### Forma **Cumplimiento de requerimientos**

La materialización que leen las matrices (MX-01, MX-04, ME-07, pestaña Requerimientos del contrato). La escribe solo el motor de ME-15; nadie la captura.

| Clave | Tipo | Notas |
| --- | --- | --- |
| `relacion` | catálogo `relaciones_entre_empresas` | el cliente que exige |
| `contrato` | catálogo `contratos_de_servicio` | vacío si viene de una asignación a la relación y no de un contrato |
| `requerimiento` | catálogo `requerimientos_de_cumplimiento` | |
| `limitante` | casilla | copia del requerimiento al generar la fila |
| `sujeto_tipo` | select | `Empresa` \| `Persona` \| `Equipo` |
| `sujeto_empresa` / `sujeto_empleado` / `sujeto_equipo` | catálogo / catálogo / texto (id) | según `sujeto_tipo`; `sujeto_empresa` siempre lleno |
| `periodo` | grupo (no repetible) | `clave`, `inicio`, `fin`, `vence` |
| `documento` | catálogo `documentos_de_cumplimiento` | el documento que lo cubre, si hay |
| `estado` | select, calculado | ver abajo |
| `estado_manual` / `motivo_manual` | select / texto | lo que el diseño llama `ccOv`: un revisor fija `No aplica` o corrige el estado con motivo |

**Estados del cumplimiento** (unifican los de documento y los de requerimiento del diseño):

| Estado | Cuándo | Se muestra como |
| --- | --- | --- |
| `Por transcurrir` | el periodo no ha empezado | gris |
| `En plazo` | periodo en curso, sin documento, aún no vence | Pendiente |
| `Por subir` | ya venció y no hay documento | Pendiente (rojo) |
| `Por revisar` | hay documento y este cliente no ha decidido | En revisión |
| `Cumplido` | este cliente aprobó y está vigente | Cumplido / Aceptado |
| `Rechazado` | este cliente rechazó | Rechazado |
| `Vencido` | estaba cumplido y venció su vigencia | Vencido |
| `En ceros` | acuse en ceros aprobado | En ceros |
| `No aplica` | `estado_manual` | No aplica |

**% de cumplimiento** = filas en `Cumplido` o `En ceros` / filas aplicables (sin `No aplica`, `Por transcurrir` ni `En plazo`). Semáforo: ≥ 90 verde, 51–89 ámbar, ≤ 50 rojo. Con esto se llenan `cumplimiento_*_pct` del contrato y `cumplimiento_pct` de la relación.

**Cuándo se generan filas:** un requerimiento único genera una fila por sujeto; uno por periodo genera las filas del año en curso (las futuras en `Por transcurrir`). El motor regenera al cambiar un contrato (renglones, empleados, ubicaciones), al cambiar un requerimiento o una asignación, y una vez al día para cambiar de periodo y marcar vencidos.

### Forma **Sesiones de capacitación**

| Clave | Tipo | Notas |
| --- | --- | --- |
| `nombre` / `descripcion` | texto / texto largo | |
| `tipo` | select | `Curso` \| `Taller` \| `Webinar` \| `Plática` |
| `instructor` | texto | |
| `fecha_inicio` / `fecha_fin` | fecha | |
| `hora_inicio` / `hora_fin` | hora | |
| `recurrencia` | grupo `recurrencia` | opcional; con `repetir_hasta` (fecha) |
| `lugar` / `enlace` | texto | la modalidad se deduce: lugar = Presencial, enlace = Virtual, ambos = Híbrida |
| `areas` | catálogo de Áreas, múltiple | |
| `cupo` | número | |
| `examen` | catálogo `requerimientos_de_cumplimiento` (tipo Examen) | opcional |
| `otorga` | catálogo `requerimientos_de_cumplimiento` | requerimiento que se cumple al aprobar |
| `temario` | grupo repetible | `tema`, `leccion`, `minutos`, `material_tipo` (`Video` \| `Lectura` \| `Presentación` \| `Cuestionario` \| `Clase en vivo`), `material_origen` (`Archivo` \| `Enlace`), `material` (archivo o URL) |
| `participantes` | grupo repetible | `empleado` (catálogo Empleados), `asistencia` (texto JSON: fecha → `Asistió` \| `Faltó`), `calificacion`, `resultado` (`Aprobado` \| `No aprobado` \| vacío) |
| `cancelada` / `motivo_cancelacion` | casilla / texto | |
| `estatus` | select, calculado | `Programada` \| `En curso` \| `Finalizada` \| `Cancelada` |

Regla: al marcar `Aprobado` a un participante (calificación ≥ `calificacion_minima` del examen, o asistencia completa si no hay examen), el back crea un Documento con `origen = Sesión`, dueño el empleado y requerimiento `otorga`, ya `Aceptado`. El temario se aplana en renglones (tema y lección se repiten) porque LinkaForm no anida grupos.

### Tipos para el front (F0-08)

```ts
type Ambito = 'Empresa' | 'Persona' | 'Equipo';
type Ref = { id: Id; nombre: string };

interface Recurrencia {
  tipo: 'Por día' | 'Semanal' | 'Mensual' | 'Configurable';
  dias_semana?: number[]; cada_horas?: number; semanas_mes?: number[];
  mensual_modo?: 'dia' | 'ordinal'; mensual_dia?: number; mensual_ordinal?: number; mensual_dia_semana?: number;
  meses?: number[]; cada_n?: number; unidad?: 'día' | 'semana' | 'mes' | 'año';
  hora_desde?: string; hora_hasta?: string;
}

interface RecursoContrato {
  id: Id; tipo: 'Servicio' | 'Perfil' | 'Equipo'; nombre: string; descripcion?: string;
  categoria?: string; clase?: 'Equipo' | 'Vehículo' | 'Herramienta';
  requerimientos: Ref[]; estatus: Estatus;
}

interface Requerimiento {
  id: Id; nombre: string; descripcion?: string;
  tipo: 'Documento' | 'Examen' | 'Inspección'; ambito: Ambito;
  plataforma: string; plataforma_url?: string;
  vigencia_modo: 'vigencia' | 'periodo';
  vigencia?: { n: number; unidad: 'días' | 'meses' | 'años' } | null;   // null = permanente
  periodicidad?: string; meses_periodo?: number[]; dia_limite?: number;
  recurrencia?: Recurrencia; tolerancia_dias?: number;
  aviso?: { n: number; unidad: string; repetir: boolean } | null;
  requiere_acuse: boolean; limitante: boolean; criterios: string[];
  documento_ejemplo?: Archivo;
  examen?: { modalidad: 'fisico' | 'digital'; intentos: number; calificacion_minima: number;
             preguntas_aleatorias: boolean; respuestas_aleatorias: boolean;
             vigencia_resultado?: { n: number; unidad: string } };
  inspeccion?: string; estatus: Estatus;
}

type EstatusContrato = 'Activo' | 'Por vencer' | 'En documentación' | 'Vencido' | 'Pausado' | 'Cancelado';

interface Contrato {
  id: Id; folio: string; numero_contrato?: string;
  relacion: Id;
  cliente: { id: Id; razon_social: string; rfc: string };
  contratista: { id: Id; razon_social: string; rfc: string };
  objeto: string; descripcion?: string; monto?: number; inicio: string; fin: string;
  responsable?: { id: number; nombre: string }; contrato_firmado?: Archivo;
  permite_subcontratacion: boolean;
  servicios: Ref[];
  perfiles: { perfil: Ref; cantidad: number; requerimientos_excluidos: Id[] }[];
  equipos: { equipo: Ref; clase: 'Equipo' | 'Vehículo' | 'Herramienta'; cantidad: number; requerimientos_excluidos: Id[] }[];
  ubicaciones: { ubicacion: Ref; estatus: 'Activa' | 'En apertura' | 'Inactiva' }[];
  empleados: { empleado: Ref; perfil: Ref; ubicacion?: Ref; fecha_alta: string }[];
  recurrencia?: Recurrencia;
  estatus: EstatusContrato; motivo_estatus?: string;
  cumplimiento: { total: number; contrato: number; empleados: number; periodicos: number };
}

interface EventoContrato {
  id: Id; contrato: Id; evento: string; detalle: string;
  antes?: Record<string, unknown>; despues?: Record<string, unknown>;
  documento?: Archivo; autor: string; fecha: string;
}

type EstatusDocumento = 'Por revisar' | 'Aceptado' | 'Rechazado' | 'Vencido';

interface Documento {
  id: Id; folio: string; nombre: string; categoria?: string;
  requerimiento: Ref | null;
  dueno: { tipo: Ambito; empresa: Ref; empleado?: Ref; equipo?: Ref };
  periodo?: { clave: string; inicio: string; fin: string }; en_ceros: boolean;
  vigencia_inicio?: string; vigencia_fin?: string | null;
  archivo: Archivo; estatus: EstatusDocumento;
  compartido_con: Ref[]; contratos: Ref[];
  origen: 'Carga' | 'Carga masiva' | 'Sesión';
  lectura_ia?: Record<string, unknown>;
  versiones: { numero: number; archivo: Archivo; estatus: EstatusDocumento; subido_por: string; fecha: string; motivo_rechazo?: string }[];
  comentarios: { autor: string; fecha: string; texto: string }[];
  aprobaciones: { cliente: Ref; decision: 'Pendiente' | 'Aprobado' | 'Rechazado'; revisor?: string; fecha?: string; motivo?: string }[];
}

type EstadoCumplimiento =
  'Por transcurrir' | 'En plazo' | 'Por subir' | 'Por revisar' | 'Cumplido' |
  'Rechazado' | 'Vencido' | 'En ceros' | 'No aplica';

interface CumplimientoFila {
  id: Id; relacion: Id; contrato: Id | null; requerimiento: Ref; limitante: boolean;
  sujeto: { tipo: Ambito; empresa: Ref; empleado?: Ref; equipo?: Ref };
  periodo: { clave: string; inicio: string; fin: string; vence: string };
  documento: Id | null; estado: EstadoCumplimiento; motivo_manual?: string;
}

interface Sesion {
  id: Id; nombre: string; descripcion?: string; tipo: 'Curso' | 'Taller' | 'Webinar' | 'Plática';
  instructor?: string; fecha_inicio: string; fecha_fin: string; hora_inicio?: string; hora_fin?: string;
  recurrencia?: Recurrencia & { repetir_hasta?: string };
  lugar?: string; enlace?: string; modalidad: 'Presencial' | 'Virtual' | 'Híbrida';
  areas: Ref[]; cupo?: number; examen: Ref | null; otorga: Ref | null;
  temario: { tema: string; leccion: string; minutos?: number;
             material_tipo: string; material_origen: 'Archivo' | 'Enlace'; material?: Archivo | string }[];
  participantes: { empleado: Ref; asistencia: Record<string, 'Asistió' | 'Faltó'>;
                   calificacion?: number; resultado?: 'Aprobado' | 'No aprobado' }[];
  estatus: 'Programada' | 'En curso' | 'Finalizada' | 'Cancelada';
}
```

## Plan de implementación

1. **Revisión** de esta spec con Maricruz junto con empresa-001 y relaciones-001.
2. **F0-02** crea las siete formas y sus catálogos, carga los requerimientos iniciales de ME-07 y registra los ids en `accesos/models.py`. Prueba: instalar en una cuenta de pruebas y capturar un registro de cada forma a mano.
3. **ME-14** implementa contratos e historial; **ME-15** el motor de cumplimiento y los estatus calculados; **CF-01/02/03** la configuración; **F0-11** la lectura con IA.
4. **F0-08** escribe los tipos y los mocks.

## Criterios de aceptación

- [ ] Cada forma tiene nombre, claves de campo, tipo y valores de select definidos.
- [ ] Están definidas las reglas de estatus de contrato, documento (con varios clientes) y cumplimiento, y el cálculo del %.
- [ ] Está definido qué requerimientos exige un contrato y a qué sujetos aplica cada uno.
- [ ] Los tipos TypeScript cubren lo que leen ME-06, ME-07, ME-09 a ME-12, CF-01 a CF-04, MX-01, MX-02, MX-04 y MX-05.
- [ ] Maricruz revisó las tres specs del modelo.

## Decisiones tomadas y descartadas

- **Sí:** cumplimiento **materializado** en su propia forma, escrita solo por el motor. **No** calcularlo en cada consulta: cuatro matrices × sujetos × requerimientos × periodos sería muy lento con agregaciones al vuelo.
- **Sí:** versiones, comentarios y aprobaciones como **grupos dentro del documento**. **No** un registro por versión: un documento es una cosa con historia, y así la lista no repite versiones.
- **Sí:** servicios, perfiles y equipos en **una sola forma** con `tipo` (CF-02 es un solo componente). **No** tres formas.
- **Sí:** tipos de requerimiento `Documento`, `Examen` e `Inspección`. **No** `Capacitación` como cuarto tipo: una capacitación es una sesión que **otorga** un requerimiento.
- **Sí:** el ámbito se llama `Persona` (no Empleado) y aplica igual en el catálogo maestro de ME-13.
- **Sí:** clases de equipo `Equipo`, `Vehículo` y `Herramienta` en todos lados.
- **Sí:** estatus del contrato calculado por el back con el orden de esta spec; contrato nuevo nace `En documentación`.
- **Sí:** cada cliente decide su aprobación; el estatus global del documento sale de la regla de esta spec.
- **Sí:** las obligaciones de ME-07 son requerimientos con `requiere_acuse`, no una forma aparte; el acuse es un documento con `periodo` y `en_ceros`.
- **Sí:** temario aplanado en renglones: LinkaForm no anida grupos repetibles.
- **Supuestos** que se pueden cambiar sin tocar el modelo: 30 días para Por vencer de un contrato, 60 para REPSE, día límite 17, calificación mínima 80, semáforo 90/50.

## Riesgos identificados

| Riesgo | Mitigación |
| --- | --- |
| La forma de cumplimiento crece mucho (sujetos × requerimientos × periodos) | Solo se generan periodos del año en curso; índices en `relacion`, `contrato`, `sujeto_*`, `periodo.clave`; medir en F0-02 con datos de prueba de tamaño real |
| El motor y los documentos se desfasan (una fila dice Por subir y ya hay documento) | Toda escritura de documentos pasa por el back, que dispara el recálculo de las filas del sujeto; tarea diaria de recálculo completo |
| Contratos con cientos de empleados en el grupo repetible | Si pasa de ~300 renglones, se mueve `empleados` a su propia forma (cambio local a ME-14, el tipo del front no cambia) |
| `dueno_equipo` apunta a activos que define ME-08 | Se guarda como id de texto; ME-08 decide si es la forma de Activos existente |
| Las reglas de estatus no coinciden con lo que espera el cliente | Están en un solo lugar (back) y son constantes; se validan en la revisión con Maricruz y en la demo |

## Lo que **no** está en esta spec

- Rutas de Sanic y permisos de menú.
- Banco de preguntas, catálogo de inspecciones, catálogo maestro y mapeo, activos, sanciones e invitaciones.
- Notificaciones y avisos enviados (MX-03): se definen con su tarea.
