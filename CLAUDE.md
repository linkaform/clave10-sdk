# clave10-sdk

Repo paraguas del entorno de desarrollo de Clave 10. Junta seis repos como
submodulos y los levanta con **un solo `docker compose`** desde la raiz.

```
clave10-sdk/
  docker-compose.yml   <- el stack completo, autocontenido
  addons/              <- scripts de addons + el mini-back   (submodulos propios)
  lkf-sanic-apps/      <- app Sanic, destino de los *_sdk.py
  clave10/             <- el front (servicio "clave10")
  linkaform_api/       <- libreria, se monta dentro de los dos backends
  clave10-app/         <- app movil (no participa en el compose)
  lkf-claude/          <- tooling: plugin de Claude Code
```

## Submodulos

`addons` tiene submodulos propios (`modules` y `test/sdk_testing`), asi que
**siempre `--recursive`**:

```bash
git submodule update --init --recursive
```

Sin `--recursive`, `addons/modules` queda vacio, el compose lo monta igual y
`/api/health` reporta `scripts: 0`. Es el sintoma tipico de un clon a medias.

Tras un clon todos quedan en HEAD detached — es lo normal, no esta roto. Para
dejarlos en `master` y en el ultimo commit:

```bash
git submodule foreach --recursive 'git checkout master && git pull --ff-only origin master'
```

`master` es el punto de partida: `addons/modules` tiene una rama por cuenta y
`./lkf workwith <dominio>` la elige despues, dejando un ` M modules` esperado
que no se commitea. El README lo detalla en su seccion "Submodulos".

Cada submodulo es un repo independiente con su propia rama: un cambio se
commitea y se pushea **en el submodulo**, y solo despues se actualiza el
puntero aqui. Antes de pushear el paraguas, verifica que los commits que
apunta existan en el remoto de cada submodulo — un puntero a un commit local
rompe el clon de todos los demas:

```bash
git submodule foreach 'git log --oneline @{u}..HEAD'   # vacio = todo pusheado
```

## Levantar el stack

```bash
cp .env.example .env    # opcional, todo tiene default
docker compose up -d --build

curl -s localhost:8000/api/health   # ok:true, los dos targets con scripts > 0
curl -s localhost:8888/health       # {"status": "ok", ...}
```

Antes del primer `up` hacen falta las dos redes externas y los secrets de
`addons/`, que **no viajan en el clon** (estan en .gitignore) y se crean a
mano en cada maquina: `secrets/accounts.ini` y `config/local_settings.py`.
Este ultimo no tiene plantilla y lleva credenciales reales, asi que se pide al
equipo; sin el, `config/settings.py` imprime `local_settings... NOT FOUND!!!`
y el contenedor arranca sin servir scripts. El README tiene la secuencia.

| Servicio        | Host | Contenedor |
| --------------- | ---- | ---------- |
| `clave10`       | 3000 | 3000       |
| `lkf-miniback`  | 8000 | 8000       |
| `lkf-sanic-app` | 8888 | 8000       |
| `lkf-addons`    | 5001 | 5000       |

El mini-back no le habla a los backends por red: hace `docker exec` por
**nombre de contenedor** contra el `docker.sock` del host. Por eso los
`container_name` del compose son fijos y no se deben cambiar. Decide el
destino por el nombre del script: `*_sdk.py` va a `lkf-sanic-app`, lo demas a
`lkf-addons`.

## Plugin de Claude Code

El conocimiento de como desarrollar sobre `linkaform_sdk` — convenciones,
patrones, anti-patrones y schemas — vive en el plugin `lkf-claude`, no en este
repo. Se instala una vez:

```
/plugin marketplace add linkaform/lkf-claude
/plugin install lkf-claude@lkf-claude
```

Aporta las skills `/lkf-claude:lkf`, `:lkf-module`, `:lkf-learn`,
`:lkf-review`, `:worktree`, el command `:commit`, y el MCP server
`lkf-knowledge` para consultar la knowledge base en vivo.

Instalarlo o no es decision de cada quien: Claude Code lo guarda en tu
`.claude/settings.json` local, que estos repos no versionan.

## Trampas conocidas

- **`~/lkf` literal.** `addons/lkf:325`, `lkf-sanic-apps/lkf:324` y
  `addons/test/docker/docker-compose.yaml:9,32` asumen que los repos viven en
  `~/lkf`. El stack no las usa, pero `./lkf test` si. Se resuelve con
  `ln -s ~/clave10-sdk ~/lkf`.
- **`infosync_scripts` sin montar.** Viene del repo `lkf`, que no es submodulo
  de aqui. Las lineas quedaron comentadas en el compose.
- **Config del front congelada en la imagen.** `clave10/Dockerfile:28-29` copia
  `tsconfig.json` y los `*.config.*` en build time, y el compose solo monta
  `src/`, `public/` y `cache/`. Tocar `next.config.ts`, `tailwind.config.ts` o
  las dependencias pide `docker compose build clave10`; no basta reiniciar. El
  rebuild es barato: `yarn install` corre en una capa anterior y se reusa.
- **`scripts: 0` en `/api/health`** significa que el montaje de `modules` de
  ese contenedor quedo mal — casi siempre, submodulos sin `--recursive`.
