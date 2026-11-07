# User Stories - Komponenty bazy danych

## 8. Schematy Pydantic - Walidacja danych wejściowych

**Jako** deweloper API  
**Chcę** mieć automatyczną walidację danych wejściowych  
**Aby** zapewnić poprawność danych przed zapisem do bazy danych

**Akceptacja:**
- Dla każdego modelu istnieją schematy: Base, Create i Response
- Schematy Base zawierają wspólne pola
- Schematy Create dziedziczą po Base (dla danych wejściowych)
- Schematy Response zawierają ID i dziedziczą po Base (dla danych wyjściowych)
- Wszystkie pola są opcjonalne w schematach Base (zgodnie z modelami)
- Używa Pydantic v2 z `ConfigDict(from_attributes=True)` dla konwersji z SQLAlchemy

**Schematy:**
- Location: LocationBase, LocationCreate, Location
- Building: BuildingBase, BuildingCreate, Building
- Owner: OwnerBase, OwnerCreate, Owner
- Features: FeaturesBase, FeaturesCreate, Features
- Listing: ListingBase, ListingCreate, Listing, ListingDetail

---

## 9. Schemat szczegółowy oferty z relacjami (ListingDetail)

**Jako** użytkownik API  
**Chcę** otrzymywać pełne informacje o ofercie wraz z powiązanymi danymi  
**Aby** nie musieć wykonywać wielu zapytań do API

**Akceptacja:**
- ListingDetail dziedziczy po Listing
- Zawiera zagnieżdżone obiekty: location, building, owner, features
- Wszystkie zagnieżdżone obiekty są opcjonalne
- Umożliwia zwrócenie kompleksowych danych w jednym zapytaniu

**Użycie:**
- Endpoint zwracający szczegóły oferty może użyć ListingDetail jako response_model
- Automatycznie serializuje relacje SQLAlchemy do JSON

---

## 10. Inicjalizacja bazy danych

**Jako** deweloper  
**Chcę** móc łatwo zainicjalizować bazę danych  
**Aby** szybko utworzyć wszystkie tabele bez użycia migracji Alembic

**Akceptacja:**
- Skrypt `init_db.py` tworzy wszystkie tabele na podstawie modeli SQLAlchemy
- Używa asynchronicznego engine
- Automatycznie tworzy wszystkie tabele zdefiniowane w Base.metadata
- Wyświetla komunikat potwierdzający inicjalizację
- Można uruchomić przez `python sql_app/init_db.py`

**Szczegóły techniczne:**
- Używa `Base.metadata.create_all()` w trybie synchronicznym przez `run_sync`
- Engine jest prawidłowo zamykany po inicjalizacji

---

## Podsumowanie funkcjonalności

System bazy danych umożliwia:
- ✅ Asynchroniczne operacje na bazie danych SQLite
- ✅ Automatyczne zarządzanie sesjami przez dependency injection
- ✅ Modelowanie danych dla systemu nieruchomości (5 głównych encji)
- ✅ Relacje między encjami (one-to-many, many-to-one)
- ✅ Walidację danych przez schematy Pydantic v2
- ✅ Inicjalizację bazy danych przez skrypt
- ✅ Zarządzanie migracjami przez Alembic
- ✅ Automatyczne generowanie migracji na podstawie zmian w modelach

**Struktura danych:**
- Location (lokalizacja) - 1:N → Listing
- Building (budynek) - 1:N → Listing
- Owner (właściciel) - 1:N → Listing
- Features (cechy) - 1:N → Listing
- Listing (oferta) - N:1 → Location, Building, Owner, Features

