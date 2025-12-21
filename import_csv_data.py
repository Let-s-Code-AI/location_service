"""
Skrypt do importu danych z pliku CSV do bazy danych.

Użycie:
    python import_csv_data.py [ścieżka_do_pliku.csv]
    
Domyślnie: data/ogloszenia_warszawa_detailed.csv
"""
import asyncio
import csv
import sys
from pathlib import Path
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sql_app.database import AsyncSessionLocal, engine, Base
from sql_app import models  # Import modeli, żeby Base.metadata zawierał wszystkie tabele


def parse_floor(floor_str: str) -> Optional[int]:
    """Wyciąga numer piętra z tekstu (np. '3 / winda' -> 3, 'parter' -> 0)."""
    if not floor_str or not floor_str.strip():
        return None
    
    floor_str = floor_str.strip().lower()
    
    # Obsługa "parter"
    if "parter" in floor_str:
        return 0
    
    # Wyciągnij pierwszą liczbę z tekstu
    import re
    match = re.search(r'\d+', floor_str)
    if match:
        return int(match.group())
    
    return None


def parse_price_per_sqm(price_str: str) -> Optional[float]:
    """Parsuje cenę za m² usuwając spacje (np. '24 664' -> 24664.0)."""
    if not price_str or not price_str.strip():
        return None
    
    # Usuń spacje i zamień na float
    price_clean = price_str.strip().replace(' ', '').replace(',', '.')
    try:
        return float(price_clean)
    except ValueError:
        return None


def parse_boolean(value: str) -> Optional[bool]:
    """Konwertuje tekst na boolean (tak -> True, nie -> False, puste -> None)."""
    if not value or not value.strip():
        return None
    
    value_lower = value.strip().lower()
    if value_lower in ['tak', 'yes', 'true', '1']:
        return True
    elif value_lower in ['nie', 'no', 'false', '0']:
        return False
    
    return None


def extract_city(locality: str) -> Optional[str]:
    """Wyciąga nazwę miasta z locality (np. 'Warszawa Praga-Północ' -> 'Warszawa')."""
    if not locality:
        return None
    
    # Warszawa zawsze na początku
    if locality.startswith('Warszawa'):
        return 'Warszawa'
    
    # Dla innych przypadków, weź pierwszą część
    parts = locality.split(',')
    return parts[0].strip() if parts else None


async def get_or_create_location(
    db: AsyncSession,
    locality: Optional[str],
    street: Optional[str],
    city_district: Optional[str],
    full_address: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float]
) -> models.Location:
    """Znajduje istniejącą lokalizację lub tworzy nową."""
    # Wyciągnij miasto z locality
    city = extract_city(locality) if locality else None
    
    # Jeśli wszystkie ważne pola są puste, utwórz pustą lokalizację z domyślną wartością
    if not any([locality, street, city_district, full_address, latitude, longitude, city]):
        # Utwórz domyślną pustą lokalizację
        location = models.Location(
            city=None,
            locality=None,
            city_district=None,
            street=None,
            full_address=None,
            latitude=None,
            longitude=None
        )
        db.add(location)
        await db.flush()
        return location
    
    # Sprawdź czy istnieje już taka lokalizacja (po street + full_address lub latitude/longitude)
    query = select(models.Location)
    
    conditions = []
    if street:
        conditions.append(models.Location.street == street)
    if full_address:
        conditions.append(models.Location.full_address == full_address)
    if latitude is not None and longitude is not None:
        conditions.append(
            (models.Location.latitude == latitude) & 
            (models.Location.longitude == longitude)
        )
    
    if conditions:
        # Użyj pierwszego warunku lub kombinacji
        if street and full_address:
            query = query.where(
                (models.Location.street == street) &
                (models.Location.full_address == full_address)
            )
        elif latitude is not None and longitude is not None:
            query = query.where(
                (models.Location.latitude == latitude) &
                (models.Location.longitude == longitude)
            )
        else:
            # Użyj dostępnego warunku
            query = query.where(conditions[0])
        
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing
    
    # Utwórz nową lokalizację
    location = models.Location(
        city=city,
        locality=locality if locality else None,
        city_district=city_district if city_district else None,
        street=street if street else None,
        full_address=full_address if full_address else None,
        latitude=latitude,
        longitude=longitude
    )
    db.add(location)
    await db.flush()  # Flush żeby otrzymać location_id
    return location


