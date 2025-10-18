# R087: Async-Only Handlers Violation
# This file demonstrates blocking calls in async functions

import time
import requests
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
async def get_users():
    # Blocking call in async function
    time.sleep(1)  # Should use asyncio.sleep

    # Blocking HTTP request
    response = requests.get("https://api.example.com/users")  # Should use httpx

    return response.json()
