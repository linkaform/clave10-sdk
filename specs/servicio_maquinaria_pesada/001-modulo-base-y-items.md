# SPEC servicio_maquinaria_pesada-001 — Módulo base, items de Ecuaire y scripts modularizados

> **Status:** Aprobado
> **Depends on:** ninguna (el módulo hereda solo de `Base`; si necesita otro módulo, lo carga con `self.load`)
> **Date:** 2026-11-10
> **Objective:** Crear el módulo `servicio_maquinaria_pesada` en `addons`, con su paquete Python (`model.py` y `app.py`), los 8 formularios y 5 catálogos de la cuenta Ecuaire, y los 6 scripts de esa cuenta convertidos en métodos de la clase `ServicioMaquinariaPesada`.

## Por qué existe esta spec

La solución de servicio de maquinaria de Ecuaire vive hoy en la cuenta 15667, mezclada con los módulos genéricos (`oracle`, `location`, `employee`, `base`). No hay un módulo que agrupe lo propio del servicio. El módulo `service` actual es un esqueleto vacío, así que se crea uno nuevo al lado.

Los 6 scripts de la cuenta eran archivos sueltos, con funciones y globales propios y cada uno armando su objeto `LKF_Base`. Para modularizarlos, su lógica pasa a la clase del módulo y cada script queda como un arranque corto.

## Alcance

**Dentro:**

- **Paquete Python** en `addons/lkf_addons/addons/servicio_maquinaria_pesada/` (base del módulo), creado desde `lkf_addons/addons/_template/`:
  - `model.py` con `ServicioMaquinariaPesadaModel(Base)`. Hereda **solo** de `Base` y guarda los IDs de campos en `self.f`.
  - `app.py` con `ServicioMaquinariaPesada(ServicioMaquinariaPesadaModel)`. Hereda **solo** de `model.py` y contiene la lógica de los scripts.
  - Para usar otro módulo no se hereda: se carga con `self.load(module='Employee', **self.kwargs)` y el objeto queda en `self.Employee`.
- **Formularios** (8) y **catálogos** (5), en `addons/lkf_addons/addons/servicio_maquinaria_pesada/items/{forms,catalogs}/Servicios/`. Son la base del módulo; en `addons/modules` solo van las personalizaciones. Se descargaron con `lkfaddons download -m servicio_maquinaria_pesada -i forms|catalogs -id <ID>`:

  | ID | Forma |
  | --- | --- |
  | 120576 | Care Inspection - Oportunidades Comerciales CSR |
  | 124647 | Care Inspection - Oportunidades Comerciales Tecnico |
  | 120574 | Entrada y salida de equipos |
  | 124648 | Informe de Gestion Comercial - Postventa |
  | 124649 | Informe de Gestion Comercial - Ventas |
  | 119972 | Informe de servicio |
  | 120422 | Informe de servicio en taller |
  | 125650 | Programacion de servicios |

  | ID | Catálogo |
  | --- | --- |
  | 121872 | Fabricantes |
  | 121921 | Fabricantes (Sync) |
  | 125652 | Formularios |
  | 121922 | Modelos (Sync) |
  | 121899 | Tipos de orden de servicio |

- **Scripts** (6), en `addons/modules/servicio_maquinaria_pesada/items/scripts/Servicios/`. Son los de la captura que no existen en ningún otro módulo:

  | ID | Script |
  | --- | --- |
  | 122629 | add_fecha_to_field.py |
  | 121939 | calcula_gastos.py |
  | 140688 | get_data_gastos.py |
  | 148793 | get_data_hours.py |
  | 126611 | script_event_records.py |
  | 127090 | update_reasignado.py |

- **`servicios_utils.py`** en la misma carpeta: `ServicioMaquinariaPesada` que hereda de la clase de `app.py`. Los scripts lo importan con `from servicios_utils import ServicioMaquinariaPesada`.
- **Modularización de los scripts.** Las funciones de cada script pasan a métodos de `ServicioMaquinariaPesada` en `app.py`. Cada script queda con su import y su arranque `lkf_obj = ServicioMaquinariaPesada(settings, sys_argv=sys.argv)`, más la llamada al método. Se conserva el `use_api` que cada script tenía.
- **Origen de los scripts.** El comando `lkfaddons download -i scripts` devuelve 404 (los archivos no están en el bucket público de Backblaze), así que los 6 `.py` se tomaron de producción a mano.

