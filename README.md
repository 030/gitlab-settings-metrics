# gitlab-settings-monitor

Program created using ChatGPT 3.5 using the following input:

- python
- classes
- check how the following settings look like for a GitLab project: merge
  method, merge options, squash commits when merging, merge checks, all threads
  must be resolved
- count
- main method
- read api token should be read from a file that resides in the home folder in
  a separate folder called .gitlab-settings-monitor
- error handling
- use the gitlab api instead of a gitlab pip package
- use the native python logger
- if the file does not exist then an exception should be thrown that that file
  does not exist and it should indicate where to find it
- name of the file that contains the read token should be:
  ~/.gitlab-settings-monitor/api_read
- all projects in a certain GitLab group should be checked
- it should be possible to pass arguments to the program using click library
- the tool should indicate how many projects reside in the group and also the
  count of the other settings that have been mentioned earlier
- do not add comments in the code
- the tool should also find the projects in the subgroups
- NameError: name 'logger' is not defined
- why do you put the "# Configure logger" comment then?
- save each project json in a local directory
- create the dir as well and it should be identical to the gilab structure so
  that means if group/subgroup/project then it should be saved like that
- NameError: name 'json' is not defined
- the structure of the directory is incorrect. The group should be first and
  only three subgroups have been saved. Where are all other projects?
- KeyError: 'children'
- there should be more than 20 projects
- omit the archived projects. Add a parameter and omit archived repos by default
- the structure of the output dir should be: the name of the group then a dir with the subgroup name and then the project name that contains the json
- output/<group-name>/<subgroup-name>/<project-name>/<id>.json
- why do you add the group-name as a suffix to the subgroup? I do not want that. I only want the group-name and then the subgroup should be the name of the folder that resides in the group
- listen. If group is a and subgroup is b why do you not store the file in output/a/b?
- should the count not happen in a separate function
- check the value of merge check "Pipelines must succeed"

| key                                              | value   |
| ------------------------------------------------ | ------- |
| allow_merge_on_skipped_pipeline                  | false   |
| merge_method                                     | merge   |
| only_allow_merge_if_pipeline_succeeds            | true    |
| only_allow_merge_if_all_discussions_are_resolved | true    |
| squash_option                                    | require |

## config

- create a ~/.gitlab-settings-monitor folder
- create a `read_api` token and store it in

## usage

```bash
pip3 install -r requirements.txt
python3 main.py --group-id 7659975
```

## usage

```bash
7891460
```
