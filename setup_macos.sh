#!/bin/bash

# ARAT-RL Setup Script for macOS
# This script sets up the ARAT-RL environment on macOS systems

set -e  # Exit on any error

echo "Setting up ARAT-RL on macOS..."

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Common Utilities
echo "Installing common utilities..."
brew install wget curl git vim tmux

# Install Java 8 and 11
echo "Installing Java 8 and 11..."
brew install openjdk@11

# Check architecture and handle Java 8 installation
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    echo "ARM64 architecture detected. Java 8 is not available via Homebrew on ARM64."
    echo "You may need to install Java 8 manually or use a different approach."
    echo "For now, we'll proceed with Java 11 and update the environment files accordingly."
    JAVA8_AVAILABLE=false
else
    brew install openjdk@8
    JAVA8_AVAILABLE=true
fi

# Install Maven
echo "Installing Maven..."
brew install maven

# Install Docker
echo "Installing Docker..."
brew install --cask docker

# Install mitmproxy
echo "Installing mitmproxy..."
brew install mitmproxy

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Install .NET 6 (required for RESTler)
echo "Installing .NET 6..."
brew install --cask dotnet

# Set up Java environment files for macOS
echo "Setting up Java environment files..."

# Get the correct Java paths for macOS
JAVA8_PATH=$(/usr/libexec/java_home -v 1.8 2>/dev/null || echo "/opt/homebrew/opt/openjdk@8/libexec/openjdk.jdk/Contents/Home")
JAVA11_PATH=$(/usr/libexec/java_home -v 11 2>/dev/null || echo "/opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk/Contents/Home")

# Create java8.env
cat > java8.env << EOF
export JAVA_HOME=$JAVA8_PATH
export PATH=\$JAVA_HOME/bin:\$PATH
EOF

# Create java11.env
cat > java11.env << EOF
export JAVA_HOME=$JAVA11_PATH
export PATH=\$JAVA_HOME/bin:\$PATH
EOF

echo "Java 8 path: $JAVA8_PATH"
echo "Java 11 path: $JAVA11_PATH"

# Build RESTful Services
echo "Building RESTful services..."

# Build JDK 8 services
echo "Building JDK 8 services..."
export JAVA_HOME=$JAVA8_PATH
export PATH=$JAVA_HOME/bin:$PATH

cd ./service/jdk8_1
mvn clean install -DskipTests
mvn dependency:build-classpath -Dmdep.outputFile=cp.txt

cd ../jdk8_2/genome-nexus
mvn clean install -DskipTests
mvn dependency:build-classpath -Dmdep.outputFile=cp.txt

cd ../person-controller
mvn clean install -DskipTests
mvn dependency:build-classpath -Dmdep.outputFile=cp.txt

cd ../user-management
mvn clean install -DskipTests
mvn dependency:build-classpath -Dmdep.outputFile=cp.txt

# Build JDK 11 services
echo "Building JDK 11 services..."
export JAVA_HOME=$JAVA11_PATH
export PATH=$JAVA_HOME/bin:$PATH

cd ../../jdk11/market
mvn clean install -DskipTests
mvn dependency:build-classpath -Dmdep.outputFile=cp.txt

cd ../project-tracking-system
mvn clean install -DskipTests
mvn dependency:build-classpath -Dmdep.outputFile=cp.txt

cd ../../..

# Pull Docker images
echo "Pulling required Docker images..."
docker pull genomenexus/gn-mongo
docker pull mongo
docker pull mysql

# Install EvoMaster 1.6.0
echo "Installing EvoMaster 1.6.0..."
if [ ! -f "evomaster.jar" ]; then
    wget https://github.com/EMResearch/EvoMaster/releases/download/v1.6.0/evomaster.jar.zip
    unzip evomaster.jar.zip
    rm evomaster.jar.zip
fi

# Install RESTler 9.1.1
echo "Installing RESTler 9.1.1..."
if [ ! -d "restler" ]; then
    source ./venv/bin/activate
    wget https://github.com/microsoft/restler-fuzzer/archive/refs/tags/v9.1.1.tar.gz
    tar -xvf v9.1.1.tar.gz
    rm v9.1.1.tar.gz
    mv restler-fuzzer-9.1.1 restler
    cd restler
    mkdir restler_bin
    python ./build-restler.py --dest_dir ./restler_bin
    cd ..
fi

# Install JaCoCo
echo "Installing JaCoCo..."
if [ ! -f "org.jacoco.agent-0.8.7-runtime.jar" ]; then
    wget https://repo1.maven.org/maven2/org/jacoco/org.jacoco.agent/0.8.7/org.jacoco.agent-0.8.7-runtime.jar
fi
if [ ! -f "org.jacoco.cli-0.8.7-nodeps.jar" ]; then
    wget https://repo1.maven.org/maven2/org/jacoco/org.jacoco.cli/0.8.7/org.jacoco.cli-0.8.7-nodeps.jar
fi

echo ""
echo "Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Start Docker Desktop if you haven't already"
echo "2. Run a test: python3 arat-rl.py spec/features.yaml http://localhost:30100/ 60"
echo "3. Check the troubleshooting guide in TROUBLESHOOTING.md if you encounter issues"
echo ""
echo "Java 8: $JAVA8_PATH"
echo "Java 11: $JAVA11_PATH"
