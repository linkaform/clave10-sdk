#!/usr/bin/env python3
# coding: utf-8
"""workon (raiz): elige el environment activo en addons/ y lkf-sanic-apps/ a la vez.

Orquestador sobre addons/lkf workon y lkf-sanic-apps/lkf workon, cada uno con
su propio secrets/current_env. lkf-sanic-apps no tiene environment "local"
(el sanic-app siempre es el destino local de los *_sdk.py, no hay otro modo
para el), asi que workon local solo se aplica a addons y aqui se avisa en vez
de fallar.

    ./lkf workon <local|preprod|prod>
    ./lkf workon            # muestra el environment actual de ambos repos
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGETS = (
    ('addons', os.path.join(REPO, 'addons', 'lkf')),
    ('lkf-sanic-apps', os.path.join(REPO, 'lkf-sanic-apps', 'lkf')),
)

# Ver lkf-sanic-apps/bin/workon.py: su ENVS es (preprod, prod), sin local.
SIN_SOPORTE = {
    'lkf-sanic-apps': {'local'},
}


def run(nombre, script, args):
    print('== %s ==' % nombre, flush=True)
    res = subprocess.run([script, 'workon'] + list(args), cwd=os.path.dirname(script))
    print()
    return res.returncode


def main(argv):
    args = argv[1:]
    env = args[0].strip().lower() if args else None

    codigos = []
    for nombre, script in TARGETS:
        if not os.path.exists(script):
            print('== %s ==\n  x no existe %s, se omite\n' % (nombre, script))
            continue
        if env in SIN_SOPORTE.get(nombre, set()):
            print('== %s ==\n  (sin cambios: este repo no tiene environment "%s")\n'
                  % (nombre, env))
            continue
        codigos.append(run(nombre, script, args))
    return max(codigos) if codigos else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
