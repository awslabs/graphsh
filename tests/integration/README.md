# Integration Tests for GraphSh

This directory contains integration tests for GraphSh that test the application's interaction with actual graph databases.

## Test Setup

### Prerequisites

- Docker installed and running
- Python 3.9+ with pytest

### Database Containers

The integration tests use Docker containers to run the necessary graph databases:

1. **TinkerPop Gremlin Server**
   ```bash
   docker run -d --name tinkerpop-server -p 8182:8182 tinkerpop/gremlin-server:latest
   ```

2. **Neptune (Local Development Version)**
   ```bash
   docker run -d --name neptune-test --shm-size=16g -p 8182:8182 neptune-test
   ```
   Note: The Neptune container requires more resources and may not be available in all environments.

3. **Neo4j**
   ```bash
   docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
   ```

## Running Tests

### All Tests

```bash
cd tests
python -m pytest integration/
```

### Specific Database Tests

```bash
# TinkerPop Gremlin Server tests
python -m pytest integration/test_gremlin_server.py

# Neptune tests
python -m pytest integration/test_neptune.py

# Neo4j tests
python -m pytest integration/test_neo4j.py
```

## Test Configuration

The tests use environment variables to configure database connections:

- **Gremlin Server / Neptune**:
  - `NEPTUNE_HOST`: Hostname (default: localhost)
  - `NEPTUNE_PORT`: Port (default: 8182)

- **Neo4j**:
  - `NEO4J_HOST`: Hostname (default: localhost)
  - `NEO4J_PORT`: Port (default: 7687)
  - `NEO4J_USER`: Username (default: neo4j)
  - `NEO4J_PASSWORD`: Password (default: password)

## Test Structure

Each test file follows a similar pattern:

1. A fixture that sets up the database connection and test data
2. Test functions that verify different aspects of the GraphSh functionality

## Known Issues

- SSL certificate verification issues with Neptune may require disabling SSL verification in tests
- Connection timeouts may occur if the database containers are not fully initialized
- The tests use `pytest.skip()` to handle cases where the database is not available
- When using HTTPS with Neptune, make sure to use the hostname only (not the protocol) in the endpoint parameter

## Adding New Tests

When adding new tests:

1. Create a new test file in the `integration/` directory
2. Use the existing test files as templates
3. Create a fixture that sets up the necessary database connection and test data
4. Write test functions that verify the functionality being tested
5. Use `pytest.skip()` to handle cases where the database is not available
