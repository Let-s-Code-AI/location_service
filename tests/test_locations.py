import pytest
from fastapi import status


@pytest.mark.asyncio
class TestLocationEndpoints:
    """Testy integracyjne dla endpointów Location API."""

    async def test_create_location(self, client):
        """Test tworzenia nowej lokalizacji."""
        location_data = {
            "city": "Warszawa",
            "locality": "Śródmieście",
            "city_district": "Centrum",
            "street": "Marszałkowska",
            "full_address": "Marszałkowska 1, Warszawa",
            "latitude": 52.2297,
            "longitude": 21.0122
        }
        
        response = await client.post("/locations/", json=location_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["city"] == location_data["city"]
        assert data["locality"] == location_data["locality"]
        assert data["city_district"] == location_data["city_district"]
        assert data["street"] == location_data["street"]
        assert data["full_address"] == location_data["full_address"]
        assert data["latitude"] == location_data["latitude"]
        assert data["longitude"] == location_data["longitude"]
        assert "location_id" in data
        assert isinstance(data["location_id"], int)

    async def test_create_location_minimal_data(self, client):
        """Test tworzenia lokalizacji z minimalnymi danymi."""
        location_data = {
            "city": "Kraków"
        }
        
        response = await client.post("/locations/", json=location_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["city"] == location_data["city"]
        assert "location_id" in data

    async def test_get_locations_empty(self, client):
        """Test pobierania listy lokalizacji gdy baza jest pusta."""
        response = await client.get("/locations/")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    async def test_get_locations_with_data(self, client):
        """Test pobierania listy lokalizacji z danymi."""
        # Utwórz kilka lokalizacji
        locations_data = [
            {
                "city": "Warszawa",
                "locality": "Śródmieście",
                "latitude": 52.2297,
                "longitude": 21.0122
            },
            {
                "city": "Kraków",
                "locality": "Stare Miasto",
                "latitude": 50.0647,
                "longitude": 19.9450
            },
            {
                "city": "Gdańsk",
                "locality": "Główne Miasto",
                "latitude": 54.3520,
                "longitude": 18.6466
            }
        ]
        
        created_ids = []
        for loc_data in locations_data:
            response = await client.post("/locations/", json=loc_data)
            assert response.status_code == status.HTTP_200_OK
            created_ids.append(response.json()["location_id"])
        
        # Pobierz wszystkie lokalizacje
        response = await client.get("/locations/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert all("location_id" in loc for loc in data)
        assert all(loc["location_id"] in created_ids for loc in data)

    async def test_get_locations_with_pagination(self, client):
        """Test paginacji przy pobieraniu lokalizacji."""
        # Utwórz 5 lokalizacji
        for i in range(5):
            location_data = {
                "city": f"City{i}",
                "locality": f"Locality{i}"
            }
            await client.post("/locations/", json=location_data)
        
        # Test skip i limit
        response = await client.get("/locations/?skip=2&limit=2")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    async def test_get_location_by_id(self, client):
        """Test pobierania pojedynczej lokalizacji po ID."""
        # Utwórz lokalizację
        location_data = {
            "city": "Warszawa",
            "locality": "Śródmieście",
            "street": "Marszałkowska",
            "latitude": 52.2297,
            "longitude": 21.0122
        }
        
        create_response = await client.post("/locations/", json=location_data)
        location_id = create_response.json()["location_id"]
        
        # Pobierz lokalizację po ID
        response = await client.get(f"/locations/{location_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["location_id"] == location_id
        assert data["city"] == location_data["city"]
        assert data["locality"] == location_data["locality"]
        assert data["street"] == location_data["street"]
        assert data["latitude"] == location_data["latitude"]
        assert data["longitude"] == location_data["longitude"]

    async def test_get_location_by_id_not_found(self, client):
        """Test pobierania nieistniejącej lokalizacji."""
        response = await client.get("/locations/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Location not found"

    async def test_get_location_by_id_invalid_id(self, client):
        """Test pobierania lokalizacji z nieprawidłowym ID."""
        response = await client.get("/locations/abc")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

