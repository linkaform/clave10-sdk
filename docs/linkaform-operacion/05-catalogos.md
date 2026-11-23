# Catálogos

Un catálogo tiene un **modelo** (`<catalogo>.xml`, sus campos) y
**registros** (viven en CouchDB y se ven por la API). Las formas lo usan con un
campo tipo `catalog`, cuyo `field_id` es el `obj_id` del catálogo; los
subcampos (`catalog-select`) son los campos del catálogo que se muestran.

- `lkm.catalog_id('<nombre>')` → `{'id', 'name', 'obj_id'}`.
- Una forma no puede tener el mismo catálogo dos veces.
- Los catálogos no tienen workflow: editarlos no dispara nada.

## Leer registros

```python
# ...preámbulo...
CAT = lkm.catalog_id('catalogo_de_items')['id']
regs = api.search_catalog(CAT, {})
print(len(regs))
for r in regs[:5]:
    print({k: v for k, v in r.items() if not k.startswith('_')})
```

Si sale vacío y sabes que hay datos, prueba con un selector explícito:
`api.search_catalog(CAT, {"selector": {"_id": {"$gt": None}}, "limit": 500})`.

## Instalar un solo catálogo

`lkfaddons install -m <mod> -i catalogs` pasa por **todos** los catálogos del
módulo, aunque pongas `-id`; `-id` solo limita la carga de registros. Para
uno solo, usa un script:

```python
# ...preámbulo...
import importlib
from lkf_addons import items
sys.path.insert(0, items.ADDONS_PATH)
MOD, NOMBRES = 'base', ['mi_catalogo']
CARGAR_DATA = False                       # True = también sube <nombre>_data.json

cats = importlib.import_module(f'{MOD}.items.catalogs')
_o, sys.stdout = sys.stdout, sys.stderr
cr = cats.CatalogResource(path=cats.__path__[0], module=MOD, settings=settings,
                          load_data=CARGAR_DATA)
todos = cr.instalable_catalogs()
sys.stdout = _o
sel = {n: todos[n] for n in NOMBRES}
for n in NOMBRES:
    print(n, sel[n], 'ya instalado:', lkm.catalog_id(n))
if APLICAR:
    sel['install_order'] = NOMBRES
    cr.install_catalogs(sel)
    print({n: lkm.catalog_id(n) for n in NOMBRES})
```

```bash
docker exec -i -w /srv/scripts/addons/modules lkf-addons python3 - < instalar_catalogo.py
```

Si una forma del módulo depende de un catálogo que la cuenta no tiene, instala
primero el catálogo y luego la forma.

## Importar registros

### Desde Google Sheets (`_data.json`)

Junto al XML del catálogo va un `<catalogo>_data.json`:

```json
{
    "mapping": {"Concepto": "649b2a84dac4914e02aadb24", "Cuenta Contable": "649b2a84dac4914e02aadb25"},
    "spreadsheet_url": "https://docs.google.com/spreadsheets/d/<id>/edit#gid=0"
}
```

- `mapping`: encabezado de columna de la hoja → `field_id` del catálogo.
- La hoja tiene que poder abrirse con el link.
- Se carga instalando el catálogo con `CARGAR_DATA = True` (script de arriba).
- Cada archivo se carga **una sola vez**: queda marcado en `LKFModules`
  (`load_data.<archivo>: true`) y no se vuelve a subir, así que no duplica.
  Para volver a cargar, hay que quitar esa marca (pregúntale a Paco).

### Por API (pocos registros o datos que ya tienes en Python)

```python
# ...preámbulo...
CAT = lkm.catalog_id('mi_catalogo')['id']
nuevos = [
    {'649b2a84dac4914e02aadb24': 'Gasolina', '649b2a84dac4914e02aadb25': '601-01'},
]
existentes = {r.get('649b2a84dac4914e02aadb24') for r in api.search_catalog(CAT, {})}
faltan = [a for a in nuevos if a['649b2a84dac4914e02aadb24'] not in existentes]
print('a crear', len(faltan))
if APLICAR:
    for a in faltan:
        meta = api.get_catalog_metadata(catalog_id=CAT)
        meta['answers'] = a
        print(api.post_catalog_answers(meta).get('status_code'))
```

Revisa duplicados antes de crear, como en el ejemplo: crear no valida si ya
existe.

## Migraciones (renombres)

Cuando el código cambia el nombre con el que busca un item (por ejemplo
`catalogo_de_formas` → `catalogo_de_items`), el módulo trae una migración en
`addons/lkf_addons/addons/<mod>/migrations/000N_*.py`. La migración solo
cambia el nombre en `LKFModules`: conserva el mismo `item_id`, el mismo
`obj_id` y los registros.

- Corre sola en cualquier `lkfaddons install -m <mod>`.
- Para correr **solo** las migraciones, sin instalar nada más:

```python
# ...preámbulo...
from lkf_addons import items
from lkf_addons.items.migration_resource import MigrationResource
MOD = 'base'
m = MigrationResource(path=items.ADDONS_PATH, module=MOD, settings=settings)
print('migraciones', [x.name for x in m.load_migrations()])
print('antes', lkm.catalog_id('catalogo_de_formas'), lkm.catalog_id('catalogo_de_items'))
if APLICAR:
    print('aplicadas', m.run_migrations())
```

- Si existen **los dos** nombres (el viejo con datos y el nuevo vacío), la
  migración se detiene a propósito. No borres ninguno; avisa a Paco.
- Después de migrar, busca el nombre viejo en la rama de la cuenta
  (`git grep -n catalogo_de_formas origin/<rama>`) y actualízalo. Si no, la
  próxima instalación de esa forma falla.
