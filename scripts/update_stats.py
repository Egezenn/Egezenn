import urllib.request
import json
import re
import os

USERNAME = "Egezenn"
README_PATH = "readme.md"


def get_user_data(username):
    try:
        url = f"https://api.github.com/users/{username}"
        req = urllib.request.Request(url)
        if os.getenv("GITHUB_TOKEN"):
            req.add_header("Authorization", f"Bearer {os.getenv('GITHUB_TOKEN')}")
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching user data: {e}")
        return {}


def get_repos(username):
    repos = []
    page = 1
    while True:
        try:
            url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}"
            req = urllib.request.Request(url)
            if os.getenv("GITHUB_TOKEN"):
                req.add_header("Authorization", f"Bearer {os.getenv('GITHUB_TOKEN')}")
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                if not data:
                    break
                repos.extend(data)
                page += 1
        except Exception as e:
            print(f"Error fetching repos: {e}")
            break
    return repos


def update_readme(stats):
    try:
        with open(README_PATH, encoding="utf-8") as f:
            content = f.read()

        # Update Total Stars
        # Pattern: ![Total Stars](https://img.shields.io/badge/Total%20Stars-123-blue)
        content = re.sub(
            r"(!\[Total Stars\]\(https://img\.shields\.io/badge/Total%20Stars-)(\d+)(-blue\))",
            f"\\g<1>{stats['total_stars']}\\g<3>",
            content,
        )

        # Update Followers
        # Pattern: ![Followers](https://img.shields.io/badge/Followers-123-green)
        content = re.sub(
            r"(!\[Followers\]\(https://img\.shields\.io/badge/Followers-)(\d+)(-green\))",
            f"\\g<1>{stats['followers']}\\g<3>",
            content,
        )

        # Update Public Repos
        # Pattern: ![Public Repos](https://img.shields.io/badge/Public%20Repos-123-orange)
        content = re.sub(
            r"(!\[Public Repos\]\(https://img\.shields\.io/badge/Public%20Repos-)(\d+)(-orange\))",
            f"\\g<1>{stats['public_repos']}\\g<3>",
            content,
        )

        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print("Readme updated successfully.")
    except Exception as e:
        print(f"Error updating readme: {e}")


def main():
    user_data = get_user_data(USERNAME)
    repos = get_repos(USERNAME)

    if not user_data or not repos:
        print("Failed to fetch data.")
        return

    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    followers = user_data.get("followers", 0)
    public_repos = user_data.get("public_repos", 0)

    print(f"Total Stars: {total_stars}")
    print(f"Followers: {followers}")
    print(f"Public Repos: {public_repos}")

    update_readme({"total_stars": total_stars, "followers": followers, "public_repos": public_repos})


if __name__ == "__main__":
    main()
