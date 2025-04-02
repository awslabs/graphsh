# GraphSh

GraphSh is an interactive terminal client for graph databases, inspired by the `psql` experience but designed specifically for graph query languages.

## Features

- Interactive shell for graph database queries
- Support for multiple query languages:
  - Gremlin (TinkerPop)
  - SPARQL 1.1
  - OpenCypher
- Compatible with:
  - Amazon Neptune
  - Amazon Neptune Analytics
  - Neo4j
  - Any TinkerPop-compliant database
- Authentication support:
  - AWS IAM for Neptune
  - Username/password for Neo4j
  - No authentication option for open endpoints
- Rich terminal features:
  - Command history
  - Tab completion
  - Syntax highlighting
  - Result formatting
- Connection profiles:
  - Save and reuse connection settings
  - Manage multiple database connections
  - Store language preferences with profiles

## Installation

```bash
# Install from PyPI
pip install graphsh

# Or install from source with pip
git clone https://github.com/awslabs/graphsh.git
cd graphsh
pip install -e .

# Or install from source with UV (recommended for faster installation)
git clone https://github.com/awslabs/graphsh.git
cd graphsh
uv venv
source .venv/bin/activate
uv pip install -e .

# Install with development dependencies
uv pip install -e ".[dev]"
```

## Quick Start

```bash
# Connect to Neptune with IAM auth
graphsh --endpoint https://neptune-instance.region.amazonaws.com:8182 --auth iam --type neptune

# Connect to Neptune Analytics with IAM auth
graphsh --graph-id my-graph-id --type neptune-analytics --region us-east-1

# Connect to Neo4j
graphsh --endpoint bolt://localhost:7687 --auth basic --username neo4j --password password --type neo4j

# Connect to an endpoint with no authentication
graphsh --endpoint https://localhost:8182 --auth none --type neptune --no-verify-ssl

# Connect using a saved profile
graphsh --profile my-neptune-profile

# Execute commands from a file
graphsh --commands-file commands.txt
```

## Interactive Shell Commands

Once in the interactive shell, you can use these special commands:

```
/help                   - Show help for commands
/help <command>         - Show detailed help for a specific command
/quit                   - Exit the shell
/language <lang>        - Switch query language (gremlin, sparql, cypher)
/connect <profile>      - Connect to a database using a saved profile
/connect --endpoint <url> [options] - Connect directly with connection parameters
/clear                  - Clear the screen
/timing on|off          - Toggle query execution timing
/format <format>        - Set output format (table, raw)
/preferences            - Show current user preferences
/preferences reset      - Reset preferences to defaults
/profile list           - List all saved connection profiles
/profile save <name>    - Save current connection as a profile
/profile delete <name>  - Delete a saved profile
/profile show <name>    - Show details of a saved profile
```

