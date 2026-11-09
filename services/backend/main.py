import math

import jwt
from sqlalchemy import select, delete, func
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional
from sql_app.database import get_db
from sql_app import models, schemas
from sql_app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> models.User:
    try:
        user_id = decode_access_token(token)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await db.get(models.User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@app.get("/")
async def root():
    return {"message": "API is running"}


# Auth endpoints
@app.post("/auth/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def register(
    data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(models.User).where(models.User.email == data.email)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = models.User(email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    # OAuth2PasswordRequestForm wymaga pola "username" — traktujemy je jako email.
    result = await db.execute(
        select(models.User).where(models.User.email == form.username)
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form.password, user.password_hash):
        raise INVALID_CREDENTIALS
    if not user.is_active:
        raise INVALID_CREDENTIALS
    return schemas.Token(access_token=create_access_token(user.user_id))


@app.get("/auth/me", response_model=schemas.User)
async def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user


# Listing endpoints
def _range_conditions(column, name: str, low: Optional[float], high: Optional[float]) -> list:
    for value in (low, high):
        if value is not None and not math.isfinite(value):
            raise HTTPException(status_code=422, detail=f"{name} musi być skończoną liczbą")
    if low is not None and high is not None and low > high:
        raise HTTPException(
            status_code=422, detail=f"{name}_min nie może być większe niż {name}_max"
        )
    conditions = []
    if low is not None:
        conditions.append(column >= low)
    if high is not None:
        conditions.append(column <= high)
    return conditions


def listing_filters(
    price_total_min: Optional[float] = Query(None, ge=0),
    price_total_max: Optional[float] = Query(None, ge=0),
    price_sqm_min: Optional[float] = Query(None, ge=0),
    price_sqm_max: Optional[float] = Query(None, ge=0),
    area_min: Optional[float] = Query(None, ge=0),
    area_max: Optional[float] = Query(None, ge=0),
    rooms: List[int] = Query([]),
) -> list:
    """Builds SQL conditions for GET /listings/. A NULL in a filtered column excludes the row."""
    if any(r < 1 for r in rooms):
        raise HTTPException(status_code=422, detail="rooms musi być liczbą większą od 0")
    conditions = [
        *_range_conditions(models.Listing.price_total_zl, "price_total", price_total_min, price_total_max),
        *_range_conditions(models.Listing.price_sqm_zl, "price_sqm", price_sqm_min, price_sqm_max),
        *_range_conditions(models.Listing.area, "area", area_min, area_max),
    ]
    if rooms:
        conditions.append(models.Listing.rooms.in_(rooms))
    return conditions


@app.get("/listings/", response_model=schemas.ListingPage)
async def read_listings(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    conditions: list = Depends(listing_filters),
    db: AsyncSession = Depends(get_db),
):
    # One list of conditions shared by the rows query and the count query,
    # so `total` always reflects exactly the same filters as `items`.

    total = await db.scalar(
        select(func.count()).select_from(models.Listing).where(*conditions)
    )
    result = await db.execute(
        select(models.Listing)
        .options(selectinload(models.Listing.location))
        .where(*conditions)
        .order_by(models.Listing.listing_id)
        .offset(skip)
        .limit(limit)
    )
    return schemas.ListingPage(
        items=result.scalars().all(), total=total, skip=skip, limit=limit
    )


# Location endpoints
@app.post("/locations/", response_model=schemas.Location)
async def create_location(
    location: schemas.LocationCreate,
    db: AsyncSession = Depends(get_db),
    _user: models.User = Depends(get_current_user),
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
    db: AsyncSession = Depends(get_db),
    _user: models.User = Depends(get_current_user),
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
    db: AsyncSession = Depends(get_db),
    _user: models.User = Depends(get_current_user),
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
