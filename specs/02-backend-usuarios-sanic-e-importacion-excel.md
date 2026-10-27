# SPEC 02 — Backend de usuarios en sanic, Uso Horario e Idioma, y alta masiva por Excel

> **Status:** Aprobado
> **Depends on:** SPEC 01
> **Date:** 2026-10-21
> **Objective:** Mover a sanic el backend del alta de usuarios (hoy en `addons`), agregar a los usuarios los campos Uso Horario e Idioma, y permitir dar de alta usuarios nuevos en bloque con un Excel (con plantilla descargable).

---

## Por qué existe esta spec

Se quiere dar mantenimiento a un solo backend. Después de la spec 01, la pantalla de usuarios ya vive en sanic (`UsersAdmin`), pero el alta sigue partida: `create_user_account` y `setup_user_employee` corren en el contenedor `lkf-addons` como acción de un workflow. Cada contenedor monta su propio `lkf_addons`, así que el código de uno no lo puede llamar el otro; el workflow solo sabe ejecutar un script.

Sobre ese alta ya en sanic se montan dos cosas: dos datos del usuario que LinkaForm sí guarda y clave10 no deja elegir (zona horaria e idioma; hoy todos nacen con `America/Santo_Domingo`) y el alta en bloque por Excel. La spec tenía una importación de usuarios que ya existen, conservando su `_id`; se retiró porque el Excel es para dar de alta usuarios nuevos (ver Decisiones).

## Alcance

**Dentro:**

- **Fase 1 del alta en sanic.** `UsersAdmin.create_user_account` (valida el empleado a ligar, crea el usuario en LinkaForm, genera token y liga, deja el estatus en `creado`) expuesto como `POST /base/create_user_account`.
- **Fase 2 del alta en sanic.** `UsersAdmin.setup_user_employee` (crea o liga el empleado y crea su Configuración Accesos, idempotente) expuesto como `POST /base/setup_user_employee`. Incluye portar a sanic las definiciones de Configuración Accesos que hoy solo existen en `addons`.
- **Script puente.** Nuevo `create_user_sdk.py` en `sdk-modules-sanic` (`base/items/scripts/Base/`), con el mismo patrón que `update_qr_sdk.py`: lee el registro de `sys.argv[1]`, llama a las dos rutas con `dispatch` y devuelve el mismo contrato al workflow (`replace_ans` y `metadata.id` en la fase `before`). Las dos acciones de script de `usuarios_workflow.xml` pasan a `{{ script.create_user_sdk.id }}`. LinkaForm ejecuta el script que el workflow referencia y, para un `*_sdk.py`, lo corre dentro del contenedor sanic de la cuenta (`account_<id>_linkaform.sanic-app..<tag>`, imagen `linkaform/sanic-app`), donde `dispatch` llega al propio servidor en `0.0.0.0:<PORT>`. El script recibe el registro en `argv[1]` (con `record_id` en texto) y el JWT en la clave `jwt` de `argv[2]`.
- **Limpieza en `addons`.** Se elimina de `lkf_addons/addons/base/app.py` el código del flujo de usuarios ya migrado, una vez verificada la paridad.
- **Uso Horario e Idioma.** Dos campos nuevos en el form Usuarios. `create_user_account` los aplica al usuario de LinkaForm justo después de crearlo (el alta ignora `timezone`: hay que parchear). `update_user` también los edita. Se ven en la lista y en el panel de detalle, y se eligen en el alta y en la edición. Por defecto: **Español** (`es_MX`) y **`America/Mexico_City`**.
- **Alta masiva por Excel.** Botón "Importar" en `/dashboard/users`; un modal lee el `.xlsx` en el navegador, muestra una vista previa y manda las filas por lotes pequeños a `POST /base/create_users`. Columnas: `Nombre`, `Username`, `Email`, `Teléfono`, `Rol`, `Uso Horario` e `Idioma` (las dos últimas opcionales, con los valores por defecto). Cada fila corre el alta completa. Un username que ya existe se rechaza y se reporta; no detiene a las demás.
- **Crear empleados en el modal.** Una casilla "Crear empleado para todos" (`crear_empleado` para todas las filas). No hay columna de empleado ni opción de ligar en el Excel.
- **Plantilla.** Botón "Descargar plantilla" en el modal: un `.xlsx` generado en el navegador con las columnas, filas de ejemplo y una hoja con los valores válidos de Idioma.
- **Resultado.** Conteo de creados y rechazados, con el motivo por fila.

