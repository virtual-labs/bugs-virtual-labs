import os
import logging
import json
import requests
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.FileHandler('prediction.log'))

# Load environment variables
TOKEN = os.getenv('REPO_ACCESS_TOKEN')
KEY = os.getenv('GEMINI_API_KEY') or os.getenv('API_KEY')
assert TOKEN and KEY, "Set both REPO_ACCESS_TOKEN & GEMINI_API_KEY in env"

# Configure GenAI
client = genai.Client(api_key=KEY)
MODEL_ID = "gemini-2.5-flash"

OWNER = "virtual-labs"
REPO = "bugs-virtual-labs"
BASE_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Load prompt template
with open('data/prompt_template.txt') as f:
    template = f.read().strip()
assert template, "Prompt template is empty!"

def predict_label(comment: str) -> dict:
    prompt = template.format(comment)
    logger.info("Prompt:\n%s", prompt)

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.9,
            max_output_tokens=512
        )
    )
    # Safe access to response.text
    if response.candidates and response.candidates[0].content.parts:
        text = response.text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.error("Invalid JSON from AI: %s", text)
            return {"category": "Unknown", "explanation": ""}
    else:
        reason = response.candidates[0].finish_reason if response.candidates else "None"
        logger.warning("No content parts (finish_reason=%s)", reason)
        return {"category": "Unknown", "explanation": ""}

def get_unprocessed_issues():
    params = {"labels": "UNPROCESSED", "state": "open", "per_page": 100}
    resp = requests.get(BASE_URL, headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()

def extract_content(issue):
    body = issue.get('body') or ""
    lines = body.splitlines()
    extract = []
    flag = False
    for line in lines:
        if line.startswith(("**Type(s) of Issue -**", "**Additional info-**")):
            flag = True
        elif flag and line.strip().startswith("**") and "UserAgent" in line:
            break
        if flag:
            extract.append(line.strip())
    return "\n".join(extract)

def process_issues():
    issues = get_unprocessed_issues()
    issues.sort(key=lambda i: i['created_at'])
    for issue in issues[:12]:
        num = issue['number']
        comment = extract_content(issue)
        logger.info("Issue #%s -> comment extracted", num)

        result = predict_label(comment)
        category = result.get("category", "Unknown")

        # Add label if needed
        if category == "Inappropriate":
            add = requests.post(
                f"{BASE_URL}/{num}/labels",
                headers=HEADERS,
                json={"labels": ["Inappropriate"]}
            )
            logger.info("Labeled #%s -> %s", num, add.status_code)

        # Always remove UNPROCESSED label
        rem = requests.delete(f"{BASE_URL}/{num}/labels/UNPROCESSED", headers=HEADERS)
        logger.info("Removed UNPROCESSED from #%s -> %s", num, rem.status_code)

if __name__ == "__main__":
    process_issues()
