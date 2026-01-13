import hashlib
import os

import requests

# --- CONFIGURATION ---
CACHE_DIR = "cache"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


def get_github_stats(username, token):
    """
    Fetches GitHub statistics for a given user using GraphQL API.

    Includes:
    - Repository count
    - Total stars
    - Total commits (last year)
    - Followers
    - Lines of Code (LOC) with caching mechanism
    """
    if not token:
        print("Missing GITHUB_TOKEN! Set it in your environment variables.")
        return mock_stats()

    headers = {"Authorization": f"token {token}"}

    os.makedirs(CACHE_DIR, exist_ok=True)

    try:
        print(f"Fetching GraphQL data for: {username}...")

        # 1. Get user ID and followers
        user_id, _, followers = get_user_id_and_followers(username, headers)

        # 2. Get total stars
        stars = get_total_stars(username, headers)

        # 3. Get total commits (contributions from the last year)
        commits, total_contributions, other_contributions = get_contribution_stats(
            username, headers
        )

        # 4. Count Lines of Code (LOC) - requires local cache for performance
        loc_stats = count_loc(username, user_id, headers)

        # 5. Get total repository count
        repos_count = get_repo_count(username, headers)

        return {
            "repos": f"{repos_count}",
            "stars": f"{stars:,}",
            "commits": f"{commits:,}",
            "total_contributions": f"{total_contributions:,}",
            "other_contributions": f"{other_contributions:,}",
            "followers": f"{followers:,}",
            "loc_total": f"{loc_stats[2]:,}",
            "loc_add": f"{loc_stats[0]:,}++",
            "loc_del": f"{loc_stats[1]:,}--",
        }

    except Exception as e:
        print(f"Error fetching stats: {e}")
        return mock_stats()


# --- HELPER FUNCTIONS (GraphQL) ---


def run_query(query, variables, headers):
    """Executes a GraphQL query and handles errors."""
    response = requests.post(
        GITHUB_GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers=headers,
    )
    if response.status_code == 200:
        result = response.json()

        if "errors" in result:
            raise Exception(f"GraphQL Error: {result['errors'][0]['message']}")

        return result
    raise Exception(f"Query failed: {response.status_code} {response.text}")


def get_user_id_and_followers(username, headers):
    """Retrieves user ID and total followers count."""
    query = """
    query($login: String!){
        user(login: $login) {
            id
            createdAt
            followers { totalCount }
        }
    }
    """
    data = run_query(query, {"login": username}, headers)
    return (
        data["data"]["user"]["id"],
        data["data"]["user"]["createdAt"],
        data["data"]["user"]["followers"]["totalCount"],
    )


def get_repo_count(username, headers):
    """Retrieves total count of owned repositories."""
    query = """
    query($login: String!) {
        user(login: $login) {
            repositories(ownerAffiliations: OWNER) { totalCount }
        }
    }
    """
    data = run_query(query, {"login": username}, headers)
    return data["data"]["user"]["repositories"]["totalCount"]


def get_total_stars(username, headers):
    """Calculates total stargazers earned across first 100 repositories."""
    query = """
    query($login: String!) {
        user(login: $login) {
            repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: STARGAZERS, direction: DESC}) {
                nodes { stargazers { totalCount } }
            }
        }
    }
    """
    data = run_query(query, {"login": username}, headers)
    stars = sum(
        node["stargazers"]["totalCount"]
        for node in data["data"]["user"]["repositories"]["nodes"]
    )
    return stars


