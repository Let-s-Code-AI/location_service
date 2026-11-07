# User Stories

---

## Podsumowanie funkcjonalności

Aplikacja FastAPI umożliwia:
- ✅ Podstawową weryfikację działania API
- ✅ Testowanie komunikacji z API przez spersonalizowane powitanie
- ✅ Zarządzanie lokalizacjami (CRUD):
  - Tworzenie nowych lokalizacji
  - Przeglądanie listy lokalizacji z paginacją
  - Wyświetlanie szczegółów pojedynczej lokalizacji
  - Dodawanie opisu lokalizacji (pole `description`)

**Uwaga:** Obecnie zaimplementowane są tylko operacje odczytu i tworzenia dla lokalizacji. Operacje aktualizacji (PUT/PATCH) i usuwania (DELETE) nie są jeszcze dostępne.

---

## Modyfikacja istniejącego modelu Location - pole description

**Jako** deweloper  
**Chcę** rozszerzyć istniejący model `Location` o pole `description`  
**Aby** przechowywać opis lokalizacji bez tworzenia nowej tabeli

**Akceptacja:**
- Model `Location` w `sql_app/models.py` zawiera nową kolumnę `description` (typ `Text`, opcjonalna)
- Istniejące pola i relacja `listings` pozostają bez zmian
- Istniejące rekordy w tabeli `location` nie tracą danych (nowa kolumna ma wartość `NULL`)
- Zmiana jest odzwierciedlona w schematach `LocationBase`, `LocationCreate` i `Location`
- Dodana zostaje migracja Alembic dla zmiany tabeli `location`

**Szczegóły techniczne:**
- Kolumna: `description = Column(Text)` (lub `String(1000)`, jeśli zdecydujemy się na limit długości)
- Migracja: `alembic revision --autogenerate` z opisem zmiany, następnie `alembic upgrade head`

