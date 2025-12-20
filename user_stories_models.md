# User Stories - Modele danych (SQLAlchemy)

## 1. Model Location - Przechowywanie informacji o lokalizacji

**Jako** użytkownik systemu nieruchomości  
**Chcę** przechowywać szczegółowe informacje geograficzne i adresowe lokalizacji  
**Aby** móc wyszukiwać i filtrować oferty według lokalizacji geograficznej

**Akceptacja:**
- Tabela `location` jest zdefiniowana w bazie danych
- Zawiera unikalny identyfikator `location_id` jako klucz główny z indeksem
- Wszystkie pola są opcjonalne (nullable), pozwalając na elastyczne wprowadzanie danych
- Obsługuje różne poziomy szczegółowości adresu (miasto, dzielnica, ulica, pełny adres)
- Zawiera współrzędne geograficzne (latitude, longitude) dla wyszukiwania na mapie
- Ma relację one-to-many z modelami Listing

**Pola modelu:**
- `location_id` (Integer, PK, indexed) - unikalny identyfikator lokalizacji
- `city` (String 255) - miasto
- `locality` (String 255) - miejscowość
- `city_district` (String 255) - dzielnica miasta
- `street` (String 255) - ulica
- `full_address` (String 500) - pełny adres (dłuższe pole dla kompleksowych adresów)
- `latitude` (Float) - szerokość geograficzna
- `longitude` (Float) - długość geograficzna

**Relacje:**
- `listings` - relacja one-to-many z Listing (back_populates="location")

---

## 2. Model Building - Przechowywanie informacji o budynku

**Jako** użytkownik systemu nieruchomości  
**Chcę** przechowywać informacje techniczne o budynku  
**Aby** móc filtrować oferty według typu budynku, roku budowy i piętra

**Akceptacja:**
- Tabela `building` jest zdefiniowana w bazie danych
- Zawiera unikalny identyfikator `building_id` jako klucz główny z indeksem
- Wszystkie pola są opcjonalne, umożliwiając częściowe wprowadzanie danych
- Przechowuje informacje o roku budowy, typie budynku i piętrze
- Ma relację one-to-many z modelami Listing

**Pola modelu:**
- `building_id` (Integer, PK, indexed) - unikalny identyfikator budynku
- `year_built` (Integer) - rok budowy
- `building_type` (String 100) - typ budynku (np. blok, dom, kamienica)
- `floor` (Integer) - numer piętra

**Relacje:**
- `listings` - relacja one-to-many z Listing (back_populates="building")

---

## 3. Model Owner - Przechowywanie danych kontaktowych właściciela

**Jako** użytkownik systemu nieruchomości  
**Chcę** przechowywać informacje kontaktowe właściciela nieruchomości  
**Aby** móc się z nim skontaktować w sprawie oferty

**Akceptacja:**
- Tabela `owner` jest zdefiniowana w bazie danych
- Zawiera unikalny identyfikator `owner_id` jako klucz główny z indeksem
- Wszystkie pola kontaktowe są opcjonalne, chroniąc prywatność
- Obsługuje różne typy właścicieli (osoba prywatna, firma, biuro nieruchomości)
- Przechowuje dane kontaktowe: imię/nazwa, telefon, email
- Ma relację one-to-many z modelami Listing

**Pola modelu:**
- `owner_id` (Integer, PK, indexed) - unikalny identyfikator właściciela
- `owner_type` (String 50) - typ właściciela (np. "private", "agency", "company")
- `contact_name` (String 255) - imię i nazwisko lub nazwa firmy
- `contact_phone` (String 50) - numer telefonu kontaktowego
- `contact_email` (String 255) - adres email kontaktowy

**Relacje:**
- `listings` - relacja one-to-many z Listing (back_populates="owner")

---

## 4. Model Features - Przechowywanie cech i wyposażenia nieruchomości

**Jako** użytkownik systemu nieruchomości  
**Chcę** przechowywać szczegółowe cechy i wyposażenie nieruchomości  
**Aby** móc filtrować oferty według różnych parametrów (piwnica, parking, typ kuchni, okna itp.)

