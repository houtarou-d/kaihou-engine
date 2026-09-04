#!/usr/bin/env bash
set -euo pipefail

prompt() {
    local msg="$1"
    local default="$2"
    read -rp "$msg [$default]: " answer
    echo "${answer:-$default}"
}

remove_alias() {
    local rc_file="$1"
    local alias_cmd="alias nlp='python -m nlp_engine.cli'"
    if grep -qxF "$alias_cmd" "$rc_file" 2>/dev/null; then
        sed -i "/^${alias_cmd//\//\\/}$/d" "$rc_file"
        echo "✅ Alias eliminado de $rc_file"
    fi
}

echo "=== Desinstalador del NLP Engine ==="
INSTALL_DIR=$(prompt "Directorio donde está instalado" "$HOME/kaihou-nlp-engine")
if [[ ! -d "$INSTALL_DIR" ]]; then
    echo "❌ No se encontró $INSTALL_DIR"
    exit 1
fi

rm -rf "$INSTALL_DIR"
echo "🗑️  Carpeta $INSTALL_DIR eliminada."

if [[ -n "${ZSH_VERSION-}" ]]; then
    RC_FILE="$HOME/.zshrc"
else
    RC_FILE="$HOME/.bashrc"
fi
remove_alias "$RC_FILE"

echo -e "\n✅ Desinstalación completada."
echo "Abre una nueva terminal o ejecuta: source $RC_FILE para que desaparezca el alias."
