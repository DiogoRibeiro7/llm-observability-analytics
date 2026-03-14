from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

GITHUB_API = "https://api.github.com/graphql"


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def gql(token: str, query: str, variables: dict[str, object]) -> dict[str, object]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(GITHUB_API, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/vnd.github+json")

    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GraphQL request failed: HTTP {exc.code} {body}") from exc

    data = json.loads(raw)
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data["data"]


def resolve_project_id(token: str, owner: str, number: int) -> str:
    user_query = """
    query($owner: String!, $number: Int!) {
      user(login: $owner) {
        projectV2(number: $number) { id }
      }
    }
    """
    user_data = gql(token, user_query, {"owner": owner, "number": number})
    user_project = (user_data.get("user") or {}).get("projectV2")
    if user_project and user_project.get("id"):
        return str(user_project["id"])

    org_query = """
    query($owner: String!, $number: Int!) {
      organization(login: $owner) {
        projectV2(number: $number) { id }
      }
    }
    """
    org_data = gql(token, org_query, {"owner": owner, "number": number})
    org_project = (org_data.get("organization") or {}).get("projectV2")
    if org_project and org_project.get("id"):
        return str(org_project["id"])
    raise RuntimeError(f"Could not resolve ProjectV2 id for owner='{owner}', number={number}.")


def resolve_status_field_and_options(
    token: str,
    project_id: str,
    field_name: str,
    open_option_name: str,
    closed_option_name: str,
) -> tuple[str, str, str]:
    query = """
    query($projectId: ID!, $cursor: String) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 50, after: $cursor) {
            nodes {
              ... on ProjectV2SingleSelectField {
                id
                name
                options { id name }
              }
            }
            pageInfo { hasNextPage endCursor }
          }
        }
      }
    }
    """

    target_field: dict[str, object] | None = None
    cursor: str | None = None
    while True:
        data = gql(token, query, {"projectId": project_id, "cursor": cursor})
        node = data["node"]
        page = node["fields"]
        for field in page["nodes"]:
            if field and field.get("name") == field_name:
                target_field = field
                break
        if target_field:
            break
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    if not target_field:
        raise RuntimeError(f"Project field '{field_name}' was not found.")

    options = target_field.get("options", [])
    open_option_id: str | None = None
    closed_option_id: str | None = None
    for option in options:
        option_name = option.get("name")
        if option_name == open_option_name:
            open_option_id = option.get("id")
        if option_name == closed_option_name:
            closed_option_id = option.get("id")

    if not open_option_id:
        raise RuntimeError(
            f"Status option '{open_option_name}' not found in field '{field_name}'."
        )
    if not closed_option_id:
        raise RuntimeError(
            f"Status option '{closed_option_name}' not found in field '{field_name}'."
        )

    return str(target_field["id"]), str(open_option_id), str(closed_option_id)


def list_repo_issues(token: str, owner: str, name: str) -> list[dict[str, str]]:
    query = """
    query($owner: String!, $name: String!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        issues(first: 100, after: $cursor, states: [OPEN, CLOSED]) {
          nodes { id number state }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
    """

    issues: list[dict[str, str]] = []
    cursor: str | None = None
    while True:
        data = gql(token, query, {"owner": owner, "name": name, "cursor": cursor})
        repo = data["repository"]
        page = repo["issues"]
        for node in page["nodes"]:
            issues.append({"id": node["id"], "state": node["state"], "number": str(node["number"])})
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    return issues


def list_project_items_for_repo(
    token: str,
    project_id: str,
    target_repo: str,
) -> dict[str, str]:
    query = """
    query($projectId: ID!, $cursor: String) {
      node(id: $projectId) {
        ... on ProjectV2 {
          items(first: 100, after: $cursor) {
            nodes {
              id
              content {
                ... on Issue {
                  id
                  repository { nameWithOwner }
                }
              }
            }
            pageInfo { hasNextPage endCursor }
          }
        }
      }
    }
    """

    mapping: dict[str, str] = {}
    cursor: str | None = None
    while True:
        data = gql(token, query, {"projectId": project_id, "cursor": cursor})
        node = data["node"]
        page = node["items"]
        for item in page["nodes"]:
            content = item.get("content")
            if not content:
                continue
            repo = content.get("repository", {}).get("nameWithOwner")
            if repo != target_repo:
                continue
            issue_id = content.get("id")
            if issue_id:
                mapping[issue_id] = item["id"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    return mapping


def add_item_to_project(token: str, project_id: str, issue_id: str) -> str:
    mutation = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item { id }
      }
    }
    """
    data = gql(token, mutation, {"projectId": project_id, "contentId": issue_id})
    return data["addProjectV2ItemById"]["item"]["id"]


def update_status_field(
    token: str,
    project_id: str,
    item_id: str,
    field_id: str,
    option_id: str,
) -> None:
    mutation = """
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
      updateProjectV2ItemFieldValue(
        input: {
          projectId: $projectId,
          itemId: $itemId,
          fieldId: $fieldId,
          value: { singleSelectOptionId: $optionId }
        }
      ) {
        projectV2Item { id }
      }
    }
    """
    gql(
        token,
        mutation,
        {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "optionId": option_id,
        },
    )


def main() -> int:
    token = require_env("GITHUB_TOKEN")
    repository = require_env("GITHUB_REPOSITORY")

    owner, name = repository.split("/", 1)
    project_id = optional_env("PROJECT_V2_ID")
    if not project_id:
        project_owner = optional_env("PROJECT_OWNER") or owner
        project_number_raw = require_env("PROJECT_NUMBER")
        try:
            project_number = int(project_number_raw)
        except ValueError as exc:
            raise RuntimeError(f"PROJECT_NUMBER must be an integer, got: {project_number_raw}") from exc
        project_id = resolve_project_id(token, project_owner, project_number)

    status_field_id = optional_env("PROJECT_STATUS_FIELD_ID")
    status_open_option_id = optional_env("PROJECT_STATUS_OPEN_OPTION_ID")
    status_closed_option_id = optional_env("PROJECT_STATUS_CLOSED_OPTION_ID")
    if not (status_field_id and status_open_option_id and status_closed_option_id):
        status_field_name = optional_env("PROJECT_STATUS_FIELD_NAME") or "Status"
        status_open_option_name = optional_env("PROJECT_STATUS_OPEN_OPTION_NAME") or "Todo"
        status_closed_option_name = optional_env("PROJECT_STATUS_CLOSED_OPTION_NAME") or "Done"
        status_field_id, status_open_option_id, status_closed_option_id = (
            resolve_status_field_and_options(
                token,
                project_id,
                status_field_name,
                status_open_option_name,
                status_closed_option_name,
            )
        )

    issues = list_repo_issues(token, owner, name)
    if not issues:
        print("No issues found. Nothing to sync.")
        return 0

    project_items = list_project_items_for_repo(token, project_id, repository)

    added = 0
    updated = 0
    for issue in issues:
        issue_id = issue["id"]
        item_id = project_items.get(issue_id)
        if not item_id:
            item_id = add_item_to_project(token, project_id, issue_id)
            project_items[issue_id] = item_id
            added += 1

        option_id = status_open_option_id if issue["state"] == "OPEN" else status_closed_option_id
        update_status_field(token, project_id, item_id, status_field_id, option_id)
        updated += 1

    print(f"Sync complete for {repository}: issues={len(issues)} added={added} updated={updated}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}")
        raise
