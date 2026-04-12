import requests
import json
import os
import time

# Use BACKEND_URL env var (set on Render); falls back to localhost for local dev
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

class Generator:
    def __init__(self, nutrition_input:list, ingredients:list=[], params:dict={'n_neighbors':5,'return_distance':False}):
        self.nutrition_input = nutrition_input
        self.ingredients = ingredients
        self.params = params

    def set_request(self, nutrition_input:list, ingredients:list, params:dict):
        self.nutrition_input = nutrition_input
        self.ingredients = ingredients
        self.params = params

    def generate(self):
        request = {
            'nutrition_input': self.nutrition_input,
            'ingredients': self.ingredients,
            'params': self.params
        }

        # Retry up to 3 times to handle Render free-tier cold-start (spin-up ~30s)
        last_error = None
        for attempt in range(3):
            try:
                response = requests.post(
                    url=f'{BACKEND_URL}/predict/',
                    data=json.dumps(request),
                    headers={'Content-Type': 'application/json'},
                    timeout=60   # 60 s — enough for cold-start
                )
                # Raise on HTTP error codes (4xx/5xx)
                response.raise_for_status()
                return response
            except requests.exceptions.Timeout:
                last_error = "Request timed out. The backend may be starting up — please try again in a moment."
            except requests.exceptions.ConnectionError:
                last_error = "Cannot reach the backend server. Please try again."
            except requests.exceptions.HTTPError as e:
                last_error = f"Backend returned an error: {e}"
            except Exception as e:
                last_error = str(e)

            # Wait before retrying (except on the last attempt)
            if attempt < 2:
                time.sleep(5)

        # Return a mock response-like object carrying the error so callers can display it
        raise RuntimeError(last_error)