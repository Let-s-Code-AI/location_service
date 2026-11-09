"""Wstawia przykładowe ogłoszenia do lokalnej bazy (do ręcznego testowania wyszukiwarki).

Skrypt jest idempotentny: gdy tabela `listing` ma już wiersze, nic nie robi.
Bazę trzeba wcześniej zmigrować (`alembic upgrade head` albo ./start.sh).

Użycie (z katalogu services/backend):
    venv/bin/python scripts/seed_listings.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from config import settings  # noqa: E402
from sql_app import models  # noqa: E402

# (miasto, dzielnica, ulica, pokoje, metraż m², cena zł)
LISTINGS = [
    ("Warszawa", "Mokotów", "Puławska", 3, 62.0, 1_050_000),
    ("Warszawa", "Mokotów", "Racławicka", 2, 48.5, 820_000),
    ("Warszawa", "Wola", "Prosta", 1, 32.0, 610_000),
    ("Warszawa", "Praga-Południe", "Grochowska", 2, 51.0, 690_000),
    ("Warszawa", "Ursynów", "Puszczyka", 4, 85.0, 1_250_000),
    ("Kraków", "Stare Miasto", "Floriańska", 2, 55.0, 990_000),
    ("Kraków", "Podgórze", "Limanowskiego", 3, 67.0, 870_000),
    ("Kraków", "Nowa Huta", "Bulwarowa", 2, 44.0, 480_000),
    ("Gdańsk", "Śródmieście", "Długa", 2, 50.0, 940_000),
    ("Gdańsk", "Przymorze", "Obrońców Wybrzeża", 3, 58.0, 720_000),
    ("Gdynia", "Śródmieście", "Świętojańska", 3, 72.0, 980_000),
    ("Wrocław", "Krzyki", "Powstańców Śląskich", 2, 47.0, 640_000),
    ("Wrocław", "Śródmieście", "Jedności Narodowej", 1, 29.0, 420_000),
    ("Wrocław", "Fabryczna", "Legnicka", 4, 90.0, 950_000),
    ("Poznań", "Jeżyce", "Dąbrowskiego", 2, 52.0, 560_000),
    ("Poznań", "Wilda", "Górna Wilda", 3, 64.0, 610_000),
    ("Łódź", "Śródmieście", "Piotrkowska", 2, 58.0, 450_000),
    ("Łódź", "Bałuty", "Zgierska", 1, 35.0, 280_000),
    ("Lublin", "Czechów", "Północna", 3, 61.0, 520_000),
    ("Katowice", "Ligota", "Panewnicka", 2, 46.0, 390_000),
]


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        if await db.scalar(select(func.count()).select_from(models.Listing)):
            print("Tabela listing nie jest pusta — pomijam seed.")
            await engine.dispose()
            return

        for city, district, street, rooms, area, price in LISTINGS:
            location = models.Location(city=city, city_district=district, street=street)
            building, owner, features = models.Building(), models.Owner(), models.Features()
            db.add_all([location, building, owner, features])
            await db.flush()
            db.add(
                models.Listing(
                    location_id=location.location_id,
                    building_id=building.building_id,
                    owner_id=owner.owner_id,
                    features_id=features.features_id,
                    rooms=rooms,
                    area=area,
                    price_total_zl=price,
                    price_sqm_zl=round(price / area, 2),
                )
            )
        await db.commit()
    await engine.dispose()
    print(f"Dodano {len(LISTINGS)} ogłoszeń.")


if __name__ == "__main__":
    asyncio.run(main())
