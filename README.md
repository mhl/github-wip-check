*WARNING: treat this as alpha quality code - this was written
quickly and hasn't been used much by anyone yet*

# GitHub webhook handler for checking for WIP commits

It's often useful to create "WIP" (work-in-progress) commits
while you're working on a branch, with the intention of
rewriting the branch and commit messages later. Similarly,
"fixup!" and "squash!" commits (created by `git commit --fixup`
or `git commit --squash`) are useful to create are you're
working, but should always be squashed out before merging the
branch.

This little Flask app can be set up as a webhook handler that's
listening for changes to pull requests, and it will create a
GitHub status for the commit at the head of the pull request
that success if the PR would introduce no such WIP commits, or
fails it if finds any.

## Setup

This code should be run with the following two environment
variables set:

* `GITHUB_SECRET`: this value should be the same as the one you
  set in the webhook configuration on GitHub.
* `GITHUB_ACCESS_TOKEN`: this should be an access token that is
  allowed to create statuses for commits. If you want to set
  this up for a private repo, it will need the `repo` scope
  (which is very broad - it allows read and write access to the
  repository, so make sure you understand the implications). If
  you only want to use this for public repositories, however,
  the only scope that it needs is `repo:status`.  You can create
  personal access tokens at: https://github.com/settings/tokens
  (Bear in mind you might want to create a new GitHub user
  account with access to the minimal repositories you need to
  check, since personal access tokens will have access to every
  repository the user can see.)

When setting up the webhook in GitHub you should use the
following settings:

* Payload URL: this is the URL of wherever you're hosting this
  code. (Heroku works fine.)
* Content type: set this to `application/json`
* Secret: this should be the same as the value in the
  `GITHUB_SECRET` environment variable.
* Which events would you like to trigger the webhook? Select
  "Let me select individual events" and then make sure that only
  "Pull requests" is selected.

## Credits

The idea from this code is from Matthew Somerville, who set up a
Git hook to do the same check for mySociety's internal Git
repositories while I worked there.
