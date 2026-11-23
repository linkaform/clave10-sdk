# Reglas y workflows

## Reglas

Las reglas viven en un doc aparte de la forma: `reglas(form_id)` (del
preámbulo) regresa `[{'id', 'form_id', 'rules': [...]}]`. Cada regla tiene `conditions`
(campo, condición y valor) y acciones (mostrar u ocultar campos).

Cuando una forma "pierde sus reglas", lo normal es que alguien la instaló o
guardó con un XML sin reglas. Ver [03-formas.md](03-formas.md#qué-reemplaza-una-instalación).

### Restaurar solo las reglas (sin reinstalar la forma)

Sube el `_rules.xml` sin tocar campos, plantillas ni workflow. Es lo que se
hizo en Morpho.

```python
# ...preámbulo...
from lkf_addons import items
from lkf_addons.items.form_resource import FormResource

FORM_ID = 123695
# Carpeta donde está el _rules.xml. Con override de cuenta está en modules:
#   /srv/scripts/addons/modules/<mod>/items/forms/<Carpeta>
# Sin override: items.ADDONS_PATH + '/<mod>/items/forms/<Carpeta>'
PATH = '/srv/scripts/addons/modules/base/items/forms/Base/Config'
NOMBRE = 'programar_tareas_rules'              # sin .xml

_o, sys.stdout = sys.stdout, sys.stderr
fr = FormResource(path=PATH, module='base', settings=settings)
model = fr.load_module_template_file(PATH, NOMBRE)   # resuelve los {{ }}
sys.stdout = _o

pend = [s for s in json.dumps(model).split('"') if '{{' in s]
actuales = reglas(FORM_ID)
print('form_id', model.get('form_id'), 'reglas en XML', len(model.get('rules', [])))
print('plantillas sin resolver', pend)
print('reglas actuales', [(r['id'], len(r['rules'])) for r in actuales])
assert str(model.get('form_id')) == str(FORM_ID)
assert not pend

if APLICAR:
    if actuales:
        model['id'] = actuales[0]['id']
        res = api.upload_rules(model, 'PATCH')     # reemplaza las que hay
    else:
        model.pop('id', None)
        res = api.upload_rules(model, 'POST')      # la forma no tiene reglas
    print(res.get('status_code'))
    print('después', [(r['id'], len(r['rules'])) for r in reglas(FORM_ID)])
```

Revisa en la salida en seco:
- que el `form_id` sea el de la forma de esa cuenta;
- que no haya plantillas sin resolver;
- el número de reglas actuales. Si la forma tiene reglas que el XML no trae,
  detente: son reglas propias de la cuenta.

Después, `POST`/`PATCH` tiene que regresar `201`/`200`/`202` y la lectura de
"después" tiene que mostrar el número del XML.

## Workflows

El workflow se define en `<forma>_workflow.xml`. Al guardar un registro
puede mandar correos, correr scripts o cambiar campos.

- **Ver qué corrió:** `db.workflow_log` guarda cada ejecución, con el correo
  ya renderizado (asunto, cuerpo, remitente). Sirve para saber si la cuenta
  tiene plantillas propias.
- **Cambiar un workflow:** edita el `_workflow.xml`, sube la versión del
  `<forma>.xml` e instala la forma sola ([03-formas.md](03-formas.md#instalar-una-sola-forma-ya-existe-en-la-cuenta)).
  El workflow solo se sube cuando la forma se instala (`create` o `update`).
- Antes de instalar, compara el workflow de la cuenta (lo descargas con
  `lkfaddons download`) contra el XML. Ignora ids y fechas; lo que importa es
  qué dispara y con qué plantilla. Algunas cuentas tienen workflow propio
  (por ejemplo grupoviso y litoprocess en la Bitácora de Rondines).

### Ojo: los workflows corren al editar registros

Editar un registro de forma por API dispara su workflow, igual que si lo
guardara un usuario. En cambios masivos eso puede mandar cientos de correos o
saturar el servicio (por ejemplo, `set_permissions` en Usuarios). Antes de
editar en lote:
- revisa qué workflow tiene la forma;
- si solo necesitas cambiar un catálogo, edita el catálogo: los catálogos no tienen workflow;
- si hay que tocar registros, cuéntalos primero y hazlo de uno en uno.
