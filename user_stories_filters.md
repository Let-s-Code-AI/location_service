# User Stories - EPIC 4: Filtry i sortowanie

## Opis EPIC

**EPIC 4 — Filtry i sortowanie**

Celem tego epiku jest dostarczenie użytkownikowi precyzyjnych narzędzi do przeszukiwania bazy danych listingów w sposób tradycyjny (parametryczny), stanowiący uzupełnienie dla wyszukiwania semantycznego (AI).

---

## 1. Filtry podstawowe (Szybki wybór)

**Jako** użytkownik  
**Chcę** mieć możliwość filtrowania ofert po kluczowych parametrach (cena, metraż, lokalizacja, liczba pokoi)  
**Aby** błyskawicznie odrzucić ogłoszenia poza moim budżetem lub wymaganiami przestrzennymi

**Akceptacja:**
- Suwaki (range sliders) dla ceny całkowitej oraz ceny za $m^2$
- Wybór wielokrotny (multi-select) dla liczby pokoi (np. 2 i 3 pokojowe jednocześnie)
- Autouzupełnianie w polu lokalizacji (miasto, dzielnica)
- Licznik wyników aktualizujący się dynamicznie po każdej zmianie filtra ("Pokaż 124 oferty")

**Szczegóły techniczne:**
- Filtry ceny: `price_total_zl` (min-max), `price_sqm_zl` (min-max)
- Filtr liczby pokoi: `rooms` (multi-select)
- Filtr lokalizacji: `city`, `city_district` (autouzupełnianie)
- Filtr metrażu: `area` (min-max)

---

## 2. Filtry zaawansowane (Techniczne)

**Jako** użytkownik szukający konkretnego standardu  
**Chcę** filtrować oferty według cech budynku i udogodnień (rok budowy, winda, garaż, ogrzewanie miejskie)  
**Aby** znaleźć mieszkanie dopasowane do mojego stylu życia

**Akceptacja:**
- Sekcja „Udogodnienia" z checkboxami (balkon, ogród, piwnica, parking)
- Filtr „Typ zabudowy" (blok, kamienica, apartamentowiec, dom)
- Filtr „Piętro" z opcją zaznaczenia „brak parteru" lub „ostatnie piętro"
- Możliwość filtrowania po roku budowy (od – do)

**Szczegóły techniczne:**
- Filtr udogodnień: `has_basement`, `has_parking` (checkboxy)
- Filtr typu zabudowy: `building_type` (select/multi-select)
- Filtr piętra: `floor` (range + opcje specjalne: floor > 0, floor = max)
- Filtr roku budowy: `year_built` (min-max range)
- Dodatkowe filtry z tabeli Features: `equipment` (wyszukiwanie tekstowe w wyposażeniu)

---

## 3. Sortowanie wyników

**Jako** użytkownik  
**Chcę** mieć możliwość zmiany kolejności wyświetlanych ofert  
**Aby** najpierw widzieć te najtańsze, najnowsze lub o najlepszym stosunku ceny do metrażu

**Akceptacja:**
- Dostępne opcje sortowania:
  - Cena (rosnąco/malejąco)
  - Cena za $m^2$ (rosnąco/malejąco)
  - Data dodania (najnowsze)
  - Metraż (rosnąco/malejąco)
- Domyślne sortowanie ustawione na „Najtrafniejsze" (bazujące na algorytmie dopasowania)

**Szczegóły techniczne:**
- Sortowanie po cenie: `price_total_zl` (ASC/DESC)
- Sortowanie po cenie za m²: `price_sqm_zl` (ASC/DESC)
- Sortowanie po dacie: `date_posted` (DESC dla najnowszych)
- Sortowanie po metrażu: `area` (ASC/DESC)
- Sortowanie domyślne: algorytm dopasowania (do zdefiniowania w przyszłości)

**Parametry:**
- `sort_by`: `price_total`, `price_sqm`, `date_posted`, `area`, `relevance`
- `sort_order`: `asc`, `desc` (dla sortowania po cenie/metrażu)

---

## 4. Zapisywanie filtrów i alerty

**Jako** użytkownik  
**Chcę** zapisać moje aktualne ustawienia filtrów jako „Wyszukiwanie"  
**Aby** system powiadomił mnie, gdy pojawi się nowa oferta spełniająca te kryteria

**Akceptacja:**
- Przycisk „Zapisz wyszukiwanie" dostępny nad wynikami
- Możliwość nazwania zapisanego filtru (np. „Moje wymarzone na Bałutach")
- Integracja z systemem powiadomień (Epic 10)

**Szczegóły techniczne:**
- Endpoint `POST /saved-searches/` do zapisywania wyszukiwań
- Endpoint `GET /saved-searches/` do pobierania zapisanych wyszukiwań
- Endpoint `DELETE /saved-searches/{search_id}` do usuwania zapisanych wyszukiwań
- Model danych SavedSearch zawierający:
  - `search_id` (PK)
  - `user_id` (FK - do zaimplementowania w przyszłości)
  - `name` - nazwa wyszukiwania
  - `filters` - JSON z zapisanymi filtrami
  - `sort_by` - zapisane sortowanie
  - `sort_order` - zapisany kierunek sortowania
  - `created_at` - data utworzenia
  - `last_notified_at` - ostatnia data powiadomienia (dla Epic 10)

**Integracja:**
- Powiązanie z Epic 10 (System powiadomień) - automatyczne sprawdzanie nowych ofert spełniających kryteria zapisanego wyszukiwania

---

## Podsumowanie funkcjonalności

EPIC 4 umożliwia:
- ✅ Filtrowanie podstawowe (cena, metraż, lokalizacja, liczba pokoi)
- ✅ Filtrowanie zaawansowane (udogodnienia, typ zabudowy, piętro, rok budowy)
- ✅ Sortowanie wyników według różnych kryteriów
- ✅ Zapisywanie wyszukiwań dla późniejszego użycia
- ✅ Integracja z systemem powiadomień (Epic 10)

**Filtry podstawowe:**
- Cena całkowita (range slider)
- Cena za m² (range slider)
- Liczba pokoi (multi-select)
- Lokalizacja (autouzupełnianie)
- Metraż (range slider)

**Filtry zaawansowane:**
- Udogodnienia (checkboxy: piwnica, parking)
- Typ zabudowy (select)
- Piętro (range + opcje specjalne)
- Rok budowy (range)

**Opcje sortowania:**
- Cena (rosnąco/malejąco)
- Cena za m² (rosnąco/malejąco)
- Data dodania (najnowsze)
- Metraż (rosnąco/malejąco)
- Najtrafniejsze (domyślne)

**Zapisywanie wyszukiwań:**
- Zapisywanie aktualnych filtrów i sortowania
- Nazywanie zapisanych wyszukiwań
- Powiadomienia o nowych ofertach (Epic 10)