**Akceptacja:**
- Tabela `features` jest zdefiniowana w bazie danych
- Zawiera unikalny identyfikator `features_id` jako klucz główny z indeksem
- Wszystkie pola są opcjonalne, umożliwiając elastyczne definiowanie cech
- Obsługuje cechy binarne (has_basement, has_parking) jako Boolean
- Przechowuje informacje o typach elementów wyposażenia (kuchnia, okna, własność)
- Pole `equipment` jako Text pozwala na długie opisy wyposażenia
- Ma relację one-to-many z modelami Listing

**Pola modelu:**
- `features_id` (Integer, PK, indexed) - unikalny identyfikator cech
- `has_basement` (Boolean) - czy nieruchomość ma piwnicę
- `has_parking` (Boolean) - czy nieruchomość ma parking/miejsce parkingowe
- `kitchen_type` (String 100) - typ kuchni (np. "w pełni wyposażona", "aneks")
- `window_type` (String 100) - typ okien (np. "plastikowe", "drewniane", "aluminiowe")
- `ownership_type` (String 100) - typ własności (np. "własność", "spółdzielcze", "dzierżawa")
- `equipment` (Text) - szczegółowe wyposażenie (długi tekst)

**Relacje:**
- `listings` - relacja one-to-many z Listing (back_populates="features")

---

## 5. Model Listing - Główny model oferty nieruchomości

**Jako** użytkownik systemu nieruchomości  
**Chcę** przechowywać kompleksowe informacje o ofercie nieruchomości  
**Aby** móc przeglądać, wyszukiwać i filtrować oferty z pełnymi szczegółami

**Akceptacja:**
- Tabela `listing` jest zdefiniowana w bazie danych jako główna tabela ofert
- Zawiera unikalny identyfikator `listing_id` jako klucz główny z indeksem
- Wszystkie foreign keys są wymagane (nullable=False), zapewniając integralność danych
- Łączy informacje z Location, Building, Owner i Features przez foreign keys
- Przechowuje szczegóły oferty: liczba pokoi, powierzchnia, ceny, data dodania
- Obsługuje informacje o mediach: liczba zdjęć, URL oferty, URL głównego zdjęcia
- Zawiera opis tekstowy oferty
- Ma relacje many-to-one z Location, Building, Owner i Features

**Pola modelu:**
- `listing_id` (Integer, PK, indexed) - unikalny identyfikator oferty
- `location_id` (Integer, FK → location.location_id, required) - ID lokalizacji
- `building_id` (Integer, FK → building.building_id, required) - ID budynku
- `owner_id` (Integer, FK → owner.owner_id, required) - ID właściciela
- `features_id` (Integer, FK → features.features_id, required) - ID cech
- `rooms` (Integer) - liczba pokoi
- `area` (Float) - powierzchnia w m²
- `price_total_zl` (Float) - cena całkowita w PLN
- `price_sqm_zl` (Float) - cena za metr kwadratowy w PLN
- `price_per_sqm_detailed` (Float) - szczegółowa cena za m² (może różnić się od obliczonej)
- `date_posted` (Date) - data dodania/publikacji oferty
- `photo_count` (Integer) - liczba zdjęć w ofercie
- `url` (Text) - link do pełnej oferty (zewnętrzny lub wewnętrzny)
- `image_url` (Text) - URL do głównego/okładkowego zdjęcia oferty
- `description_text` (Text) - pełny opis tekstowy oferty

**Relacje:**
- `location` - relacja many-to-one z Location (back_populates="listings")
- `building` - relacja many-to-one z Building (back_populates="listings")
- `owner` - relacja many-to-one z Owner (back_populates="listings")
- `features` - relacja many-to-one z Features (back_populates="listings")

---

## 6. Relacje między modelami - Architektura danych

**Jako** deweloper systemu  
**Chcę** mieć poprawnie zdefiniowane relacje między modelami  
**Aby** zapewnić integralność danych i umożliwić efektywne zapytania z joinami