async def get_or_create_building(
    db: AsyncSession,
    year_built: Optional[int],
    building_type: Optional[str],
    floor: Optional[int]
) -> models.Building:
    """Znajduje istniejący budynek lub tworzy nowy."""
    # Sprawdź czy istnieje już taki budynek
    query = select(models.Building)
    conditions = []
    
    if year_built:
        conditions.append(models.Building.year_built == year_built)
    if building_type:
        conditions.append(models.Building.building_type == building_type)
    if floor is not None:
        conditions.append(models.Building.floor == floor)
    
    if conditions:
        # Połącz wszystkie warunki operatorem AND
        combined_condition = conditions[0]
        for condition in conditions[1:]:
            combined_condition = combined_condition & condition
        
        query = query.where(combined_condition)
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing
    
    # Utwórz nowy budynek
    building = models.Building(
        year_built=year_built,
        building_type=building_type if building_type else None,
        floor=floor
    )
    db.add(building)
    await db.flush()
    return building


async def get_or_create_owner(
    db: AsyncSession,
    owner_type: Optional[str]
) -> models.Owner:
    """Znajduje istniejącego właściciela lub tworzy nowego."""
    if not owner_type:
        owner_type = None
    
    query = select(models.Owner).where(models.Owner.owner_type == owner_type)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        return existing
    
    # Utwórz nowego właściciela
    owner = models.Owner(owner_type=owner_type)
    db.add(owner)
    await db.flush()
    return owner


async def get_or_create_features(
    db: AsyncSession,
    has_basement: Optional[bool],
    has_parking: Optional[bool],
    kitchen_type: Optional[str],
    window_type: Optional[str],
    ownership_type: Optional[str],
    equipment: Optional[str]
) -> models.Features:
    """Znajduje istniejące cechy lub tworzy nowe."""
    # Sprawdź czy istnieją już takie cechy (dokładne dopasowanie wszystkich pól)
    query = select(models.Features).where(
        (models.Features.has_basement == has_basement) &
        (models.Features.has_parking == has_parking) &
        (models.Features.kitchen_type == kitchen_type) &
        (models.Features.window_type == window_type) &
        (models.Features.ownership_type == ownership_type) &
        (models.Features.equipment == equipment)
    )
    
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        return existing
    
    # Utwórz nowe cechy
    features = models.Features(
        has_basement=has_basement,
        has_parking=has_parking,
        kitchen_type=kitchen_type if kitchen_type else None,
        window_type=window_type if window_type else None,
        ownership_type=ownership_type if ownership_type else None,
        equipment=equipment if equipment else None
    )
    db.add(features)
    await db.flush()
    return features


def safe_float(value: str) -> Optional[float]:
    """Bezpiecznie konwertuje wartość na float."""
    if not value or not value.strip() or value.strip().lower() in ['', 'nan', 'none']:
        return None
    try:
        return float(value.replace(',', '.'))
    except (ValueError, AttributeError):
        return None


def safe_int(value: str) -> Optional[int]:
    """Bezpiecznie konwertuje wartość na int."""
    if not value or not value.strip() or value.strip().lower() in ['', 'nan', 'none']:
        return None
    try:
        # Usuń nie-numeryczne znaki (oprócz minusa)
        cleaned = ''.join(c for c in value if c.isdigit() or c == '-')
        if cleaned and cleaned != '-':
            return int(cleaned)
    except (ValueError, AttributeError):
        pass
    return None


