import os
import json
import requests
import logging
from google import genai
from google.genai import types
from tabulate import tabulate

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(logging.FileHandler('prediction.log'))

# Environment variables
TOKEN = os.getenv('REPO_ACCESS_TOKEN')
KEY = os.getenv('GEMINI_API_KEY') or os.getenv('API_KEY')
assert TOKEN and KEY, "Set both REPO_ACCESS_TOKEN & GEMINI_API_KEY in env"

# GenAI client config
client = genai.Client(api_key=KEY)
MODEL_ID = "gemini-2.5-flash"

# GitHub repo info
OWNER = "virtual-labs"
REPO = "bugs-virtual-labs"
BASE_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Load prompt template
with open('data/prompt_template.txt') as f:
    template = f.read().strip()
assert template, "Prompt template is empty!"

def safe_parse_json(text: str) -> dict:
    """
    Strips backticks/markdown and safely parses JSON output.
    """
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON from AI: %s\nError: %s", text, e)
        return {"category": "Unknown", "explanation": ""}

def predict_label(comment: str) -> dict:
    prompt = template.format(comment)

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.9,
                max_output_tokens=4096 
            )
        )

        if not response.candidates or not response.candidates[0].content.parts:
            reason = response.candidates[0].finish_reason if response.candidates else "None"
            logger.warning("No content parts (finish_reason=%s)", reason)
            return {"category": "Unknown", "explanation": ""}

        return safe_parse_json(response.text)

    except Exception as e:
        logger.error("Gemini call failed: %s", e)
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

    summary = []

    for issue in issues[:12]:
        num = issue['number']
        comment = extract_content(issue)

        print(f"\n🪲 Issue #{num}")
        print(f"---------------------\n{comment}\n")

        result = predict_label(comment)
        category = result.get("category", "Unknown")
        explanation = result.get("explanation", "")

        print(f"🤖 Gemini Prediction: {json.dumps(result, indent=2)}\n")

        action = "None"

        if category == "Inappropriate":
            add = requests.post(
                f"{BASE_URL}/{num}/labels",
                headers=HEADERS,
                json={"labels": ["Inappropriate"]}
            )
            action = "Labeled Inappropriate" if add.ok else "Failed to Label"

        # ✅ Only remove UNPROCESSED label if AI gave a valid category
        if category != "Unknown":
            rem = requests.delete(f"{BASE_URL}/{num}/labels/UNPROCESSED", headers=HEADERS)
            if rem.ok:
                action += " + Removed UNPROCESSED"
            else:
                action += " + Failed to Remove UNPROCESSED"

        summary.append([f"#{num}", category, action])

    print("\n📊 Summary Table:")
    print(tabulate(summary, headers=["Issue", "Category", "Action"], tablefmt="fancy_grid"))

if __name__ == "__main__":
    process_issues()