**Fuera de alcance (otra spec):**

- Desactivar y eliminar usuarios (botones `user-x` y papelera de la lista): SPEC 03.
- Validar el permiso `admin_users` en el backend: spec de permisos de todas las rutas de administración.
- Un `DataTable` genérico compartido por todas las tablas.
- Migrar el resto del módulo Base de `addons` (cargas masivas, logs, menús).
- Importar usuarios que ya existen conservando su `_id` (retirado en esta spec).
- Ligar empleados existentes desde el Excel.
- Actualizar usuarios existentes desde el Excel.

## Modelo de datos

Campos nuevos en el form Usuarios (`usuarios.xml`):

```text
Uso Horario   6a31d4e6f8a0b2c4d6e8f101   select con las 143 zonas `America/…` de pytz.common_timezones (por ahora solo América); default America/Mexico_City
Idioma        6a31d4e6f8a0b2c4d6e8f102   select; Español (es_MX, default) | English (en_US)
```

Sobre el usuario de LinkaForm (`PATCH /api/infosync/user_admin/{id}/`): `timezone` es el texto de la zona y `lang` un objeto `{code}` (LinkaForm completa el nombre del idioma).

Rutas en `lkf-sanic-apps/addons/base/routes.py` y opciones en `users_sdk.py`:

```text
POST /base/create_user_account   { record_id, answers }                     -> { answers }   (fase 1, "before")
POST /base/setup_user_employee   { answers }                                -> { skipped }   (fase 2, "after")
GET  /base/get_user_options                                                 -> { timezones[], languages[{value,label}], defaults }
POST /base/create_users          { rows: [UserCreateRow], create_employee } -> UserCreateResult
```

```ts
interface UserCreateRow {
  name: string; username: string; email: string; phone: string; role: string;
  timezone?: string; language?: string;   // vacío = default
}
interface UserCreateResult {
  created: number;
  rejected: { row: number; username: string; msg: string }[];
}
```

Columnas del Excel y su mapeo: `Nombre`→`name`, `Username`→`username`, `Email`→`email`, `Teléfono`→`phone`, `Rol`→`role`, `Uso Horario`→`timezone`, `Idioma`→`language` (acepta "Español", "English" o el código).

## Plan de implementación

