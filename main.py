import os
import click
import requests
import logging
import json
import csv
from datetime import datetime
import glob
import pandas as pd


def get_project_settings(id: int, access_token: str) -> []:
    projects = []

    url = f"https://gitlab.com/api/v4/projects/{id}"
    headers = {"PRIVATE-TOKEN": access_token}
    params = {"per_page": 100, "page": 1}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to retrieve projects: {response.status_code} - {response.text}")
        return None


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


def write_to_file(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)


def write_to_csv(data, filename):
    keys = data.keys()
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)


def read_csv_and_count_values(filename, column_names):
    counts = {name: {} for name in column_names}
    total_counts = {name: 0 for name in column_names}

    with open(filename, 'r', newline='') as file:
        reader = csv.DictReader(file)
        total_rows = 0

        for row in reader:
            total_rows += 1
            for column in column_names:
                value = row[column]
                if value not in counts[column]:
                    counts[column][value] = 1
                else:
                    counts[column][value] += 1
                total_counts[column] += 1

    percentages = {}
    for column, value_counts in counts.items():
        percentages[column] = {value: (count / total_counts[column]) * 100 for value, count in value_counts.items()}

    return counts, total_counts, percentages, total_rows


def get_protected_branches(project_id, access_token):
    url = f"https://gitlab.com/api/v4/projects/{project_id}/protected_branches"
    headers = {"PRIVATE-TOKEN": access_token}
    response = requests.get(url, headers=headers)
    return response.json()


def get_approvals(project_id, access_token):
    url = f"https://gitlab.com/api/v4/projects/{project_id}/approvals"
    headers = {"PRIVATE-TOKEN": access_token}
    response = requests.get(url, headers=headers)
    return response.json()


def count_project_settings(filename) -> []:
    column_names = [
        "allow_merge_on_skipped_pipeline",
        "default_branch",
        "merge_method",
        "only_allow_merge_if_all_discussions_are_resolved",
        "only_allow_merge_if_pipeline_succeeds",
        "remove_source_branch_after_merge",
        "squash_option",
    ]
    rows = count(column_names, filename)
    return rows


def count_project_protected_branches_settings(filename) -> []:
    column_names = [
        "code_owner_approval_required",
        "name",
        "merge_access_levels",
        "allow_force_push",
        "push_access_levels",
    ]
    rows = count(column_names, filename)
    return rows


def count_project_approvals_settings(filename) -> []:
    column_names = [
        "approvers",
        "approver_groups",
        "approvals_before_merge",
        "reset_approvals_on_push",
        "selective_code_owner_removals",
        "disable_overriding_approvers_per_merge_request",
        "merge_requests_author_approval",
        "merge_requests_disable_committers_approval",
    ]
    rows = count(column_names, filename)
    return rows


def count(column_names: [], filename: str) -> []:
    rows = []
    counts, total_counts, percentages, total_rows = read_csv_and_count_values(filename, column_names)
    for column, value_counts in counts.items():
        logging.debug(f"Counts for {column}:")
        for value, count in value_counts.items():
            percentage = percentages[column][value]
            logging.debug(f"  {value}: {count} ({percentage:.2f}%)")

            row = {
                "setting": column,
                "value": value,
                "count": count,
                "percentage": percentage
            }
            rows.append(row)

        logging.debug(f"Total {column} count: {total_counts[column]}")
        logging.debug(
            f"Percentage of {column} values in total rows: {(total_counts[column] / total_rows) * 100:.2f}%\n")

    return rows


def write_project_settings_to_csv(access_token: str, projectID: int) -> str:
    filename = f"gitlab_project_settings.csv"
    project_setting = get_project_settings(projectID, access_token)
    write_to_csv(project_setting, filename)
    return filename


def write_project_protected_branches_settings_to_csv(access_token: str, projectID: int) -> str:
    filename = f"gitlab_project_protected_branches_settings.csv"
    protected_branches = get_protected_branches(projectID, access_token)
    for protected_branch in protected_branches:
        key_to_remove = 'id'
        if key_to_remove in protected_branch:
            del protected_branch[key_to_remove]

        for level in protected_branch['push_access_levels']:
            del level['id']

        for level in protected_branch['merge_access_levels']:
            del level['id']

        write_to_csv(protected_branch, filename)
    return filename


def write_project_approvals_settings_to_csv(access_token: str, projectID: int) -> str:
    filename = f"gitlab_project_approvals_settings.csv"
    approvals = get_approvals(projectID, access_token)
    write_to_csv(approvals, filename)
    return filename


def add_rows_with_empty_total_and_percentage(filename: str):
    existing_df = pd.read_csv(filename)
    empty_list_count = existing_df.applymap(lambda x: isinstance(x, list) and len(x) == 0
                                            or isinstance(x, int) and x == 0
                                            or x == '[]').sum()
    column_counts = existing_df.count()
    empty_list_percentage = (empty_list_count / column_counts) * 100
    summary_df = pd.concat([empty_list_count, empty_list_percentage], axis=1, keys=['Count', 'Percentage']).transpose()
    existing_df = pd.concat([existing_df, summary_df])
    existing_df.to_csv(filename, index=False)


def write_rows_to_csv(rows: []) -> []:
    data_frame_rows = []
    for row in rows:
        row_df1 = pd.DataFrame([row])
        data_frame_rows.append(row_df1)
    return data_frame_rows


def write_csv_report(access_token: str, group_id: str, projects: []):
    project_settings_file, project_protected_branches_settings_file, project_approvals_settings_file = "", "", ""
    logging.info(f"Total projects in group {group_id}: {len(projects)}")
    for project in projects:
        projectID = project['id']
        project_settings_file = write_project_settings_to_csv(access_token, projectID)
        project_protected_branches_settings_file = write_project_protected_branches_settings_to_csv(
            access_token, projectID)
        project_approvals_settings_file = write_project_approvals_settings_to_csv(access_token, projectID)
    results = [
        count_project_settings(project_settings_file),
        count_project_protected_branches_settings(project_protected_branches_settings_file),
        count_project_approvals_settings(project_approvals_settings_file)
    ]
    data_frame_rows = []
    for result in results:
        data_frame_rows.extend(write_rows_to_csv(result))
    combined_df = pd.concat(data_frame_rows, ignore_index=True)
    combined_df.to_csv("report.csv", index=False)


@click.command()
@click.option('--group-id', prompt='Enter GitLab Group ID', help='GitLab Group ID to check')
@click.option('--archived-only', is_flag=True, help='Only archived projects')
@click.option('--logging-level', default="INFO", help='Set the logging level')
@click.option('--token-file', default='~/.gitlab-settings-metrics/api_read', help='File containing GitLab API token')
def main(group_id, archived_only, logging_level, token_file):
    configure_logging(logging_level)
    access_token = read_access_token(token_file)
    projects = get_projects(group_id, access_token, archived_only)
    write_csv_report(access_token, group_id, projects)


if __name__ == "__main__":
    main()
