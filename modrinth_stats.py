"""Fetch public Modrinth user/project statistics without Discord credentials."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_ROOT = "https://api.modrinth.com/v2"
USER_AGENT = "MimikzuScripts/1.0 (public Modrinth stats CLI)"
TIMEOUT_SECONDS = 12


class ModrinthError(RuntimeError):
    """Raised when the public Modrinth API request fails."""


def fetch_json(path: str) -> Any:
    if not path.startswith("/"):
        raise ValueError("API path must start with '/'.")
    request = urllib.request.Request(
        API_ROOT + path,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise ModrinthError("Modrinth user or project was not found.") from error
        if error.code == 429:
            raise ModrinthError("Modrinth rate limit reached. Wait a bit and retry.") from error
        raise ModrinthError(f"Modrinth returned HTTP {error.code}.") from error
    except urllib.error.URLError as error:
        raise ModrinthError(f"Could not reach Modrinth: {error.reason}") from error
    except json.JSONDecodeError as error:
        raise ModrinthError("Modrinth returned invalid JSON.") from error


def user_stats(username: str) -> dict[str, Any]:
    if not username.strip():
        raise ValueError("Username cannot be empty.")
    encoded = urllib.parse.quote(username.strip(), safe="")
    user = fetch_json(f"/user/{encoded}")
    projects = fetch_json(f"/user/{encoded}/projects")
    if not isinstance(projects, list):
        raise ModrinthError("Modrinth returned an unexpected projects response.")

    ordered = sorted(
        projects,
        key=lambda project: int(project.get("downloads") or 0),
        reverse=True,
    )
    return {
        "username": user.get("username", username),
        "project_count": len(projects),
        "total_downloads": sum(int(project.get("downloads") or 0) for project in projects),
        "total_followers": sum(int(project.get("followers") or 0) for project in projects),
        "projects": [
            {
                "title": project.get("title") or "Untitled",
                "slug": project.get("slug"),
                "project_type": project.get("project_type"),
                "downloads": int(project.get("downloads") or 0),
                "followers": int(project.get("followers") or 0),
                "url": (
                    "https://modrinth.com/"
                    + str(project.get("project_type") or "project")
                    + "/"
                    + str(project.get("slug") or project.get("id") or "")
                ),
            }
            for project in ordered
        ],
        "source": "Public Modrinth API; no Discord login or API token used.",
    }


def project_stats(project_id_or_slug: str) -> dict[str, Any]:
    if not project_id_or_slug.strip():
        raise ValueError("Project id or slug cannot be empty.")
    encoded = urllib.parse.quote(project_id_or_slug.strip(), safe="")
    project = fetch_json(f"/project/{encoded}")
    return {
        "title": project.get("title") or "Untitled",
        "slug": project.get("slug"),
        "project_type": project.get("project_type"),
        "downloads": int(project.get("downloads") or 0),
        "followers": int(project.get("followers") or 0),
        "updated": project.get("updated"),
        "url": (
            "https://modrinth.com/"
            + str(project.get("project_type") or "project")
            + "/"
            + str(project.get("slug") or project.get("id") or "")
        ),
        "source": "Public Modrinth API; no Discord login or API token used.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--user", help="Modrinth username.")
    mode.add_argument("--project", help="Modrinth project id or slug.")
    parser.add_argument("--output", help="Optional path to save the JSON report.")
    args = parser.parse_args(argv)
    try:
        result = user_stats(args.user) if args.user else project_stats(args.project)
    except (ModrinthError, ValueError) as error:
        parser.error(str(error))
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as file:
                file.write(rendered + "\n")
        except OSError as error:
            parser.error(f"Could not write output: {error}")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
