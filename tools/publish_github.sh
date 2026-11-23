#!/bin/sh
# Publish the current `main` on the local `github` branch as ONE new commit (its files, not its history):
# GitHub gets a short history of releases, while `main` keeps the full development history locally.
#
#   tools/publish_github.sh "Modern Sheet 0.36.0"     # make the commit (message optional) and the tag v<version>
#   git push origin github:main v0.36.0                # push both: the tag starts the desktop builds (Release)
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
tag="v$version"
if git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
    echo "Tag $tag already exists (bump the version to make a new release): pushing without it"
    echo "Now: git push origin github:main"
else
    git tag -a "$tag" -m "Modern Sheet $version" github
    echo "Tag $tag on github"
    echo "Now: git push origin github:main $tag      (the tag builds the apps for macOS, Windows, Linux)"
fi
