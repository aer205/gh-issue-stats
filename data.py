import datetime
import urllib.parse
import requests


def get_ncommits_in_last_n_days(
    url: str,
    token: str,
    n: int = 90,
) -> int:
    owner, name = urllib.parse.urlparse(url).path.strip("/").split("/")[-2:]


    get_url = f"https://api.github.com/repos/{owner}/{name}/commits"
    
    get_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"token {token}"
    }

    get_parameters = {
        "since": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=n)).isoformat() + "Z",
        "per_page": 1
    }

    response = requests.get(url=get_url, params=get_parameters, headers=get_headers)
    
    if response.status_code not in range(200, 299):
        raise Exception(f"GitHub API failure: {response.content}")
    
    ncommits = len(response.json())
    last = response.links.get("last")

    if last:
        query = urllib.parse.urlparse(last["url"]).query
        ncommits = int(dict(urllib.parse.parse_qsl(query))["page"])

    return ncommits

if __name__ == "__main__":
    exit(0)