# Diagnóstico

## 1. Ubicar la cuenta

El reporte trae un correo o un nombre de cliente. Busca el dominio:

```bash
lkf workwith --list | grep -i morpho
grep -n -A4 "^\[morpho\]" ~/clave10-sdk/addons/secrets/accounts.ini | grep -v -i "key\|pass"
```

Luego `lkf workwith <dominio>` y confirma el `account_id` con el preámbulo.

## 2. Ver el error real

Si el reporte trae captura, el traceback dice el archivo y la línea. Si no,
busca en `script_log` (solo guarda las ejecuciones de scripts):

```python
# ...preámbulo...
for x in db.script_log.find({}, {'status': 1, 'script_id': 1, 'traceback': 1,
                                 'start_date': 1, 'run_success': 1}).sort('_id', -1).limit(10):
    print(x)
```

- `traceback` es una URL a un `.log` en Backblaze con la salida completa.
- `status: running` con `Sin permisos usuario: …` = el usuario no tiene permiso
  sobre el script.
- Para saber qué script es: `db.LKFModules.find_one({'item_id': <script_id>})['item_name']`.

## 3. Revisar lo que el código espera

El código busca items por nombre. Si el traceback cae en una línea que lee
`answers[...]` o algo con `CATALOGO_`/`FORM_`, revisa que ese nombre exista en
la cuenta:

```bash
cd ~/clave10-sdk/addons
grep -rn "catalog_id('\|form_id('" lkf_addons/addons/<mod>/model.py | head -40
```

```python
# ...preámbulo...
for n in ('catalogo_de_items', 'catalogo_de_formas'):
    print(n, lkm.catalog_id(n))                # {} = no existe con ese nombre
print(lkm.form_id('programar_tareas', 'id'))
for x in db.LKFModules.find({'item_type': 'catalog'}, {'_id': 0, 'item_name': 1, 'item_id': 1, 'module': 1}):
    print(x)
```

Si el código pide un nombre y la cuenta tiene otro, casi siempre falta una
**migración**. Revisa `addons/lkf_addons/addons/<mod>/migrations/` y ve
[05-catalogos.md](05-catalogos.md#migraciones-renombres).

## 4. Revisar la forma, sus reglas y su catálogo

```python
# ...preámbulo...
FORM_ID = 123695
forma = api.get_form_id_fields(FORM_ID)
forma = forma[0] if isinstance(forma, list) else forma
for f in forma.get('fields', []):
    print(f['field_id'], f.get('field_type'), f.get('label'),
          (f.get('catalog') or {}).get('catalog_id'))
print('reglas', [(r['id'], len(r['rules'])) for r in reglas(FORM_ID)])
print('registros', db.form_answer.count_documents({'form_id': FORM_ID, 'deleted_at': {'$exists': False}}))
print('último', db.form_answer.find_one({'form_id': FORM_ID}, {'folio': 1, 'updated_at': 1}, sort=[('updated_at', -1)]))
```

- Reglas en `[]` cuando la forma debería tener = se perdieron. Se restauran
  desde el XML ([04-reglas-y-workflows.md](04-reglas-y-workflows.md)).
- Un último registro muy viejo indica desde cuándo está roto.

## 5. Revisar la rama de la cuenta en `modules`

```bash
cd ~/clave10-sdk/addons/modules
git fetch -q origin
git diff --stat origin/master...origin/account_10975        # lo propio de la cuenta
git log --oneline origin/master..origin/account_10975 -- base | head
git grep -n "catalogo_de_formas" origin/account_10975 -- base   # referencias viejas
```

Lo que aparezca en `<mod>/items/forms/` de esa rama es un **override**: se
instala esa versión, no la de `lkf_addons`. Si el arreglo es en el XML, se
corrige ahí.

## 6. Escribir el diagnóstico

Antes de arreglar, anota en el hilo o en tu tarea:
- causa, con la evidencia (qué consultaste y qué salió);
- qué vas a cambiar y en qué cuenta;
- qué no vas a tocar.
