from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Location schemas
class LocationBase(BaseModel):
    city: str | None = None
    locality: str | None = None
    city_district: str | None = None
    street: str | None = None
    full_address: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class LocationCreate(LocationBase):
    pass


class LocationUpdate(LocationBase):
    pass


class Location(LocationBase):
    location_id: int

    model_config = ConfigDict(from_attributes=True)


# Building schemas
class BuildingBase(BaseModel):
    year_built: int | None = None
    building_type: str | None = None
    floor: int | None = None


class BuildingCreate(BuildingBase):
    pass


class Building(BuildingBase):
    building_id: int

    model_config = ConfigDict(from_attributes=True)


# Owner schemas
class OwnerBase(BaseModel):
    owner_type: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None


class OwnerCreate(OwnerBase):
    pass


class Owner(OwnerBase):
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


# Features schemas
class FeaturesBase(BaseModel):
    has_basement: bool | None = None
    has_parking: bool | None = None
    kitchen_type: str | None = None
    window_type: str | None = None
    ownership_type: str | None = None
    equipment: str | None = None


class FeaturesCreate(FeaturesBase):
    pass


class Features(FeaturesBase):
    features_id: int

    model_config = ConfigDict(from_attributes=True)


# Listing schemas
class ListingBase(BaseModel):
    location_id: int
    building_id: int
    owner_id: int
    features_id: int
    rooms: int | None = None
    area: float | None = None
    price_total_zl: float | None = None
    price_sqm_zl: float | None = None
    price_per_sqm_detailed: float | None = None
    date_posted: date | None = None
    photo_count: int | None = None
    url: str | None = None
    image_url: str | None = None
    description_text: str | None = None


class ListingCreate(ListingBase):
    pass


class Listing(ListingBase):
    listing_id: int

    model_config = ConfigDict(from_attributes=True)


# Listing with relationships
class ListingDetail(Listing):
    location: Location | None = None
    building: Building | None = None
    owner: Owner | None = None
    features: Features | None = None


# Short schemas for the listings list (no description, URLs or FKs).
class LocationSummary(BaseModel):
    city: str | None = None
    city_district: str | None = None
    street: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ListingSummary(BaseModel):
    listing_id: int
    rooms: int | None = None
    area: float | None = None
    price_total_zl: float | None = None
    price_sqm_zl: float | None = None
    location: LocationSummary

    model_config = ConfigDict(from_attributes=True)


class ListingPage(BaseModel):
    items: list[ListingSummary]
    total: int  # count after filters, independent of skip/limit
    skip: int
    limit: int


# Auth schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class User(BaseModel):
    user_id: int
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
