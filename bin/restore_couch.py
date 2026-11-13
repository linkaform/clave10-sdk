#!/usr/bin/env python3
# coding: utf-8
"""restore-couch (raiz): replica las bases CouchDB de una cuenta de produccion a tu sandbox sbx-*.

Wrapper fino: la logica vive en addons/lkf_addons/bin/restore_couch.py y corre DENTRO del
contenedor lkf-addons (python3 + requests). Credenciales: secrets/accounts.ini.

    ./lkf restore-couch --check     # prueba conexion y credenciales; no borra nada
    ./lkf restore-couch --dry-run   # muestra el plan
    ./lkf restore-couch [account_id] [--with-imagenes] [-y]

Requiere el stack arriba:  ./lkf start lkf-addons
"""
import os
import subprocess
import sys

CONTAINER = 'lkf-addons'
SCRIPT = '/usr/local/lib/python3.12/site-packages/lkf_addons/bin/restore_couch.py'


def contenedor_corriendo():
    res = subprocess.run(['docker', 'inspect', '-f', '{{.State.Running}}', CONTAINER],
                         capture_output=True, text=True)
    return res.returncode == 0 and res.stdout.strip() == 'true'


def main(argv):
    if not contenedor_corriendo():
        print('El contenedor %s no esta corriendo.\nLevantalo con:  ./lkf start %s'
              % (CONTAINER, CONTAINER), file=sys.stderr)
        return 1
    cmd = ['docker', 'exec', '-i']
    if sys.stdin.isatty():
        cmd.append('-t')
    if os.environ.get('LKF_ENV'):
        cmd += ['-e', 'LKF_ENV']  # pasa el valor del shell, sin ponerlo en el argv
    cmd += [CONTAINER, 'python3', SCRIPT] + argv[1:]
    return subprocess.call(cmd)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