**Fuera de alcance (otra spec):**

- Lógica nueva, distinta de la que ya traen los 6 scripts (por ejemplo, la sincronización con Oracle).
- Scripts de infraestructura que ya existen en otros módulos: `base_utils`, `schedule`, `create_qr`, `carga_universal_module` (módulo `base`), `area_acceso_qr_code`, `location_util`, `test_generate_qr` (módulo `location`), `sync_catalogs` (módulo `oracle`). Quedan fuera `account_settings` y `oracle_connection`.
- Cargar `Oracle`, `Location` o `Employee` desde el módulo: ningún script los usa.
- Cambiar el módulo `service` existente.
- Front en `clave10`, backend en sanic y menús.
- La forma `Informe de servicio (Demo)` (ID 125644), que no aparece en la captura.
- Instalar el módulo en otras cuentas.

## Modelo de datos

Esta spec no introduce estructuras de datos nuevas. Los `field_id` de formas y catálogos son los que ya tienen en la cuenta 15667 y se conservan tal cual en los XML descargados.

Las 16 constantes de campos de `calcula_gastos.py` (`field_group_gastos`, `field_total_gastos`, etc.) pasan a `self.f` en `model.py`, con el mismo nombre como llave.

Estructura final del módulo:

```text
addons/lkf_addons/addons/servicio_maquinaria_pesada/
  __init__.py   depends = ['base', 'location', 'employee', 'activo_fijo']
  model.py      class ServicioMaquinariaPesadaModel(Base)
  app.py        class ServicioMaquinariaPesada(ServicioMaquinariaPesadaModel)
  report.py
  items/
    forms/Servicios/     8 XML y sus complementos (_rules y _workflow), 24 archivos
    catalogs/Servicios/  5 XML
    catalogs/__init__.py install_order = ['fabricantes_sync']
addons/modules/servicio_maquinaria_pesada/items/scripts/Servicios/
  servicios_utils.py    + 6 scripts de arranque
```

Métodos que quedan en `app.py` (25), por script de origen:

| Script | Métodos |
| --- | --- |
| calcula_gastos | `get_optios_and_fields_subtotales`, `get_status_on_db`, `get_str_date_updated`, `msg_error_app`, `get_item_to_update`, `calculates_dates_group`, `add_fecha_field`, `calcula_gastos` |
| update_reasignado | `update_reasignado` |
| get_data_gastos | `get_query_informe_servicio_gastos`, `get_query_comercial` |
| get_data_hours | `get_format_informe_servicio`, `get_format_care_inspection`, `get_format_salida_equipos`, `get_format_gestion_post_venta`, `get_format_gestion_ventas`, `get_query_informe_servicio_hours`, `get_query_care_inspection`, `get_query_entrada_salida_equipos`, `get_query_gestion_post_venta`, `get_query_gestion_ventas` |
| script_event_records | `created_record`, `get_information_catalogs`, `get_query_events`, `format_query_events` |

## Plan de implementación

