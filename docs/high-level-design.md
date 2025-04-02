# GraphSh: High-Level Design (Updated March 2025)

## Overview

GraphSh is a command-line interface (CLI) tool designed for interacting with graph databases. It provides an interactive shell experience similar to `psql` for PostgreSQL, but specialized for graph query languages including Gremlin, SPARQL, and OpenCypher. The tool supports multiple graph database backends, with primary focus on Amazon Neptune and Neo4j.

## Key Features and Status

### Query Language Support (✅ Complete)
- Gremlin (TinkerPop)
- SPARQL 1.1
- OpenCypher
- Language-specific syntax highlighting
- Query validation and formatting
- Auto-completion support

### Database Support (✅ Complete)
- Amazon Neptune (primary)
- Neo4j (primary)
- Any TinkerPop-compliant database
- Any SPARQL 1.1 endpoint
- Any OpenCypher-compatible database

### Authentication Methods (✅ Complete)
- AWS IAM for Neptune
- Username/password for Neo4j
- No authentication for open endpoints
- Support for connection profiles

### Interactive Features (✅ Complete)
- Command history with search
- Tab completion for commands and queries
- Multi-line query support
- Result formatting options
- Command file execution
- Session logging

### Data Visualization (🔄 In Progress)
- Terminal-friendly table formatting
- Basic graph visualization
- Custom visualization themes (planned)

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      GraphSh CLI                            │
├─────────────┬─────────────────────────┬───────────────────┬─┘
│ CLI Parser  │    Interactive Shell    │  Config Manager   │
│ (click)     │    (prompt_toolkit)     │  (pydantic)       │
└─────────────┴─────────────────────────┴───────────────────┘
┌─────────────┬─────────────────────────┬───────────────────┐
│ Language    │    Connection           │  Result Renderer  │
│ Processors  │    Manager              │  (rich)           │
└─────────────┴─────────────────────────┴───────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                Database-Specific Adapters                   │
├─────────────┬─────────────────────────┬───────────────────┬─┘
│  Neptune    │        Neo4j           │  Generic          │
│  Adapter    │        Adapter         │  Adapters         │
└─────────────┴─────────────────────────┴───────────────────┘
```

### Key Components

1. **CLI Layer**
   - Command-line argument parsing
   - Configuration file handling
   - Interactive shell management
   - Command processing

2. **Query Processing**
   - Language-specific processors
   - Query validation
   - Syntax highlighting
   - Auto-completion

3. **Database Connectivity**
   - Connection management
   - Authentication handling
   - Query execution
   - Error handling

4. **Result Handling**
   - Result parsing
   - Data formatting through unified renderer system
   - Export functionality
   - Visualization rendering

## Implementation Details

### Core Classes

1. **GraphShApp**
   - Application lifecycle management
   - Component coordination
   - Session state management
   - Error handling

2. **Connection Manager**
   - Database connection pooling
   - Query routing
   - Transaction management
   - Connection recovery

3. **Language Processors**
   - Query parsing and validation
   - Language-specific optimizations
   - Completion suggestions
   - Error detection

4. **Result Renderers**
   - Data transformation
   - Output formatting
   - Export handling
   - Visualization rendering

### Data Flow

1. **Query Execution Flow**
```
User Input -> Language Processor -> Connection Manager -> 
Database Adapter -> Result Parser -> Renderer -> Display
```

2. **Command Processing Flow**
```
User Input -> Command Parser -> Command Handler -> 
Action Execution -> State Update -> Display
```

3. **Configuration Flow**
```
Config File -> Config Manager -> Profile Loading -> 
Connection Setup -> Session Configuration
```

## Recent Improvements

### Architecture
- Unified renderer system replacing legacy formatters
- Enhanced error handling
- Improved connection management
- Streamlined configuration handling

### Performance
- Optimized query execution
- Reduced memory usage
- Enhanced connection pooling
- Faster result processing

### Developer Experience
- Comprehensive logging
- Better error messages
- Enhanced debugging tools
- Improved test coverage

## Testing Strategy

### Unit Testing (✅ Complete)
- Component-level tests
- Mock database interactions
- Error handling verification
- Configuration validation

### Integration Testing (✅ Complete)
- Cross-component interaction
- Database connectivity
- Query execution
- Authentication flows

### End-to-End Testing (✅ Complete)
- Full application flows
- Command file processing
- Interactive sessions
- Result formatting

## Development Tools

### Core Tools
- UV: Package management
- pytest: Testing framework
- ruff: Code formatting and linting
- coverage: Test coverage analysis

### Dependencies
All dependencies are up-to-date as of March 2025:
- prompt_toolkit: 3.0.43
- rich: 13.7.0
- click: 8.1.7
- pydantic: 2.6.1
- gremlinpython: 3.7.1
- neo4j: 5.14.1
- boto3: 1.34.34
- requests: 2.31.0

## Future Roadmap

### Phase 3: Advanced Features (🔄 In Progress)
1. **Enhanced Visualization**
   - Advanced graph visualization
   - Custom visualization themes
   - Interactive graph exploration

2. **Performance Optimization**
   - Query result caching
   - Connection pool improvements
   - Memory optimization
   - Query performance analysis

3. **Developer Tools**
   - Plugin system
   - API documentation
   - Example collection
   - Development guides

4. **Quality Assurance**
   - Increased test coverage
   - Performance benchmarks
   - Security audits
   - Compatibility testing

## Conclusion

GraphSh has evolved into a robust and feature-complete tool for interacting with graph databases. The recent architectural improvements and feature additions have enhanced its stability and usability. The focus now is on advanced features and optimizations while maintaining the core functionality that makes it a valuable tool for graph database users.
