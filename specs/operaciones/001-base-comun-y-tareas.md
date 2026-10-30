# SPEC operaciones-001 — Módulo Operaciones: base común y Tareas

> **Status:** Borrador
> **Depends on:** ninguna (sigue el patrón de SPEC usuarios-001 y usuarios-002)
> **Date:** 2026-10-27
> **Objective:** Crear el módulo Operaciones con su base común de campos y el primer tipo de registro, Tarea, con pantalla de lista, panel de detalle, alta, edición, cambio de estatus y comentarios en clave10.

---

## Por qué existe esta spec

El módulo Operaciones llevará el control de actividades operativas con cuatro tipos de registro: Ticket, Orden de Servicio, Acción Correctiva y Tarea. Cada uno tiene su propio formulario, flujo de estatus y criterio de cierre, pero comparten una base común de campos. Hacerlo todo en una sola spec tocaría cuatro formularios, cuatro flujos y las relaciones entre ellos, y no se podría verificar.

La Tarea va primero porque es la unidad mínima de trabajo: no involucra activos, materiales ni firma, y no depende de ningún otro tipo. Al construirla se fija la base común (folio, creador, asignado, fechas, estatus, prioridad, evidencias, comentarios, origen) que reutilizarán las specs siguientes.

Plan de specs del módulo (carpeta `specs/operaciones/`):

| Spec | Contenido |
| --- | --- |
| 001 | Base común y Tarea (esta spec) |
| 002 | Ticket (Tipos de Solicitud, SLA, triage) |
| 003 | Acción Correctiva |
| 004 | Orden de Servicio |

El orden de 002 a 004 es tentativo; se decide al terminar la 001.

## Alcance

**Dentro:**

- **Form Tareas** en LinkaForm, dentro de un módulo nuevo `operaciones` en `addons`, con la base común y los campos propios de la Tarea.
- **Backend en sanic.** `tareas_sdk.py` con las opciones `list_tareas`, `get_tarea`, `create_tarea`, `update_tarea`, `change_status`, `add_comment` y `get_tarea_options`, y su servicio en un módulo `operaciones` de `lkf-sanic-apps`, con el mismo patrón que `users_sdk.py` y `UsersAdmin`.
- **Visibilidad.** Una tarea solo la ven su creador y su asignado. No hay vista de administrador. El filtro lo aplica el backend con el usuario del JWT.
- **Front en `clave10`.** Ruta `/dashboard/operaciones/tareas` con `RequireMenuAccess requiredKey="operaciones"`: lista (`PageHeader`, `FacetSearch`, tabla TanStack con `DataTablePagination`), panel lateral de detalle, modal de alta y formulario de edición.
- **Estatus.** Pendiente → En proceso → Completada, o Cancelada. El creador y el asignado pueden cambiarlo. Una tarea Completada se puede reabrir a En proceso; una Cancelada es final. Completar no exige evidencia y guarda la fecha de cierre.
- **Vencida como condición calculada.** El backend devuelve `overdue` cuando la fecha compromiso ya pasó y el estatus es Pendiente o En proceso. La lista tiene una faceta "Vencidas". No es un estatus.
- **Comentarios.** Se agregan desde el panel. Cada cambio de estatus agrega además un comentario automático (`Estatus: Pendiente → En proceso`), que hace de historial.
- **Evidencias.** Campo de archivos del form, visible en el panel como enlaces.
- **Origen.** `origen_tipo` y `origen_id` existen en el form. En esta spec todas las tareas nacen con `origen_tipo = manual` y `origen_id` vacío. Si una tarea trae origen, el panel lo muestra.

**Fuera de alcance (otra spec):**

- Los tipos Ticket, Orden de Servicio y Acción Correctiva (specs 002 a 004).
- Generar tareas derivadas desde otro registro (botón "Generar tarea"): lo agrega cada spec del tipo de origen.
- Recurrencia de tareas, ni siquiera como campo. El motor que genera instancias (¿Airflow?, ¿con cuánta anticipación?) es una pregunta abierta de Ingeniería y va en su propia spec.
- Una vista de administrador que vea todas las tareas.
- Validar la key `operaciones` en el backend; el backend solo exige JWT, como en `admin_users`.
- Notificaciones por correo al asignar o vencer una tarea.
- Tablero kanban, vista de tarjetas y reportes.
- Dar de alta el ítem "Operaciones" en el catálogo de menús: lo hace el usuario a mano, como con "Usuarios".