**Akceptacja:**
- Wszystkie relacje są zdefiniowane dwukierunkowo (back_populates)
- Location ma relację one-to-many z Listing
- Building ma relację one-to-many z Listing
- Owner ma relację one-to-many z Listing
- Features ma relację one-to-many z Listing
- Listing ma relacje many-to-one z wszystkimi powyższymi modelami
- Foreign keys są wymagane w Listing, zapewniając że każda oferta ma powiązane dane
- Relacje umożliwiają łatwe pobieranie powiązanych danych przez SQLAlchemy ORM

**Struktura relacji:**
```
Location (1) ──< (N) Listing
Building (1) ──< (N) Listing
Owner (1) ──< (N) Listing
Features (1) ──< (N) Listing
```

**Korzyści:**
- Możliwość pobierania wszystkich ofert dla danej lokalizacji
- Możliwość pobierania wszystkich ofert dla danego właściciela
- Możliwość pobierania oferty z pełnymi szczegółami w jednym zapytaniu
- Automatyczne zarządzanie relacjami przez SQLAlchemy

---

## 7. Indeksowanie kluczy głównych dla wydajności

**Jako** deweloper systemu  
**Chcę** mieć zindeksowane klucze główne we wszystkich modelach  
**Aby** zapewnić szybkie wyszukiwanie i joinowanie tabel

**Akceptacja:**
- Wszystkie klucze główne (location_id, building_id, owner_id, features_id, listing_id) są zindeksowane
- Indeksy są automatycznie tworzone przez SQLAlchemy przy `index=True`
- Foreign keys w Listing są automatycznie indeksowane przez SQLAlchemy
- Zapewnia to optymalną wydajność zapytań JOIN i WHERE

**Zindeksowane pola:**
- `location.location_id` - indeksowany
- `building.building_id` - indeksowany
- `owner.owner_id` - indeksowany
- `features.features_id` - indeksowany
- `listing.listing_id` - indeksowany
- `listing.location_id` - automatycznie indeksowany jako FK
- `listing.building_id` - automatycznie indeksowany jako FK
- `listing.owner_id` - automatycznie indeksowany jako FK
- `listing.features_id` - automatycznie indeksowany jako FK

---

## 8. Elastyczność danych - Pola opcjonalne

**Jako** użytkownik systemu  
**Chcę** móc wprowadzać dane częściowo  
**Aby** nie być zmuszonym do podawania wszystkich informacji od razu

**Akceptacja:**
- Wszystkie pola oprócz kluczy głównych i foreign keys są opcjonalne (nullable)
- Pozwala to na stopniowe uzupełnianie danych
- System nie wymusza podania wszystkich informacji przy tworzeniu rekordu
- Elastyczne wprowadzanie danych ułatwia import z różnych źródeł

**Pola wymagane:**
- Tylko klucze główne (ID) są zawsze wymagane (automatycznie generowane)
- W modelu Listing: wszystkie foreign keys są wymagane (location_id, building_id, owner_id, features_id)

**Pola opcjonalne:**
- Wszystkie pozostałe pola we wszystkich modelach są opcjonalne
- Umożliwia to tworzenie rekordów z minimalnymi danymi i późniejsze uzupełnianie

---

## Podsumowanie modeli

System zawiera 5 głównych modeli danych:

1. **Location** - informacje geograficzne i adresowe (8 pól)
2. **Building** - informacje techniczne o budynku (4 pola)
3. **Owner** - dane kontaktowe właściciela (5 pól)
4. **Features** - cechy i wyposażenie nieruchomości (7 pól)
5. **Listing** - główna tabela ofert (17 pól + 4 relacje)

**Charakterystyka:**
- ✅ Wszystkie modele dziedziczą po `Base` (SQLAlchemy declarative base)
- ✅ Wszystkie klucze główne są zindeksowane
- ✅ Relacje są zdefiniowane dwukierunkowo
- ✅ Foreign keys zapewniają integralność danych
- ✅ Elastyczne wprowadzanie danych (większość pól opcjonalna)
- ✅ Wsparcie dla różnych typów danych (String, Integer, Float, Boolean, Date, Text)

**Relacje:**
- Listing jest centralnym modelem łączącym wszystkie pozostałe
- Każda oferta musi mieć powiązane: Location, Building, Owner i Features
- Jeden Location/Building/Owner/Features może mieć wiele ofert (Listing)


