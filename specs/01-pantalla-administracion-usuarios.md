# SPEC 01 — Pantalla de administración de usuarios

> **Status:** Aprobado
> **Depends on:** ninguna
> **Date:** 2026-10-20
> **Objective:** Una pantalla en Administración (clave10) para listar, dar de alta, editar y restaurar la contraseña de los usuarios del form Usuarios, con panel lateral de detalle que muestra los empleados ligados.

---

## Por qué existe esta spec

Hoy los usuarios se dan de alta capturando el form Usuarios directo en LinkaForm. No hay vista de administración en clave10 y no hay forma de restaurar una contraseña: el único correo con liga es el de bienvenida, disparado por el estatus `crear`. Esta spec agrega la pantalla, el flujo de restauración y la vista de empleados ligados.

## Alcance

**Dentro:**

- Ruta `/dashboard/users` con lista: `PageHeader`, `FacetSearch`, tabla azul (`#DBEAFE`) con badge de estatus y `DataTablePagination`, con TanStack Table (columnas en archivo aparte) como la bitácora de `media/bb.png`. Sin tabs Personal/Vehículos ni toggle de vistas: solo tabla.
- Panel lateral de detalle (mismo patrón que `WorkflowLogPanel` / panel de script-logs) con datos del usuario y la sección **Empleados ligados** (solo lectura, con "Ver registro").
- Alta: botón "+ Nuevo usuario" con nombre, username, email, teléfono, **Rol** y opción Empleado (crear / ligar por nombre exacto). Dispara el flujo existente (estatus `crear` → correo con liga de activación).
- Edición de nombre, teléfono, **Rol** y email. Se actualiza el registro y se sincroniza el usuario de LinkaForm. `username` e `Id de Usuario` no son editables.
- Botón "Restaurar contraseña" visible solo en usuarios con estatus `activado`: nuevo estatus `restaurar` en el form, token nuevo, correo con liga a `/auth/set-password`. Al restaurar contraseña debe de crear un token nuevo y enviar correo a usuario.
- Renombrar la etiqueta "Puesto" a "Rol" en el form Usuarios (`field_id` `67be0c43a31e5161c47f2bbb`, no cambia) y en la UI.
- `users_sdk.py` nuevo en `lkf-sanic-apps` con las opciones `list_users`, `get_user_detail`, `create_user`, `update_user`, `reset_password`.
- Permisos: la ruta se protege en el front con `RequireMenuAccess` y una key nueva (`admin_users`); el backend solo exige JWT.

**Fuera de alcance (otra spec):**

- Dar de alta el ítem "Usuarios" en el catálogo de menús: lo hace el usuario a mano (queda arriba de "Configuración de menús", `order` menor).
- Desactivar / eliminar usuarios.
- Ligar o desligar empleados desde el panel.
- Cambiar el `username`.
- Expiración de la liga de restauración.
- Toggle de vistas (tarjetas / lista) y tabs de la bitácora.
- Pantalla pública `/auth/set-password`: se reutiliza tal cual.
- Validar el permiso `admin_users` también en el backend.
- Migrar a sanic `create_user_account` y `setup_user_employee` (hoy en `addons`); va en la spec 02, junto con dejar los scripts de `addons` como puentes delgados.

Tareas para siguientes spec.

1. **SPEC 02** : Alta masiva de usuarios, el poder cargar un formato de excel con los campos de excel,  Desactivar usuarios y borrar usuarios.

## Modelo de datos

Sin colecciones nuevas. Cambios sobre el form **Usuarios** (`addons/lkf_addons/addons/base/items/forms/Base/usuarios.xml` y `usuarios_rules.xml`):

```text
Estatus (679d023876ad7f5ba642f4ed): crear | creado | activado | restaurar   <- nuevo valor
Puesto -> etiqueta "Rol" (field_id 67be0c43a31e5161c47f2bbb sin cambio)
```

Reutilizados: `new_user_token` (`6a2f1c0e5b3d4a7c9e8f1a01`) y `new_user_link` (`6a2f1c0e5b3d4a7c9e8f1a02`). Las reglas de visibilidad de ambos campos deben contemplar `restaurar`.

Contrato de `users_sdk.py` (mismo patrón que `workflow_logs_sdk.py`):

```ts
interface UserRow {
  id: string;            // record_id del registro Usuarios
  user_id: number;       // Id de Usuario (LinkaForm)
  name: string; username: string; email: string;
  phone: string; role: string;   // role = campo "Rol"
  status: "crear" | "creado" | "activado" | "restaurar";
  created_at: string;
}
interface LinkedEmployee { id: string; name: string; status: string; position?: string; }
// get_user_detail -> { user: UserRow, employees: LinkedEmployee[] }
```

