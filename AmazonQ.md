# Amazon Q Development Guidelines

Always follow these guidelines when assisting in development for the Amazon Q CLI.

## AmazonQ.md

DO NOT create or modify an AmazonQ.md file unless I explicitly tell you to do so.

## Overview
GraphSh is an interactive terminal client for graph databases that supports multiple query languages (Gremlin, SPARQL, and OpenCypher) and is compatible with various graph databases including Amazon Neptune and Neo4j.

## Design Docs
Both high level and code base summary are present under docs/ folder. These docs can be used to gain more
understanding of the project and how various modules interact with each other. Always look at this before starting
on a task.

## Python Best Practices

### Project Management
This project uses ```uv``` for managing the project.
1. Dependencies can be added to project such as ```uv add pytest```
2. Tools can be invoked such as ```uv run pytest```

## Verification

BEFORE reporting task is complete, ALWAYS do the following steps:

1. First, run `uv run ruff format` to auto-format the code.
2. Then Run `uv run pytest -v` to run all tests with verbose output and fix any failing tests. 

## Git

### Committing Changes

Follow the git best practice of committing early and often. Run `git commit` often, but DO NOT ever run `git push`

BEFORE committing a change, ALWAYS run the verification steps mentioned above.

### Commit Messages

All commit messages should follow the [Conventional Commits](https://www.conventionalcommits.org/) specification and include best practices:

```
<type>[optional scope]: <description>

Assisted by [Amazon Q Developer](https://aws.amazon.com/q/developer)
```

Types:
- feat: A new feature
- fix: A bug fix
- docs: Documentation only changes
- style: Changes that do not affect the meaning of the code
- refactor: A code change that neither fixes a bug nor adds a feature
- perf: A code change that improves performance
- test: Adding missing tests or correcting existing tests
- chore: Changes to the build process or auxiliary tools
- ci: Changes to CI configuration files and scripts

Best practices:
- Use the imperative mood ("add" not "added" or "adds")
- Don't end the subject line with a period
- Limit the subject line to 50 characters
- Capitalize the subject line
- Separate subject from body with a blank line

Example:
```
feat(lambda): Add Go implementation of DDB stream forwarder

Assisted by [Amazon Q Developer](https://aws.amazon.com/q/developer)
```