## Modelo de datos

Un form nuevo **Tareas** en `addons/lkf_addons/addons/operaciones/items/forms/Operaciones/tareas.xml`. Los `field_id` se generan al crear el form y se fijan en el XML. No se inventan aquí.

```text
Base común (se repetirá en Ticket, OS y AC)
  Folio          texto, autogenerado con contador por cuenta, formato TA-00001
  Creador        usuario que da de alta, lo fija el backend con el JWT
  Asignado       select sobre el catálogo de usuarios (catalogs/Base/usuarios.xml)
  Fecha creación la fija LinkaForm
  Fecha compromiso   fecha
  Fecha cierre   fecha, la fija el backend al pasar a Completada o Cancelada
  Estatus        pendiente | en_proceso | completada | cancelada
  Prioridad      baja | media | alta | critica
  Evidencias     campo de archivos
  Comentarios    grupo repetible: Texto, Autor, Fecha
  Origen tipo    manual | ticket | orden_servicio | accion_correctiva   (default manual)
  Origen id      texto, vacío en esta spec

Propios de Tarea
  Título         texto, requerido
  Descripción    texto largo
```

Rutas en `lkf-sanic-apps` y opciones de `tareas_sdk.py` (patrón de `users_sdk.py`):

```text
list_tareas       { filtros, page, page_size }              -> { rows: TareaRow[], total }
get_tarea         { id }                                    -> { tarea: TareaDetail }
create_tarea      { title, description, assigned_to, due_date, priority, evidences? } -> { id, folio }
update_tarea      { id, title?, description?, assigned_to?, due_date?, priority?, evidences? } -> { id }
change_status     { id, status }                            -> { id, status }
add_comment       { id, text }                              -> { id }
get_tarea_options {}                                        -> { priorities[], statuses[], users[] }
```

```ts
type TareaStatus = "pendiente" | "en_proceso" | "completada" | "cancelada";
type TareaPriority = "baja" | "media" | "alta" | "critica";

interface TareaRow {
  id: string; folio: string; title: string;
  status: TareaStatus; priority: TareaPriority;
  assigned_to: { user_id: number; name: string };
  created_by: { user_id: number; name: string };
  due_date: string | null; overdue: boolean; created_at: string;
}
interface TareaDetail extends TareaRow {
  description: string; closed_at: string | null;
  evidences: { name: string; url: string }[];
  comments: { text: string; author: string; date: string; system: boolean }[];
  origin_type: "manual" | "ticket" | "orden_servicio" | "accion_correctiva";
  origin_id: string | null;
}
```

Reglas de transición de `change_status` (el backend rechaza cualquier otra):

```text
pendiente   -> en_proceso | cancelada
en_proceso  -> completada | cancelada | pendiente
completada  -> en_proceso
cancelada   -> (ninguna)
```

Solo el creador o el asignado pueden llamar `get_tarea`, `update_tarea`, `change_status` y `add_comment` sobre una tarea; para cualquier otro usuario regresan 403.

## Plan de implementación

