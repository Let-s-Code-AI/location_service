#!/bin/bash

# Skrypt do konfiguracji środowiska wirtualnego dla projektu FastAPI

# Tworzenie środowiska wirtualnego jeśli nie istnieje
if [ ! -d "venv" ]; then
    echo "Tworzenie środowiska wirtualnego..."
    python3 -m venv venv
    echo "Środowisko wirtualne utworzone!"
else
    echo "Środowisko wirtualne już istnieje."
fi

# Aktywacja środowiska wirtualnego
echo "Aktywacja środowiska wirtualnego..."
source venv/bin/activate

# Aktualizacja pip
echo "Aktualizacja pip..."
pip install --upgrade pip

# Instalacja zależności
echo "Instalacja zależności z requirements.txt..."
pip install -r requirements.txt

echo ""
echo "✅ Konfiguracja zakończona!"
echo ""
echo "Aby aktywować środowisko wirtualne w przyszłości, użyj:"
echo "  source venv/bin/activate"
echo ""
echo "Aby uruchomić aplikację:"
echo "  uvicorn main:app --reload"


