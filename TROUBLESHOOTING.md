# ARAT-RL Troubleshooting Guide

This guide addresses common issues encountered when setting up and running ARAT-RL.

## Table of Contents
- [Setup Issues](#setup-issues)
- [Build Issues](#build-issues)
- [Runtime Issues](#runtime-issues)
- [Result Differences](#result-differences)
- [Platform-Specific Issues](#platform-specific-issues)

## Setup Issues

### Issue: Maven Not Found
**Symptoms**: `command not found: mvn`

**Solutions**:
- **Ubuntu**: `sudo apt-get install maven`
- **macOS**: `brew install maven`
- **Verify**: `mvn -version`

### Issue: Java Version Conflicts
**Symptoms**: Build failures, version mismatch errors

**Solutions**:
1. Install both Java 8 and 11
2. Use environment files:
   ```bash
   source ./java8.env  # For JDK 8 services
   source ./java11.env # For JDK 11 services
   ```
3. Verify correct version:
   ```bash
   java -version
   mvn -version
   ```

### Issue: Docker Not Running
**Symptoms**: Services fail to start, database connection errors

**Solutions**:
1. Start Docker Desktop
2. Verify Docker is running: `docker ps`
3. Test Docker: `docker run hello-world`

## Build Issues

### Issue: Maven Build Failures
**Symptoms**: `mvn clean install` fails with errors

**Common Causes & Solutions**:

1. **Memory Issues**:
   ```bash
   export MAVEN_OPTS="-Xmx4g -XX:MaxPermSize=512m"
   mvn clean install -DskipTests
   ```

2. **Dependency Resolution**:
   ```bash
   mvn clean install -DskipTests -U
   ```

3. **Network Issues**:
   ```bash
   mvn clean install -DskipTests -o  # Offline mode
   ```

4. **Java Version Mismatch**:
   ```bash
   # Check and set correct Java version
   export JAVA_HOME=/path/to/correct/java
   export PATH=$JAVA_HOME/bin:$PATH
   mvn clean install -DskipTests
   ```

### Issue: Missing cp.txt Files
**Symptoms**: Services fail to start, classpath errors

**Solutions**:
1. Verify all services built successfully:
   ```bash
   find service -name "cp.txt" -type f
   # Should show 6 files
   ```

2. Rebuild missing services:
   ```bash
   cd service/jdk8_1
   mvn dependency:build-classpath -Dmdep.outputFile=cp.txt
   ```

### Issue: Spring Boot Version Conflicts
**Symptoms**: Dependency resolution errors, version conflicts

**Solutions**:
1. Check Spring Boot versions in pom.xml files
2. Update conflicting dependencies manually
3. Use `mvn dependency:tree` to identify conflicts

## Runtime Issues

### Issue: Services Won't Start
**Symptoms**: Services fail to start, connection refused errors

**Diagnostic Steps**:
1. Check Docker containers:
   ```bash
   docker ps -a
   ```

2. Check port availability:
   ```bash
   lsof -i :30100  # Check specific port
   netstat -an | grep LISTEN
   ```

3. Check tmux sessions:
   ```bash
   tmux list-sessions
   ```

4. Check service logs:
   ```bash
   tmux attach -t service_name
   ```

### Issue: Database Connection Errors
**Symptoms**: MongoDB/MySQL connection failures

**Solutions**:
1. Start required Docker containers:
   ```bash
   docker run --name=gn-mongo --restart=always -p 27018:27017 -d genomenexus/gn-mongo:latest
   docker run -d -p 27019:27017 --name mongodb mongo:latest
   docker run -d -p 3306:3306 --name mysqldb -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=users mysql
   ```

2. Wait for containers to be ready (30 seconds)
3. Verify connections:
   ```bash
   docker logs gn-mongo
   docker logs mongodb
   docker logs mysqldb
   ```

### Issue: Port Conflicts
**Symptoms**: "Address already in use" errors

**Solutions**:
1. Find processes using ports:
   ```bash
   lsof -i :30100
   ```

2. Kill conflicting processes:
   ```bash
   kill -9 <PID>
   ```

3. Or use different ports by modifying the configuration

## Result Differences

### Issue: Different Results from Paper
**Symptoms**: Coverage/bug counts don't match published results

**Common Causes**:

1. **Java Version Differences**: Use exact versions specified in environment files
2. **Missing Coverage**: Ensure JaCoCo agent is properly configured
3. **Service Configuration**: Verify all services use the same configuration as in the paper
4. **Environment Variables**: Ensure consistent environment setup

**Verification Steps**:
1. Check Java versions match requirements
2. Verify all cp.txt files exist
3. Ensure Docker containers are running
4. Test with single service first
5. Compare with known working setup

### Issue: Coverage Collection Problems
**Symptoms**: Zero or incorrect coverage metrics

**Solutions**:
1. Verify JaCoCo agent configuration
2. Check coverage collection scripts
3. Ensure services are instrumented correctly
4. Verify coverage ports are accessible

## Platform-Specific Issues

### macOS Issues

1. **Java Path Issues**:
   ```bash
   # Use /usr/libexec/java_home to find correct paths
   /usr/libexec/java_home -v 1.8
   /usr/libexec/java_home -v 11
   ```

2. **Permission Issues**:
   ```bash
   # Grant necessary permissions
   sudo chmod +x setup_macos.sh
   ```

3. **Homebrew Issues**:
   ```bash
   # Update Homebrew
   brew update && brew upgrade
   ```

### Ubuntu Issues

1. **Package Repository Issues**:
   ```bash
   sudo apt-get update
   sudo apt-get upgrade
   ```

2. **Java Installation Issues**:
   ```bash
   sudo apt-get install openjdk-8-jdk openjdk-11-jdk
   sudo update-alternatives --config java
   ```

## Getting Help

### Before Asking for Help

1. **Check Prerequisites**:
   - [ ] Java 8 and 11 installed
   - [ ] Maven installed
   - [ ] Docker running
   - [ ] All dependencies installed

2. **Verify Setup**:
   - [ ] All cp.txt files exist
   - [ ] Java environment files are correct
   - [ ] Docker containers are running
   - [ ] No port conflicts

3. **Test Basic Functionality**:
   ```bash
   # Test single service
   python3 run_service.py features-service 11000 blackbox
   
   # Check service health
   curl http://localhost:30100/health
   ```

4. **Collect Information**:
   - OS version and architecture
   - Java versions (`java -version`, `mvn -version`)
   - Docker version (`docker --version`)
   - Error messages and logs
   - Steps taken to reproduce the issue

### Debugging Commands

```bash
# Check service status
tmux list-sessions

# Check Docker containers
docker ps -a

# Check port usage
lsof -i :30100

# Check Java environment
echo $JAVA_HOME
java -version

# Check Maven environment
mvn -version

# Verify build artifacts
find service -name "cp.txt" -type f
```

### Log Locations

- Service logs: Check tmux sessions
- Docker logs: `docker logs <container_name>`
- Maven logs: Check console output during build
- Python logs: Check console output during tool execution

## Common Error Messages

### "command not found: mvn"
- Install Maven: `brew install maven` (macOS) or `sudo apt-get install maven` (Ubuntu)

### "JAVA_HOME not set"
- Set JAVA_HOME: `export JAVA_HOME=/path/to/java`
- Use environment files: `source ./java8.env`

### "Connection refused"
- Check if service is running: `tmux list-sessions`
- Check port availability: `lsof -i :port`
- Restart service if needed

### "Docker daemon not running"
- Start Docker Desktop
- Verify: `docker ps`

### "cp.txt not found"
- Rebuild service: `mvn dependency:build-classpath -Dmdep.outputFile=cp.txt`
- Check if build was successful: `mvn clean install -DskipTests`
