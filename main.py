from sqlalchemy import select, delete, func
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sql_app.database import get_db
from sql_app import models, schemas

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "API is running"}


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
        select(models.Location).offset(skip).limit(limit)
    )
    return result.scalars().all()


@app.get("/locations/{location_id}", response_model=schemas.Location)
async def read_location(
    location_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(models.Location).where(models.Location.location_id == location_id)
    )
    location = result.scalar_one_or_none()
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@app.patch("/locations/{location_id}", response_model=schemas.Location)
async def update_location(
    location_id: int,
    location_update: schemas.LocationUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(models.Location).where(models.Location.location_id == location_id)
    )
    location = result.scalar_one_or_none()
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")

    for field, value in location_update.model_dump(exclude_unset=True).items():
        setattr(location, field, value)

    await db.commit()
    await db.refresh(location)
    return location


@app.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(models.Location).where(models.Location.location_id == location_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Location not found")

    listings_count = await db.scalar(
        select(func.count())
        .select_from(models.Listing)
        .where(models.Listing.location_id == location_id)
    )
    if listings_count:
        raise HTTPException(
            status_code=409,
            detail="Location is used by existing listings and cannot be deleted",
        )

    await db.execute(
        delete(models.Location).where(models.Location.location_id == location_id)
    )
    await db.commit()
