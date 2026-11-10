# SPEC servicio_maquinaria_pesada-001 — Módulo base y items descargados de Ecuaire

> **Status:** Aprobado
> **Depends on:** ninguna (hereda de los módulos existentes `oracle`, `location` y `employee`)
> **Date:** 2026-11-10
> **Objective:** Crear el módulo `servicio_maquinaria_pesada` en `addons`, con el esqueleto Python de la plantilla y los 8 formularios, 5 catálogos y 6 scripts de la cuenta Ecuaire descargados con `lkfaddons download`.

## Por qué existe esta spec

La solución de servicio de maquinaria de Ecuaire vive hoy en la cuenta 15667, mezclada con los módulos genéricos (`oracle`, `location`, `employee`, `base`). No hay un módulo que agrupe lo propio del servicio. El módulo `service` actual es un esqueleto vacío, así que se crea uno nuevo al lado. Esta spec solo deja la base: estructura, herencia y los items versionados en git. La lógica nueva va en otras specs.

## Alcance

**Dentro:**

- **Items del módulo.** Carpeta `addons/modules/servicio_maquinaria_pesada/` creada desde `addons/modules/_module_template/`, con `items/forms`, `items/catalogs`, `items/scripts` e `items/reports`.
- **Paquete Python.** `addons/lkf_addons/addons/servicio_maquinaria_pesada/` creado desde `lkf_addons/addons/_template/`. Es el que importan `app.py`, `start_here.py` y `module_utils.py`, que la plantilla trae como `from lkf_addons.addons.module_name.app import ModuleName`.
- **Herencia.** La clase `ServicioMaquinariaPesada` hereda de `Oracle`, `Location` y `Employee`. No duplica la conexión Oracle ni el código de QR.
- **Formularios** (8), descargados con `lkfaddons download -m servicio_maquinaria_pesada -i forms -id <ID>`:

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

- **Catálogos** (5), con `-i catalogs`:

  | ID | Catálogo |
  | --- | --- |
  | 121872 | Fabricantes |
  | 121921 | Fabricantes (Sync) |
  | 125652 | Formularios |
  | 121922 | Modelos (Sync) |
  | 121899 | Tipos de orden de servicio |

- **Scripts** (6), con `-i scripts`. Son los de la captura que no existen en ningún otro módulo:

  | ID | Script |
  | --- | --- |
  | 122629 | add_fecha_to_field.py |
  | 121939 | calcula_gastos.py |
  | 140688 | get_data_gastos.py |
  | 148793 | get_data_hours.py |
  | 126611 | script_event_records.py |
  | 127090 | update_reasignado.py |

- **Descarga.** Se corre dentro del contenedor `lkf-addons`, contra la BD local (dominio `ecuaire`, cuenta 15667, entorno `local`). Los items se guardan en `_downloads` y se mueven a su carpeta final.
- **Rama.** Los cambios van en `addons/modules`, rama `ecuaire`, y luego se actualiza el puntero en `addons` y en el paraguas.

**Fuera de alcance (otra spec):**

- Lógica de negocio nueva en `app.py` (programación de servicios, cálculo de horas y gastos, sincronización Oracle).
- Scripts de infraestructura que ya existen en otros módulos: `base_utils`, `schedule`, `create_qr`, `carga_universal_module` (módulo `base`), `area_acceso_qr_code`, `location_util`, `test_generate_qr` (módulo `location`), `sync_catalogs` (módulo `oracle`). Quedan fuera `account_settings` y `oracle_connection`.
- Cambiar el módulo `service` existente.
- Front en `clave10`, backend en sanic y menús.
- La forma `Informe de servicio (Demo)` (ID 125644), que no aparece en la captura.
- Instalar el módulo en otras cuentas.

## Modelo de datos

Esta spec no introduce estructuras de datos nuevas. Los `field_id` de formas y catálogos son los que ya tienen en la cuenta 15667 y se conservan tal cual en los XML descargados.

Estructura final del módulo:

```text
addons/modules/servicio_maquinaria_pesada/items/
  forms/       8 XML (con sus _rules y _workflow si existen)
  catalogs/    5 XML
  scripts/     start_here.py, app.py, module_utils.py + 6 scripts descargados
  reports/     __init__.py
addons/lkf_addons/addons/servicio_maquinaria_pesada/
  __init__.py
  app.py       class ServicioMaquinariaPesada(Oracle, Location, Employee)
  report.py
```

## Plan de implementación

