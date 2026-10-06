import requests
import pandas as pd

owner = "sophia-dao"
repo = "cloud_computing_proj"

url = f"https://api.github.com/repos/{owner}/{repo}/issues"

params = {
    "state": "all",
    "per_page": 100
}

response = requests.get(url, params=params)
response.raise_for_status()

issues = response.json()

data = []

for issue in issues:
    # GitHub's Issues API also returns pull requests,
    # so exclude them.
    if "pull_request" in issue:
        continue

    data.append({
        "Number": issue["number"],
        "Title": issue["title"],
        "State": issue["state"],
        "Author": issue["user"]["login"],
        "Assignee": (
            issue["assignee"]["login"]
            if issue["assignee"]
            else ""
        ),
        "Labels": ", ".join(
            label["name"] for label in issue["labels"]
        ),
        "Created": issue["created_at"],
        "Updated": issue["updated_at"],
        "Closed": issue["closed_at"],
        "URL": issue["html_url"],
        "Description": issue["body"] or ""
    })

df = pd.DataFrame(data)

df.to_csv("github_issues.csv", index=False)

print(f"Exported {len(df)} issues.")