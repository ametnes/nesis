# Contribution Guide

Thanks for your interest in contributing to the Github Repository.

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change. 

Please note we have a code of conduct, please follow it in all your interactions with the project.

Here is how you get the code working locally.:
    1. Fork the repository

    ```bash
    git clone git@github.com:<your_github_name>/nesis.git
    cd nesis
    git remote add upstream https://github.com/ametnes/nesis.git
    git remote -v
    ```
    2. Fetch commits

    ```bash
    git fetch origin
    git fetch upstream
    ```
    3. Create branch to ensure you have a referral point from main

    ```bash
    git checkout -b <my_new_branch> origin/main
    ```
    4. Work on your changes

## Coding Style

    1. Write clear code.
    2. Comment on your changes.
    3. Add unit tests for your changes.

## Testing

Add clear unit tests for your changes.

## Submitting your changes

When you are ready to submit a pull request, commit your changes.
The commit should be: <type>(<module>): the change in lower chase. Here type can be feat, chore, fix and module can be frontend, docs, api, rag. e.g(git commit -m "(fix(docs): add contribution.md)")

    ```bash
    git status
    git add <your_file_name>   \\for each file changed
    git commit -m "Your commit message"
    git push origin <my_new_branch>
    ```
Create a PR with these guidelines

### PR Titles

    1. Title the PR using `<type>(<module>): the change in lower chase`. Here `type` can be `feat`, `chore`, `fix` and `module` can be `frontend`, `docs`, `api`, `rag`.
    2. Describe the change in no more than two lines.


### Merging your PR

Sometimes reviewers commit to your pull request. Before making any other changes, fetch those commits.
Fetch commits from your remote fork and rebase your working branch:

    ```bash
    git fetch origin
    git rebase origin/<your-branch-name>
    git push --force-with-lease origin <your-branch-name>
    ```

If another contributor commits changes to the same file in another PR, it can create a merge conflict. You must resolve all merge conflicts in your PR.

Update your fork and rebase your local branch:

    ```bash
    git fetch origin
    git rebase origin/<your-branch-name>
    git push --force-with-lease origin <your-branch-name>
    ```
If necessary, update the README.md with details of your changes, this includes new environment 
variables, exposed ports, useful file locations and container parameters.
You may merge the Pull Request in once you have the sign-off of two other developers, or if you 
do not have permission to do that, you may request the second reviewer to merge it for you.
