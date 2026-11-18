#!/usr/bin/env python3
# coding: utf-8
"""restore-psql: copia la base PostgreSQL de produccion al postgres de tu sandbox sbx-*.

El ambiente sale de `lkf workon` (secrets/current_env, o LKF_ENV). En la VM de sandbox cada
ambiente tiene su contenedor `<nombre>-postgres-1` (sbx-preprod -> preprod-postgres-1,
sbx-dev0 -> dev0-postgres-1, sbx-josepato0 -> josepato0-postgres-1).

Flujo (todo por stream, sin archivos intermedios):
    ssh PROD 'sudo -u postgres pg_dump -d infosync | gzip' | gunzip \
        | ssh SANDBOX 'docker exec -i <env>-postgres-1 psql ...'

    ./lkf restore-psql --dry-run     # muestra el plan; no toca nada
    ./lkf restore-psql [-y]          # pide teclear el nombre del ambiente
    ./lkf restore-psql --no-reset-passwords --password-user 126

Variables (opcionales):
    LKF_PSQL_PROD_SSH      default 10.128.10.121
    LKF_PSQL_SANDBOX_SSH   default vmsandbox0.lkf.cloud
    LKF_PSQL_PROD_DB       default infosync     (base en produccion)
    LKF_PSQL_DB            default infosync_qa  (base en el sandbox; o --db)
"""
import argparse
import os
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENVS = ('sbx-dev0', 'sbx-preprod', 'sbx-josepato0')


def env_activo():
    env = os.environ.get('LKF_ENV')
    if not env:
        try:
            with open(os.path.join(ROOT, 'addons', 'secrets', 'current_env')) as f:
                env = f.read().strip()
        except OSError:
            env = ''
    return env


def ssh(host, remote_cmd, **kw):
    return subprocess.run(['ssh', '-T', host, remote_cmd], **kw)


def main(argv):
    ap = argparse.ArgumentParser(prog='lkf restore-psql', description=__doc__.split('\n')[0])
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('-y', '--yes', action='store_true', help='no pedir confirmacion')
    ap.add_argument('--no-reset-passwords', action='store_true',
                    help='no igualar el password de todos los usuarios al de --password-user')
    ap.add_argument('--db', default=os.environ.get('LKF_PSQL_DB', 'infosync_qa'),
                    help='base destino en el sandbox (default infosync_qa)')
    ap.add_argument('--password-user', default='126', help='id de usuario cuyo hash se copia a todos (default 126)')
    args = ap.parse_args(argv[1:])

    env = env_activo()
    if env not in ENVS:
        print('El ambiente activo es "%s". restore-psql solo corre contra sandbox (%s).\n'
              'Cambialo con:  ./lkf workon sbx-<ambiente>' % (env, ', '.join(ENVS)), file=sys.stderr)
        return 1
    if not args.password_user.isdigit():
        print('--password-user debe ser un id numerico', file=sys.stderr)
        return 1

    container = '%s-postgres-1' % env[len('sbx-'):]
    prod = os.environ.get('LKF_PSQL_PROD_SSH', '10.128.10.121')
    sandbox = os.environ.get('LKF_PSQL_SANDBOX_SSH', 'vmsandbox0.lkf.cloud')
    prod_db = os.environ.get('LKF_PSQL_PROD_DB', 'infosync')

    # Los contenedores de sandbox no definen POSTGRES_DB: la base destino es --db y se verifica que exista.
    pg_user, pg_db = 'postgres', args.db
    probe = ssh(sandbox, "docker exec %s psql -U %s -d postgres -Atc %s"
                % (shlex.quote(container), pg_user, shlex.quote("SELECT datname FROM pg_database WHERE NOT datistemplate")),
                capture_output=True, text=True)
    if probe.returncode != 0:
        print('No pude leer el contenedor %s en %s:\n%s' % (container, sandbox, probe.stderr.strip()), file=sys.stderr)
        return 1
    existentes = probe.stdout.split()
    existe = pg_db in existentes

    print('Plan restore-psql')
    print('  origen : %s  (pg_dump %s)' % (prod, prod_db))
    print('  destino: %s  contenedor %s  db %s  usuario %s' % (sandbox, container, pg_db, pg_user))
    print('  se BORRA y recrea la db "%s" en %s%s' % (pg_db, env, '' if existe else '  (NO existe todavia; bases: %s)' % ', '.join(existentes)))
    if not args.no_reset_passwords:
        print('  luego todos los passwords de users_customuser = el del usuario %s' % args.password_user)
    if args.dry_run:
        return 0

    if not args.yes:
        if input('Teclea "%s" para continuar: ' % env).strip() != env:
            print('Cancelado.')
            return 1

    psql = 'docker exec -i %s psql -v ON_ERROR_STOP=0 -U %s' % (shlex.quote(container), shlex.quote(pg_user))
    q = shlex.quote
    prep = (
        "%s -d postgres -c %s && %s -d postgres -c %s && %s -d postgres -c %s"
        % (psql,
           q("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='%s' AND pid <> pg_backend_pid();" % pg_db),
           psql, q('DROP DATABASE IF EXISTS "%s";' % pg_db),
           psql, q('CREATE DATABASE "%s" ENCODING UNICODE;' % pg_db)))
    print('1/3 recreando la db destino...')
    if ssh(sandbox, prep).returncode != 0:
        print('Fallo al recrear la db.', file=sys.stderr)
        return 1

    print('2/3 copiando prod -> sandbox (puede tardar)...')
    dump = subprocess.Popen(['ssh', '-T', prod, "sudo -u postgres pg_dump -d %s | gzip" % shlex.quote(prod_db)],
                            stdout=subprocess.PIPE)
    gun = subprocess.Popen(['gzip', '-d'], stdin=dump.stdout, stdout=subprocess.PIPE)
    dump.stdout.close()
    load = subprocess.Popen(['ssh', '-T', sandbox, '%s -d %s -f-' % (psql, q(pg_db))], stdin=gun.stdout)
    gun.stdout.close()
    rc_load = load.wait()
    rc_gun = gun.wait()
    rc_dump = dump.wait()
    if rc_dump or rc_gun or rc_load:
        print('Fallo la copia (ssh/pg_dump=%s, gzip=%s, psql=%s).' % (rc_dump, rc_gun, rc_load), file=sys.stderr)
        return 1

    if not args.no_reset_passwords:
        print('3/3 igualando passwords...')
        sql = ('UPDATE users_customuser SET password=(SELECT password FROM users_customuser WHERE id=%s);'
               % args.password_user)
        if ssh(sandbox, '%s -d %s -c %s' % (psql, q(pg_db), q(sql))).returncode != 0:
            print('Fallo el UPDATE de passwords.', file=sys.stderr)
            return 1
    print('Listo: %s restaurado en %s.' % (pg_db, env))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
