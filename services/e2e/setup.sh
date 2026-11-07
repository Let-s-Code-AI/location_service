#!/bin/bash

# Konfiguracja środowiska dla testów E2E (Playwright + pytest).
# Wymaga Python 3.11+ i Node.js (frontend jest uruchamiany przez Vite).

set -e

if [ ! -d "venv" ]; then
    echo "Tworzenie środowiska wirtualnego..."
    python3 -m venv venv
fi

echo "Instalacja zależności Pythona..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Instalacja przeglądarki Chromium dla Playwright..."
playwright install chromium

echo "Instalacja zależności frontendu (potrzebne do uruchomienia Vite)..."
(cd ../frontend && npm install)

echo ""
echo "✅ Gotowe. Uruchom testy poleceniem: pytest -q"
