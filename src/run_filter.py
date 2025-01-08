import requests
import os
import logging
import json
import google.generativeai as genai

import typing_extensions as typing

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)  

# Load environment variables
TOKEN = os.getenv('TOKEN')
KEY = os.getenv('KEY')

if not TOKEN or not KEY:
    logger.critical("Please set the environment variables REPO_ACCESS_TOKEN and API_KEY")
    exit(1)

OWNER = "virtual-labs"
REPO = "bugs-virtual-labs"

# Configure generative AI
genai.configure(api_key=KEY)

# Template for labeling issues
# Read template from file
file_path = os.path.join(os.getcwd(), 'data', 'prompt_template.txt')
with open(file_path, 'r') as f:
    template = f.read().strip()

if not template:
    
    template = 'You are a content moderator for GitHub issues. Your task is to label issues as inappropriate or not. Inappropriate refers to issues containing hateful/profane language. Given an issue return only NSFW if inappropriate else return SFW. Nothing else.\nIssue\n'


class ContentCategory(typing.TypedDict):
    category: str
    explanation: str


def predict_label(comment):
    # Create the model
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 512,
        "response_mime_type": "application/json",
        "response_schema": ContentCategory
    }
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )
    # chat_session = model.start_chat(history=[])
    # chat_message = (f"{template}{comment}")
    # logger.info(chat_message)
    # response = chat_session.send_message(f"{template}{comment}")

    prompt = template.format(comment)
    logger.info("Comment to be moderated:: %s", comment)
    response = model.generate_content(prompt)
    logger.info(response.text)
    category = json.loads(response.text)
    # if 'NSFW' in response.text:
    #     return 'NSFW'
    # return 'SFW'
    return category

def get_comments(issues):
    infos = []
    for issue in issues:
        curr_issue = {issue['number']: ''}
        flag = False
        content = issue['body'].split("\n")
        for line in content:
            if 'Additional info' in line:
                flag = True
            elif 'UserAgent' in line:
                break

            if flag:
                curr_issue[issue['number']] += line.replace('**Additional info-**', '').strip()
        infos.append(curr_issue)
    return infos

def get_labels(comments):
    labels = []
    for comment in comments:
        comment_str = list(comment.values())[0]
        classificationData = predict_label(comment_str)
        labels.append({list(comment.keys())[0]: classificationData['category']})
    return labels

# API URL and headers
url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"
headers = {
    "Authorization": f"token {TOKEN}"
}

# Get all the issues with the Unprocessed label
def get_issues(url, headers):
    logger.debug("Fetching all issues from %s", url)
    issues = []
    params = {
        "labels": "UNPROCESSED",
        "state": "open",
        "per_page": 100,
        "page": 1
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        issues = response.json()
        logger.debug("Succesfully fetched all issues")
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
    return issues

# Remove a label from an issue
def remove_label(issue_number, label):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues/{issue_number}/labels/{label}"
    response = requests.delete(url, headers=headers)
    if response.status_code == 200:
        print(f"Successfully removed label '{label}' from issue #{issue_number}")
    else:
        print(f"Error removing label '{label}' from issue #{issue_number}: {response.status_code} - {response.text}")

# Fetch and process issues
issues = get_issues(url, headers)

# Sort issues by created date and get the oldest 12
issues = sorted(issues, key=lambda x: x['created_at'])
issues = issues[:12]

# Get labels for the issues
comments = get_comments(issues)
labels = get_labels(comments)

# Process issues for labeling and removing Unprocessed label
for label in labels:
    issue_number = list(label.keys())[0]
    label_value = list(label.values())[0]

    # Add the Inappropriate label for NSFW issues
    if label_value == 'Inappropriate':
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues/{issue_number}/labels"
        response = requests.post(url, headers=headers, json={"labels": ["Inappropriate"]})
        print(response.status_code)
        print(response.text)

    # Remove the Unprocessed label for all issues
    remove_label(issue_number, "UNPROCESSED")