1. **Fase 2 en sanic.** Portar a `UsersAdmin` las definiciones de Configuración Accesos que usa `_setup_employee_and_access` (ids de forma y campos, y `PERMISSION_MODULE_MAP`) y escribir `setup_user_employee` con la ruta `/base/setup_user_employee`. `addons` sigue funcionando sin cambios. Prueba: llamar la ruta con un usuario `activado` sin empleado crea empleado y accesos; con empleado ya ligado regresa `skipped`.
2. **Fase 1 en sanic.** Escribir `UsersAdmin.create_user_account` y su ruta, con la misma lógica (validar empleado a ligar antes de crear, `create_user`, `get_updated_users` para el id, token y liga, estatus `creado`). Prueba: llamar la ruta con las respuestas de un registro en `crear` y recibir las respuestas con `Id de Usuario`, token, liga y estatus `creado`.
3. **Script puente.** Crear `create_user_sdk.py` en `sdk-modules-sanic` (verificado con una sonda: el workflow le pasa `jwt` y `dispatch` autentica), apuntar las dos acciones de script de `usuarios_workflow.xml` a `{{ script.create_user_sdk.id }}`, instalar el script (`lkfaddons install -m base -i scripts` desde sanic) y el form (`-i forms` desde addons, subiendo `updated_at`). `create_user.py` de `linkaform/modules` no se toca hasta el paso 4. Prueba de punta a punta: alta desde la pantalla, correo de activación y activación crean usuario, empleado y accesos igual que con la spec 01.
4. **Limpieza en `addons`.** Eliminar de `lkf_addons/addons/base/app.py` `create_user_account`, `setup_user_employee`, `_find_employee_to_link`, `_employee_user_answers`, `_setup_employee_and_access`, `_retry_catalog` y `_ensure_employee_modules`, junto con las constantes que solo usaban. Prueba: `lkfaddons` carga el módulo y el paso 3 sigue pasando.
5. **Uso Horario e Idioma en el backend.** Agregar los dos campos a `usuarios.xml` (subir `updated_at`), instalar el form, y en sanic: `create_user_account` parchea `timezone` y `lang` del usuario de LinkaForm tras crearlo (con default si vienen vacíos, validando la zona contra la misma lista del select y el idioma contra `es_MX`/`en_US`), `update_user` acepta y parchea los dos, las filas de `list_users` y `get_user_detail` los devuelven, y la ruta `get_user_options` entrega las listas de zonas e idiomas para el front. Prueba: un alta con zona e idioma deja al usuario de LinkaForm con esos valores; editar los cambia.
6. **Alta masiva en el backend.** Retirar el código de la importación con `_id` (`import_users`, `_next_folio`, `_import_record`, `_clean_import_row`, su ruta y su opción en `users_sdk.py`) y escribir `UsersAdmin.create_users(rows, create_employee)` con su ruta y la opción de `users_sdk.py`: valida cada fila, rechaza los usernames ya presentes en el form y para el resto corre el mismo alta que `create_user`; un rechazo no detiene a las demás. Prueba: 3 filas (2 nuevas y 1 con username repetido) crean 2 usuarios y rechazan 1 con su motivo.
7. **Front: campos Uso Horario e Idioma.** Selects en el modal de alta y en el formulario de edición del panel (con las listas de `get_user_options`; default `America/Mexico_City` y Español), columnas Idioma y Uso Horario en la lista, y mostrarlos en el panel de detalle. Prueba: dar de alta un usuario con otra zona e idioma y verlos en el panel y en LinkaForm.
8. **Front: alta masiva por Excel.** Reemplazar el parser y el modal de importación con `_id` por `lib/users-import.ts` (columnas del alta, default de zona e idioma), `UserImportModal.tsx` (vista previa, casilla "Crear empleado para todos", envío por lotes con progreso, resultado y "Descargar plantilla") y la plantilla `.xlsx`. Prueba: descargar la plantilla, llenarla, cargarla y ver los usuarios creados y los rechazados en pantalla.
9. **Commits.** Commit y push en cada submódulo (`addons`, `lkf-sanic-apps`, `sdk-modules-sanic`, `clave10`) y luego los punteros del paraguas, verificando con `git submodule foreach 'git log --oneline @{u}..HEAD'`.

## Criterios de aceptación

