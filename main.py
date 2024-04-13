import os
import click
import requests
import logging
import json

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitLabProject:
    def __init__(self, project_data, save_directory):
        self.project_data = project_data
        self.save_directory = save_directory

    def check_settings(self):
        # Extract project settings
        merge_method = self.project_data.get('merge_method', None)
        merge_options = self.project_data.get('merge_options', [])
        squash_commits = self.project_data.get('squash', False)
        merge_checks = self.project_data.get('merge_checks_enabled', False)
        threads_resolved = self.project_data.get('only_allow_merge_if_all_discussions_are_resolved', False)
        pipelines_succeed = self.project_data.get('only_allow_merge_if_pipeline_succeeds', False)

        # Count settings
        count = sum([merge_method is not None, len(merge_options) > 0, squash_commits,
                    merge_checks, threads_resolved, pipelines_succeed])

        return count, merge_method, merge_options, squash_commits, merge_checks, threads_resolved, pipelines_succeed

    def save_json(self):
        project_id = self.project_data['id']
        full_path = self.project_data['namespace']['full_path']
        project_name = self.project_data['name'].replace('/', '-')
        file_path = os.path.join(self.save_directory, full_path, project_name, f"{project_id}.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as json_file:
            json.dump(self.project_data, json_file)


def collect_projects(group_id, access_token, include_archived=False):
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
        else:
            logger.error(f"Failed to retrieve projects from GitLab. Status code: {response.status_code}")
            break

    return projects


def count_settings(projects):
    # Initialize counts for settings
    total_count = 0
    merge_method_count = 0
    merge_options_count = 0
    squash_commits_count = 0
    merge_checks_count = 0
    threads_resolved_count = 0
    pipelines_succeed_count = 0
    skipped_pipelines_count = 0

    # Iterate over projects
    for project_data in projects:
        count, merge_method, merge_options, squash_commits, merge_checks, threads_resolved, pipelines_succeed = GitLabProject(
            project_data, '').check_settings()

        # Update counts
        total_count += count
        merge_method_count += 1 if merge_method else 0
        merge_options_count += len(merge_options)
        squash_commits_count += 1 if squash_commits else 0
        merge_checks_count += 1 if merge_checks else 0
        threads_resolved_count += 1 if threads_resolved else 0
        pipelines_succeed_count += 1 if pipelines_succeed else 0
        skipped_pipelines_count += 0 if project_data.get('skipped_ci_status', True) else 1

    return total_count, merge_method_count, merge_options_count, squash_commits_count, merge_checks_count, threads_resolved_count, pipelines_succeed_count, skipped_pipelines_count


@click.command()
@click.option('--group-id', prompt='Enter GitLab Group ID', help='GitLab Group ID to check')
@click.option('--token-file', default='~/.gitlab-settings-monitor/api_read', help='File containing GitLab API token')
@click.option('--include-archived', is_flag=True, help='Include archived projects')
def main(group_id, token_file, include_archived):
    token_file = os.path.expanduser(token_file)
    if not os.path.exists(token_file):
        raise FileNotFoundError(
            f"Token file '{token_file}' does not exist. Please create it at the specified location.")

    with open(token_file, 'r') as f:
        access_token = f.read().strip()

    projects_data = collect_projects(group_id, access_token, include_archived)
    logger.info(f"Total projects in group {group_id}: {len(projects_data)}")

    total_count, merge_method_count, merge_options_count, squash_commits_count, merge_checks_count, threads_resolved_count, pipelines_succeed_count, skipped_pipelines_count = count_settings(
        projects_data)

    logger.info(f"Total settings checked: {total_count}")
    logger.info(f"Merge method set: {merge_method_count}")
    logger.info(f"Merge options set: {merge_options_count}")
    logger.info(f"Squash commits enabled: {squash_commits_count}")
    logger.info(f"Merge checks enabled: {merge_checks_count}")
    logger.info(f"All threads resolved: {threads_resolved_count}")
    logger.info(f"Pipelines must succeed: {pipelines_succeed_count}")
    logger.info(f"Skipped pipelines considered successful: {skipped_pipelines_count}")

    # Print the summary to the console
    click.echo(f"Total projects in group {group_id}: {len(projects_data)}")
    click.echo(f"Total settings checked: {total_count}")
    click.echo(f"Merge method set: {merge_method_count}")
    click.echo(f"Merge options set: {merge_options_count}")
    click.echo(f"Squash commits enabled: {squash_commits_count}")
    click.echo(f"Merge checks enabled: {merge_checks_count}")
    click.echo(f"All threads resolved: {threads_resolved_count}")
    click.echo(f"Pipelines must succeed: {pipelines_succeed_count}")
    click.echo(f"Skipped pipelines considered successful: {skipped_pipelines_count}")


if __name__ == "__main__":
    main()
