# User Stories - Komponenty bazy danych

## 1. Konfiguracja połączenia z bazą danych SQLite

**Jako** deweloper systemu  
**Chcę** mieć skonfigurowane asynchroniczne połączenie z bazą danych SQLite  
**Aby** móc wykonywać operacje na bazie danych w sposób asynchroniczny

**Akceptacja:**
- Połączenie używa SQLite z adapterem aiosqlite dla asynchroniczności
- Connection string: `sqlite+aiosqlite:///./sql_app.db`
- Ustawiony `check_same_thread=False` dla kompatybilności z SQLite
- Utworzona fabryka sesji asynchronicznych (`AsyncSessionLocal`)
- Sesje są automatycznie zamykane po użyciu (`expire_on_commit=False`)

**Szczegóły techniczne:**
- Engine jest tworzony z `create_async_engine`
- Sesje są zarządzane przez `async_sessionmaker`
- Funkcja `get_db()` jest dependency injection dla FastAPI

---

## 2. Dependency Injection dla sesji bazy danych

**Jako** deweloper API  
**Chcę** mieć automatycznie zarządzane sesje bazy danych  
**Aby** nie martwić się o ręczne zamykanie połączeń i zapewnić bezpieczeństwo transakcji

**Akceptacja:**
- Funkcja `get_db()` jest używana jako dependency w FastAPI
- Sesja jest automatycznie otwierana przy rozpoczęciu requestu
- Sesja jest automatycznie zamykana po zakończeniu requestu (w bloku `finally`)
- Każdy request ma własną sesję bazy danych

**Szczegóły techniczne:**
- Używa `yield` dla generatora dependency
- Zapewnia prawidłowe zarządzanie zasobami przez context manager

---

## 3. Model danych - Lokalizacja (Location)

**Jako** użytkownik systemu  
**Chcę** przechowywać informacje o lokalizacji nieruchomości  
**Aby** móc wyszukiwać i filtrować oferty według lokalizacji

**Akceptacja:**
- Tabela `location` zawiera pola: location_id (PK), city, locality, city_district, street, full_address, latitude, longitude
- Wszystkie pola oprócz location_id są opcjonalne (nullable)
- Location ma relację one-to-many z Listing
- location_id jest indeksowane dla szybkiego wyszukiwania

**Pola:**
- `location_id` - unikalny identyfikator (Integer, PK)
- `city` - miasto (String 255)
- `locality` - miejscowość (String 255)
- `city_district` - dzielnica miasta (String 255)
- `street` - ulica (String 255)
- `full_address` - pełny adres (String 500)
- `latitude` - szerokość geograficzna (Float)
- `longitude` - długość geograficzna (Float)

---

## 4. Model danych - Budynek (Building)

**Jako** użytkownik systemu  
**Chcę** przechowywać informacje o budynku  
**Aby** móc filtrować oferty według typu budynku, roku budowy i piętra

**Akceptacja:**
- Tabela `building` zawiera pola: building_id (PK), year_built, building_type, floor
- Wszystkie pola oprócz building_id są opcjonalne
- Building ma relację one-to-many z Listing
- building_id jest indeksowane

**Pola:**
- `building_id` - unikalny identyfikator (Integer, PK)
- `year_built` - rok budowy (Integer)
- `building_type` - typ budynku (String 100)
- `floor` - piętro (Integer)

---

## 5. Model danych - Właściciel (Owner)

**Jako** użytkownik systemu  
**Chcę** przechowywać informacje kontaktowe właściciela nieruchomości  
**Aby** móc się z nim skontaktować w sprawie oferty

**Akceptacja:**
- Tabela `owner` zawiera pola: owner_id (PK), owner_type, contact_name, contact_phone, contact_email
- Wszystkie pola oprócz owner_id są opcjonalne
- Owner ma relację one-to-many z Listing
- owner_id jest indeksowane

**Pola:**
- `owner_id` - unikalny identyfikator (Integer, PK)
- `owner_type` - typ właściciela (String 50)
- `contact_name` - imię i nazwisko kontaktowe (String 255)
- `contact_phone` - telefon kontaktowy (String 50)
- `contact_email` - email kontaktowy (String 255)

---

## 6. Model danych - Cechy nieruchomości (Features)

**Jako** użytkownik systemu  
**Chcę** przechowywać szczegółowe cechy nieruchomości  
**Aby** móc filtrować oferty według różnych parametrów (piwnica, parking, typ kuchni itp.)