Empleados ligados: registros del form Empleados cuyo bloque Usuario (`USUARIOS_OBJ_ID`) trae el `user_id` del usuario. La relación vive en el empleado, no en el usuario.

Flujo `restaurar`: el botón llama `reset_password` → backend valida `status == activado`, genera token (`secrets.token_urlsafe(32)`), escribe token + liga y pone estatus `restaurar` → workflow "after" por estatus `restaurar` manda el correo → el usuario fija la contraseña en `/auth/set-password` → `set_user_password` borra el token y regresa el registro a `activado`. Sin expiración, un solo uso.

## Plan de implementación

1. **Form y flujo (addons).** Agregar `restaurar` a Estatus, renombrar "Puesto" a "Rol", ajustar reglas en `usuarios_rules.xml`, y crear el workflow de correo para `restaurar` (plantilla de restauración, no la de bienvenida). Verificar que el estatus `restaurar` no dispare `create_user_account` (hoy rechaza solo `creado`/`activado`, ver `addons/lkf_addons/addons/base/app.py:76`).
2. **`reset_password` en sanic.** Método `UsersAdmin.reset_password` en `lkf-sanic-apps/addons/base/app.py` que valida estatus `activado`, genera token y liga, y pone `restaurar`. Vive en sanic y no en `addons` porque el botón del front entra por sanic y cada contenedor monta su propio `lkf_addons`. Prueba: ejecutarlo sobre un usuario activado y recibir el correo.
3. **`set_user_password` acepta `restaurar`.** Ajustar `lkf-sanic-apps/addons/base/app.py` para que el cambio de contraseña valide token tanto en `creado` como en `restaurar`, y deje el registro en `activado`. La fase 2 (`setup_user_employee`, en `addons`) no debe duplicar empleado al reactivar: si el usuario ya tiene un empleado ligado, se omite. Prueba: fijar contraseña con la liga de restauración y entrar con ella.
4. **`users_sdk.py` — lectura.** `list_users` (filtros por estatus, nombre, email, username; paginación) y `get_user_detail` con empleados ligados. Prueba: curl al runner con un JWT de admin.
5. **`users_sdk.py` — escritura.** `create_user`, `update_user` (usuario de LinkaForm por `PATCH /api/infosync/user_admin/{id}/` y luego el registro) y `reset_password`, con las validaciones de campos en el servicio.
6. **Front: servicio y hooks.** `clave10/src/lib/users-sdk.ts`, `hooks/Users/useUsers.ts`, `useUsersFilters.ts`, siguiendo `workflow-logs-sdk.ts`.
7. **Front: lista.** `app/dashboard/users/{layout,page}.tsx` con `RequireMenuAccess requiredKey="admin_users"` y `components/Users/UsersTable.tsx` + `users-columns.tsx` (TanStack, mismo patrón que `components/table/bitacoras`).
8. **Front: panel de detalle.** `UserPanel.tsx` con datos, sección Empleados ligados y botón "Restaurar contraseña" (solo `activado`, con `confirm-modal`).
9. **Front: alta y edición.** Modal/formulario de alta y edición, con campos y validaciones del form (email válido; Rol y teléfono requeridos; nombre exacto si se liga empleado).
10. **Actualizar punteros.** Commit y push en cada submódulo (`addons`, `lkf-sanic-apps`, `clave10`) y luego el puntero en el paraguas, verificando con `git submodule foreach 'git log --oneline @{u}..HEAD'`.

## Criterios de aceptación

