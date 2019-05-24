#!/usr/bin/env python3

from flask import Flask, request, jsonify
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import requests
import sys

if "GITHUB_ACCESS_TOKEN" in os.environ:
    access_token = os.environ["GITHUB_ACCESS_TOKEN"]
else:
    access_token = (
        (Path(__file__).resolve().parent / "access-token").read_text().rstrip()
    )

standard_headers = {
    "User-Agent": "github-wip-commit-checker/1.0",
    "Authorization": f"bearer {access_token}",
}

app = Flask(__name__)


def check_signature(request):
    if "GITHUB_SECRET" not in os.environ:
        raise Exception("No GITHUB_SECRET was set in the environment")
    signature = request.headers.get("X-Hub-Signature")
    if not signature:
        raise Exception("GitHub didn't send a signagure in X-Hub-Signature")
    mac = hmac.new(
        os.environb[b"GITHUB_SECRET"], msg=request.get_data(), digestmod=hashlib.sha1
    )
    if not hmac.compare_digest("sha1=" + mac.hexdigest(), signature):
        raise Exception("The signature didn't match the data in the payload")


@app.route("/", methods=["GET"])
def hello():
    return "Hello, world!"


@app.route("/", methods=["POST"])
def handle_webhook():
    try:
        check_signature(request)
    except Exception as e:
        return jsonify({"msg": str(e)})
    event = request.headers.get("X-GitHub-Event")
    if event == "ping":
        return "pong"
    elif event == "pull_request":
        payload = request.get_json()
        action = payload["action"]
        if action not in ("opened", "edited", "synchronize"):
            return f"This webhook doesn't handle {action} requests"
        pull_request = payload["pull_request"]
        base = pull_request["base"]["sha"]
        head = pull_request["head"]["sha"]
        repo = pull_request["head"]["repo"]["full_name"]
        return check_commits_and_create_status(repo, base, head)
    else:
        return f"Unknown event: {event}"


def check_commits_and_create_status(repo, base, head):
    url = f"https://api.github.com/repos/{repo}/compare/{base}...{head}"

    r = requests.get(url, headers=standard_headers)
    r.raise_for_status()

    bad_message_patterns = [
        {"re": re.compile(r"^fixup!"), "name": "fixup!"},
        {"re": re.compile(r"^squash!"), "name": "squash!"},
        {"re": re.compile(r"\bwip\b"), "name": "WIP"},
    ]

    all_bad_message_names = [d["name"] for d in bad_message_patterns]

    problems_found = set()

    for commit in r.json()["commits"]:
        message = commit["commit"]["message"]
        for b in bad_message_patterns:
            if b["re"].search(message):
                problems_found.add(b["name"])

    def join_commas(seq, conjuction):
        if not seq:
            return ""
        l = list(seq)
        if len(l) == 1:
            return l[0]
        return "{} {} {}".format(", ".join(l[:-1]), conjuction, l[-1])

    if problems_found:
        state = "failure"
        description = "Failed because we found one or more {} commits. Please rewrite this branch before merging!".format(
            join_commas(problems_found, "or")
        )
    else:
        state = "success"
        description = "No {} commits found!".format(
            join_commas(all_bad_message_names, "or")
        )

    r = requests.post(
        f"https://api.github.com/repos/{repo}/statuses/{head}",
        data=json.dumps(
            {"state": state, "description": description, "context": "kiln: WIP check"}
        ),
        headers=standard_headers,
    )
    r.raise_for_status()
    return f"Created a status of '{state}' with description '{description}'"
