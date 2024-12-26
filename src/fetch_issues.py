import csv
import os
import requests

def get_college_from_label(issue):
    college_list = [
        'AMRT',
        'COEP',
        'DEI',
        'DLBG',
        'IIITH',
        'IITB',
        'IITD',
        'IITG',
        'IITK',
        'IITKGP',
        'IITR',
        'NITK'
    ]
    
    ##in label check which college is present, labels are like "Inappropriate,IIITH...etc"
    for label in issue.get("labels", []):
        for college in college_list:
            if college in label["name"]:
                return college
        
    return None
    

def fetch_issues():
    # GitHub repository details
    repo_owner = "virtual-labs"  # Replace with the repo owner's username/org
    repo_name = "bugs-virtual-labs"     # Replace with the repository name

    # GitHub API endpoint for issues
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"

    # Token from environment variable
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is not set.")

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Parameters for fetching issues
    params = {
        "state": "all",  # Fetch both open and closed issues
        "per_page": 100,  # Maximum number of results per page
    }

    issues = []

    # Fetch all pages of issues
    while url:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        issues.extend(response.json())

        # Check for pagination
        if 'next' in response.links:
            url = response.links['next']['url']
        else:
            url = None

    # Write issues to a CSV file
    output_file = "issues.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "id", "number", "title", "state", "created_at", "updated_at",
            "closed_at", "url", "user", "assignee", "labels", "comments", "body", "college"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for issue in issues:
            writer.writerow({
                "id": issue.get("id", ""),
                "number": issue.get("number", ""),
                "title": issue.get("title", ""),
                "state": issue.get("state", ""),
                "created_at": issue.get("created_at", ""),
                "updated_at": issue.get("updated_at", ""),
                "closed_at": issue.get("closed_at", ""),
                "url": issue.get("html_url", ""),
                "user": issue.get("user", {}).get("login", "") if issue.get("user") else "",
                "assignee": issue.get("assignee", {}).get("login", "") if issue.get("assignee") else "",
                "labels": ", ".join([label["name"] for label in issue.get("labels", [])]) if issue.get("labels") else "",
                "comments": issue.get("comments", ""),
                "body": issue.get("body", ""),
                "college": get_college_from_label(issue)
            })

    print(f"Issues successfully written to {output_file}")

if __name__ == "__main__":
    fetch_issues()