def get_contribution_stats(username, headers):
    years_query = """
    query($login: String!) {
        user(login: $login) {
            contributionsCollection {
                contributionYears
            }
        }
    }
    """
    years_data = run_query(years_query, {"login": username}, headers)
    years = years_data["data"]["user"]["contributionsCollection"]["contributionYears"]

    total_commits = 0
    total_contribs = 0

    query_per_year = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
        user(login: $login) {
            contributionsCollection(from: $from, to: $to) {
                totalCommitContributions
                contributionCalendar {
                    totalContributions
                }
            }
        }
    }
    """

    print(f"Fetching stats for years: {years}...")

    for year in years:
        start_date = f"{year}-01-01T00:00:00Z"
        end_date = f"{year}-12-31T23:59:59Z"

        variables = {"login": username, "from": start_date, "to": end_date}

        data = run_query(query_per_year, variables, headers)
        collection = data["data"]["user"]["contributionsCollection"]

        commits = collection["totalCommitContributions"]
        contribs = collection["contributionCalendar"]["totalContributions"]

        total_commits += commits
        total_contribs += contribs

        print(f"Year {year}: {commits} commits, {contribs} total contribs")

    other_contribs = total_contribs - total_commits

    return total_commits, total_contribs, other_contribs


# --- LINES OF CODE (LOC) CALCULATION ---


def count_loc(username, user_id, headers):
    """
    Iterates through repositories and counts added/deleted lines for the specific user.
    Uses a local cache file to avoid re-calculating historical data for unchanged repos.
    """
    cache_file = os.path.join(CACHE_DIR, f"{username}_loc_cache.txt")
    cached_repos = {}

    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 4:
                    cached_repos[parts[0]] = {
                        "commits": int(parts[1]),
                        "add": int(parts[2]),
                        "del": int(parts[3]),
                    }

    repos_data = fetch_all_repos(username, headers)

    total_add = 0
    total_del = 0
    new_cache_lines = []

    for repo in repos_data:
        name = repo["nameWithOwner"]
        hashed_name = hashlib.sha256(name.encode("utf-8")).hexdigest()
        curr_commits = (
            repo["defaultBranchRef"]["target"]["history"]["totalCount"]
            if repo["defaultBranchRef"]
            else 0
        )

        r_add = 0
        r_del = 0

        if (
            hashed_name in cached_repos
            and cached_repos[hashed_name]["commits"] == curr_commits
        ):
            r_add = cached_repos[hashed_name]["add"]
            r_del = cached_repos[hashed_name]["del"]
        else:
            if curr_commits > 0:
                print(f"Recalculating LOC for: {name}...")
                r_add, r_del = fetch_repo_loc(name, user_id, headers)

        total_add += r_add
        total_del += r_del
        new_cache_lines.append(f"{hashed_name} {curr_commits} {r_add} {r_del}\n")

    with open(cache_file, "w") as f:
        f.writelines(new_cache_lines)

    return [total_add, total_del, total_add - total_del]


def fetch_all_repos(username, headers):
    """Fetches all repository names and commit counts using pagination."""
    repos = []
    cursor = None
    while True:
        query = """
        query($login: String!, $cursor: String) {
            user(login: $login) {
                repositories(first: 60, after: $cursor, ownerAffiliations: [OWNER, COLLABORATOR]) {
                    pageInfo { hasNextPage endCursor }
                    nodes {
                        nameWithOwner
                        defaultBranchRef {
                            target { ... on Commit { history { totalCount } } }
                        }
                    }
                }
            }
        }
        """
        data = run_query(query, {"login": username, "cursor": cursor}, headers)
        repos.extend(data["data"]["user"]["repositories"]["nodes"])
        if not data["data"]["user"]["repositories"]["pageInfo"]["hasNextPage"]:
            break
        cursor = data["data"]["user"]["repositories"]["pageInfo"]["endCursor"]
    return repos


def fetch_repo_loc(repo_name, user_id, headers):
    """Fetches additions and deletions for a specific user in a repository."""
    owner, name = repo_name.split("/")
    additions = 0
    deletions = 0
    cursor = None

    while True:
        query = """
        query($owner: String!, $name: String!, $cursor: String) {
            repository(owner: $owner, name: $name) {
                defaultBranchRef {
                    target {
                        ... on Commit {
                            history(first: 100, after: $cursor) {
                                pageInfo { hasNextPage endCursor }
                                nodes {
                                    author { user { id } }
                                    additions
                                    deletions
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        try:
            data = run_query(
                query, {"owner": owner, "name": name, "cursor": cursor}, headers
            )
            history = data["data"]["repository"]["defaultBranchRef"]["target"][
                "history"
            ]

            for commit in history["nodes"]:
                if (
                    commit["author"]["user"]
                    and commit["author"]["user"]["id"] == user_id
                ):
                    additions += commit["additions"]
                    deletions += commit["deletions"]

            if not history["pageInfo"]["hasNextPage"]:
                break
            cursor = history["pageInfo"]["endCursor"]
        except Exception:
            break

    return additions, deletions


def mock_stats():
    """Returns fallback values if the API call fails."""
    return {
        "repos": "??",
        "stars": "??",
        "commits": "??",
        "followers": "??",
        "loc_total": "0",
        "loc_add": "0++",
        "loc_del": "0--",
    }
