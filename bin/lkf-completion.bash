# bash completion para lkf (el orquestador de la raiz de clave10-sdk).
#
# Lo instala `lkf install` como ~/.bash_completion.d/lkf, que ~/.bashrc ya carga.
# Para probarlo en el shell actual:  source ~/.bash_completion.d/lkf
#
# La gramatica espeja la de `lkf --help`; si agregas una accion o un servicio en el
# lkf de la raiz, agregalo aqui tambien.

_lkf_services="clave10 lkf-sanic-app lkf-addons miniback lkf-miniback"

# Dominios de la cuenta, uno por linea. Se le piden a bin/workwith.py --list en vez de
# leer accounts.ini aqui: ese archivo lleva credenciales. La ruta del repo sale de
# resolver el symlink con el que se invoco lkf, igual que hace el propio lkf.
_lkf_domains() {
    local bin="${COMP_WORDS[0]}" real
    [[ "$bin" == */* ]] || bin="$(command -v "$bin")" || return 0
    real="$(readlink -f "$bin")" || return 0
    python3 "$(dirname "$real")/bin/workwith.py" --list 2>/dev/null
}

_lkf() {
    local cur="${COMP_WORDS[COMP_CWORD]}" cmd
    COMPREPLY=()

    if [[ $COMP_CWORD -eq 1 ]]; then
        mapfile -t COMPREPLY < <(compgen -W "start stop workwith workon install -h --help" -- "$cur")
        return 0
    fi

    cmd="${COMP_WORDS[1]}"
    case "$cmd" in
        start)
            mapfile -t COMPREPLY < <(compgen -W "$_lkf_services -b --build" -- "$cur")
            ;;
        stop)
            mapfile -t COMPREPLY < <(compgen -W "$_lkf_services" -- "$cur")
            ;;
        workon)
            [[ $COMP_CWORD -eq 2 ]] && mapfile -t COMPREPLY < <(compgen -W "local preprod prod" -- "$cur")
            ;;
        workwith)
            [[ $COMP_CWORD -eq 2 ]] && mapfile -t COMPREPLY < <(compgen -W "$(_lkf_domains)" -- "$cur")
            ;;
        install)
            mapfile -t COMPREPLY < <(compgen -W "-y" -- "$cur")
            ;;
    esac
    return 0
}

complete -F _lkf lkf
complete -F _lkf ./lkf
