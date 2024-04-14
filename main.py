import os
import click
import requests
import logging
import json


class GitLabProject:
    def __init__(self, project_data, save_directory):
        self.project_data = project_data
        self.save_directory = save_directory

    def check_settings(self, access_token):
        # Extract project settings
        merge_method = self.project_data.get('merge_method', None)
        merge_options = self.project_data.get('merge_options', [])
        squash_commits = self.project_data.get('squash', False)
        merge_checks = self.project_data.get('merge_checks_enabled', False)
        threads_resolved = self.project_data.get('resolved_all_discussions', False)
        pipelines_succeed = self.project_data.get('only_allow_merge_if_pipeline_succeeds', False)
        # protected_branches_enabled, allowed_to_merge, allowed_to_push, allow_force_push, _ = self.check_protected_branches(
        #     access_token)

        # Count settings
        count = sum([merge_method is not None, len(merge_options) > 0, squash_commits,
                    merge_checks, threads_resolved, pipelines_succeed])

        return count, merge_method, merge_options, squash_commits, merge_checks, threads_resolved, pipelines_succeed

    def check_protected_branches_settings(self, access_token) -> dict:
        project_id = self.project_data['id']
        protected_branches_url = f"https://gitlab.com/api/v4/projects/{project_id}/protected_branches"
        allowed_to_merge = []
        allowed_to_push = []
        allow_force_push = []
        protected_branches_data = []

        params = {"private_token": access_token}
        response = requests.get(protected_branches_url, params=params)
        if response.status_code == 200:
            protected_branches_data = response.json()
            logging.debug(f"protected_branches_data: {protected_branches_data}")
            protected_branches_enabled = len(protected_branches_data) > 0
            for branch_data in protected_branches_data:
                if branch_data.get('allowed_to_merge', {}).get('users', []) or branch_data.get('allowed_to_merge', {}).get('groups', []):
                    allowed_to_merge.append(branch_data['name'])
                if branch_data.get('allowed_to_push', {}).get('users', []) or branch_data.get('allowed_to_push', {}).get('groups', []):
                    allowed_to_push.append(branch_data['name'])
                if not branch_data.get('allow_force_push', False):
                    allow_force_push.append(branch_data['name'])
        else:
            logger.error(
                f"Failed to fetch protected branches for project '{self.project_data.get('path_with_namespace')}'. Status code: {response.status_code}")
            protected_branches_enabled = False

        settings = {
            'protected_branches_enabled': protected_branches_enabled,
            'allowed_to_merge': allowed_to_merge,
            'allowed_to_push': allowed_to_push,
            'allow_force_push': allow_force_push,
            'protected_branches_data': protected_branches_data,
        }
        logging.info(f"protected_branches_enabled: {settings['protected_branches_enabled']}")

        protected_branches = settings['protected_branches_data']
        for protected_branch in protected_branches:
            # logging.info(f"protected_branch: {protected_branch}")
            logging.info(f"protected_branch_id: {protected_branch['id']}")
            logging.info(f"protected_branch_name: {protected_branch['name']}")
            logging.info(f"protected_branch_merge_access_levels: {protected_branch['merge_access_levels']}")
            logging.info(f"protected_branch_push_access_levels: {protected_branch['push_access_levels']}")
            logging.info(f"protected_branch_allow_force_push: {protected_branch['allow_force_push']}")
            # for key, value in protected_branch.items():
            #     logging.info(key, value)
        #
        # logging.info(f"allowed_to_merge: {settings['allowed_to_merge']}")
        # logging.info(f"protected_branches_data: {settings['protected_branches_data']}")

        return settings

    def save_json(self):
        project_id = self.project_data['id']
        full_path = self.project_data['namespace']['full_path']
        project_name = self.project_data['name'].replace('/', '-')
        file_path = os.path.join(self.save_directory, "output", full_path, project_name, f"{project_id}.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as json_file:
            json.dump(self.project_data, json_file)

    def save_protected_branches_json(self, protected_branches_data):
        project_id = self.project_data['id']
        full_path = self.project_data['namespace']['full_path']
        project_name = self.project_data['name'].replace('/', '-')
        file_path = os.path.join(self.save_directory, "output", full_path,
                                 project_name, f"{project_id}_protected_branches.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as json_file:
            json.dump(protected_branches_data, json_file)


def collect_projects(group_id, access_token, include_archived=False) -> []:
    projects = []

    url = f"https://gitlab.com/api/v4/groups/{group_id}/projects"
    params = {"private_token": access_token, "include_subgroups": True, "per_page": 100, "page": 1}

    while True:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            projects_data = response.json()
            if not projects_data:
                break
            if not include_archived:
                projects_data = [project for project in projects_data if not project['archived']]
            projects.extend(projects_data)
            params["page"] += 1
            logging.info(f"Total projects in group {group_id}: {len(projects_data)}")
        else:
            logger.error(f"Failed to retrieve projects from GitLab. Status code: {response.status_code}")
            break
    return projects


def count_settings(projects: [], access_token: str) -> dict:
    total_count = 0
    merge_method_count = 0
    merge_options_count = 0
    squash_commits_count = 0
    merge_checks_count = 0
    threads_resolved_count = 0
    pipelines_succeed_count = 0
    protected_branches_count = 0
    skipped_pipelines_count = 0

    for project_data in projects:
        project = GitLabProject(project_data, '')
        # for generating and storing test data on disk
        # project.save_json()
        protected_branches_settings = project.check_protected_branches_settings(access_token)
        # for generating and storing test data on disk
        # project.save_protected_branches_json(protected_branches_settings)
        count, merge_method, merge_options, squash_commits, merge_checks, threads_resolved, pipelines_succeed = project.check_settings(
            access_token)
        merge_method_count += 1 if merge_method else 0
        merge_options_count += len(merge_options)
        squash_commits_count += 1 if squash_commits else 0
        merge_checks_count += 1 if merge_checks else 0
        threads_resolved_count += 1 if threads_resolved else 0
        pipelines_succeed_count += 1 if pipelines_succeed else 0
        # protected_branches_count += 1 if protected_branches_enabled else 0
        skipped_pipelines_count += 0 if project_data.get('skipped_ci_status', True) else 1

    settings = {
        'merge_method_count': merge_method_count,
        'merge_options_count': merge_options_count,
        'squash_commits_count': squash_commits_count,
        'merge_checks_count': merge_checks_count,
        'threads_resolved_count': threads_resolved_count,
        "pipelines_succeed_count": pipelines_succeed_count,
        'protected_branches_count': protected_branches_count,
        'skipped_pipelines_count': skipped_pipelines_count
    }
    logging.info(f"settings: {settings['pipelines_succeed_count']}")

    return settings


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
@click.option('--include-archived', is_flag=True, help='Include archived projects')
@click.option('--logging-level', default="INFO", help='Set the logging level')
@click.option('--token-file', default='~/.gitlab-settings-monitor/api_read', help='File containing GitLab API token')
def main(group_id, include_archived, logging_level, token_file, ):
    configure_logging(logging_level)
    access_token = read_access_token(token_file)
    projects_data = collect_projects(group_id, access_token, include_archived)
    settings = count_settings(projects_data, access_token)

    # logger.info(f"Total settings checked: {total_count}")
    # logger.info(f"Merge method set: {merge_method_count}")
    # logger.info(f"Merge options set: {merge_options_count}")
    # logger.info(f"Squash commits enabled: {squash_commits_count}")
    # logger.info(f"Merge checks enabled: {merge_checks_count}")
    # logger.info(f"All threads resolved: {threads_resolved_count}")
    # logger.info(f"Pipelines must succeed: {pipelines_succeed_count}")
    # logger.info(f"Protected branches enabled: {protected_branches_count}")
    # logger.info(f"Skipped pipelines considered successful: {skipped_pipelines_count}")

    # # Print the summary to the console
    # click.echo(f"Total projects in group {group_id}: {len(projects_data)}")
    # click.echo(f"Total settings checked: {total_count}")
    # click.echo(f"Merge method set: {merge_method_count}")
    # click.echo(f"Merge options set: {merge_options_count}")
    # click.echo(f"Squash commits enabled: {squash_commits_count}")
    # click.echo(f"Merge checks enabled: {merge_checks_count}")
    # click.echo(f"All threads resolved: {threads_resolved_count}")
    # click.echo(f"Pipelines must succeed: {pipelines_succeed_count}")
    # click.echo(f"Protected branches enabled: {protected_branches_count}")
    # click.echo(f"Skipped pipelines considered successful: {skipped_pipelines_count}")


if __name__ == "__main__":
    main()
