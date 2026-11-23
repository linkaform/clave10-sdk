# Entorno, cuenta activa y cómo correr scripts

## Cuenta y entorno activos

Se corren en el host, desde cualquier carpeta (`lkf install` una vez por máquina):

```bash
lkf workwith --list          # dominios disponibles
lkf workwith morpho          # cuenta activa en addons y lkf-sanic-apps
lkf workwith                 # muestra en qué cuenta está cada repo
lkf workon prod              # entorno: local | preprod | prod
```

`workwith` además:
- cambia `addons/modules` a la rama de la cuenta (`account_<id>` o el nombre del dominio);
- hace merge de `origin/master` en esa rama. Es normal que quede 1 o 2 commits adelante;
- **falla si `modules/` tiene cambios** y deja la cuenta anterior. Revisa
  siempre la salida, o `cat addons/secrets/current_domain`.

Si `modules` tiene un cambio local que necesitas conservar, guárdalo con
`git stash` antes del `workwith` y aplícalo al volver. No lo commitees solo
para poder cambiar de cuenta.

## Plantilla de script

Todos los scripts de esta guía empiezan igual. Guárdalos fuera del repo (por
ejemplo `~/lkf-trabajo/`) y córrelos mandándolos por stdin, así no se copia
nada al contenedor:

```bash
docker exec -i lkf-addons python3 - < ~/lkf-trabajo/mi_script.py               # en seco
docker exec -i -e APLICAR=1 lkf-addons python3 - < ~/lkf-trabajo/mi_script.py  # escribe
```

Preámbulo (cópialo tal cual y cambia `ACCOUNT_ID`):

```python
import sys, os, json
sys.path.insert(0, '/srv/scripts/addons/config')
ACCOUNT_ID = '10975'                          # candado: la cuenta que esperas
APLICAR = os.environ.get('APLICAR') == '1'    # sin APLICAR=1 solo lee

_out, sys.stdout = sys.stdout, sys.stderr     # el login imprime ruido; va a stderr
from account_settings import settings         # cuenta de `lkf workwith`
from linkaform_api import utils, lkf_models
from linkaform_api.network import Network
api = utils.Cache(settings)                   # API de LinkaForm
lkm = lkf_models.LKFModules(settings)         # nombre → id (LKFModules)
db = Network(settings).get_user_connection()['db']   # Mongo de la cuenta
sys.stdout = _out

def reglas(form_id):
    # sin reglas la API regresa {'meta', 'objects': []}; con reglas, una lista
    r = api.get_form_rules(form_id)
    return r.get('objects', []) if isinstance(r, dict) else (r or [])

assert str(settings.config['ACCOUNT_ID']) == ACCOUNT_ID, settings.config['ACCOUNT_ID']
print('cuenta', settings.config['ACCOUNT_ID'], 'env', settings.ENV, 'APLICAR', APLICAR)
```

Con eso tienes:

| Objeto | Para qué |
| --- | --- |
| `lkm.form_id('<nombre>', 'id')` | `form_id` de una forma por su nombre de XML |
| `lkm.catalog_id('<nombre>')` | `{'id', 'name', 'obj_id'}` del catálogo, o `{}` si no existe |
| `api.get_form_id_fields(form_id)` | definición de la forma (campos en `fields`) |
| `reglas(form_id)` | docs de reglas de la forma: `[{'id', 'form_id', 'rules': [...]}]`, `[]` si no tiene |
| `api.search_catalog(catalog_id, {})` | registros del catálogo |
| `db.form_answer` | registros de formas (`form_id`, `folio`, `answers`, `user_id`) |
| `db.LKFModules` | items instalados (`item_name`, `item_type`, `item_id`, `module`) |
| `db.script_log` | ejecuciones de scripts (`status`, `script_id`, `traceback`) |

Reglas para estos scripts:
- Todo lo que escribe va dentro de `if APLICAR:`.
- Antes del `if APLICAR:` imprime qué vas a cambiar y cuántos registros.
- Mongo se **lee** directo; se **escribe** por la API (ver [06-registros.md](06-registros.md)).
- No imprimas contraseñas, tokens ni datos personales (INE, teléfonos). Para
  revisar, imprime conteos o ids.

## Respaldo

Antes de escribir, guarda lo que vas a tocar. Ejemplo para una forma:

```python
# ...preámbulo...
FORM_ID = 123695
bk = {
    'forma': api.get_form_id_fields(FORM_ID),
    'reglas': reglas(FORM_ID),
    'lkfmodules': list(db.LKFModules.find({}, {'_id': 0})),
}
print(json.dumps(bk, default=str))
```

```bash
mkdir -p ~/backups/morpho_10975_$(date +%F)
docker exec -i lkf-addons python3 - < respaldo.py 2>/dev/null > ~/backups/morpho_10975_$(date +%F)/forma_123695.json
```

Para registros: guarda el documento completo de `form_answer` de cada uno que vayas a editar.

## lkfaddons

Se corre dentro del contenedor, con la cuenta de `workwith`:

```bash
docker exec -it lkf-addons lkfaddons <accion> -m <modulo> -i <items> [-id <ids>] [-f]
```

- `accion`: `install` o `download`.
- `-i`: `forms`, `catalogs`, `scripts`, `reports` o `data`. Puedes pasar varios separados por espacio.
- `-id`: ids **de esa cuenta**, separados por coma.
- `-f`: fuerza la instalación aunque la versión local no sea más nueva.
- En prod pregunta dos veces "are you sure". Para no contestar a mano, usa
  `yes y | lkfaddons …` dentro de `sh -c`.
- **Nunca uses `-y`**: además de contestar que sí, activa la carga de `data` y
  `demo` de todo lo que instale.
- Todo `install -m <mod>` corre primero las **migraciones** de ese módulo.
  Normalmente no pasa nada, pero tenlo presente.
