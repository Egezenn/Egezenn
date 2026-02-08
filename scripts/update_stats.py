import json
import os
import re
import urllib.request


def fetch_github_api(url, method="GET", data=None, headers=None):
    try:
        req = urllib.request.Request(url, method=method, data=data)
        if os.getenv("GITHUB_TOKEN"):
            req.add_header("Authorization", f"Bearer {os.getenv('GITHUB_TOKEN')}")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)

        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode()), response.getheader("Link")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None, None


def get_user_data(username):
    data, _ = fetch_github_api(f"https://api.github.com/users/{username}")
    return data or {}


def get_repos(username):
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}"
        data, _ = fetch_github_api(url)
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos


def get_commit_count(username):
    headers = {"Accept": "application/vnd.github.cloak-preview"}
    data, _ = fetch_github_api(f"https://api.github.com/search/commits?q=author:{username}", headers=headers)
    return data.get("total_count", 0) if data else 0


def get_issue_count(username, is_pr=False):
    kind = "pr" if is_pr else "issue"
    data, _ = fetch_github_api(f"https://api.github.com/search/issues?q=author:{username}+is:{kind}")
    return data.get("total_count", 0) if data else 0


def get_top_language(username):
    query = """
    query($login: String!) {
      user(login: $login) {
        repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
          nodes {
            name
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node {
                  name
                  color
                }
              }
            }
          }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"login": username}}).encode("utf-8")
    data, _ = fetch_github_api("https://api.github.com/graphql", method="POST", data=payload)

    if not data:
        return {}, {}

    repos = data.get("data", {}).get("user", {}).get("repositories", {}).get("nodes", [])
    lang_stats = {}
    lang_colors = {}

    for repo in repos:
        languages = repo.get("languages", {}).get("edges", [])
        for edge in languages:
            size = edge.get("size", 0)
            node = edge.get("node", {})
            name = node.get("name")
            color = node.get("color")

            if name:
                lang_stats[name] = lang_stats.get(name, 0) + size
                if color:
                    lang_colors[name] = color

    return lang_stats, lang_colors


def get_repo_details(username, repo_name):
    data, _ = fetch_github_api(f"https://api.github.com/repos/{username}/{repo_name}")
    return data or {}


def get_release_downloads(username, repo_name):
    releases = []
    url = f"https://api.github.com/repos/{username}/{repo_name}/releases?per_page=100"

    while url:
        data, link_header = fetch_github_api(url)
        if not data:
            break
        releases.extend(data)

        url = None
        if link_header:
            match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
            if match:
                url = match.group(1)

    total_downloads = 0
    for release in releases:
        for asset in release.get("assets", []):
            total_downloads += asset.get("download_count", 0)
    return total_downloads


def create_list_svg(items, filename, col_widths=(130, 110)):
    row_height = 28
    gap_y = 5
    padding = 10
    cols = 1
    rows = len(items)

    w_label_col, w_value_col = col_widths
    total_col_width = w_label_col + w_value_col

    width = (cols * total_col_width) + (padding * 2)
    height = (rows * row_height) + ((rows - 1) * gap_y) + (padding * 2)

    svg_content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
    )
    svg_content += f'<rect width="{width}" height="{height}" fill="#1a1b27" rx="5" ry="5"/>\n'

    for i, (label, value, color) in enumerate(items):
        row = i
        y = padding + (row * (row_height + gap_y))
        x = padding

        label = str(label).upper()
        value = str(value).upper()

        w_label = w_label_col
        w_value = w_value_col

        x_label_center = x + (w_label / 2)
        x_value_center = x + w_label + (w_value / 2)

        svg_content += f"""
  <g shape-rendering="crispEdges">
    <rect x="{x}" y="{y}" width="{w_label}" height="{row_height}" fill="#555"/>
    <rect x="{x + w_label}" y="{y}" width="{w_value}" height="{row_height}" fill="{color}"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">
    <text x="{x_label_center}" y="{y+19}" transform="scale(1)" fill="#fff" font-size="11">{label}</text>
    <text x="{x_value_center}" y="{y+19}" transform="scale(1)" fill="#fff" font-weight="bold" font-size="11">{value}</text>
  </g>