- [ ] `/dashboard/users` carga sin errores en consola y lista los registros del form Usuarios con paginación de 20 (el paginador compartido `DataTablePagination` no ofrece 25).
- [ ] La lista usa los mismos componentes (`PageHeader`, `FacetSearch`, estilo de tabla, TanStack + `DataTablePagination`) que la bitácora; no hay tabs ni toggle de vistas.
- [ ] Filtrar por faceta Estatus = `activado` muestra solo usuarios activados.
- [ ] Hacer clic en el ojo abre el panel lateral derecho; cerrarlo regresa a la lista sin recargar.
- [ ] El panel muestra nombre, username, email, teléfono, Rol, estatus y la sección Empleados ligados.
- [ ] Un usuario ligado a un empleado muestra 1 empleado con enlace "Ver registro"; uno sin empleados muestra el estado vacío.
- [ ] El botón "Restaurar contraseña" aparece solo con estatus `activado`.
- [ ] Al confirmarlo, el registro pasa a `restaurar` y llega un correo con liga a `/auth/set-password` al email registrado.
- [ ] Usar la liga de restauración fija la nueva contraseña, el estatus vuelve a `activado`, y la misma liga ya no funciona una segunda vez.
- [ ] Restaurar contraseña no crea un empleado ni una Configuración Accesos nuevos.
- [ ] Crear un usuario desde "+ Nuevo usuario" deja el registro en `creado` y envía el correo de activación.
- [ ] Editar nombre, teléfono, Rol y email actualiza el registro y el usuario de LinkaForm; `username` no es editable.
- [ ] En ninguna pantalla ni en el form aparece "Puesto"; dice "Rol".
- [ ] Un usuario sin la key `admin_users` no accede a la ruta.
- [ ] `git submodule foreach 'git log --oneline @{u}..HEAD'` regresa vacío antes de pushear el paraguas.

## Decisiones tomadas y descartadas

- **Sí:** estatus `restaurar` en el mismo form. Queda trazable en workflow-logs y reutiliza `set-password`.
- **No:** script directo sin cambio de estatus (menos trazable) ni volver el registro a `crear` (duplicaría el usuario en `create_user`).
- **Sí:** liga sin expiración y de un solo uso, igual que la de activación. No se agrega campo nuevo.
- **Sí:** `users_sdk.py` en `lkf-sanic-apps` con el patrón de `workflow_logs_sdk.py`.
- **Sí:** el backend nuevo vive en sanic. Se quiere dar mantenimiento a un solo back; la migración de lo que sigue en `addons` va en la spec 02.
- **Sí:** el permiso `admin_users` se valida solo en el front (igual que `admin/menus`). **No** en backend: acoplaría con `accesos/service.get_user_menus`, donde un usuario sin configuración de menús recibe todos.
- **No:** llamar la API de formularios desde el front: sin validación de permisos ni orquestación del alta.
- **Sí:** editar nombre, teléfono, Rol y email, sincronizando LinkaForm. **No** username.
- **Sí:** solo tabla, sin tarjetas ni toggle. Evita diseñar vistas nuevas.
- **Sí:** empleados ligados en solo lectura. La relación vive en el empleado; ligar/desligar es otro alcance.
- **Sí:** el ítem de menú lo agrega el usuario en el catálogo de menús; esta spec solo define la key `admin_users`.

## Riesgos identificados

| Riesgo | Mitigación |
| --- | --- |
| `admin_menus` no está definido en el repo; el catálogo de menús vive fuera (backend/BD) | La key `admin_users` se acuerda aquí y se carga a mano. Sin ella nadie ve la ruta. |
| `set_user_password` y la fase 2 asumen el flujo `creado → activado` | Paso 3: aceptar `restaurar` y no repetir `setup_user_employee` si el empleado ya existe. |
| El email no es único en LinkaForm; cambiarlo puede apuntar la liga a otra persona | Mostrar el email actual en la confirmación de "Restaurar contraseña". |
| El workflow "after" de correo corre por estatus; un `restaurar` repetido puede no reenviar | Verificar en el paso 1 que la regla dispare en cada cambio a `restaurar`. |
| Cambiar la etiqueta en el XML no actualiza el form en LinkaForm hasta sincronizar | Incluir la sincronización del form en el paso 1 (flujo de `clave10-scripts`/addons). |
| Sin validación de permiso en backend, un usuario autenticado puede llamar las rutas directo | Aceptado en esta spec; se resuelve al migrar el back (spec 02) o con una spec de permisos. |
| `PATCH user_admin/{id}` podría no aceptar `first_name`, `phone` o `position` | Se prueba en el paso 5; el error de LinkaForm se muestra tal cual y el registro no se toca. |
| Editar nombre o email de un usuario `activado` no re-sincroniza el catálogo `usuarios` (el workflow solo corre con `creado`) | Los empleados ligados pueden mostrar el dato viejo; se revisa al verificar la edición. |

## Lo que **no** está en esta spec

- Alta del ítem "Usuarios" en el catálogo de menús.
- Desactivar o eliminar usuarios; cambiar `username`.
- Ligar o desligar empleados desde el panel.
- Expiración de ligas de activación o restauración.
- Vistas de tarjetas/lista y tabs de la bitácora.
- Cambios en la pantalla pública `/auth/set-password`.
