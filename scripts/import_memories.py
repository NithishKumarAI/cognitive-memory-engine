import json
import requests

BACKEND_URL = "https://cognitive-memory-backend-244986175934.asia-south1.run.app"

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzgyMjU3Njk4fQ.0FC95sQefHY38K__eyhXye7A8ZViuuFb0w7zG1D2kec"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

from pathlib import Path

json_file = Path(__file__).parent / "memories.json"

with open(json_file, "r", encoding="utf-8") as f:
    memories = json.load(f)

for memory in memories:
    response = requests.post(
        f"{BACKEND_URL}/memories",
        json=memory,
        headers=headers
    )

    print(
        response.status_code,
        memory["title"]
    )