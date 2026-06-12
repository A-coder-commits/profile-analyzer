"""
GitHub profile scraper using the GitHub REST API.

Fetches public repositories, README files, language stats, and
aggregates everything into a structured dictionary ready for
chunking and embedding.
"""

from __future__ import annotations

import re
from typing import Any

import httpx

from core.config import GITHUB_TOKEN

# ── Constants ────────────────────────────────────────────────────────────────

_API_BASE = "https://api.github.com"
_TOP_REPOS_FOR_README = 5
_REQUEST_TIMEOUT = 30.0


def _headers() -> dict[str, str]:
    """Build request headers, including auth token if available."""
    h: dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def _extract_username(github_url: str) -> str:
    """
    Extract a GitHub username from a URL or plain username string.

    Handles formats like:
      - https://github.com/torvalds
      - github.com/torvalds
      - torvalds

    Raises:
        ValueError: If the input cannot be parsed into a valid username.
    """
    github_url = github_url.strip().rstrip("/")

    # Full URL
    match = re.match(r"(?:https?://)?github\.com/([A-Za-z0-9\-_]+)", github_url)
    if match:
        return match.group(1)

    # Bare username (no slashes, no dots)
    if re.match(r"^[A-Za-z0-9\-_]+$", github_url):
        return github_url

    raise ValueError(
        f"Cannot extract GitHub username from: '{github_url}'. "
        "Please provide a valid GitHub URL or username."
    )


async def scrape_github_profile(github_url: str) -> dict[str, Any]:
    """
    Scrape a GitHub user's public profile data.

    Args:
        github_url: GitHub profile URL or plain username.

    Returns:
        A dictionary containing:
        - username: str
        - bio: str | None
        - total_repos: int
        - repos: list of repo dicts (name, description, language, stars, forks, last_updated)
        - top_languages: dict mapping language → count
        - readmes: dict mapping repo_name → readme text (for top repos)

    Raises:
        httpx.HTTPStatusError: On non-2xx GitHub API responses.
        ValueError: If the username cannot be parsed.
    """
    username = _extract_username(github_url)

    async with httpx.AsyncClient(
        base_url=_API_BASE,
        headers=_headers(),
        timeout=_REQUEST_TIMEOUT,
    ) as client:
        # 1. Fetch user profile
        user_resp = await client.get(f"/users/{username}")
        user_resp.raise_for_status()
        user_data = user_resp.json()

        # 2. Fetch all public repos (paginated, up to 100)
        repos_resp = await client.get(
            f"/users/{username}/repos",
            params={"type": "owner", "sort": "updated", "per_page": 100},
        )
        repos_resp.raise_for_status()
        repos_raw: list[dict] = repos_resp.json()

        # 3. Parse repos
        repos = []
        language_counts: dict[str, int] = {}
        for repo in repos_raw:
            if repo.get("fork"):
                continue  # skip forks

            lang = repo.get("language")
            repos.append(
                {
                    "name": repo["name"],
                    "description": repo.get("description") or "",
                    "language": lang,
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "last_updated": repo.get("updated_at", ""),
                }
            )
            if lang:
                language_counts[lang] = language_counts.get(lang, 0) + 1

        # Sort by stars descending
        repos.sort(key=lambda r: r["stars"], reverse=True)

        # Sort languages by frequency
        top_languages = dict(
            sorted(language_counts.items(), key=lambda kv: kv[1], reverse=True)
        )

        # 4. Fetch READMEs for top repos
        top_repos = repos[:_TOP_REPOS_FOR_README]
        readmes: dict[str, str] = {}
        for repo_info in top_repos:
            readme_text = await _fetch_readme(client, username, repo_info["name"])
            if readme_text:
                readmes[repo_info["name"]] = readme_text

    return {
        "username": username,
        "bio": user_data.get("bio"),
        "total_repos": len(repos),
        "repos": repos,
        "top_languages": top_languages,
        "readmes": readmes,
    }


async def _fetch_readme(
    client: httpx.AsyncClient,
    username: str,
    repo_name: str,
) -> str | None:
    """
    Fetch the decoded README content for a repository.

    Returns None if the README doesn't exist or can't be fetched.
    """
    try:
        resp = await client.get(
            f"/repos/{username}/{repo_name}/readme",
            headers={"Accept": "application/vnd.github.v3.raw"},
        )
        if resp.status_code == 200:
            # Truncate very long READMEs to ~4000 chars
            text = resp.text
            return text[:4000] if len(text) > 4000 else text
    except httpx.HTTPError:
        pass
    return None


def format_github_data_for_embedding(profile_data: dict[str, Any]) -> list[str]:
    """
    Convert the scraped GitHub profile data into text documents
    suitable for chunking and embedding.

    Produces several documents:
    1. A profile overview document
    2. One document per repository
    3. One document per README

    Args:
        profile_data: The dict returned by scrape_github_profile().

    Returns:
        A list of text strings, each representing one document.
    """
    documents: list[str] = []

    # Profile overview
    overview_lines = [
        f"GitHub Profile: {profile_data['username']}",
        f"Bio: {profile_data.get('bio') or 'N/A'}",
        f"Total Original Repositories: {profile_data['total_repos']}",
        "",
        "Top Languages by Repository Count:",
    ]
    for lang, count in profile_data.get("top_languages", {}).items():
        overview_lines.append(f"  - {lang}: {count} repos")
    documents.append("\n".join(overview_lines))

    # Per-repo documents
    for repo in profile_data.get("repos", []):
        repo_doc = (
            f"Repository: {repo['name']}\n"
            f"Description: {repo['description'] or 'No description'}\n"
            f"Primary Language: {repo['language'] or 'Not specified'}\n"
            f"Stars: {repo['stars']} | Forks: {repo['forks']}\n"
            f"Last Updated: {repo['last_updated']}"
        )
        documents.append(repo_doc)

    # README documents
    for repo_name, readme_text in profile_data.get("readmes", {}).items():
        documents.append(
            f"README for repository '{repo_name}':\n\n{readme_text}"
        )

    return documents