1. Crear `addons/lkf_addons/addons/servicio_maquinaria_pesada/` desde `_template`, con `model.py` (hereda solo de `Base`), `app.py` (hereda de `model.py`) y `depends = ['base']`. Verificar que el import funciona dentro de `lkf-addons`.
2. Crear `addons/modules/servicio_maquinaria_pesada/` con `items/scripts/Servicios/servicios_utils.py`. La clase hereda de la de `app.py`.
3. Descargar la forma 125650 con el comando del usuario, ya con el nombre bien escrito, para validar el flujo. Revisar el XML en `_downloads`.
4. Descargar las otras 7 formas y dejar los XML en `items/forms/Servicios/` del paquete.
5. Descargar los 5 catálogos y dejarlos en `items/catalogs/Servicios/` del paquete.
6. Colocar los 6 scripts en `items/scripts/Servicios/` y revisar que ninguno importe algo que solo exista en la cuenta (`account_settings`, `oracle_connection`). `account_settings` lo pone la plataforma al ejecutar.
7. Mover la lógica de los 6 scripts a métodos de `ServicioMaquinariaPesada` en `app.py`:
   - `lkf`, `lkf_obj` y `script_obj` pasan a `self`.
   - `current_record`, `lkf_api`, `cr` y `answers` pasan a `self.current_record`, `self.lkf_api`, `self.cr` y `self.answers`.
   - Las constantes de `calcula_gastos` pasan a `self.f`.
   - Los nombres repetidos se resuelven con sufijo (`_gastos`, `_hours`).
   - Cada script queda con su arranque y conserva su `use_api`.

## Criterios de aceptación

- [ ] Existen `addons/lkf_addons/addons/servicio_maquinaria_pesada/{model.py,app.py}` y `addons/modules/servicio_maquinaria_pesada/items/scripts/Servicios/servicios_utils.py`.
- [ ] `model.py` hereda solo de `Base` y `app.py` solo de `model.py`; ninguno importa `Oracle`, `Location` ni `Employee`.
- [ ] No queda ninguna ocurrencia de `ModuleName` ni de `module_name` en el módulo.
- [ ] Dentro de `lkf-addons`, `python -c "from lkf_addons.addons.servicio_maquinaria_pesada.app import ServicioMaquinariaPesada"` no da error.
- [ ] Hay 8 XML de formas y sus complementos (`_rules` y `_workflow`), un total de 24 archivos, en `items/forms/Servicios`, y los IDs de origen son los de la tabla.
- [ ] Hay exactamente 5 XML de catálogos en `items/catalogs/Servicios`.
- [ ] Los 6 scripts de la tabla están en `items/scripts/Servicios` y ninguno es copia de un script de `base`, `location` u `oracle`.
- [ ] Ningún script define funciones propias ni crea `base.LKF_Base`: todos arrancan con `ServicioMaquinariaPesada(settings, sys_argv=sys.argv)`.
- [ ] `install_order` de `items/catalogs/__init__.py` lista `fabricantes_sync` y las dependencias entre formas quedan cubiertas en `items/forms/__init__.py`.
- [ ] `app.py` no contiene IDs numéricos de formas o catálogos ni ObjectIds crudos: todo sale de `self.<NOMBRE>`, `self.<CAT>_OBJ_ID` o `self.f['campo']`, y cada ID de `self.f` tiene una sola llave.
- [ ] `ServicioMaquinariaPesada` tiene los 25 métodos de la tabla y ninguno pisa un método de `Base`.
- [ ] Ejecutados dentro de `lkf-addons` contra la BD local, `get_data_gastos.py`, `get_data_hours.py` y `script_event_records.py` (opción `get_records`) terminan con código 0 y devuelven el JSON esperado.
- [ ] `calcula_gastos` con un registro de prueba escribe en stdout `status: 101` y `replace_ans` con los subtotales, el total y el saldo.
- [ ] `curl -s localhost:8014/api/health` responde `ok:true` y el módulo aparece en el conteo de scripts.
- [ ] `git submodule foreach 'git log --oneline @{u}..HEAD'` sale vacío.
- [ ] El commit no lleva línea `Co-Authored-By` de Claude.

## Decisiones tomadas y descartadas

