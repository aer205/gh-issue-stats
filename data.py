from datetime import datetime, timezone, timedelta
import json
from typing import Iterable, Optional, Sequence, TypedDict

import os
import urllib.parse
import pandas
import requests
import tqdm
import github
from github.Repository import Repository
from github.Issue import Issue
from github.Commit import Commit

DEFAULT_OUTPUT = "out"
DEFAULT_INPUT = "in.json"

IssuesStats = TypedDict(
    "IssueStats",
    {
        "number": int,
        "created_at": datetime,
        "closed_at": datetime,
        "start_event": Optional[str],
        "started_at": Optional[datetime],
        "start_id": Optional[int],
        "finish_event": Optional[str],
        "finished_at": Optional[datetime],
        "finish_id": Optional[int],
        "state_reason": Optional[str],
        "is_pull": bool,
        "is_squash": bool,
    }
)
"""
The format used to represent issue statistics
"""

def issue_stats_from_api(
    repo: Repository,
    issue: Issue,
) -> IssuesStats | Exception:
    """
    Extract the statistics of `issue` from `repo` from the GitHub API.
    returns a dictionary whose format is defined by `IssueStats`
    """

    # Constants
    START_OF_WORK_EVENT_TYPES = {"connected", "assigned", "committed"}
    END_OF_WORK_EVENT_TYPES = {"closed", "convert_to_draft", "converted_to_discussion", "deployed", "marked_as_duplicate", "merged"}

    # Fields
    number = issue.number
    created_at = issue.created_at
    closed_at = issue.closed_at
    start_event = None
    started_at = None
    start_id = None
    finish_event = None
    finished_at = None
    finish_id = None
    state_reason = issue.state_reason
    is_pull = issue.pull_request() is not None
    is_squash = False

    try:
        # Extract first commit in this Issue is a Pull Request.
        if is_pull:
            pr = issue.as_pull_request()
            if pr.commits > 0:
                first_commit: Commit = pr.get_commits()[0]
                if pr.commits == 1 and len(first_commit.parents) == 1:
                    is_squash == True
                else:
                    start_event = "<commit>"
                    started_at = first_commit.commit.author.date
                    start_id = None # "<commit>" has no event-id
        
        timeline = [event for event in issue.get_timeline()]

        # Extract start-of-work.
        start_of_work = next((event for event in timeline if event.event in START_OF_WORK_EVENT_TYPES), None)

        if start_of_work is None:
            pass
        elif start_of_work.event == "committed":
            committed_date = repo.get_commit(start_of_work.url.split('/')[-1]).commit.author.date

            # Only register "committed" as start-of-work if it is not preceded by "<commit>"
            if committed_date <= started_at:
                start_event = "committed"
                started_at = committed_date
                start_id = None # "committed" has no event-id
        else:
            start_event = start_of_work.event
            started_at = start_of_work.created_at
            start_id = start_of_work.id

        # Extract end-of-work.
        end_of_work = next((event for event in reversed(timeline) if event.event in START_OF_WORK_EVENT_TYPES - {"closed"}), None)

        if end_of_work is None:
            end_of_work = next((event for event in reversed(timeline) if event.event in {"closed"}), None)

        if end_of_work is not None:
            finish_event = end_of_work.event
            finished_at = end_of_work.created_at
            finish_id = end_of_work.id

        return {
            "number": number,
            "created_at": created_at,
            "closed_at": closed_at,
            "start_event": start_event,
            "started_at": started_at,
            "start_id": start_id,
            "finish_event": finish_event,
            "finished_at": finished_at,
            "finish_id": finish_id,
            "state_reason": state_reason,
            "is_pull": is_pull,
            "is_squash": is_squash,
        }
    except Exception as e:
        return e


RepositoryStats = TypedDict(
    "RepositoryStats",
    {
        "url": str,
        "issues": Optional[Sequence[IssuesStats]]
    }
)
"""
The format used to represent repository statistics
"""



