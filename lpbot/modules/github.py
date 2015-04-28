# -*- coding: utf-8 -*-

# Copyright 2015 Nikola Kovacevic <nikolak@outlook.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests
import re

from lpbot import tools
from lpbot.module import rule


github_pull = r'https?://(?:www\.)?github.com/([A-z0-9\-]+/[A-z0-9\-]+)/(?:pull)/([\d]+)'
github_issue = r'https?://(?:www\.)?github.com/([A-z0-9\-]+/[A-z0-9\-]+)/(?:issues)/([\d]+)'
pull_regex = re.compile(github_pull)
issue_regex = re.compile(github_issue)


def setup(bot):
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.lpbotMemory()

    bot.memory['url_callbacks'][github_pull] = get_pull_info
    bot.memory['url_callbacks'][github_issue] = get_issue_info


def shutdown(bot):
    del bot.memory['url_callbacks'][github_pull]
    del bot.memory['url_callbacks'][github_issue]


@rule('.*%s.*' % github_pull)
def get_pull_info(bot, trigger, match=None):
    match = match or trigger
    username, repo = match.group(1).split('/')
    pull_id = match.group(2)

    pull_api = "https://api.github.com/repos/{user}/{repo}/pulls/{pull}"
    pull_endpoint = pull_api.format(user=username,
                                    repo=repo,
                                    pull=pull_id)

    r = requests.get(pull_endpoint)
    if r.status_code != 200:
        if r.status_code == 404:
            bot.say("Pull request not found.")
        else:
            bot.say("HTTP request failed, HTTP status: {}".format(r.status_code))
        return

    pull_data = r.json()

    output = "\x02'{owner}/{repo}'\x02 pull request #{pull_id}: \x02'{title}'\x02" \
             " by '{author}' | [\x02State: {state}\x02] [Merged: " \
             "{merged} (Mergeable: {mergeable})]:  | {head} --> {base} | " \
             "{commits} commits with {additions} additions and {deletions} " \
             "deletions in {files} files."

    resp_values = {
        'owner': username,
        'repo': repo,
        'pull_id': pull_id,
        'state': pull_data['state'],
        'merged': pull_data['merged'],
        'mergeable': pull_data['mergeable'] or "N/A",
        'title': pull_data['title'],
        'author': pull_data['user']['login'],
        'head': pull_data['head']['label'],
        'base': pull_data['base']['label'],
        'commits': pull_data['commits'],
        'additions': pull_data['additions'],
        'deletions': pull_data['deletions'],
        'files': pull_data['changed_files']
    }

    bot.say(output.format(**resp_values))


@rule('.*%s.*' % github_issue)
def get_issue_info(bot, trigger, match=None):
    match = match or trigger
    username, repo = match.group(1).split('/')
    issue_id = match.group(2)

    issue_api = "https://api.github.com/repos/{user}/{repo}/issues/{issue}"
    issue_endpoint = issue_api.format(user=username,
                                      repo=repo,
                                      issue=issue_id)

    r = requests.get(issue_endpoint)
    if r.status_code != 200:
        if r.status_code == 404:
            bot.say("Issue page not found.")
        else:
            bot.say("HTTP request failed, HTTP status: {}".format(r.status_code))
        return

    issue_data = r.json()

    resp_values = {
        'owner': username,
        'repo': repo,
        'issue_id': issue_id,
        'state': issue_data['state'],
        'title': issue_data['title'],
        'author': issue_data['user']['login']
    }

    output = "'\x02{owner}/{repo}'\x02 issue [#{issue_id}] [\x02State: {state}\x02]: " \
             "'{title}' Opened by: {author} "

    if issue_data.get("assignee"):
        output += "| \x02Assigned to:\x02 {assignee}"
        resp_values['assignee'] = issue_data['assignee']['login']

    if issue_data.get('closed_by'):
        output += "| \x02Closed by:\x02 {closed_by} "
        resp_values['closed_by'] = issue_data['closed_by']['login']

    if issue_data.get('labels'):
        output += "| \x02Labels:\x02 {labels}"

        labels_list = issue_data['labels']
        labels_names = [label['name'] for label in labels_list]

        resp_values['labels'] = ",".join(labels_names[:3])

    if issue_data.get("body"):
        output += " | \x02Description:\x02 {body}"
        resp_values['body'] = issue_data['body']

    bot.say(output.format(**resp_values))