async def import_csv_row(db: AsyncSession, row: dict) -> Optional[models.Listing]:
    """Importuje pojedynczy wiersz z CSV do bazy danych."""
    # Pomijaj puste wiersze (gdy większość pól jest pusta)
    if not row.get('locality') and not row.get('street') and not row.get('url'):
        return None
    
    # Parsuj dane
    rooms = safe_int(row.get('rooms', ''))
    area = safe_float(row.get('area', ''))
    price_total_zl = safe_float(row.get('price_total_zl', ''))
    price_sqm_zl = safe_float(row.get('price_sqm_zl', ''))
    photo_count = safe_int(row.get('photo_count', ''))
    
    # Parsuj price_per_sqm_detailed (może zawierać spacje)
    price_per_sqm_detailed = None
    if row.get('price_per_sqm_detailed'):
        price_per_sqm_detailed = parse_price_per_sqm(row.get('price_per_sqm_detailed'))
    
    # Parsuj floor
    floor = parse_floor(row.get('floor', ''))
    
    # Parsuj year_built
    year_built = safe_int(row.get('year_built', ''))
    
    # Parsuj boolean values
    has_basement = parse_boolean(row.get('has_basement', ''))
    has_parking = parse_boolean(row.get('has_parking', ''))
    
    # Parsuj współrzędne
    latitude = safe_float(row.get('latitude', ''))
    longitude = safe_float(row.get('longitude', ''))
    
    # Utwórz lub znajdź powiązane obiekty
    locality_val = row.get('locality', '').strip() if row.get('locality') else None
    street_val = row.get('street', '').strip() if row.get('street') else None
    city_district_val = row.get('city_district', '').strip() if row.get('city_district') else None
    full_address_val = row.get('full_address', '').strip() if row.get('full_address') else None
    
    location = await get_or_create_location(
        db=db,
        locality=locality_val if locality_val else None,
        street=street_val if street_val else None,
        city_district=city_district_val if city_district_val else None,
        full_address=full_address_val if full_address_val else None,
        latitude=latitude,
        longitude=longitude
    )
    
    building = await get_or_create_building(
        db=db,
        year_built=year_built,
        building_type=row.get('building_type', '').strip() if row.get('building_type') else None,
        floor=floor
    )
    
    owner = await get_or_create_owner(
        db=db,
        owner_type=row.get('owner_type', '').strip() if row.get('owner_type') else None
    )
    
    features = await get_or_create_features(
        db=db,
        has_basement=has_basement,
        has_parking=has_parking,
        kitchen_type=row.get('kitchen_type', '').strip() if row.get('kitchen_type') else None,
        window_type=row.get('window_type', '').strip() if row.get('window_type') else None,
        ownership_type=row.get('ownership_type', '').strip() if row.get('ownership_type') else None,
        equipment=row.get('equipment', '').strip() if row.get('equipment') else None
    )
    
    # Sprawdź czy listing już istnieje (po URL)
    url = row.get('url', '').strip() if row.get('url') else None
    if url:
        query = select(models.Listing).where(models.Listing.url == url)
        result = await db.execute(query)
        existing_listing = result.scalar_one_or_none()
        if existing_listing:
            # Aktualizuj istniejący listing zamiast tworzyć nowy
            print(f"Listing już istnieje: {url}")
            return existing_listing
    
    # Utwórz nowy listing
    listing = models.Listing(
        location_id=location.location_id,
        building_id=building.building_id,
        owner_id=owner.owner_id,
        features_id=features.features_id,
        rooms=rooms,
        area=area,
        price_total_zl=price_total_zl,
        price_sqm_zl=price_sqm_zl,
        price_per_sqm_detailed=price_per_sqm_detailed,
        date_posted=None,  # TODO: parsować daty z formatu "wczorajnowe", "2 dni temu" itp.
        photo_count=photo_count,
        url=url,
        image_url=row.get('image_url', '').strip() if row.get('image_url') else None,
        description_text=row.get('description_text', '').strip() if row.get('description_text') else None
    )
    
    db.add(listing)
    await db.flush()
    return listing


async def init_database():
    """Tworzy wszystkie tabele w bazie danych, jeśli nie istnieją."""
    print("Sprawdzanie struktury bazy danych...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Baza danych jest gotowa!")


async def import_csv_file(csv_path: Path):
    """Importuje dane z pliku CSV do bazy danych."""
    if not csv_path.exists():
        print(f"Błąd: Plik {csv_path} nie istnieje!")
        return
    
    print(f"Importowanie danych z {csv_path}...")
    
    async with AsyncSessionLocal() as db:
        try:
            imported_count = 0
            skipped_count = 0
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):  # start=2 bo 1 to nagłówek
                    try:
                        listing = await import_csv_row(db, row)
                        if listing:
                            imported_count += 1
                            if imported_count % 100 == 0:
                                print(f"Zaimportowano {imported_count} rekordów...")
                                await db.commit()  # Commit co 100 rekordów
                        else:
                            skipped_count += 1
                    except Exception as e:
                        print(f"Błąd przy przetwarzaniu wiersza {row_num}: {e}")
                        print(f"  Wiersz: {row.get('url', 'brak URL')}")
                        await db.rollback()  # Rollback przed kontynuacją
                        continue
            
            # Final commit
            await db.commit()
            print(f"\nZakończono import!")
            print(f"  Zaimportowano: {imported_count} rekordów")
            print(f"  Pominięto: {skipped_count} rekordów")
            
        except Exception as e:
            await db.rollback()
            print(f"Błąd podczas importu: {e}")
            raise


async def main():
    """Główna funkcja skryptu."""
    # Utwórz tabele w bazie danych, jeśli nie istnieją
    await init_database()
    
    # Określ ścieżkę do pliku CSV
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    else:
        csv_path = Path(__file__).parent / "data" / "ogloszenia_warszawa_detailed.csv"
    
    await import_csv_file(csv_path)


if __name__ == "__main__":
    asyncio.run(main())

