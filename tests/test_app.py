import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Test that the home page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"StockSage" in response.data or b"<html" in response.data

def test_invalid_route(client):
    """Test that an invalid route returns 404"""
    response = client.get('/this_route_does_not_exist')
    assert response.status_code == 404
