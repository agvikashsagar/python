import requests
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Azure DevOps API configuration
username = ""
pat = ""
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Basic {pat}"
}
base_url = "https://dev.azure.com/<organization>/<project>"

# Get work items and commits for a single user
def getCommitWorkItem(user_id):
    """
    Fetch work items and commit details for the given user.
    """
    from_date = datetime.now() - timedelta(days=30)
    to_date = datetime.now()
    commitReportList = {
        "workItemCount": 0,
        "storyCount": 0,
        "bugCount": 0,
        "totalStoryPoints": 0.0
    }

    try:
        # Get repositories
        repos_url = f"{base_url}/_apis/git/repositories?api-version=7.1-preview.1"
        repos_response = requests.get(repos_url, headers=headers)
        repos = repos_response.json().get("value", [])

        # Process each repository
        for repo in repos:
            repo_id = repo["id"]
            commits_url = f"{base_url}/_apis/git/repositories/{repo_id}/commits"
            params = {
                "searchCriteria.fromDate": from_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "searchCriteria.toDate": to_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "searchCriteria.author": user_id
            }
            commits_response = requests.get(commits_url, headers=headers, params=params)

            if commits_response.status_code == 200:
                commits = commits_response.json().get("value", [])

                # Process commits
                for commit in commits:
                    # Fetch work items linked to the commit
                    work_item_ids = commit.get("workItemIds", [])
                    for work_item_id in work_item_ids:
                        work_item_url = f"{base_url}/_apis/wit/workitems/{work_item_id}?api-version=7.1-preview.1"
                        work_item_response = requests.get(work_item_url, headers=headers)

                        if work_item_response.status_code == 200:
                            work_item = work_item_response.json()
                            work_item_type = work_item.get("fields", {}).get("System.WorkItemType", "")
                            story_points = work_item.get("fields", {}).get("Microsoft.VSTS.Scheduling.StoryPoints", 0)

                            commitReportList["workItemCount"] += 1
                            if work_item_type == "Story":
                                commitReportList["storyCount"] += 1
                                commitReportList["totalStoryPoints"] += story_points
                            elif work_item_type == "Bug":
                                commitReportList["bugCount"] += 1

    except Exception as e:
        print(f"Error processing user {user_id}: {e}")
    return commitReportList

# Process a single user's data
def process_user(user_id):
    """
    Wrapper to process user and return the result.
    """
    return user_id, getCommitWorkItem(user_id)

# Main function to process commits for all users
def processCommits():
    excel_name = "commit.xlsx"
    output_file = "updated_commit.xlsx"

    try:
        df = pd.read_excel(excel_name, engine="openpyxl")
    except FileNotFoundError:
        print(f"File {excel_name} not found.")
        return
    except Exception as e:
        print(f"Error reading file {excel_name}: {e}")
        return

    # Initialize columns if not present
    if "PSID" in df.columns:
        df["PSID"] = df["PSID"].astype(str).str.rstrip(".0")
        df["number_of_workitems"] = 0
        df["number_of_story"] = 0
        df["number_of_bugs"] = 0
        df["total_story_points"] = 0.0

        psid_list = df["PSID"].tolist()

        # Parallel processing of users
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(process_user, psid): psid for psid in psid_list}
            for future in as_completed(futures):
                user_id, commitReportList = future.result()
                if commitReportList:
                    # Update DataFrame
                    index = df[df["PSID"] == user_id].index[0]
                    df.at[index, "number_of_workitems"] = commitReportList["workItemCount"]
                    df.at[index, "number_of_story"] = commitReportList["storyCount"]
                    df.at[index, "number_of_bugs"] = commitReportList["bugCount"]
                    df.at[index, "total_story_points"] = commitReportList["totalStoryPoints"]

        # Save results to Excel
        df.to_excel(output_file, index=False, engine="openpyxl")
        print(f"Updated data saved to {output_file}.")
    else:
        print("Column 'PSID' not found in the Excel file.")

# Run the script
if __name__ == "__main__":
    processCommits()