1. **Módulo y form (addons).** Crear `addons/lkf_addons/addons/operaciones/` desde `_template` con el form `tareas.xml` (campos del modelo, folio con contador) y registrar el módulo. Instalar con `lkfaddons install -m operaciones -i forms`. Prueba: capturar una tarea a mano en LinkaForm y ver el folio `TA-00001`.
2. **Servicio base en sanic.** Crear el módulo `operaciones` en `lkf-sanic-apps` con el servicio de Tareas, `get_tarea_options` y el filtro de visibilidad (creador o asignado) a partir del JWT. Prueba: `get_tarea_options` regresa prioridades, estatus y usuarios.
3. **Lectura.** `list_tareas` (filtros por estatus, prioridad, asignado, texto y `overdue`; paginación) y `get_tarea`, calculando `overdue`. Prueba: con dos usuarios, cada uno solo ve sus tareas; un tercero recibe 403 en `get_tarea`.
4. **Escritura.** `create_tarea` (fija creador, folio, estatus `pendiente` y origen `manual`), `update_tarea`, `change_status` con la tabla de transiciones y fecha de cierre, y `add_comment`. Cada cambio de estatus agrega su comentario automático. Prueba: curl al runner recorriendo pendiente → en proceso → completada → en proceso, y una transición inválida rechazada.
5. **`tareas_sdk.py`.** Exponer las siete opciones con el patrón de `users_sdk.py` y verificar que el runner las despacha. Prueba: llamar cada opción con un JWT de usuario.
6. **Front: servicio y hooks.** `clave10/src/lib/tareas-sdk.ts`, `hooks/Operaciones/useTareas.ts` y `useTareasFilters.ts`, siguiendo `users-sdk.ts` y `hooks/Users/`.
7. **Front: lista.** `app/dashboard/operaciones/tareas/{layout,page}.tsx` con `RequireMenuAccess requiredKey="operaciones"`, y `components/Operaciones/TareasTable.tsx` y `tareas-columns.tsx` (badge de estatus, de prioridad y marca de vencida). Prueba: la lista carga con paginación de 20 y la faceta "Vencidas" filtra.
8. **Front: panel de detalle.** `TareaPanel.tsx` con datos, origen, evidencias, comentarios (con formulario para agregar), botones de cambio de estatus según las transiciones válidas y confirmación al cancelar. Prueba: avanzar el estatus desde el panel agrega el comentario automático.
9. **Front: alta y edición.** `TareaFormModal.tsx` con título y asignado requeridos, descripción, fecha compromiso, prioridad y evidencias, y la edición del mismo formulario. Antes de escribirlo, revisar cómo el front de clave10 sube archivos hoy y reutilizar ese mecanismo para Evidencias. Prueba: crear una tarea y verla en la lista del asignado.
10. **Commits.** Commit y push en cada submódulo (`addons`, `lkf-sanic-apps`, `clave10`) y luego los punteros del paraguas, verificando con `git submodule foreach 'git log --oneline @{u}..HEAD'`.

## Criterios de aceptación

- [ ] `/dashboard/operaciones/tareas` carga sin errores en consola y lista tareas con paginación de 20.
- [ ] Un usuario sin la key `operaciones` no accede a la ruta.
- [ ] Crear una tarea desde el modal deja estatus `pendiente`, prioridad elegida, creador igual al usuario del JWT, `origen_tipo = manual` y un folio `TA-NNNNN` consecutivo.
- [ ] Crear una tarea sin título o sin asignado se rechaza con mensaje.
- [ ] El creador y el asignado ven la tarea en su lista; un tercer usuario no la ve.
- [ ] Un tercer usuario que llama `get_tarea`, `update_tarea`, `change_status` o `add_comment` sobre esa tarea recibe 403.
- [ ] El creador y el asignado pueden pasar la tarea de `pendiente` a `en_proceso` y de `en_proceso` a `completada`.
- [ ] Una transición fuera de la tabla (por ejemplo `pendiente` → `completada`, o cualquiera desde `cancelada`) se rechaza en el backend.
- [ ] Completar una tarea sin evidencias es válido y guarda `closed_at`.
- [ ] Una tarea `completada` se puede reabrir a `en_proceso` y su `closed_at` se limpia.
- [ ] Cada cambio de estatus agrega un comentario automático con estatus anterior y nuevo, visible en el panel.
- [ ] Un comentario agregado desde el panel aparece con autor y fecha.
- [ ] Una tarea `pendiente` o `en_proceso` con fecha compromiso pasada tiene `overdue = true` y la muestra la faceta "Vencidas"; una `completada` con fecha pasada tiene `overdue = false`.
- [ ] Editar título, descripción, asignado, fecha compromiso y prioridad actualiza el registro; el folio y el creador no cambian.
- [ ] Las evidencias subidas aparecen como enlaces en el panel.
- [ ] `git submodule foreach 'git log --oneline @{u}..HEAD'` regresa vacío antes de pushear el paraguas.

