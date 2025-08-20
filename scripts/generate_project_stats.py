import os, re, sys, json, textwrap
import requests
from datetime import datetime, timezone

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
LOGIN = os.environ.get("GITHUB_LOGIN")
INCLUDE_REPOS = [r.strip() for r in os.environ.get("INCLUDE_REPOS","").split(",") if r.strip()]
OWNED_ONLY = os.environ.get("OWNED_ONLY","false").lower() == "true"
RECENT_LIMIT = int(os.environ.get("RECENT_LIMIT","20"))

if not GITHUB_TOKEN or not LOGIN:
    print("Missing GITHUB_TOKEN or GITHUB_LOGIN", file=sys.stderr)
    sys.exit(1)

API = "https://api.github.com/graphql"
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

def gql(query, variables=None):
    r = requests.post(API, headers=HEADERS, json={"query": query, "variables": variables or {}})
    r.raise_for_status()
    j = r.json()
    if "errors" in j:
        raise RuntimeError(j["errors"])
    return j["data"]

# --- Helpers -------------------------------------------------------------

def get_recent_contributions(login, limit=20):
    """
    Fetch repos the user recently contributed to (commits/PRs/issues) + owned repos.
    """
    query = """
    query($login:String!, $limit:Int!) {
      user(login:$login) {
        repositoriesContributedTo(first:$limit, contributionTypes:[COMMIT, PULL_REQUEST, ISSUE], includeUserRepositories: !OWNED_ONLY, orderBy:{field:UPDATED_AT, direction:DESC}) {
          nodes { nameWithOwner isFork }
        }
        repositories(first:$limit, orderBy:{field:UPDATED_AT, direction:DESC}, affiliations:[OWNER, COLLABORATOR, ORGANIZATION_MEMBER]) {
          nodes { nameWithOwner isFork }
        }
      }
    }
    """
    # Replace !OWNED_ONLY inside the query string at runtime
    q = query.replace("!OWNED_ONLY", "false" if not OWNED_ONLY else "true")
    data = gql(q, {"login": login, "limit": limit})
    a = {n["nameWithOwner"] for n in data["user"]["repositories"]["nodes"]}
    b = {n["nameWithOwner"] for n in data["user"]["repositoriesContributedTo"]["nodes"]}
    repos = list(a.union(b))
    if INCLUDE_REPOS:
        repos.extend(INCLUDE_REPOS)
    # Deduplicate while preserving order
    seen, out = set(), []
    for r in repos:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out

def repo_stats(owner, name, login):
    """
    For a repo, compute:
     - commits authored by login on default branch
     - PRs opened by login
     - Issues opened by login
     - last push date
    """
    query = """
    query($owner:String!, $name:String!, $login:String!) {
      repository(owner:$owner, name:$name) {
        nameWithOwner
        isPrivate
        isArchived
        url
        defaultBranchRef {
          name
          target {
            ... on Commit {
              history(author:{id: $authorId}) { totalCount }
            }
          }
        }
        pushedAt
        pullRequests(filterBy:{createdBy:$login}, states:[OPEN, CLOSED, MERGED]) { totalCount }
        issues(filterBy:{createdBy:$login}, states:[OPEN, CLOSED]) { totalCount }
        owner { login }
      }
      user(login:$login){ id }
    }
    """
    # Need the user id first to filter commit history by author id
    uid = gql("query($login:String!){ user(login:$login){ id }}", {"login": login})["user"]["id"]

    data = gql(query, {"owner": owner, "name": name, "login": login, "authorId": uid})
    repo = data["repository"]
    if not repo:
        return None
    commits = 0
    if repo.get("defaultBranchRef") and repo["defaultBranchRef"].get("target"):
        hist = repo["defaultBranchRef"]["target"]["history"]
        if hist:
            commits = hist.get("totalCount", 0)
    prs = repo["pullRequests"]["totalCount"]
    issues = repo["issues"]["totalCount"]
    pushed = repo["pushedAt"]
    return {
        "nameWithOwner": repo["nameWithOwner"],
        "url": repo["url"],
        "commits": commits,
        "prs": prs,
        "issues": issues,
        "pushedAt": pushed,
        "isPrivate": repo["isPrivate"],
        "isArchived": repo["isArchived"],
    }

def format_date(iso):
    if not iso: return "—"
    dt = datetime.fromisoformat(iso.replace("Z","+00:00")).astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%d")

def make_table(rows):
    if not rows:
        return "_No repositories found._"
    header = "| Repository | Commits | PRs | Issues | Last Push |\n|---|---:|---:|---:|---|\n"
    lines = []
    for r in rows:
        name = r["nameWithOwner"]
        if r["isPrivate"]:
            name_md = f"**{name}** 🔒"
        else:
            name_md = f"[{name}]({r['url']})"
        lines.append(f"| {name_md} | {r['commits']:,} | {r['prs']:,} | {r['issues']:,} | {format_date(r['pushedAt'])} |")
    return header + "\n".join(lines)

# --- Main ---------------------------------------------------------------

repos = get_recent_contributions(LOGIN, limit=RECENT_LIMIT)
rows = []
for full in repos:
    if "/" not in full: 
        continue
    owner, name = full.split("/", 1)
    try:
        s = repo_stats(owner, name, LOGIN)
        if s: rows.append(s)
    except Exception as e:
        # Skip repos we can't access (private from orgs, etc.)
        continue

# Sort by recent push
rows.sort(key=lambda x: x["pushedAt"] or "", reverse=True)

table_md = make_table(rows)

# Write into README between markers
readme_path = "README.md"
with open(readme_path, "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"(<!-- PROJECT_STATS:START -->)(.*?)(<!-- PROJECT_STATS:END -->)"
replacement = r"\1\n" + table_md + r"\n\3"
new = re.sub(pattern, replacement, content, flags=re.S)

if new != content:
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new)
    print("Updated README with latest project stats.")
else:
    print("No changes.")
