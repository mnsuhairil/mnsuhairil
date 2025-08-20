import os
import requests

# GitHub username
USERNAME = os.getenv("GH_LOGIN")

# Token from GitHub Secrets
TOKEN = os.getenv("GH_TOKEN")

if not TOKEN:
    print("❌ Missing GH_TOKEN. Please set it in GitHub Secrets.")
    exit(1)

# GitHub API headers
headers = {"Authorization": f"token {TOKEN}"}

# Fetch repos
repos_url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100"
repos = requests.get(repos_url, headers=headers).json()

if not repos or "message" in repos:
    print("❌ No repositories found or invalid response:", repos)
    exit(1)

output_lines = ["## 📊 Project Contribution Stats\n"]

for repo in repos:
    repo_name = repo["name"]

    # Get commit count
    commits_url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/commits?per_page=1"
    commits = requests.get(commits_url, headers=headers)
    commit_count = commits.links.get("last", {}).get("url", "")
    if commit_count:
        commit_count = int(commit_count.split("page=")[-1])
    else:
        commit_count = commits.json() if isinstance(commits.json(), list) else 0

    # Get PR count
    prs_url = f"https://api.github.com/search/issues?q=repo:{USERNAME}/{repo_name}+type:pr"
    prs = requests.get(prs_url, headers=headers).json()
    pr_count = prs.get("total_count", 0)

    # Get issue count
    issues_url = f"https://api.github.com/search/issues?q=repo:{USERNAME}/{repo_name}+type:issue"
    issues = requests.get(issues_url, headers=headers).json()
    issue_count = issues.get("total_count", 0)

    output_lines.append(
        f"- **{repo_name}** → Commits: `{commit_count}` | PRs: `{pr_count}` | Issues: `{issue_count}`"
    )

with open("PROJECT_STATS.md", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print("✅ Project stats generated in PROJECT_STATS.md")
