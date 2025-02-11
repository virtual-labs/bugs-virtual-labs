import os
import time
import json
import re
import requests
from datetime import datetime
import pytz
from github import Github

# GitHub credentials (Securely accessed from environment variables)
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("❌ GitHub Token not found. Ensure it is set in GitHub Secrets!")

SOURCE_REPO = "virtual-labs/bugs-virtual-labs"
TARGET_REPO = "virtual-labs/bugs-virtual-labs"

# Headers for authentication
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

class RateLimitError(Exception):
    pass

def check_rate_limit():
    """Check remaining API rate limit."""
    url = "https://api.github.com/rate_limit"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()['rate']['remaining']
    return 0

def wait_for_rate_limit_reset():
    """Wait until rate limit resets."""
    url = "https://api.github.com/rate_limit"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        reset_time = response.json()['rate']['reset']
        current_time = int(time.time())
        sleep_time = reset_time - current_time + 60  # Add buffer time
        if sleep_time > 0:
            print(f"⏳ Rate limit exceeded. Waiting {sleep_time//60} min...")
            time.sleep(sleep_time)

def process_issue_body(body):
    """Modify issue body to update image URLs."""
    if not body:
        return body  # Skip if body is empty
    
    markdown_pattern = r'!\[(?:.*?)\]\((https?://[^\s)]+\.(?:png|jpg|jpeg|gif))\)'
    html_pattern = r'<img [^>]*src=["\'](https?://[^"\']+\.(?:png|jpg|jpeg|gif))["\'][^>]*>'
    
    def replace_path(image_url):
        if 'raw.githubusercontent.com' in image_url:
            url_parts = image_url.split('/')
            try:
                branch_index = url_parts.index('main') if 'main' in url_parts else url_parts.index('master')
                if 'older' not in url_parts:
                    url_parts.insert(branch_index + 1, 'img/older')
                return '/'.join(url_parts)
            except ValueError:
                return image_url
        return image_url
    
    def replace_markdown(match):
        return f'![ScreenShot of Issue]({replace_path(match.group(1))})'
    
    def replace_html(match):
        return match.group(0).replace(match.group(1), replace_path(match.group(1)))
    
    body = re.sub(markdown_pattern, replace_markdown, body)
    body = re.sub(html_pattern, replace_html, body)
    
    return body

def get_issue(issue_id):
    """Fetch a single issue from GitHub with rate limit handling."""
    url = f"https://api.github.com/repos/{SOURCE_REPO}/issues/{issue_id}"
    
    if check_rate_limit() < 50:
        wait_for_rate_limit_reset()
    
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 404:
        print(f"⚠️ Issue {issue_id} not found (skipping).")
        return None
    elif response.status_code == 403:
        raise RateLimitError("🚨 Rate limit exceeded")
    elif response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error fetching issue {issue_id}: {response.status_code}")
        return None

def update_issue(issue_id, title, body):
    """Update an issue in the target repository."""
    url = f"https://api.github.com/repos/{TARGET_REPO}/issues/{issue_id}"
    issue_data = {"title": title, "body": body}

    if check_rate_limit() < 50:
        wait_for_rate_limit_reset()
    
    while True:
        response = requests.patch(url, json=issue_data, headers=HEADERS)

        if response.status_code == 200:
            print(f"✅ Issue [#{issue_id}] '{title}' updated successfully!")
            return True
        elif response.status_code == 403 and "secondary rate limit" in response.text.lower():
            print(f"⚠️ Secondary rate limit hit! Waiting 45 sec before retrying...")
            time.sleep(45)
        else:
            print(f"❌ Failed to update issue [#{issue_id}] '{title}': {response.status_code}")
            return False

# def save_progress(last_processed_id):
#     """Save last processed issue ID to a file."""
#     with open('issue_progress.json', 'w') as f:
#         json.dump({'last_id': last_processed_id}, f)

# def load_progress():
#     """Load last processed issue ID from a file."""
#     try:
#         with open('issue_progress.json', 'r') as f:
#             data = json.load(f)
#             return data.get('last_id', 0)
#     except FileNotFoundError:
#         return 0

def process_issues(start_id=1101, end_id=4494, delay=3):
    """Process issues, modify body, and update them with rate limit handling."""
    # last_processed_id = load_progress()
    # start_id = max(start_id, last_processed_id + 1)  # Resume from last progress

    print(f"🚀 Starting from issue ID: {start_id}")

    failed_issues = []

    for issue_id in range(start_id, end_id + 1):
        try:
            print(f"🔄 Processing issue {issue_id}...")
            issue = get_issue(issue_id)
            if issue:
                modified_body = process_issue_body(issue.get("body", "No description provided."))
                
                if modified_body != issue["body"]:  # Update only if modified
                    success = update_issue(issue["number"], issue["title"], modified_body)
                    if not success:
                        failed_issues.append(issue["number"])
                
                # save_progress(issue_id)  # Save progress after each issue

            time.sleep(delay)  # Add delay between requests to prevent rate limits

        except RateLimitError:
            wait_for_rate_limit_reset()
            issue_id -= 1  # Retry current issue
            continue
        except Exception as e:
            print(f"❌ Error processing issue {issue_id}: {str(e)}")
            failed_issues.append(issue_id)

    print("\n✅ Processing completed!")
    if failed_issues:
        print(f"⚠️ Failed issues: {failed_issues}")
        with open('failed_issues.json', 'w') as f:
            json.dump(failed_issues, f)
    else:
        print("🎉 All issues processed successfully!")

if __name__ == "__main__":
    process_issues()