## Decisiones tomadas y descartadas

- **Sí:** partir el módulo en una spec por tipo de registro, empezando por Tarea. **No** los cuatro juntos: cuatro flujos y las relaciones entre ellos harían la spec inverificable. **No** empezar por Ticket: arrastra el catálogo de Tipos de Solicitud, el SLA y preguntas de Producto abiertas.
- **Sí:** los specs del módulo viven en `specs/operaciones/NNN-slug.md`, con carpeta propia, y no con el prefijo `operaciones-NNN` de los de usuarios.
- **Sí:** el mismo patrón que usuarios: un form por tipo en LinkaForm, backend `*_sdk.py` en sanic y front en clave10. **No** una colección propia en Mongo: se perderían workflows, reglas y trazabilidad nativas.
- **Sí:** la base común vive en cada form como campos con los mismos nombres, no en un form compartido. Cada tipo tiene su flujo y su cierre, y así no hay un form padre que acople a los cuatro.
- **Sí:** la visibilidad es solo creador y asignado, sin vista de administrador. Se decidió así de forma expresa. Si más adelante se necesita supervisión, va en otra spec con su permiso.
- **Sí:** el creador y el asignado pueden cambiar el estatus. **No** solo el asignado, **no** exigir evidencia para completar: la definición dice "con evidencia si aplica".
- **Sí:** reabrir una Completada a En proceso. **No** reabrir una Cancelada; se crea otra tarea.
- **Sí:** Vencida calculada en el backend, no estatus, como pide la definición del módulo.
- **Sí:** comentarios como grupo repetible dentro del form Tareas, y el historial de estatus como comentarios automáticos en ese mismo grupo. **No** un form aparte de comentarios: agrega un form y una consulta para un dato que hoy solo usa un tipo. Si las specs 002 a 004 lo piden, se migra entonces.
- **Sí:** `origen_tipo` y `origen_id` desde ahora, solo manual. Las specs de Ticket, AC y OS agregarán el botón "Generar tarea" sin tocar el form.
- **No:** recurrencia, ni como campo. Queda fuera hasta que Ingeniería defina el motor.
- **No:** validar la key `operaciones` en el backend. Se resuelve para todas las rutas de administración en su propia spec, igual que en usuarios.
- **Sí:** dejar abiertas las preguntas del documento de origen que pertenecen a otros tipos (pase vigente del contratista en OS, plazo de autocierre del ticket, AC sin hallazgo). Se resuelven en sus specs.

## Riesgos identificados

| Riesgo | Mitigación |
| --- | --- |
| No sé cómo el front de clave10 sube archivos a un campo de archivos del form | El paso 9 empieza revisando el mecanismo existente. Si no hay uno reutilizable, las evidencias pasan a una spec propia y esta se entrega sin subir archivos desde el front |
| El filtro por creador o asignado depende de resolver el `user_id` del JWT en sanic | El paso 2 lo prueba con dos usuarios antes de escribir nada más |
| El contador del folio puede no ser por cuenta o duplicarse en altas concurrentes | El paso 1 usa el contador nativo de LinkaForm y el criterio de aceptación exige folios consecutivos |
| El grupo repetible de comentarios se reescribe completo en cada edición y dos escrituras simultáneas pueden pisarse | `add_comment` lee y escribe en la misma llamada; el riesgo se acepta por el bajo volumen |
| El catálogo de usuarios solo trae usuarios que ya pasaron por el alta; uno sin sincronizar no aparece como asignable | `get_tarea_options` lee del catálogo y se documenta en la prueba del paso 2 |
| Los forms de otras cuentas no reciben el módulo hasta mezclar su rama de `addons/modules` | Se instala en la cuenta de desarrollo; el despliegue por cuenta queda fuera de la spec |

## Lo que **no** está en esta spec

- Ticket, Orden de Servicio y Acción Correctiva.
- Generar tareas desde otro registro.
- Recurrencia de tareas y su motor.
- Vista de administrador, notificaciones, kanban, tarjetas y reportes.
- Validación de la key `operaciones` en el backend.
- Alta del ítem "Operaciones" en el catálogo de menús.