- [ ] Dar de alta un usuario desde `/dashboard/users` deja el registro en `creado`, con `Id de Usuario`, token y liga, y envía el correo de activación.
- [ ] Un alta con "Ligar a empleado" y un nombre inexistente se rechaza antes de crear el usuario en LinkaForm.
- [ ] Al fijar la contraseña con la liga, el usuario pasa a `activado` y se crean su empleado y su Configuración Accesos.
- [ ] Restaurar la contraseña de un usuario `activado` no duplica empleado ni Configuración Accesos.
- [ ] `lkf_addons/addons/base/app.py` ya no contiene `create_user_account` ni `setup_user_employee`.
- [ ] `create_user_sdk.py` no contiene lógica de alta: solo llama a las rutas de sanic, y `create_user.py` de `linkaform/modules` ya no existe o ya no contiene esa lógica.
- [ ] Dar de alta un usuario con una zona horaria e idioma distintos de los de defecto deja al usuario de LinkaForm con esos valores.
- [ ] Un alta sin zona ni idioma deja `America/Mexico_City` y Español en el usuario de LinkaForm.
- [ ] Editar la zona o el idioma de un usuario desde el panel los cambia en LinkaForm y en el registro.
- [ ] La lista y el panel de detalle muestran Uso Horario e Idioma.
- [ ] Uso Horario es una selección con las zonas posibles, tanto en el form de LinkaForm como en el alta y la edición; una zona fuera de la lista se rechaza.
- [ ] El botón "Importar" abre un modal que acepta un `.xlsx` y rechaza uno sin las columnas `Nombre`, `Username`, `Email`, `Teléfono` y `Rol`.
- [ ] "Descargar plantilla" baja un `.xlsx` con las columnas del alta, filas de ejemplo y los idiomas válidos.
- [ ] La vista previa muestra las filas del Excel antes de enviarlas.
- [ ] Cargar un Excel de usuarios nuevos crea cada usuario como en el alta individual: registro en `creado`, usuario en LinkaForm y correo de activación.
- [ ] Con "Crear empleado para todos" marcada, al activarse cada usuario se crea su empleado; sin marcarla, no.
- [ ] Las columnas Uso Horario e Idioma vacías toman `America/Mexico_City` y Español.
- [ ] Una fila con un username que ya existe se rechaza con su motivo y no impide crear las demás.
- [ ] Una fila inválida (sin username, email mal formado, zona o idioma desconocidos) se reporta con su número de fila del Excel.
- [ ] Un archivo de más de un lote se envía por lotes y el resultado final suma todos.
- [ ] `git submodule foreach 'git log --oneline @{u}..HEAD'` regresa vacío antes de pushear el paraguas.

## Decisiones tomadas y descartadas

- **Sí:** backend único en sanic. Un solo lugar de mantenimiento; los workflows siguen necesitando un script, que queda como puente.
- **Sí:** migrar solo el flujo de usuarios. **No** todo el módulo Base: mezcla muchos flujos ajenos y volvería la spec inverificable.
- **Sí:** el Excel da de alta usuarios **nuevos** y cada fila corre el alta completa (usuario en LinkaForm, correo de activación). **No** la importación de usuarios que ya existen con su `_id`: se construyó y se probó en local (inserción directa en Mongo con folio del contador de `infosync`), pero el Excel es para crear de cero, no tiene `_id` ni Id de Usuario, y el código quedaría sin uso. Se retira en el paso 6.
- **Sí:** si el username ya existe, el backend lo rechaza (primero contra el form, y si no, lo rechaza LinkaForm al crear). **No** se actualizan ni se omiten en silencio.
- **Sí:** "Crear empleado para todos" como una casilla del modal. **No** columnas de empleado en el Excel: ligar exige coincidencia exacta de nombre y es fuente de errores en bloque.
- **Sí:** importación desde un botón en `/dashboard/users`, con el Excel leído en el navegador (como `import-catalog-dialog`). **No** un script de desarrollador.
- **Sí:** Uso Horario e Idioma como campos del form Usuarios. Es lo único que viaja por el workflow del alta hasta `create_user_account`, que los parcha en LinkaForm porque el alta (`POST`) ignora `timezone`.
- **Sí:** Uso Horario como select con las zonas `America/…` de `pytz.common_timezones` (143; por ahora solo América) y no como texto libre. La misma lista se usa en el form (`usuarios.xml`), en la validación del backend y en el select del front (vía `get_user_options`): LinkaForm rechaza al guardar un valor que no sea una de las opciones del select, así que no puede haber listas distintas.
- **Sí:** zona por defecto `America/Mexico_City` (la IANA de México; `America/Mexico` no existe) e idioma Español (`es_MX`). Idiomas disponibles `es_MX` y `en_US`, definidos en una constante fácil de ampliar.
- **Sí:** plantilla `.xlsx` generada en el navegador (sin archivo estático ni endpoint).
- **Sí:** el alta masiva por lotes pequeños con progreso. Cada alta tarda unos segundos porque corre el workflow completo, y un lote grande se pasaría del tiempo máximo del runner.
- **No:** validar el permiso `admin_users` en el backend. Se resuelve para todas las rutas de administración en su propia spec.
- **No:** desactivar y eliminar en esta spec. Son funcionalidad nueva sobre usuarios, no refactor ni carga.

