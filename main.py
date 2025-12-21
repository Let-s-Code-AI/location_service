from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated, List
from sql_app.database import get_db
from sql_app import models, schemas

app = FastAPI()


# Location endpoints
@app.post("/locations/", response_model=schemas.Location)
async def create_location(
    location: schemas.LocationCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    db_location = models.Location(**location.model_dump())
    db.add(db_location)
    await db.commit()
    await db.refresh(db_location)
    return db_location


@app.get("/locations/", response_model=List[schemas.Location])
async def read_locations(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100
):
    result = await db.execute(
        select(models.Location).offset(skip).limit(limit)
    )
    return result.scalars().all()


@app.get("/locations/{location_id}", response_model=schemas.Location)
async def read_location(
    location_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(models.Location).where(models.Location.location_id == location_id)
    )
    location = result.scalar_one_or_none()
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

