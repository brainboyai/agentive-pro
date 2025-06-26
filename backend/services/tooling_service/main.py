# backend/services/tooling_service/main.py
import os
import requests
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

# Import the official Google API client library
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

# --- Credentials from .env file ---
# --- FIX: Use the new, specific environment variables ---
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY") 
CUSTOM_SEARCH_ENGINE_ID = os.getenv("CUSTOM_SEARCH_ENGINE_ID")

router = APIRouter(
    prefix="/tools",
    tags=["Tooling Service"],
)

# The get_weather_data function remains unchanged
def get_weather_data(location: str):
    if not OPENWEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenWeatherMap API key is not configured.")
    sanitized_location = location.split(',')[0].strip()
    print(f"--- [TOOLING_SERVICE] Calling weather API for sanitized location: '{sanitized_location}' ---")
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": sanitized_location, "appid": OPENWEATHER_API_KEY, "units": "metric"}
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=500, detail=f"An error occurred with the external weather service: {http_err}")
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"An unknown error occurred while fetching weather data.")


# --- NEW: Google Custom Search Tool Implementation ---
def perform_google_search(query: str):
    """
    Performs a Google Custom Search and returns a digest of results.
    """
    if not GOOGLE_SEARCH_API_KEY or not CUSTOM_SEARCH_ENGINE_ID:
        raise HTTPException(status_code=500, detail="Google API Key or Custom Search Engine ID is not configured.")

    print(f"--- [TOOLING_SERVICE] Performing Google Custom Search for: '{query}' ---")
    
    try:
        # Build the service object for the Custom Search API
        service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)
        
        # Execute the search
        res = service.cse().list(q=query, cx=CUSTOM_SEARCH_ENGINE_ID, num=5).execute()

        search_digest = []
        if 'items' in res:
            for result in res['items']:
                search_digest.append({
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "snippet": result.get("snippet")
                })
        
        print(f"--- [TOOLING_SERVICE] Search successful. Returning digest. ---")
        return search_digest

    except HttpError as e:
        print(f"--- [TOOLING_SERVICE] HTTP error during Google Search: {e} ---")
        raise HTTPException(status_code=e.resp.status, detail=f"An error occurred with the Google Search API: {e._get_reason()}")
    except Exception as e:
        print(f"--- [TOOLING_SERVICE] Error during Google Search: {e} ---")
        raise HTTPException(status_code=500, detail=f"An unknown error occurred with the search service: {e}")


# Test endpoints for both tools
@router.get("/get_weather", summary="Get weather for a location")
def get_weather_endpoint(location: str):
    return get_weather_data(location)

@router.get("/Google Search", summary="Perform a Google Search")
def search_endpoint(query: str):
    return perform_google_search(query)