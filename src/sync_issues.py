import os
import requests
import json

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_ACCESS_TOKEN = os.getenv("REPO_ACCESS_TOKEN")
REPO_B = os.getenv("REPO_B")
REPO_A = os.getenv("REPO_A")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json",
}
MAX_ISSUES = 500  # Maximum issues to fetch


def fetch_issues_from_repo_b():
    url = f"https://api.github.com/repos/{REPO_B}/issues"
    all_issues = []
    per_page = 100  # GitHub API's maximum issues per request
    for page in range(1, (MAX_ISSUES // per_page) + 2):  # Loop through pages
        params = {"per_page": per_page, "page": page}
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            issues = response.json()
            if not issues:
                break  # No more issues to fetch
            all_issues.extend(issues)
        else:
            print(f"Failed to fetch issues from {REPO_B}: {response.status_code}")
            break
    return all_issues[:MAX_ISSUES]  # Return up to MAX_ISSUES


def create_issue_in_repo_a(title, body):
    url = f"https://api.github.com/repos/{REPO_A}/issues"
    data = {"title": title, "body": body}
    headers = {
        "Authorization": f"Bearer {REPO_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"Issue created: {title}")
    else:
        print(f"Failed to create issue: {title}, Status: {response.status_code}")


def load_tracked_issues():
    if not os.path.exists("tracked_issues.json"):
        with open("tracked_issues.json", "w") as f:
            json.dump([], f)
    with open("tracked_issues.json", "r") as f:
        return json.load(f)


def save_tracked_issues(tracked_issues):
    with open("tracked_issues.json", "w") as f:
        json.dump(tracked_issues, f)


def main():
    print("Fetching issues from Repository B...")
    issues = fetch_issues_from_repo_b()
    if not issues:
        print("No issues fetched.")
        return

    print(f"Fetched {len(issues)} issues.")
    print("Checking for new issues...")
    tracked_issues = load_tracked_issues()

    for issue in issues:
        issue_id = issue["id"]
        title = issue["title"]
        body = issue.get("body", "")
        if issue_id not in tracked_issues:
            print(f"Creating new issue: {title}")
            create_issue_in_repo_a(title, body)
            tracked_issues.append(issue_id)
        else:
            print(f"Issue '{title}' already tracked.")

    print("Saving updated tracked issues...")
    save_tracked_issues(tracked_issues)
    print("Done.")


if __name__ == "__main__":
    main()
