import requests
from datetime import datetime, timedelta

# Azure DevOps settings
organization = "your-organization"
project = "your-project"
personal_access_token = "your-pat"

# Headers
headers = {
    "Authorization": f"Basic {personal_access_token}",
    "Content-Type": "application/json"
}

# Date range for the last month
to_date = datetime.now()
from_date = to_date - timedelta(days=30)

# Specify the user to filter by (email or display name)
user_id = "user@example.com"  # Replace with the actual user email or display name

# Get all repositories in the project
repos_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories?api-version=7.1-preview.1"
repos_response = requests.get(repos_url, headers=headers)
repositories = repos_response.json().get("value", [])

# Iterate over each repository to get commits
for repo in repositories:
    repository_id = repo["id"]
    repository_name = repo["name"]
    print(f"\nSearching in repository: {repository_name} ({repository_id})")

    # Get commits for the last month filtered by user
    commits_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository_id}/commits"
    params = {
        "searchCriteria.fromDate": from_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "searchCriteria.toDate": to_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "searchCriteria.author": user_id,  # Filter by user
        "api-version": "7.1-preview.1"
    }

    commits_response = requests.get(commits_url, headers=headers, params=params)
    commits = commits_response.json().get("value", [])

    # Process each commit
    for commit in commits:
        commit_id = commit["commitId"]
        user = commit["author"]["name"]
        date = commit["author"]["date"]

        # Fetch commit details to get linked work items
        commit_details_url = f"{commits_url}/{commit_id}"
        commit_details = requests.get(commit_details_url, headers=headers).json()
        
        work_items = commit_details.get("workItems", [])
        for work_item in work_items:
            work_item_id = work_item["id"]
            work_item_url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.1-preview.1"
            work_item_details = requests.get(work_item_url, headers=headers).json()
            work_item_type = work_item_details["fields"]["System.WorkItemType"]
            print(f"Commit {commit_id} by {user} on {date} linked to {work_item_type} #{work_item_id}")

# End of script

