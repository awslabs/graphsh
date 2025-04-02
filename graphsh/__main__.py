"""
Entry point for GraphSh.
"""

# Use absolute imports instead of relative imports
from graphsh.cli.app import main, initialize_environment

# Initialize environment
initialize_environment()

if __name__ == "__main__":
    main()
