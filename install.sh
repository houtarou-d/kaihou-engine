#!/usr/bin/env bash
set -euo pipefail

# ---------- Funciones auxiliares ----------
prompt() {
    local msg="$1"
    local default="$2"
    read -rp "$msg [$default]: " answer
    echo "${answer:-$default}"
}

add_alias() {
    local rc_file="$1"
    local alias_cmd="alias nlp='python -m nlp_engine.cli'"
    # No duplicar líneas
    grep -qxF "$alias_cmd" "$rc_file" 2>/dev/null || echo "$alias_cmd" >> "$rc_file"
    echo "✅ Alias añadido a $rc_file"
}

# ---------- 1️⃣ Elegir carpeta de instalación ----------
echo "=== Instalador del NLP Engine ==="
INSTALL_DIR=$(prompt "Directorio donde instalar (ruta absoluta)" "$HOME/kaihou-nlp-engine")
mkdir -p "$INSTALL_DIR"
echo "📁 Carpeta de instalación: $INSTALL_DIR"

# ---------- 2️⃣ Copiar código ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -r "$SCRIPT_DIR"/nlp_engine "$INSTALL_DIR"/
cp "$SCRIPT_DIR"/requirements.txt "$INSTALL_DIR"/
# Si tienes setup.py o pyproject.toml, descomenta la siguiente línea:
# cp "$SCRIPT_DIR"/setup.py "$INSTALL_DIR"/ 2>/dev/null || true

# ---------- 3️⃣ Crear virtual‑env ----------
cd "$INSTALL_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ---------- 4️⃣ Preguntar idiomas ----------
echo "🔤 Selecciona los idiomas que deseas instalar (separados por espacio):"
echo "   es  en  fr  de  (puedes añadir más si los defines en el código)"
read -rp "Idiomas > " LANGS
LANGS=$(echo "$LANGS" | tr '[:upper:]' '[:lower:]' | tr -s ' ' '\n' | sort -u | tr '\n' ' ')

declare -A MODEL_MAP=(
    [es]="es_core_news_sm"
    [en]="en_core_web_sm"
    [fr]="fr_core_news_sm"
    [de]="de_core_news_sm"
)

for L in $LANGS; do
    if [[ -v MODEL_MAP[$L] ]]; then
        echo "📦 Descargando modelo spaCy para $L ..."
        python -m spacy download "${MODEL_MAP[$L]}"
    else
        echo "⚠️  No hay modelo predefinido para '$L'. Se omite."
    fi
done

# ---------- 5️⃣ Alias ----------
if [[ -n "${ZSH_VERSION-}" ]]; then
    RC_FILE="$HOME/.zshrc"
else
    RC_FILE="$HOME/.bashrc"
fi
add_alias "$RC_FILE"

# ---------- 6️⃣ Mensaje final ----------
echo -e "\n✅ Instalación completada."
echo "Ejecuta: nlp <comando>"
echo "Si el alias no funciona ahora, abre una nueva terminal o ejecuta: source $RC_FILE"
