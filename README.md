# clave10-sdk

Repo paraguas: junta los repos del entorno de desarrollo de clave10 como
submodulos y los levanta con **un solo `docker compose`** en la raiz.

```
clave10-sdk/
  docker-compose.yml   <- el stack completo
  addons/              <- scripts de addons + el mini-back
  lkf-sanic-apps/      <- app Sanic, destino de los *_sdk.py
  clave10/             <- el front (servicio "soter")
  linkaform_api/       <- libreria, se monta dentro de los dos backends
  clave10-app/         <- app movil
  lkf-claude/          <- tooling
```

Cada submodulo conserva su propio `docker/docker-compose.yml` para trabajar
con ese servicio aislado. El de aqui es la version integrada y es
**autocontenido**: si cambias un montaje dentro de un repo, refleja el cambio
aqui tambien.

## Que levanta

```
navegador (localhost:3000)
   |  soter, el front
   v
lkf-miniback (localhost:8000)
   |  decide por el nombre del script
   |
   |-- *_sdk.py  --> docker exec lkf-sanic-app   (puerto 8888 publicado)
   +-- lo demas  --> docker exec lkf-addons
```

El mini-back no le habla a los backends por red: hace `docker exec` por
**nombre de contenedor** contra el `docker.sock` del host. Por eso los
`container_name` del compose son fijos y no se deben cambiar.

El front tampoco usa la red interna: sus llamadas salen del navegador, asi que
`NEXT_PUBLIC_API_BASE_URL` apunta a `http://localhost:8000/api`.

## Primer arranque

```bash
git clone --recurse-submodules git@github.com:linkaform/clave10-sdk.git
cd clave10-sdk
# si ya lo clonaste sin --recurse-submodules:
git submodule update --init --recursive
# --recursive no es opcional: addons trae `modules` y `test/sdk_testing`
# como submodulos propios, y el compose monta ./addons/modules. Sin el,
# ese directorio queda vacio y /api/health reporta scripts: 0.

# redes externas, una sola vez por maquina
docker network create -d bridge --gateway 172.23.0.1 --subnet 172.23.0.0/16 linkaform
docker network create -d bridge sanic

cp .env.example .env        # opcional, todo tiene default

# secrets, antes del primer up. NINGUNO viaja en el clon: estan en .gitignore
# y hay que crearlos a mano en cada maquina.
#   addons/secrets/accounts.ini        <- desde secrets/accounts.ini.example
#   addons/config/local_settings.py    <- no tiene plantilla; pidesela a alguien
#                                         del equipo. Lee accounts.ini y arma
#                                         `config`; sin el, config/settings.py
#                                         imprime "local_settings... NOT FOUND!!!"
#                                         y el contenedor no sirve scripts.
cd addons && ./lkf workon local && ./lkf workwith <dominio> && cd ..
#   escriben current_env y current_domain EN EL HOST y mueven la rama de
#   modules/. lkf-sanic-apps los toma por el symlink de accounts.ini.

docker compose up -d --build
```

Las imagenes `develop` se construyen `FROM linkaform/{addons,sanic-app}:base`.
Si no las tienes localmente:

```bash
docker compose --profile base build lkf-addons-base lkf-sanic-app-base
```

## Submodulos

Tras un clon, cada submodulo queda en **HEAD detached**. Es lo normal: el repo
padre registra un commit exacto, no una rama, y `git submodule update` hace
checkout de ese SHA. No esta roto.

Para arrancar con todo en `master` y en el ultimo commit:

```bash
git submodule foreach --recursive 'git checkout master && git pull --ff-only origin master'
```

`--recursive` alcanza tambien los tres anidados (`addons/modules`,
`addons/test/sdk_testing`, `lkf-sanic-apps/app/modules`). `--ff-only` hace que
falle en vez de inventar un merge si algun submodulo divergio.

Los seis del paraguas declaran `branch = master` en `.gitmodules`, asi que
tambien sirve el atajo:

