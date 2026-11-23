# Caso: Morpho, "Programar Tareas Morpho v3" (noviembre 2026)

**Reporte (soporte, 19 nov):** en la cuenta de Morpho, la forma 123695
"Programar Tareas Morpho v3" marca error al guardar una programación y, otra
vez, se quedó sin reglas.

**Resultado (20 nov):** eran dos problemas distintos. Se renombró el
catálogo con su migración y se restauraron las 21 reglas desde la rama de la
cuenta. Soporte confirmó que ya funciona.

## 1. Ubicar la cuenta

```bash
lkf workwith --list | grep -i morpho      # morpho → account_id 10975, rama account_10975
lkf workwith morpho
```

## 2. Leer el error

La captura traía un `IndexError: list index out of range` en el script de
programación (`schedule.py`). El script de la rama de la cuenta llama a
`schedule_task()` en `addons/lkf_addons/addons/base/app.py`, que hace:

```python
item_id = self.answers.get(self.CATALOGO_FORMAS_CAT_OBJ_ID, {}).get(self.mf['form_id'], [])[0]
```

Y `CATALOGO_FORMAS_CAT_OBJ_ID` sale de `base/model.py`:

```python
self.CATALOGO_FORMAS_CAT = self.lkm.catalog_id('catalogo_de_items')
```

## 3. Confirmar la causa leyendo la cuenta

```python
# ...preámbulo con ACCOUNT_ID = '10975'...
print(lkm.catalog_id('catalogo_de_items'))    # {}  → no existe con ese nombre
print(lkm.catalog_id('catalogo_de_formas'))   # {'id': 123682, 'obj_id': '66f647d2…'}
print(len(api.search_catalog(123682, {})))    # 39 registros, todos completos
print(reglas(123695))                         # []  → sin reglas
```

- El código ya busca el catálogo con su nombre nuevo (`catalogo_de_items`).
  Morpho seguía con el viejo, porque la migración del 15 de octubre solo se
  corrió en las 15 cuentas de rollout y Morpho no es una de ellas.
- Como el catálogo no se encuentra, `answers.get(None, {})` regresa `{}` y el
  `[0]` sobre una lista vacía truena.
- La forma tenía 0 reglas.

## 4. Revisar la rama de la cuenta

```bash
cd ~/clave10-sdk/addons/modules
git fetch -q origin
git diff --stat origin/master...origin/account_10975
git grep -n "catalogo_de_formas" origin/account_10975 -- base
```

- La rama trae su propia `base/items/forms/Base/Config/programar_tareas.xml`
  (la v3 de Morpho), con `programar_tareas_rules.xml` (21 reglas) y
  `programar_tareas_workflow.xml`. Master no tiene esa forma.
- El XML apuntaba 8 veces a `{{ catalog.catalogo_de_formas.* }}`. Si se
  migraba el catálogo sin corregir el XML, la próxima instalación de la forma
  iba a fallar.

## 5. Respaldo

En `~/backups/morpho_10975_2026-11-20/`:
- `LKFModules_all.json`: los 39 docs, incluido el del catálogo antes del cambio;
- `form_rules_catalog.json`: definición de la forma 123695, sus reglas (0) y
  los 39 registros del catálogo.

## 6. Correr solo la migración de `base`

Script de [05-catalogos.md](../05-catalogos.md#migraciones-renombres) con `MOD = 'base'`:

```
[migrated] catalog base/catalogo_de_formas -> base/catalogo_de_items (item_id 123682)
```

Verificación: `lkm.catalog_id('catalogo_de_items')` → `{'id': 123682, 'obj_id': '66f647d25af2ce1447f09a4d'}`,
el mismo campo "Forma" que usa la 123695. Se conservaron el id, el obj_id y los registros.

## 7. Corregir la rama de la cuenta

```bash
cd ~/clave10-sdk/addons/modules        # en la rama account_10975, sin cambios pendientes
sed -i '' 's/catalog\.catalogo_de_formas\./catalog.catalogo_de_items./g' \
  base/items/forms/Base/Config/programar_tareas.xml
git diff --stat                        # 1 archivo, 8 líneas
git add base/items/forms/Base/Config/programar_tareas.xml
git commit -m "fix: programar tareas apunta a catalogo_de_items"
git push origin account_10975
```

## 8. Restaurar las reglas

Script de [04-reglas-y-workflows.md](../04-reglas-y-workflows.md#restaurar-solo-las-reglas-sin-reinstalar-la-forma)
con `FORM_ID = 123695`, `PATH = '/srv/scripts/addons/modules/base/items/forms/Base/Config'`
y `NOMBRE = 'programar_tareas_rules'`.

En seco:
```
form_id 123695 reglas en XML 21
plantillas sin resolver []
reglas actuales []
```

Con `APLICAR=1`: `POST 201`, y después `[('6b008546…', 21)]`.

No se reinstaló la forma: así no se tocaron sus campos, sus plantillas PDF
ni su workflow.

## 9. Cerrar

- Respuesta en el hilo: qué se arregló de cada problema y que el cliente
  pruebe guardando una programación.
- Soporte confirmó que ya funciona.

## Lo que quedó abierto

- **Por qué se pierden las reglas.** Ya había pasado antes y no se encontró la
  causa. Si vuelve a pasar, revisa en `LKFModules` el `item_version` y el
  `updated_at` de la forma para ver si alguien la reinstaló, y pregunta quién
  la editó desde el diseñador de formas de LinkaForm.
- **Otras cuentas fuera de las 15** pueden seguir con `catalogo_de_formas`, y
  les pasaría lo mismo. Revisa con `lkm.catalog_id(...)` antes de culpar al código.
