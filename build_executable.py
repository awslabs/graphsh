#!/usr/bin/env python3
"""
Build script for creating standalone GraphSh executables using PyInstaller.
"""

import platform
import subprocess
from pathlib import Path


def build_executable():
    """Build the GraphSh executable using PyInstaller."""
    # Determine the system
    system = platform.system().lower()

    # Base PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=graphsh",
        "--onefile",  # Create a single executable file
        "--clean",  # Clean PyInstaller cache before building
        "--log-level=INFO",
    ]

    # Add icon if available (you can add platform-specific icons later)
    # if system == "windows":
    #     cmd.append("--icon=resources/graphsh.ico")
    # elif system == "darwin":  # macOS
    #     cmd.append("--icon=resources/graphsh.icns")

    # Add hidden imports for the project's dependencies
    cmd.extend(
        [
            "--hidden-import=gremlinpython",
            "--hidden-import=neo4j",
            "--hidden-import=boto3",
            "--hidden-import=prompt_toolkit",
            "--hidden-import=rich",
            "--hidden-import=click",
            "--hidden-import=pydantic",
            "--hidden-import=rdflib",
            "--hidden-import=pygments",
        ]
    )

    # Add the entry point
    cmd.append("graphsh/__main__.py")

    # Execute PyInstaller
    print(f"Building executable with command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # Report success and location of the executable
    dist_dir = Path("dist")
    if system == "windows":
        exe_path = dist_dir / "graphsh.exe"
    else:
        exe_path = dist_dir / "graphsh"

    if exe_path.exists():
        print(f"\nBuild successful! Executable created at: {exe_path.absolute()}")
        print("\nYou can now distribute this standalone executable.")
    else:
        print("\nBuild completed, but executable not found at the expected location.")


if __name__ == "__main__":
    build_executable()