```bash
git submodule update --remote --merge
```

Ojo con la diferencia: ese trae lo ultimo pero **deja el submodulo detached**.
El `foreach` de arriba es el que ademas lo planta en la rama.

`master` es el punto de partida, no el destino: `addons/modules` tiene una
rama por cuenta (`seguridad`, `account_29954`, ...) y `./lkf workwith <dominio>`
la elige despues. Ahi si esperas ver ` M modules` en `git status` — es correcto
y no se commitea.

Mover un submodulo deja su puntero distinto al que registra el padre
(` M <submodulo>`). Mientras no lo commitees aqui, el cambio vive solo en tu
disco y el proximo clon vuelve al SHA viejo.

## Dia a dia

```bash
docker compose up -d          # levanta los 4 en orden
docker compose ps             # los 4 arriba, ningun *-base
docker compose logs -f miniback
docker compose down
```

Verificar que quedo bien:

```bash
curl -s localhost:8000/api/health   # ok:true y los dos targets con su conteo
curl -s localhost:8888/health       # {"status": "ok", ...}
```

En `/api/health`, un target con `scripts: 0` significa que el montaje de
`modules` de ese contenedor quedo mal.

Entrar a un contenedor:

```bash
docker compose exec lkf-addons bash
docker compose exec lkf-sanic-app bash
```

## Puertos

| Servicio        | Host   | Contenedor |
| --------------- | ------ | ---------- |
| `soter`         | 3000   | 3000       |
| `lkf-miniback`  | 8000   | 8000       |
| `lkf-sanic-app` | 8888   | 8000       |
| `lkf-addons`    | 5001   | 5000       |

`MINIBACK_PORT` en `.env` mueve el 8000 y el front lo sigue solo.

## Orden de arranque

`soter` espera a que `lkf-miniback` este *healthy*; el mini-back espera a que
los dos backends esten *started* (no *healthy*) a proposito: la app Sanic
conecta a mongo al arrancar, y si esa dependencia falla no queremos que se
caiga el stack entero. El mini-back degrada solo — 503 en ese destino,
`ok:false` en `/api/health` — y sigue sirviendo el otro. Para exigir que Sanic
este realmente sirviendo, cambia su `condition` a `service_healthy` en el
compose.

Los `*_sdk.py` si necesitan la app Sanic respondiendo: no son scripts
autonomos, le pegan por HTTP a su propio contenedor.

## Deuda conocida

- **`~/lkf` literal.** Quedaron rutas viejas que asumen que los repos viven en
  `~/lkf`: `addons/lkf:325` y `lkf-sanic-apps/lkf:324` (`./lkf test`), y
  `addons/test/docker/docker-compose.yaml:9,32`. Tras la mudanza a
  `~/clave10-sdk` no resuelven; el stack no las usa, pero `./lkf test` si. Se
  arreglan con un `ln -s ~/clave10-sdk ~/lkf` o parcheando esas lineas.
  `addons/docker/docker-compose.worktree.yml` ya no esta en la lista: ahora
  toma `linkaform_api` de `LKF_API` — la misma variable del resolver de
  `lkf-claude` — y solo cae a `~/lkf` como default.
- **`infosync_scripts` sin montar.** Los compose de origen montan
  `../../lkf/infosync_scripts` en `/srv/infosync_scripts`, de un repo `lkf` que
  no esta como submodulo. Hoy eso solo creaba un directorio vacio. Las lineas
  quedaron comentadas en el compose por si aparece el repo.
- **Config del front congelada en la imagen.** `clave10/Dockerfile:28-29` copia
  `tsconfig.json` y los `*.config.*` en build time, y el compose solo monta
  `src/`, `public/` y `cache/`. Tocar `next.config.ts`, `tailwind.config.ts` o
  las dependencias pide `docker compose build soter`; no basta reiniciar. El
  rebuild es barato: `yarn install` corre en una capa anterior y se reusa.