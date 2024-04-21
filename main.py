import os
import click
import requests
import logging
import json


def get_projects(group_id: int, access_token: str, archived_only: bool) -> []:
    projects = []

    url = f"https://gitlab.com/api/v4/groups/{group_id}/projects"
    headers = {"PRIVATE-TOKEN": access_token}
    params = {"include_subgroups": True, "per_page": 100, "page": 1, "archived": archived_only}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to retrieve projects: {response.status_code} - {response.text}")
        return None


def configure_logging(logging_level: str):
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def read_access_token(token_file: str) -> str:
    logging.debug(f"trying to read access token from: '{token_file}'")
    access_token = ""
    token_file = os.path.expanduser(token_file)
    if not os.path.exists(token_file):
        raise FileNotFoundError(
            f"The API token file '{token_file}' does not exist. Please create it at the specified location.")
    with open(token_file, 'r') as f:
        access_token = f.read().strip()
    return access_token


@click.command()
@click.option('--group-id', prompt='Enter GitLab Group ID', help='GitLab Group ID to check')
@click.option('--archived-only', is_flag=True, help='Only archived projects')
@click.option('--logging-level', default="INFO", help='Set the logging level')
@click.option('--token-file', default='~/.gitlab-settings-metrics/api_read', help='File containing GitLab API token')
def main(group_id, archived_only, logging_level, token_file, ):
    configure_logging(logging_level)
    access_token = read_access_token(token_file)
    projects = get_projects(group_id, access_token, archived_only)

    logging.info(f"Total projects in group {group_id}: {len(projects)}")
    for project in projects:
        print(f"Project: {project['name']}, ID: {project['id']}")


if __name__ == "__main__":
    main()
