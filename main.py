from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sql_app.database import get_db
from sql_app import models, schemas

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


# Location endpoints
@app.post("/locations/", response_model=schemas.Location)
async def create_location(
    location: schemas.LocationCreate,
    db: AsyncSession = Depends(get_db)
):
    db_location = models.Location(**location.model_dump())
    db.add(db_location)
    await db.commit()
    await db.refresh(db_location)
    return db_location


@app.get("/locations/", response_model=List[schemas.Location])
async def read_locations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        models.Location.__table__.select().offset(skip).limit(limit)
    )
    return result.scalars().all()


@app.get("/locations/{location_id}", response_model=schemas.Location)
async def read_location(
    location_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        models.Location.__table__.select().where(models.Location.location_id == location_id)
    )
    location = result.scalar_one_or_none()
    if location is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Location not found")
    return location