1. Crear `addons/lkf_addons/addons/servicio_maquinaria_pesada/` desde `_template`, con `ServicioMaquinariaPesada` heredando de `Oracle`, `Location` y `Employee`. Verificar que el import funciona dentro de `lkf-addons`. Comprobar antes que las tres clases se pueden combinar en la herencia: `Oracle.__init__` abre la conexión a Oracle y exige `ORACLE_HOST`.
2. Crear `addons/modules/servicio_maquinaria_pesada/` desde `_module_template`. Reemplazar `ModuleName` y `module_name` por los nombres reales en `app.py`, `start_here.py` y `module_utils.py`. Las dos carpetas `items` quedan vacías y listas.
3. Descargar la forma 125650 con el comando del usuario, ya con el nombre bien escrito, para validar el flujo. Revisar el XML en `_downloads`.
4. Descargar las otras 7 formas y mover los XML de `_downloads` a `items/forms/<carpeta>/`.
5. Descargar los 5 catálogos y moverlos a `items/catalogs/<carpeta>/`.
6. Descargar los 6 scripts y revisar que ninguno importe algo que solo exista en la cuenta (`account_settings`, `oracle_connection`). Si algún script depende de uno, se anota en la spec.


## Criterios de aceptación

- [ ] Existen `addons/modules/servicio_maquinaria_pesada/items/{forms,catalogs,scripts,reports}`.
- [ ] Existe `addons/lkf_addons/addons/servicio_maquinaria_pesada/app.py` con la clase `ServicioMaquinariaPesada`.
- [ ] No queda ninguna ocurrencia de `ModuleName` ni de `module_name` en el módulo.
- [ ] Dentro de `lkf-addons`, `python -c "from lkf_addons.addons.servicio_maquinaria_pesada.app import ServicioMaquinariaPesada"` no da error.
- [ ] Hay exactamente 8 XML de formas en `items/forms`, y los IDs de origen son los de la tabla.
- [ ] Hay exactamente 5 XML de catálogos en `items/catalogs`.
- [ ] Los 6 scripts de la tabla están en `items/scripts` y ninguno es copia de un script de `base`, `location` u `oracle`.
- [ ] `curl -s localhost:8014/api/health` responde `ok:true` y el módulo aparece en el conteo de scripts.
- [ ] `git submodule foreach 'git log --oneline @{u}..HEAD'` sale vacío.
- [ ] El commit no lleva línea `Co-Authored-By` de Claude.

## Decisiones tomadas y descartadas

- **Sí:** el módulo hereda de `Oracle`, `Location` y `Employee`. Evita duplicar código que ya existe y mantiene un solo lugar para la conexión Oracle y los QR. Es lo que eligió el usuario.
- **No:** módulo autocontenido con copias del código de Oracle y QR. Duplicaría código.
- **No:** reemplazar el módulo `service`. Es un esqueleto vacío que otros pueden referenciar, y se prefiere no tocarlo.
- **Sí:** solo 6 scripts, los propios de los formularios. El usuario excluyó `base_utils`, `account_settings`, `oracle_connection` y `schedule`. Los que ya existen en `base`, `location` y `oracle` también quedan fuera.
- **Sí:** buscar los IDs por nombre en la BD local (`infosync_local`, tabla `items_item`, `owner_id=15667`). No se pidió la lista al usuario.
- **Sí:** corregir el typo `servicio_maquinaira_pesada` del comando original a `servicio_maquinaria_pesada`.
- **Sí:** alcance de estructura más items descargados. La lógica de negocio va en otra spec.
- **Pendiente de confirmar en la implementación:** `calcula_gastos` y `get_data_gastos` parecen del dominio de gastos y podrían pertenecer a `expenses`. Entran porque ese módulo no los tiene. Se confirma leyendo el código al descargarlos.

## Riesgos identificados

| Riesgo | Mitigación |
| --- | --- |
| `Oracle.__init__` abre la conexión a Oracle y exige `ORACLE_HOST` en `settings.config`. Heredarlo hace que el módulo falle al instanciarse si no está configurado. | Verificar en el paso 1 que la herencia instancia sin Oracle disponible, o hacer la conexión perezosa en el módulo nuevo. |
| `local_settings.py` y `accounts.ini` no viajan en el clon. Sin ellos la descarga no autentica. | Ya existen en esta máquina. Se confirma con `/api/health` antes de descargar. |
| Un script descargado puede importar `oracle_connection` o `account_settings`, que quedan fuera. | Se revisan los imports en el paso 6 y se documentan las dependencias. |
| El puntero de `addons` apuntaría a un commit local sin pushear y rompería el clon de los demás. | El paso 7 verifica con `git submodule foreach` antes de pushear el paraguas. |
| La cuenta local no tiene `Informe de servicio (Demo)` como parte del módulo y alguna forma lo referencia. | Se revisan las referencias en los XML al descargar. |

## Qué **no** entra en esta spec

- Lógica nueva en `app.py`.
- Los scripts de infraestructura ya existentes en `base`, `location` y `oracle`.
- Cambios al módulo `service`.
- Front, backend sanic y menús.
- Instalación del módulo en otras cuentas.