**Akceptacja:**
- Tabela `features` zawiera pola: features_id (PK), has_basement, has_parking, kitchen_type, window_type, ownership_type, equipment
- Wszystkie pola oprócz features_id są opcjonalne
- Features ma relację one-to-many z Listing
- features_id jest indeksowane

**Pola:**
- `features_id` - unikalny identyfikator (Integer, PK)
- `has_basement` - czy ma piwnicę (Boolean)
- `has_parking` - czy ma parking (Boolean)
- `kitchen_type` - typ kuchni (String 100)
- `window_type` - typ okien (String 100)
- `ownership_type` - typ własności (String 100)
- `equipment` - wyposażenie (Text)

---

## 7. Model danych - Oferta nieruchomości (Listing)

**Jako** użytkownik systemu  
**Chcę** przechowywać kompleksowe informacje o ofercie nieruchomości  
**Aby** móc przeglądać, wyszukiwać i filtrować oferty

**Akceptacja:**
- Tabela `listing` zawiera wszystkie szczegóły oferty
- Listing ma relacje z Location, Building, Owner i Features (Foreign Keys)
- Wszystkie foreign keys są wymagane (nullable=False)
- listing_id jest indeksowane
- Listing ma relacje many-to-one z Location, Building, Owner i Features

**Pola:**
- `listing_id` - unikalny identyfikator (Integer, PK)
- `location_id` - ID lokalizacji (FK, wymagane)
- `building_id` - ID budynku (FK, wymagane)
- `owner_id` - ID właściciela (FK, wymagane)
- `features_id` - ID cech (FK, wymagane)
- `rooms` - liczba pokoi (Integer)
- `area` - powierzchnia (Float)
- `price_total_zl` - cena całkowita w PLN (Float)
- `price_sqm_zl` - cena za m² w PLN (Float)
- `price_per_sqm_detailed` - szczegółowa cena za m² (Float)
- `date_posted` - data dodania oferty (Date)
- `photo_count` - liczba zdjęć (Integer)
- `url` - link do oferty (Text)
- `image_url` - link do zdjęcia głównego (Text)
- `description_text` - opis tekstowy (Text)

---

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

## 11. Konfiguracja migracji Alembic

**Jako** deweloper  
**Chcę** mieć skonfigurowany system migracji bazy danych  
**Aby** móc zarządzać zmianami w schemacie bazy danych w kontrolowany sposób

**Akceptacja:**
- Alembic jest skonfigurowany do pracy z asynchronicznym SQLAlchemy
- Wspiera tryb offline (bez połączenia z bazą) i online (z połączeniem)
- Automatycznie importuje wszystkie modele z `sql_app.models`
- Używa `render_as_batch=True` dla SQLite (wymagane dla niektórych operacji)
- Target metadata jest ustawiony na `Base.metadata`

**Szczegóły techniczne:**
- `env.py` importuje Base i wszystkie modele
- Tryb online używa `NullPool` dla SQLite
- Tryb offline generuje SQL do wykonania ręcznie

---

## 12. Tworzenie migracji Alembic

**Jako** deweloper  
**Chcę** móc tworzyć migracje na podstawie zmian w modelach  
**Aby** automatycznie generować skrypty migracyjne

**Akceptacja:**
- Komenda `alembic revision --autogenerate -m "opis"` tworzy migrację
- Alembic wykrywa zmiany w modelach SQLAlchemy
- Generuje skrypty migracyjne w folderze `alembic/versions/`
- Migracje są gotowe do wykonania przez `alembic upgrade head`

**Użycie:**
- Po zmianie modeli uruchom: `alembic revision --autogenerate -m "dodano pole X"`
- Sprawdź wygenerowany plik migracji
- Zastosuj migrację: `alembic upgrade head`

---

## 13. Wykonywanie migracji Alembic

**Jako** deweloper  
**Chcę** móc stosować migracje do bazy danych  
**Aby** aktualizować schemat bazy danych zgodnie z wersją kodu

**Akceptacja:**
- Komenda `alembic upgrade head` stosuje wszystkie oczekujące migracje
- Komenda `alembic downgrade -1` cofa ostatnią migrację
- Komenda `alembic current` pokazuje aktualną wersję bazy danych
- Komenda `alembic history` pokazuje historię migracji

**Użycie:**
- `alembic upgrade head` - zastosuj wszystkie migracje
- `alembic downgrade base` - cofnij wszystkie migracje
- `alembic upgrade +1` - zastosuj następną migrację
- `alembic downgrade -1` - cofnij ostatnią migrację

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

