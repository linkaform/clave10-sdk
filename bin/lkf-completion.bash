# Completion para lkf (el orquestador de la raiz de clave10-sdk). Sirve en bash y en
# zsh via bashcompinit; por eso nada de mapfile ni otros builtins solo de bash.
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
    local bin="$1" real
    [[ "$bin" == */* ]] || bin="$(command -v "$bin")" || return 0
    real="$(readlink -f "$bin")" || return 0
    python3 "$(dirname "$real")/bin/workwith.py" --list 2>/dev/null
}

# La palabra actual llega en $2 y el comando en $1: asi se evita indexar COMP_WORDS,
# que en zsh empieza en 1. El ${arr[@]:i:1} si es base 0 en los dos shells.
_lkf() {
    local cur="$2" cmd
    COMPREPLY=()

    if [[ $COMP_CWORD -eq 1 ]]; then
        COMPREPLY=($(compgen -W "start stop workwith workon install -h --help" -- "$cur"))
        return 0
    fi

    cmd="${COMP_WORDS[@]:1:1}"
    case "$cmd" in
        start)
            COMPREPLY=($(compgen -W "$_lkf_services -b --build" -- "$cur"))
            ;;
        stop)
            COMPREPLY=($(compgen -W "$_lkf_services" -- "$cur"))
            ;;
        workon)
            [[ $COMP_CWORD -eq 2 ]] && COMPREPLY=($(compgen -W "local preprod prod" -- "$cur"))
            ;;
        workwith)
            [[ $COMP_CWORD -eq 2 ]] && COMPREPLY=($(compgen -W "$(_lkf_domains "$1")" -- "$cur"))
            ;;
        install)
            COMPREPLY=($(compgen -W "-y" -- "$cur"))
            ;;
    esac
    return 0
}

complete -F _lkf lkf
complete -F _lkf ./lkf