"""
    svg_content += "</svg>"

    try:
        filepath = f"assets/{filename}.svg"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Generated badge: {filename}")
        return filepath
    except Exception as e:
        print(f"Error generating badge {filename}: {e}")
        return None


def create_overview_badge(stats, filename):
    items = [
        ("Total Commits", stats.get("total_commits", 0), "#6f42c1"),
        ("Total Stars", stats.get("total_stars", 0), "#007ec6"),
        ("Total PRs", stats.get("total_prs", 0), "#dfb317"),
        ("Total Issues", stats.get("total_issues", 0), "#e05d44"),
        ("Public Repos", stats.get("public_repos", 0), "#fe7d37"),
        ("Followers", stats.get("followers", 0), "#97ca00"),
    ]
    create_list_svg(items, filename, col_widths=(104, 56))


def create_project_badge(username, repo_name, filename, col_widths=(90, 108)):
    details = get_repo_details(username, repo_name)
    if not details:
        return None

    display_name = repo_name
    if len(display_name) > 14:
        display_name = display_name[:17] + "..."

    items = [
        ("Repo", display_name, "#555"),
        ("Stars", details.get("stargazers_count", 0), "#007ec6"),
        ("Forks", details.get("forks_count", 0), "#6f42c1"),
        ("Language", details.get("language", "Unknown") or "Unknown", "#dfb317"),
        ("Downloads", get_release_downloads(username, repo_name), "#2ea44f"),
        ("License", details.get("license", {}).get("spdx_id", "None") if details.get("license") else "None", "#fe7d37"),
    ]
    create_list_svg(items, filename, col_widths=col_widths)


def create_language_badge(lang_stats, lang_colors, filename):
    if not lang_stats:
        return None

    total_size = sum(lang_stats.values())
    if total_size == 0:
        return None

    sorted_langs = sorted(lang_stats.items(), key=lambda item: item[1], reverse=True)
    width = 300
    bar_height = 10
    legend_item_height = 20
    padding = 10

    legend_items = []
    for lang, size in sorted_langs:
        percentage = (size / total_size) * 100
        if percentage < 1:
            continue
        color = lang_colors.get(lang, "#555")
        legend_items.append((lang, percentage, color))

    height = padding + bar_height + padding + (len(legend_items) * legend_item_height) + padding

    svg_content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
    )
    svg_content += f'<rect width="{width}" height="{height}" fill="#1a1b27" rx="5" ry="5"/>\n'

    current_x = padding
    bar_width = width - (padding * 2)
    y_pos = padding

    for _, percentage, color in legend_items:
        section_width = (percentage / 100) * bar_width
        svg_content += (
            f'<rect x="{current_x}" y="{y_pos}" width="{section_width}" height="{bar_height}" fill="{color}"/>\n'
        )
        current_x += section_width

    y_pos += bar_height + padding
    font_style = 'font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="12" fill="#fff"'

    for lang, percentage, color in legend_items:
        svg_content += f'<circle cx="{padding + 5}" cy="{y_pos + 6}" r="5" fill="{color}"/>\n'
        text = f"{lang} ({percentage:.1f}%)"
        svg_content += f'<text x="{padding + 15}" y="{y_pos + 10}" {font_style}>{text}</text>\n'
        y_pos += legend_item_height

    svg_content += "</svg>"

    try:
        filepath = f"assets/{filename}.svg"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Generated badge: {filename}")
        return filepath
    except Exception as e:
        print(f"Error generating badge {filename}: {e}")
        return None


def main():
    username = "Egezenn"
    user_data = get_user_data(username)
    repos = get_repos(username)

    if not user_data or not repos:
        print("Failed to fetch data.")
        return

    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    followers = user_data.get("followers", 0)
    public_repos = user_data.get("public_repos", 0)

    total_commits = get_commit_count(username)
    total_prs = get_issue_count(username, is_pr=True)
    total_issues = get_issue_count(username, is_pr=False)
    top_lang, top_json = get_top_language(username)

    stats = {
        "total_stars": total_stars,
        "followers": followers,
        "public_repos": public_repos,
        "total_commits": total_commits,
        "total_prs": total_prs,
        "total_issues": total_issues,
        "lang_stats": top_lang,
        "lang_colors": top_json,
    }

    create_overview_badge(stats, "overview")
    create_language_badge(top_lang, top_json, "languages")

    projects = [
        ("dota2-minify", "dota2-minify", (90, 108)),
        ("OpenDotaGuides", "OpenDotaGuides", (90, 120)),
        ("YTMASC", "YTMASC", (90, 108)),
        ("Miscellaneous-scripts-and-such", "Miscellaneous-scripts-and-such", (90, 150)),
    ]

    for repo_name, safe_name, col_widths in projects:
        filename_base = f"project_{safe_name}"
        create_project_badge(username, repo_name, filename_base, col_widths)

    print("All badges generated successfully.")


if __name__ == "__main__":
    main()