- **Sí:** `model.py` hereda solo de `Base` y `app.py` solo de `model.py`. Los demás módulos se cargan con `self.load(module=...)` y quedan en `self.<Modulo>`. El formato anterior, con herencia múltiple de `Oracle`, `Location` y `Employee`, queda descartado por el usuario.
- **No:** heredar de `Oracle`. Instanciarla abría la conexión a Oracle en cada ejecución de script, incluidos los que corren al guardar un registro. Con `self.load` solo se conecta quien lo pide.
- **Sí:** formas y catálogos en `lkf_addons` (base del módulo) y solo los scripts en `modules` (personalización). Decisión del usuario.
- **Sí:** `module_utils.py` pasa a `servicios_utils.py` y se elimina `start_here.py`, que ya no tiene sentido porque cada script arranca solo.
- **No:** módulo autocontenido con copias del código de Oracle y QR. Duplicaría código.
- **No:** reemplazar el módulo `service`. Es un esqueleto vacío que otros pueden referenciar, y se prefiere no tocarlo.
- **Sí:** solo 6 scripts, los propios de los formularios. El usuario excluyó `base_utils`, `account_settings`, `oracle_connection` y `schedule`. Los que ya existen en `base`, `location` y `oracle` también quedan fuera.
- **Sí:** descartar el `add_fecha_field` de `add_fecha_to_field.py`, un stub de prueba que solo lanza `LKFException('pruebas!')`. `add_fecha_to_field.py` llama ahora a la versión real, la de `calcula_gastos`. Antes ese script bloqueaba el guardado con el mensaje de prueba; ahora ejecuta la lógica de fechas y no escribe `replace_ans`, así que no modifica el registro.
- **Sí:** `self.current_record` y `self.LKFException`, no `self.lkf.*`. `LKF_Base` no tiene atributo `lkf`: el objeto `lkf` de los scripts es la clase misma.
- **Sí:** sufijos para el otro nombre repetido: `get_query_informe_servicio_gastos` y `get_query_informe_servicio_hours`, porque las dos consultas son distintas.
- **Sí:** conservar el `use_api` de cada script. `update_reasignado`, `get_data_gastos`, `get_data_hours` y `script_event_records` usan `use_api=True`; `add_fecha_to_field` y `calcula_gastos` no. Cambiarlo cambiaría con qué credenciales corren.
- **Sí:** buscar los IDs por nombre en la BD local (`infosync_local`, tabla `items_item`, `owner_id=15667`).
- **Sí:** corregir el typo `servicio_maquinaira_pesada` del comando original a `servicio_maquinaria_pesada`.
- **Sí:** la conversión se hizo con un script `ast` que reescribe los nombres y conserva el texto de cada función, en vez de retipear unas 1,400 líneas de queries y mapeos de campos.
- **Sí:** sin IDs fijos en `app.py`. Las 7 formas y los 4 catálogos que usa la lógica (`clientes`, `activos_fijos`, `usuarios`, `formularios`) se registran en `model.py` con `self.lkm.form_id(...)` y `self.lkm.catalog_id(...)`, y los métodos usan `self.INFORME_SERVICIO`, `self.CLIENTES_CAT_ID`, etc. Los IDs numéricos son de la cuenta 15667 y en otra cuenta apuntarían a otra cosa. Decisión del usuario.
- **Sí:** `depends = ['base', 'location', 'employee', 'activo_fijo']`. Las formas usan catálogos de esos módulos (`clientes` y `usuarios` de `base`, `empleados` y `empleados_jefes_directos` de `employee`, `activos_fijos` y `vehiculos` de `activo_fijo`) y el instalador resuelve un solo nivel, por eso se listan también las transitivas (`location`).
- **Sí:** ningún `field_id` crudo en `app.py`. Los 50 IDs de campo que usa la lógica van en `self.f` (una sola llave por ID, sin choques con `Base`) y los 5 `obj_id` de catálogo (`clientes`, `activos_fijos`, `usuarios`, `empleados`, `formularios`) como `self.<CAT>_OBJ_ID`, porque son de cada cuenta. Decisión del usuario.
- **Sí:** `install_order = ['fabricantes_sync']` en `items/catalogs/__init__.py`, porque `modelos_sync` referencia a `fabricantes_sync` con `{{ catalog.fabricantes_sync.id }}`. El instalador instala scripts, luego catálogos, luego formas, y dentro de cada tipo instala primero lo listado en `install_order`. Decisión del usuario.
- **Sí:** `install_order = ['entrada_y_salida_de_equipos']` en `items/forms/__init__.py` (lo puso el usuario). `programacion_de_servicios` referencia con `{{ form.X.id }}` a las otras 7 formas (en su `_workflow`), y `entrada_y_salida_de_equipos` es la que además se referencia a sí misma.
- **Hecho:** el usuario instaló el módulo en la cuenta `transervi` (31700) y terminó completo: 5 catálogos, 8 formas y 7 scripts (los 6 más `servicios_utils`) registrados en `LKFModules`, junto con `base`, `employee`, `location` y `activo_fijo` de `depends`. `items/forms/__init__.py` conserva solo `entrada_y_salida_de_equipos` en el repo; no se verificó si las referencias `{{ form.X.id }}` del `_workflow` de `programacion_de_servicios` se resolvieron en la primera pasada o en una reinstalación.
- **Pendiente:** `calcula_gastos` y `get_data_gastos` parecen del dominio de gastos y podrían pertenecer a `expenses`. Se quedan aquí porque ese módulo no los tiene.

