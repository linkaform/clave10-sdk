# Registros de formas

Viven en Mongo, colección `form_answer` de `infosync_answers_client_<id>`:
`form_id`, `folio`, `user_id`, `answers` (field_id → valor), `created_at`,
`updated_at` y `deleted_at` (si está borrado). Las versiones anteriores de
cada registro están en `answer_version` (`connection_record_id` = `_id` del registro).

## Leer

```python
# ...preámbulo...
from bson import ObjectId
r = db.form_answer.find_one({'form_id': 123695, 'folio': '<folio>'})
# o por id: db.form_answer.find_one({'_id': ObjectId('...')})
print(r['_id'], r['folio'], r['user_id'], r['updated_at'])
print(json.dumps(r['answers'], default=str, ensure_ascii=False, indent=1))
```

- Pon siempre `limit` y proyección en búsquedas grandes.
- Sin índice, un `$lookup` entre `form_answer` y `answer_version` es muy lento.
  Mejor saca los ids primero y busca con `$in` en lotes de unos 400.

## Editar: por API, no con `$set`

Editar por la API sube la versión, deja historial en `answer_version`,
sincroniza con la app y dispara el workflow. Un `$set` directo en Mongo se
salta todo eso. Úsalo solo si Paco lo aprueba para ese caso.

### Cambiar uno o varios campos simples

```python
# ...preámbulo...
FORM_ID, FOLIOS = 123695, ['<folio>']
CAMBIOS = {'abcde0001000000000010007': 'dia'}     # field_id: valor nuevo
for f in FOLIOS:
    r = db.form_answer.find_one({'form_id': FORM_ID, 'folio': f}, {'answers': 1})
    print(f, {k: r['answers'].get(k) for k in CAMBIOS}, '->', CAMBIOS)
if APLICAR:
    print(api.patch_multi_record(CAMBIOS, FORM_ID, folios=FOLIOS))
```

`patch_multi_record` **no acepta grupos repetitivos** (listas): regresa `400`
y no cambia nada.

### Cambiar un grupo repetitivo o reescribir el registro

`patch_record` **reemplaza todo `answers`**: lo que no mandes se borra. Siempre
mezcla con lo que ya tiene el registro:

```python
# ...preámbulo...
from bson import ObjectId
FORM_ID, RID = 123695, '6b00...'
r = db.form_answer.find_one({'_id': ObjectId(RID)})
data = api.get_metadata(FORM_ID)
data['answers'] = {**r['answers'], '<grupo_field_id>': [ {...}, {...} ]}
print('antes', len(r['answers']), 'después', len(data['answers']))
if APLICAR:
    print(api.patch_record(data=data, record_id=RID).get('status_code'))   # 202
```

## Cuidado con el dueño del registro

Si editas el registro de otro usuario con la API key de la cuenta, el
`user_id` del registro cambia al dueño de la cuenta. Para módulos que buscan
"lo abierto de este usuario" (Check In, asistencia, rondines), eso hace que el
registro desaparezca para su dueño.

- En pruebas, edita registros del dueño de la cuenta o de usuarios de prueba.
- Si tienes que editar el registro de un guardia o empleado, confirma después
  que conserva su `user_id`. Si cambió, avisa a Paco.

## Registro borrado por error

Al borrar desde LinkaForm, `answers` queda vacío. Para recuperarlo:
1. busca la última versión con datos en `answer_version`
   (`{'connection_record_id': ObjectId('<id>')}`, ordenado por `version` de mayor a menor);
2. o búscalo en la base CouchDB del usuario (`clave_<user_id>`), que guarda
   la copia de la app.

Para restaurar se crea un registro nuevo (con otro `_id`). Hazlo con Paco.

## Archivos y fotos

Las URLs de fotos y archivos (`f001.backblazeb2.com/file/app-linkaform/...`)
se guardan dentro de `answers`. Para saber a qué registro pertenece una foto,
busca la URL o el nombre del archivo en `answers` con una regex, limitada a la
forma correcta.
