# Operación de items de LinkaForm (formas, reglas, workflows, catálogos, registros)

Guía para arreglar en una cuenta de cliente problemas de formas, reglas,
workflows, catálogos y registros. Todo se hace desde `clave10-sdk`, con el
contenedor `lkf-addons` arriba.

## Dónde vive cada cosa

```
Repo (lo que se instala)                      Cuenta del cliente (lo que corre)
──────────────────────────                      ─────────────────────────────────
addons/lkf_addons/addons/<mod>/items/           LinkaForm (API)
  forms/…/<forma>.xml            ───install──▶    Forma (campos, plantillas PDF)
  forms/…/<forma>_rules.xml      ───install──▶    Reglas de la forma
  forms/…/<forma>_workflow.xml   ───install──▶    Workflow (correos, scripts)
  catalogs/…/<catalogo>.xml      ───install──▶    Catálogo (modelo)
  catalogs/…/<catalogo>_data.json ──install──▶    Registros del catálogo (CouchDB)
  migrations/000N_*.py           ───install──▶    Renombres en LKFModules

addons/modules  (rama por cuenta: account_<id>)  Mongo infosync_answers_client_<id>
  <mod>/items/forms/…  = OVERRIDE de la cuenta    form_answer   registros de formas
                         (le gana a lkf_addons)   answer_version versiones previas
                                                  LKFModules    nombre → item_id
                                                  script_log    ejecuciones de scripts
                                                  workflow_log  workflows ejecutados
```

- El código (`app.py`, scripts) busca formas y catálogos **por nombre** en
  `LKFModules` (`lkm.form_id('programar_tareas')`, `lkm.catalog_id('catalogo_de_items')`).
  Si el nombre no existe en la cuenta, regresa `{}` y el script truena más
  adelante, normalmente con `list index out of range` o `KeyError`.
- Si la rama de la cuenta en `modules` tiene su propia versión de una forma,
  esa es la que se instala y no la de `lkf_addons`.

## Lo que puedes hacer y lo que no

| Sí | No (pídeselo a Paco) |
| --- | --- |
| `lkf workwith` / `lkf workon` | `./lkf update prod <id>` (contenedor de addons) |
| Leer Mongo y la API de cualquier cuenta | Deploy o update de Sanic |
| Instalar **una** forma, sus reglas o su workflow | Build de imágenes |
| Instalar **un** catálogo y cargarle registros | `lkfaddons install -m <mod>` sin `-i` (todo el módulo) |
| Correr una migración de un módulo | `-y` en `lkfaddons` (también carga data y demo) |
| Editar un registro por API, con respaldo | `$set` directo en Mongo sin acordarlo antes |
| Commit y push en la rama de la cuenta en `modules` | Commit a `master` de `addons` o de `modules` |

## Reglas que no se negocian

1. **Respaldo antes de escribir.** Guarda en `~/backups/<dominio>_<id>_<fecha>/`
   lo que vas a tocar: la forma, sus reglas, el doc de `LKFModules` y los registros.
   Ver [01-entorno.md](01-entorno.md#respaldo).
2. **Primero lee, luego escribe.** Todo script de escritura corre primero en
   seco y solo escribe con `APLICAR=1`.
3. **Candado de cuenta.** Todo script lleva `assert` del `ACCOUNT_ID`. Si estás
   en la cuenta equivocada, se detiene antes de tocar nada.
4. **Una cuenta a la vez.** Aunque el cambio sea el mismo en 10 cuentas, se
   hace en una, se prueba y luego se pasa a la siguiente.
5. **Nada suelto en `modules/`.** Los scripts de prueba van en tu carpeta de
   trabajo y se mandan al contenedor por stdin. Si `modules/` queda sucio,
   `workwith` falla y **no cambia la cuenta**.
6. **No pisar personalizaciones.** Antes de instalar, revisa si la cuenta
   tiene su propia versión de la forma. Ver [03-formas.md](03-formas.md#antes-de-instalar).

## Orden para atacar un reporte

1. Identificar cuenta (dominio + `account_id`), forma (`form_id`) y error exacto.
   → [02-diagnostico.md](02-diagnostico.md)
2. Reproducir leyendo: `script_log`, la forma, el catálogo, `LKFModules`.
3. Revisar la rama de la cuenta en `modules`: ¿tiene override?
4. Respaldo.
5. Arreglo mínimo: solo el item roto.
   - Forma: [03-formas.md](03-formas.md)
   - Reglas y workflows: [04-reglas-y-workflows.md](04-reglas-y-workflows.md)
   - Catálogos: [05-catalogos.md](05-catalogos.md)
   - Registros: [06-registros.md](06-registros.md)
6. Verificar por API que quedó, y pedir a soporte que pruebe desde la forma.
7. Si el arreglo cambió XML, commit en la rama de la cuenta para que no se
   vuelva a perder en la próxima instalación.

Caso resuelto completo, paso a paso: [casos/2026-11-morpho-programar-tareas.md](casos/2026-11-morpho-programar-tareas.md).