def repository_stats_from_api(
    api: github.Github,
    url: str,
    last_created: timedelta = timedelta(days=int(365 * 1.5)), # 1.5 years
    last_closed: timedelta = timedelta(days=365), # 1 year
    show_progress: bool = True
) -> RepositoryStats | Exception:
    """
    Extract the statistics of `issue` from `repo` from the GitHub API.
    The `api` parameters is used to perform the API calls.
    `last_created` and `last_closed` are used to specify the maximum time passed since the creation and closure of the issue respectively.
    If `show_progress == True`, a loading bar will be shown. 
    """
    if last_created > last_closed:
        raise ValueError("`last_created` must be less than `last_closed`")

    # Get the Repository
    owner, name = urllib.parse.urlparse(url).path.strip("/").split("/")[-2:]
    now = datetime.now(timezone.utc())
    created_since = now - last_created
    closed_since = now - last_closed

    try:
        if show_progress:
            print(f"Extracting statistics from {url}...")

        repo = api.get_repo(f"{owner}/{name}")
        issuestats = [
            issue_stats_from_api(...)
            for issue
            in (tqdm.tqdm(repo.get_issues(since=created_since)) if show_progress else repo.get_issues(since=created_since))
            if (
                (issue.state == "closed" and issue.closed_at) and # Must be closed
                issue.created_at >= created_since and # Must be created within the last `last_created` days
                issue.closed_at >= closed_since # Must be closed within the last `last_created` days
            )
        ]

        if show_progress:
            print(f"Done with {url}!")

        return {
            "url": url,
            "issues": issuestats
        }
    except Exception as e:
        return e

def save_to_files(
    stats: Sequence[RepositoryStats],
    output: str = DEFAULT_OUTPUT
) -> None:
    for repo in stats:
        owner, name = urllib.parse.urlparse(repo["url"]).path.strip("/").split("/")[-2:]
        issues = repo["issues"]

        os.makedirs(f"{output}/{owner}/{name}", exist_ok=True)
        os.makedirs(f"{output}/{owner}/{name}/issues", exist_ok=True)

        if issues is None:
            continue

        for issue in issues:
            with open(f"{output}/{owner}/{name}/issues/{issue["number"]}.json", "w") as issue_json:
                json.dump(issue, issue_json)

def load_from_files(
    directory: str = DEFAULT_OUTPUT
) -> Sequence[RepositoryStats]:
    stats = []
    for owner_dir in os.scandir(directory):
        owner = owner_dir.name
        name = None
        issues = []

        for name_dir in os.scandir(f"{directory}/{owner}"):
            name = name_dir.name

            for issue_file in os.scandir(f"{directory}/{owner}/{name}/issues"):
                fd = open(issue_file.path)
                issues.append(json.load(fd))

        stats.append({
            "url": f"https://github.com/{owner}/{name}",
            "issues": issues
        })

def commits_in_last_n_days(
    url: str,
    api_token: str,
    n: int = 90,
) -> int:
    """
    Extraction the # of commits made in the last `n` days in the repository references by the GitHub `url`.
    `return 0` for Repository which could not be found (because they are, for example, deleted or private).
    `api_token` is the Personnal Access Token used to perform the API calls.
    """
    owner, name = urllib.parse.urlparse(url).path.strip("/").split("/")[-2:]


    get_url = f"https://api.github.com/repos/{owner}/{name}/commits"
    
    get_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"token {api_token}"
    }

    get_parameters = {
        "since": (datetime.now(timezone.utc) - timedelta(days=n)).isoformat() + "Z",
        "per_page": 1
    }

    response = requests.get(url=get_url, params=get_parameters, headers=get_headers)
    
    if response.status_code not in range(200, 299):
        return 0
    
    ncommits = len(response.json())
    last = response.links.get("last")

    if last:
        query = urllib.parse.urlparse(last["url"]).query
        ncommits = int(dict(urllib.parse.parse_qsl(query))["page"])

    return ncommits

def active_sample(
    urls: Iterable[str],
    api_token: str,
    n: int = 40,
    show_progress: bool = True
) -> pandas.DataFrame:
    """
    Create a selection of `n` most active GitHub repositories below the 90th-percentile in number of commits in the last 90 days,
    within the GitHub repositories in `urls`.
    Discards any repository which has no commits before doing this selection.
    `api_token` is the Personnal Access Token used to perform the API calls.
    If `show_progress == True`, then a loading bar will shown.
    """
    df = pandas.DataFrame({
        "url": list(urls),
        "last90": [commits_in_last_n_days(url, api_token) for url in (tqdm.tqdm(urls) if show_progress else urls)]
    })

    df = df[df.last90 != 0]
    df = df[df.last90 < df.last90.quantile(0.9)]
    df = df[-n:]
    return df
    


if __name__ == "__main__":
    exit(0)