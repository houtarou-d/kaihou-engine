#!/usr/bin/env bash
# ------------------------------------------------------------
# setup.sh – crea un entorno virtual (.venv) y instala kaihou‑engine
# ------------------------------------------------------------

set -euo pipefail

VENV_DIR=".venv"

# 1️⃣  Crear .venv si no existe
if [[ ! -d "$VENV_DIR" ]]; then
    echo "🔧 Creando entorno virtual en $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
else
    echo "🔧 Entorno virtual ya existente en $VENV_DIR"
fi

# 2️⃣  Activar el entorno (detecta la shell)
if [[ -n "${BASH_VERSION-}" ]]; then
    source "$VENV_DIR/bin/activate"
elif [[ -n "${ZSH_VERSION-}" ]]; then
    source "$VENV_DIR/bin/activate"
elif [[ -n "${FISH_VERSION-}" ]]; then
    source "$VENV_DIR/bin/activate.fish"
else
    echo "⚠️  Shell desconocida – activa manualmente con: source $VENV_DIR/bin/activate"
fi

# 3️⃣  Actualizar pip y wheel
pip install --upgrade pip setuptools wheel

# 4️⃣  Instalar el proyecto en modo editable (incluye todas las dependencias)
pip install -e .

# 5️⃣  (Opcional) Instalar dependencias de desarrollo
if [[ "${1-}" == "--dev" ]]; then
    echo "🔧 Instalando dependencias de desarrollo ..."
    pip install -e .[dev]
fi

echo "✅ Instalación completa. Usa 'source $VENV_DIR/bin/activate' para activar el entorno."
