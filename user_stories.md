# User Stories

## 1. Weryfikacja działania API

**Jako** deweloper/system  
**Chcę** sprawdzić czy API działa poprawnie  
**Aby** upewnić się, że serwis jest dostępny

**Akceptacja:**
- Endpoint `GET /` zwraca status 200 i komunikat "Hello World"

---

## 2. Sprawdzenie komunikacji z API

**Jako** użytkownik API  
**Chcę** otrzymać spersonalizowane powitanie  
**Aby** zweryfikować, że API poprawnie przetwarza parametry ścieżki

**Akceptacja:**
- Endpoint `GET /hello/{name}` zwraca komunikat "Hello {name}" dla podanego parametru

---

## 3. Dodawanie nowej lokalizacji

**Jako** użytkownik systemu  
**Chcę** dodać nową lokalizację do systemu  
**Aby** przechowywać informacje o lokalizacji (miasto, ulica, współrzędne geograficzne itp.)

**Akceptacja:**
- Endpoint `POST /locations/` przyjmuje dane lokalizacji (city, locality, city_district, street, full_address, latitude, longitude)
- Po utworzeniu zwraca obiekt lokalizacji z przypisanym `location_id`
- Lokalizacja jest zapisywana w bazie danych

**Dane wejściowe:**
- city (opcjonalne)
- locality (opcjonalne)
- city_district (opcjonalne)
- street (opcjonalne)
- full_address (opcjonalne)
- latitude (opcjonalne)
- longitude (opcjonalne)

---

## 4. Przeglądanie listy lokalizacji

**Jako** użytkownik systemu  
**Chcę** przeglądać listę wszystkich lokalizacji  
**Aby** znaleźć interesującą mnie lokalizację lub sprawdzić jakie lokalizacje są dostępne w systemie

**Akceptacja:**
- Endpoint `GET /locations/` zwraca listę lokalizacji
- Domyślnie zwraca maksymalnie 100 lokalizacji (parametr `limit`)
- Można pominąć określoną liczbę wyników (parametr `skip`) dla paginacji
- Każda lokalizacja zawiera wszystkie swoje pola, w tym `location_id`

**Parametry:**
- `skip` (opcjonalne, domyślnie 0) - liczba rekordów do pominięcia
- `limit` (opcjonalne, domyślnie 100) - maksymalna liczba rekordów do zwrócenia

---

## 5. Wyświetlanie szczegółów lokalizacji

**Jako** użytkownik systemu  
**Chcę** zobaczyć szczegóły konkretnej lokalizacji  
**Aby** uzyskać pełne informacje o wybranej lokalizacji

**Akceptacja:**
- Endpoint `GET /locations/{location_id}` zwraca szczegóły lokalizacji o podanym ID
- Jeśli lokalizacja nie istnieje, zwracany jest błąd 404 z komunikatem "Location not found"
- Zwracane są wszystkie pola lokalizacji (location_id, city, locality, city_district, street, full_address, latitude, longitude)

**Parametry:**
- `location_id` (wymagane) - identyfikator lokalizacji w ścieżce URL

---

## Podsumowanie funkcjonalności

Aplikacja FastAPI umożliwia:
- ✅ Podstawową weryfikację działania API
- ✅ Testowanie komunikacji z API przez spersonalizowane powitanie
- ✅ Zarządzanie lokalizacjami (CRUD):
  - Tworzenie nowych lokalizacji
  - Przeglądanie listy lokalizacji z paginacją
  - Wyświetlanie szczegółów pojedynczej lokalizacji

**Uwaga:** Obecnie zaimplementowane są tylko operacje odczytu i tworzenia dla lokalizacji. Operacje aktualizacji (PUT/PATCH) i usuwania (DELETE) nie są jeszcze dostępne.