## Riesgos identificados

| Riesgo | Mitigación |
| --- | --- |
| `calcula_gastos` y `add_fecha_to_field` corren al guardar un registro y ahora construyen `Base` completo (carga de `lkm` y IDs de formas) en vez de `utils.Cache` y `network`. Cada ejecución puede costar más. | `calcula_gastos` se probó con `use_api=True` y un registro sintético; falta probar la ruta real, con el JWT del request (`use_api=False`), y medir tiempos en la plataforma. Si pesa, se aligera `Base` en otra spec. |
| `add_fecha_to_field.py` cambia de comportamiento al descartar el stub: antes lanzaba una excepción de prueba. | Está asentado en Decisiones. Si ese script está enlazado a una forma, hay que revisar el enlace en la cuenta antes de subirlo. |
| La conversión es mecánica. Un nombre sin resolver solo falla al ejecutar ese camino. | Un análisis de nombres libres en `app.py` da cero globales sin resolver, y se ejecutaron `get_data_gastos`, `get_data_hours`, `script_event_records` y `calcula_gastos`. `update_reasignado` y `add_fecha_to_field` escriben en la BD y no se ejecutaron. |
| `lkm` resuelve por módulos instalados en la cuenta (`LKFModules`). En Ecuaire los catálogos `clientes`, `activos_fijos` y `usuarios` ya están registrados (124722, 124709, 124723), pero las 8 formas y el catálogo `formularios` no, porque el módulo no está instalado. Hasta entonces `form_id` devuelve `{}` y las consultas de `get_data_*` salen vacías sin error. | Resuelto en `transervi`: con el módulo instalado, `lkm` resuelve los 6 IDs que se probaron (`informe_de_servicio` 195521, `programacion_de_servicios` 195522, `formularios` 195507, `clientes` 195425, `activos_fijos` 195496, `usuarios` 195434) y los 8 métodos de consulta y `get_information_catalogs` ejecutan sin error (con 0 registros, la cuenta no tiene datos de estas formas). Sigue pendiente en `ecuaire`: registrar ahí las formas y el catálogo (instalar el módulo o enlazar los items existentes) y probar con esa cuenta. Revisar antes cómo trata el instalador una forma que ya existe con el mismo nombre. |
| `local_settings.py` y `accounts.ini` no viajan en el clon. Sin ellos la descarga no autentica. | Ya existen en esta máquina. Se confirma con `/api/health` antes de descargar. |
| El puntero de `addons` apuntaría a un commit local sin pushear y rompería el clon de los demás. | Verificar con `git submodule foreach` antes de pushear el paraguas. |
| La cuenta local no tiene `Informe de servicio (Demo)` como parte del módulo y alguna forma lo referencia. | Se revisan las referencias en los XML. |

## Qué **no** entra en esta spec

- Lógica nueva distinta de la que ya traen los 6 scripts.
- Los scripts de infraestructura ya existentes en `base`, `location` y `oracle`.
- Cargar `Oracle`, `Location` o `Employee` desde el módulo.
- Cambios al módulo `service`.
- Front, backend sanic y menús.
- Instalación del módulo en otras cuentas.
