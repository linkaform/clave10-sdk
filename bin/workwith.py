#!/usr/bin/env python3
# coding: utf-8
"""workwith (raiz): elige la cuenta activa en addons/ y lkf-sanic-apps/ a la vez.

Orquestador. Quien de verdad mueve un submodulo a la rama del dominio es
addons/lkf workwith y lkf-sanic-apps/lkf workwith, cada uno sobre el suyo
(modules/ y app/modules). Esto solo los llama a los dos en orden, con el
mismo cwd que tendrian si los corrieras a mano desde su propio directorio
-- addons/lkf escribe un .env relativo al cwd, y sin esto pisaria el .env
del compose de la raiz en vez del suyo.

    ./lkf workwith <domain_name>
    ./lkf workwith            # muestra el estado de ambos repos
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (nombre, script) en el orden en que se corren. addons primero: si su rama esta
# sucia y falla, mejor no tocar lkf-sanic-apps y dejar los dos repos consistentes
# en la cuenta anterior.
TARGETS = (
    ('addons', os.path.join(REPO, 'addons', 'lkf')),
    ('lkf-sanic-apps', os.path.join(REPO, 'lkf-sanic-apps', 'lkf')),
)


def run(nombre, script, args):
    print('== %s ==' % nombre, flush=True)
    res = subprocess.run([script, 'workwith'] + list(args), cwd=os.path.dirname(script))
    print()
    return res.returncode


def main(argv):
    args = argv[1:]
    codigos = []
    for nombre, script in TARGETS:
        if not os.path.exists(script):
            print('== %s ==\n  x no existe %s, se omite\n' % (nombre, script))
            continue
        codigo = run(nombre, script, args)
        codigos.append(codigo)
        if codigo != 0:
            print('x %s fallo, no se toca el resto para no dejar las cuentas '
                  'desincronizadas.' % nombre)
            break
    return max(codigos) if codigos else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
