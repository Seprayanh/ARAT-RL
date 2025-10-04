#!/usr/bin/env python3
"""
ARAT-RL Setup Verification Script

This script verifies that all components of ARAT-RL are properly installed and configured.
"""

import subprocess
import os
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description}")
            return True
        else:
            print(f"✗ {description}: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"✗ {description}: {str(e)}")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✓ {description}")
        return True
    else:
        print(f"✗ {description}: File not found")
        return False

def main():
    print("ARAT-RL Setup Verification")
    print("=" * 40)
    
    all_checks_passed = True
    
    # Check basic tools
    print("\n1. Basic Tools:")
    all_checks_passed &= run_command("java -version", "Java is installed")
    all_checks_passed &= run_command("mvn -version", "Maven is installed")
    all_checks_passed &= run_command("docker --version", "Docker is installed")
    all_checks_passed &= run_command("python3 --version", "Python 3 is installed")
    all_checks_passed &= run_command("tmux -V", "tmux is installed")
    
    # Check Java versions
    print("\n2. Java Versions:")
    java_output = subprocess.run("java -version", shell=True, capture_output=True, text=True)
    if "1.8" in java_output.stderr:
        print("✓ Java 8 detected")
    elif "11" in java_output.stderr:
        print("✓ Java 11 detected")
    else:
        print("✗ Unexpected Java version")
        all_checks_passed = False
    
    # Check environment files
    print("\n3. Environment Files:")
    all_checks_passed &= check_file_exists("java8.env", "java8.env exists")
    all_checks_passed &= check_file_exists("java11.env", "java11.env exists")
    
    # Check build artifacts
    print("\n4. Build Artifacts:")
    cp_files = list(Path("service").rglob("cp.txt"))
    if len(cp_files) == 6:
        print(f"✓ All {len(cp_files)} cp.txt files found")
    else:
        print(f"✗ Expected 6 cp.txt files, found {len(cp_files)}")
        all_checks_passed = False
    
    # Check JAR files
    print("\n5. JAR Files:")
    all_checks_passed &= check_file_exists("evomaster.jar", "EvoMaster JAR")
    all_checks_passed &= check_file_exists("org.jacoco.agent-0.8.7-runtime.jar", "JaCoCo Agent JAR")
    all_checks_passed &= check_file_exists("org.jacoco.cli-0.8.7-nodeps.jar", "JaCoCo CLI JAR")
    
    # Check Python dependencies
    print("\n6. Python Dependencies:")
    try:
        import yaml
        import requests
        print("✓ Required Python packages installed")
    except ImportError as e:
        print(f"✗ Missing Python package: {e}")
        all_checks_passed = False
    
    # Check Docker images
    print("\n7. Docker Images:")
    docker_images = subprocess.run("docker images", shell=True, capture_output=True, text=True)
    if "genomenexus/gn-mongo" in docker_images.stdout:
        print("✓ Genome Nexus MongoDB image")
    else:
        print("✗ Genome Nexus MongoDB image not found")
        all_checks_passed = False
    
    if "mongo" in docker_images.stdout:
        print("✓ MongoDB image")
    else:
        print("✗ MongoDB image not found")
        all_checks_passed = False
    
    if "mysql" in docker_images.stdout:
        print("✓ MySQL image")
    else:
        print("✗ MySQL image not found")
        all_checks_passed = False
    
    # Summary
    print("\n" + "=" * 40)
    if all_checks_passed:
        print("✓ All checks passed! ARAT-RL setup appears to be correct.")
        print("\nYou can now run:")
        print("  python3 arat-rl.py spec/features.yaml http://localhost:30100/ 60")
    else:
        print("✗ Some checks failed. Please review the issues above.")
        print("\nCommon solutions:")
        print("  - Run setup script: sh setup_macos.sh (macOS) or sh setup.sh (Ubuntu)")
        print("  - Check troubleshooting guide: TROUBLESHOOTING.md")
        print("  - Verify all dependencies are installed")
        sys.exit(1)

if __name__ == "__main__":
    main()
