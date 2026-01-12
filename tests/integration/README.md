# Integration Tests

Integration tests for GraphSh with Docker-based Neo4j and AWS-deployed Neptune.

## Structure

```
tests/integration/
├── conftest.py          # Fixtures with auto-deploy
├── stack_manager.py     # CloudFormation stack management (Neptune)
├── infra/               # CloudFormation templates
│   ├── neptune.yaml
│   └── neptune-analytics.yaml
├── neo4j/               # Neo4j tests (Docker)
├── neptune/             # Neptune tests (AWS)
└── common/              # Database-agnostic tests
```

## Running Tests

### Neo4j (Docker-based)

```bash
# Runs automatically - starts/stops Docker container
uv run pytest tests/integration/neo4j/ -v

# Keep container running after tests
KEEP_CONTAINERS=1 uv run pytest tests/integration/neo4j/ -v

# Use existing Neo4j instance
NEO4J_HOST=localhost NEO4J_PORT=7687 uv run pytest tests/integration/neo4j/ -v
```

### Neptune (AWS CloudFormation)

Requires AWS credentials with permissions to create Neptune clusters, VPCs, and security groups.

```bash
# Auto-deploys Neptune stack, runs tests, tears down
AWS_PROFILE=myprofile AWS_REGION=us-east-1 uv run pytest tests/integration/neptune/ -v

# Keep stack running after tests (useful for debugging)
AWS_PROFILE=myprofile AWS_REGION=us-east-1 KEEP_STACKS=1 uv run pytest tests/integration/neptune/ -v

# Use existing Neptune endpoint
NEPTUNE_HOST=my-cluster.region.neptune.amazonaws.com uv run pytest tests/integration/neptune/ -v
```

### Neptune Analytics (AWS CloudFormation)

Requires AWS credentials with permissions to create Neptune Analytics graphs.

```bash
# Auto-deploys Neptune Analytics graph, runs tests, tears down
AWS_PROFILE=myprofile AWS_REGION=us-east-1 uv run pytest tests/integration/neptune_analytics/ -v

# Keep graph running after tests
AWS_PROFILE=myprofile AWS_REGION=us-east-1 KEEP_STACKS=1 uv run pytest tests/integration/neptune_analytics/ -v

# Use existing graph
NEPTUNE_ANALYTICS_GRAPH_ID=g-abc123 uv run pytest tests/integration/neptune_analytics/ -v
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_HOST` | Neo4j hostname | (starts Docker) |
| `NEO4J_PORT` | Neo4j port | 7687 |
| `NEO4J_USER` | Neo4j username | neo4j |
| `NEO4J_PASSWORD` | Neo4j password | testpassword |
| `KEEP_CONTAINERS` | Don't stop Docker containers | - |
| `NEPTUNE_HOST` | Neptune hostname | (deploys stack) |
| `NEPTUNE_PORT` | Neptune port | 8192 |
| `NEPTUNE_ANALYTICS_GRAPH_ID` | Neptune Analytics graph ID | (deploys stack) |
| `AWS_REGION` | AWS region for deployment | us-east-1 |
| `KEEP_STACKS` | Don't teardown AWS stacks | - |