## Riesgos identificados

| Riesgo | Mitigación |
| --- | --- |
| El servicio de sanic no tiene las definiciones de Configuración Accesos (`CONF_ACCESOS`, `PERMISSION_MODULE_MAP`) que usa `setup_user_employee` | Paso 1: portarlas desde `addons` y compararlas campo por campo con las de origen |
| `create_user.py` vive en `linkaform/modules` y el puente nuevo en `sdk-modules-sanic`; ambos repos tienen una rama por cuenta y el cambio no llega a una cuenta hasta que se mezcle en su rama | Los pasos 3 y 4 se despliegan juntos por cuenta; hasta entonces `addons` conserva su código |
| El contenedor sanic de la cuenta que ejecuta el puente usa la imagen `linkaform/sanic-app:<tag>` de la cuenta, no el código de desarrollo: si esa imagen no trae las rutas nuevas, `dispatch` devuelve 404 | Desplegar la imagen con las rutas de los pasos 1 y 2 antes de apuntar el workflow a `create_user_sdk`; en local, crear ese contenedor con la imagen `develop` y los montajes del compose |
| En el entorno local los workflows `after` no pueden llamar de vuelta al backend (el `supervisor` usa `https://127.0.0.1:8080`), así que la sincronía del catálogo y la fase 2 no corren solos | La fase 2 se prueba llamando `setup_user_employee` y el puente a mano; el entorno local se arregla fuera de esta spec |
| El contrato del workflow `before` (`replace_ans`) ahora viaja por HTTP; un fallo de red o un 500 aborta el guardado | El script puente devuelve el error de sanic tal cual y la prueba de punta a punta del paso 3 cubre el caso de empleado inexistente |
| El alta (`POST`) de LinkaForm ignora `timezone`, así que el usuario nace con `America/Santo_Domingo` hasta que se parchea | `create_user_account` parchea justo después de crearlo; si el parche falla, el alta se aborta con un mensaje claro en vez de dejar al usuario con la zona equivocada |
| Un alta masiva de muchas filas tarda minutos (cada alta corre el workflow completo) y se pasa del tiempo máximo del runner | Lotes de 10 filas desde el front con progreso; el backend procesa un lote por llamada. Medido en local: 10 altas reales tardan unos 23 s; en prod puede ser más lento |
| Un Excel grande dispara muchos correos de activación a la vez | Se avisa en la vista previa cuántos usuarios y correos se van a crear antes de confirmar |
| Cambiar o acotar la lista de zonas deja registros con una zona que ya no es opción del select, y LinkaForm los rechaza al editar cualquier campo (revalida el select) | Elegir una zona válida al editar lo recupera (probado: alinea registro y LinkaForm). Al acotar la lista en un entorno con datos, revisar antes los usuarios con otra zona |
| La lista de zonas del select está copiada en `usuarios.xml` y puede quedar desfasada de `pytz` | Se regenera desde `pytz.common_timezones` al actualizar el form; la validación y `get_user_options` leen la misma lista de `pytz`, así que la diferencia solo afectaría a zonas nuevas |
| El idioma por código (`es_MX`, `en_US`) puede no ser el que LinkaForm acepte en otras cuentas | La lista de idiomas es una constante en un solo lugar; el parche de `lang` con un código inválido se reporta como rechazo de la fila |

## Lo que **no** está en esta spec

- Desactivar o eliminar usuarios.
- Validar el permiso `admin_users` en el backend.
- Un `DataTable` genérico para todas las tablas.
- Migrar el resto del módulo Base de `addons`.
- Importar usuarios que ya existen conservando su `_id`.
- Ligar empleados existentes ni actualizar usuarios existentes desde el Excel.
