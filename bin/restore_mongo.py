#!/usr/bin/env python3
# coding: utf-8
"""restore-mongo (raiz): copia la base de una cuenta de produccion a tu sandbox sbx-*.

Wrapper fino: la logica vive en addons/lkf_addons/bin/restore_mongo.py y corre DENTRO del
contenedor lkf-addons, que ya trae mongodump/mongorestore y pymongo. Asi nadie tiene que
instalar herramientas de mongo en su maquina.

    ./lkf restore-mongo --check     # pide claves y hace ping; no borra nada
    ./lkf restore-mongo --dry-run   # muestra el plan
    ./lkf restore-mongo [account_id] [--with-admin] [-y]

Requiere el stack arriba:  ./lkf start lkf-addons
"""
import os
import subprocess
import sys

CONTAINER = 'lkf-addons'
SCRIPT = '/usr/local/lib/python3.12/site-packages/lkf_addons/bin/restore_mongo.py'


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
