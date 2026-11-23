#!/bin/sh
# Publish the current `main` on the local `github` branch as ONE new commit (its files, not its history):
# GitHub gets a short history of releases, while `main` keeps the full development history locally.
#
#   tools/publish_github.sh "Modern Sheet 0.36.0"     # make the commit (message optional)
#   git push origin github:main                        # then push it to GitHub's main
#
# The first run creates `github` with no parent; later runs add a commit on top of the previous one.
set -e
cd "$(git rev-parse --show-toplevel)"
if ! git diff --quiet HEAD -- || ! git diff --cached --quiet; then
    echo "There are uncommitted changes on $(git branch --show-current): commit them first." >&2
    exit 1
fi
version=$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)
msg=${1:-"Modern Sheet $version"}
tree=$(git rev-parse "main^{tree}")
if git rev-parse -q --verify refs/heads/github >/dev/null; then
    if [ "$(git rev-parse 'github^{tree}')" = "$tree" ]; then
        echo "Nothing to publish: github already has the files of main."
        exit 0
    fi
    commit=$(git commit-tree "$tree" -p github -m "$msg")
else
    commit=$(git commit-tree "$tree" -m "$msg")
fi
git update-ref refs/heads/github "$commit"
echo "github -> $(git log -1 --format='%h %s (%an <%ae>)' github)"
echo "Now: git push origin github:main"
