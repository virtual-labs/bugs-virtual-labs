import requests

def get_github_issue(repository_id, issue_id, token, label):
    # Define the GitHub API URL for a specific issue in a repository
    url = f"https://api.github.com/repos/{repository_id}/issues/{issue_id}"

    # Define the headers, including the Authorization token
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Send a GET request to GitHub API
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Parse JSON response to extract the issue data
        issue_data = response.json()
        print(f"Issue Title: {issue_data['title']}")
        print(f"Issue Body: {issue_data['body']}")
        print(f"State: {issue_data['state']}")
        print(f"Created At: {issue_data['created_at']}")
        print(f"Updated At: {issue_data['updated_at']}")
    else:
        print(f"Failed to retrieve issue. HTTP Status Code: {response.status_code}")
        
    # Save the issue data to a file
    with open(f'issue_{label}.json', 'a') as file:
        file.write(f"issue_id: {issue_id}\n")
        file.write(f"Issue Title: {issue_data['title']}\n")
        file.write(f"Issue Body: {issue_data['body']}\n")
        file.write(f"State: {issue_data['state']}\n")
        
        file.write("-----------------------------\n")
        

# Example usage
repository_id = 'virtual-labs/bugs-virtual-labs'  # Replace with your GitHub repository ID
# issue_id = 4689  # Replace with the issue ID you want to query
token = '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'  # Replace with your GitHub token

FN = ['4341', '4329', '3997', '3705', '3640', '3329', '3317', '3316', '3315', '3193', '3160', '2372', '2352']
FP= ['4689', '4610', '4583', '4580', '4544', '4475', '4275', '4269', '4253', '4251', '4221', '4220', '4098', '4091', '4083', '3864', '3748', '3747', '3723', '3707', '3706', '3610', '3535', '3407', '3384', '3383', '3286', '3269', '3140', '3038', '3037', '3036', '3035', '3027', '3026', '2961', '2960', '2942', '2789', '2582', '2581', '2580', '2579', '2578', '2534', '2533', '2486', '2485', '2484', '2483', '2482', '2481', '2480']
TP = ['4589', '4347', '4343', '4330', '4291', '4285', '4160', '4049', '3943', '3942', '3941', '3940', '3843', '3842', '3841', '3496']

##get all issues and store in a file
for issue_id in FN:
    get_github_issue(repository_id, issue_id, token, 'FN')
for issue_id in FP:
    get_github_issue(repository_id, issue_id, token, 'FP')
for issue_id in TP:
    get_github_issue(repository_id, issue_id, token, 'TP')

