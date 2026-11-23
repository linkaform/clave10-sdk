# Formas

## Anatomía

Una forma son hasta tres archivos con el mismo prefijo, en
`addons/lkf_addons/addons/<mod>/items/forms/<Carpeta>/` (o en la rama de la
cuenta en `modules/<mod>/items/forms/`):

| Archivo | Qué trae |
| --- | --- |
| `<forma>.xml` | campos (`fields`), grupos, opciones, plantillas PDF (`templates`), versión |
| `<forma>_rules.xml` | reglas: mostrar u ocultar campos según condiciones |
| `<forma>_workflow.xml` | workflows: correos, scripts y cambios de estado al guardar |

Plantillas dentro del XML que se resuelven al instalar, por cuenta:

```
{{ form.<nombre>.id }}            form_id de otra forma
{{ catalog.<nombre>.id }}         catalog_id
{{ catalog.<nombre>.obj_id }}     field_id del campo catálogo dentro de las formas
```

Si el nombre no existe en la cuenta, la instalación truena o deja la referencia vacía.

## Versión

El instalador solo sube la forma si su versión es más nueva que la instalada.
Al editar **cualquiera** de los tres archivos, sube la versión en el `<forma>.xml`,
en los dos campos y con el mismo valor:

```xml
<description>version: 1795300000</description>
<updated_at>1795300000.0</updated_at>
```

```bash
date +%s
```

No toques `created_at`, `resource_uri` ni los `updated_at` anidados de
referencias a catálogos.

## Qué reemplaza una instalación

Instalar una forma ya existente (`update`) **reemplaza por completo**, con lo del XML:
- los campos;
- la lista de plantillas PDF. Si la cuenta tiene plantillas propias, se pierden;
- el workflow;
- las reglas. Si el XML no trae `_rules.xml` o trae `rules` vacío, la cuenta se queda sin reglas.

Los registros (`form_answer`) no se tocan. Pero si quitas un campo, los
registros conservan el valor con un `field_id` que la forma ya no tiene.

## Antes de instalar

1. **¿La cuenta tiene override?**
   ```bash
   cd ~/clave10-sdk/addons/modules
   git ls-tree -r --name-only origin/<rama_cuenta> -- <mod>/items/forms | grep <forma>
   ```
   Si sale algo, el cambio va en ese archivo, en esa rama.
2. **¿La forma de la cuenta tiene cosas que el XML no tiene?** Descárgala y compárala:
   ```bash
   docker exec -it lkf-addons lkfaddons download -m <mod> -i forms -id <form_id>
   ls ~/clave10-sdk/addons/modules/<mod>/items/forms/_downloads/
   ```
   Compara campos (`field_id`), reglas, workflow y `templates` contra el XML
   que vas a instalar. Al terminar **borra `_downloads/`**; si no, `modules`
   queda sucio y `workwith` falla.
   - Que haya `field_id` de más por subcampos de catálogo o por plantillas
     `{{ catalog.X.obj_id }}` es normal.
   - Cualquier otro campo de más es personalización de la cuenta: no instales
     y avisa a Paco.
3. **Respaldo** de la forma y sus reglas ([01-entorno.md](01-entorno.md#respaldo)).

## Instalar una sola forma (ya existe en la cuenta)

```bash
lkf workwith <dominio>
docker exec -i lkf-addons sh -c 'yes y | lkfaddons install -m <mod> -i forms -id <form_id>'
```

- El `form_id` es el **de esa cuenta**.
- Si imprime `sin cambios (local N <= instalada N), no se sube`, o subes la
  versión o agregas `-f`.
- En la salida tiene que aparecer `Installing Form (update): <nombre>`.
- Con `-id`, las formas que no están instaladas en la cuenta se saltan. Para
  una forma nueva, ver abajo.
- **No corras `-i forms` sin `-id`**: instala todas las formas del módulo y
  pisa las que la cuenta tenga distintas.

## Agregar un campo a una forma existente

1. Edita el `<forma>.xml` donde corresponda: en la rama de la cuenta si tiene
   override, si no en `lkf_addons`.
2. Copia un `<item>` de un campo del mismo tipo de esa u otra forma y cámbiale:
   - `field_id`: nuevo, 24 caracteres hex. Genera uno con
     `python3 -c "from bson import ObjectId; print(ObjectId())"`.
     Nunca reuses ni cambies un `field_id` que ya existe: los registros lo usan.
   - `label`, `field_type`, `required` y, si aplica, `options`.
   - Posición: los campos se ordenan por su lugar en la lista.
3. Sube la versión.
4. Instala la forma sola, primero en una cuenta de prueba. Revisa en la forma
   que el campo aparece y que las reglas siguen funcionando.
5. Si algún script del back debe leer el campo, eso lo hace un dev en
   `app.py` o en Sanic. Agregar el campo a la forma no basta.

## Crear una forma nueva

- Parte de una forma existente parecida, copia su XML y ajústalo. Ids nuevos
  para la forma y para cada campo.
- Va en `lkf_addons` si es para todas las cuentas, o en la rama de la cuenta
  si es solo de esa cuenta.
- `lkfaddons install -i forms -id` no sirve para formas nuevas porque se
  salta lo no instalado. Instálala sola con un script:

```python
# ...preámbulo...
import importlib
from lkf_addons import items
sys.path.insert(0, items.ADDONS_PATH)
MOD, NOMBRES = 'base', ['mi_forma_nueva']       # nombres de XML sin .xml

forms = importlib.import_module(f'{MOD}.items.forms')
_o, sys.stdout = sys.stdout, sys.stderr
fr = forms.FormResource(path=forms.__path__[0], module=MOD, settings=settings)
todas = fr.instalable_forms()
sys.stdout = _o
sel = {n: todas[n] for n in NOMBRES}
for n in NOMBRES:
    print(n, sel[n], 'ya instalada:', lkm.form_id(n, 'id'))
if APLICAR:
    sel['install_order'] = NOMBRES
    print(fr.install_forms(sel))
```

```bash
docker exec -i -w /srv/scripts/addons/modules lkf-addons python3 - < instalar_forma.py
docker exec -i -w /srv/scripts/addons/modules -e APLICAR=1 lkf-addons python3 - < instalar_forma.py
```

Después verifica los campos con `api.get_form_id_fields(<nuevo_id>)`.

## Misma forma en varias cuentas

1. Lista las cuentas y, por cada una, haz **solo lectura**: override en su
   rama, campos de más contra el XML y número de reglas.
2. Separa las cuentas limpias de las personalizadas. En las personalizadas no
   reinstales el XML completo: ajusta solo lo que cambió en su rama, o avisa a Paco.
3. Instala en **una** cuenta limpia, verifica y prueba. Luego la siguiente.
   Nunca encadenes el chequeo y la instalación en un mismo loop.
4. En loops de shell: `lkf workwith` se come el stdin de un heredoc, así que
   usa `< /dev/null`. En zsh, `$var` con espacios no se separa en argumentos;
   usa `bash -c`.
