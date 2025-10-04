# ARAT-RL

ARAT-RL is a tool designed to find internal server errors in REST APIs using reinforcement learning. 
This work has been published at ASE 2023, "[Adaptive REST API Testing with Reinforcement Learning](https://ieeexplore.ieee.org/document/10298580)".

[Bibtex Citation Here](https://github.com/codingsoo/arat-rl/blob/main/docs/ase2023.bib)

## Quick Start

Install Python3 and Required Packages:

```
pip3 install -r requirements.txt
```

Run ARAT-RL:

```
python3 arat-rl.py Specification_Location Server_URL Runtime_in_Minutes
```

For example:

```
python arat-rl.py spec/features.yaml http://localhost:30100/ 3600
```

After an hour, it will print a report with found internal server errors. The results will be stored in `http_500_error_report.txt`.

## Reproduce the results in our paper.

### Machine Specification

Our experiments were conducted on Google Cloud E2 machines, each with a 24-core CPU and 96 GB of RAM.

### Software Dependencies and Installation

#### Ubuntu 20.04
If your OS is Ubuntu 20.04, you can simply run our setup script with `sh setup.sh` command in your terminal.

#### macOS
For macOS users, use the dedicated setup script:
```bash
sh setup_macos.sh
```

#### Verify Installation
After running the setup script, verify your installation:
```bash
python3 verify_setup.py
```

#### Manual Installation
The following software is required for the experiment:
- Git
- Common utilities (software-properties-common, unzip, wget, gcc, git, vim, libcurl4-nss-dev, tmux, mitmproxy)
- Java 8 and 11
- Maven3
- Python 3 (with pip and virtualenv)
- Python libraries in requirements.txt
- Docker
- .NET 6 Runtime and SDK
- JaCoCo Agent and CLI 0.8.7

**Important Notes:**
- Ensure Java 8 and 11 are properly installed and accessible via `java -version` and `mvn -version`
- The setup scripts will automatically configure the correct Java environment files (`java8.env` and `java11.env`)
- If you encounter Maven build issues, see the troubleshooting section below

### Run tools and services

After installing all the required software, you can run the tools with this command:

```
python run.py [tool's name]
```

This command will run the tool and all the services in our benchmark for an hour. Possible tool names are `arat-rl`, `morest`, `evomaster-blackbox`, and `restler`. If you want to run an ablation study, you can set the tool names to: `no_prioritization`, `no_feedback`, and `no_sampling`.

### Collect the results

To collect the results, use the following command:

```
python parse_log.py
```

This will gather the coverage and number of responses for status codes 2xx, 4xx, and 5xx. The results will be stored in the `res.csv` file. Additionally, any detected bugs will be recorded in the `errors.json` file. + We noticed a bug when counting the unique number of 500 errors (we are not able to detect the ping pong between functions), so we recommend to count the number of operations that produce 500 status code.

### Review the Results

The `results` directory contains the results for each tool and each service. These results include the achieved code coverage, the number of obtained status codes, the number of bugs found, and detailed bug reports.

## Troubleshooting

### Common Setup Issues

#### Maven Build Failures
If you encounter Maven build errors:

1. **Java Version Issues**: Ensure you're using the correct Java version for each service
   ```bash
   # Check Java version
   java -version
   mvn -version
   
   # For JDK 8 services
   export JAVA_HOME=/path/to/java8
   # For JDK 11 services  
   export JAVA_HOME=/path/to/java11
   ```

2. **Memory Issues**: Increase Maven heap size
   ```bash
   export MAVEN_OPTS="-Xmx4g -XX:MaxPermSize=512m"
   mvn clean install -DskipTests
   ```

3. **Dependency Resolution**: Try with updated dependencies
   ```bash
   mvn clean install -DskipTests -U
   ```

#### Missing cp.txt Files
If `cp.txt` files are missing after build:
```bash
# Verify build success
find service -name "cp.txt" -type f | wc -l
# Should return 6

# If missing, rebuild specific service
cd service/jdk8_1
mvn dependency:build-classpath -Dmdep.outputFile=cp.txt
```

#### Service Startup Issues
If services fail to start:

1. **Docker Issues**: Ensure Docker is running
   ```bash
   docker ps  # Should show running containers
   ```

2. **Port Conflicts**: Check if required ports are available
   ```bash
   lsof -i :30100  # Check specific port
   ```

3. **Environment Variables**: Verify Java environment is loaded
   ```bash
   source ./java8.env  # or java11.env
   echo $JAVA_HOME
   ```

#### Different Results from Paper
If you're getting different results than reported:

1. **Coverage Issues**: Ensure JaCoCo agent is properly configured
2. **Service Versions**: Use exact Java versions specified in environment files
3. **Database Connections**: Verify Docker containers for MongoDB/MySQL are running
4. **Environment Consistency**: Use the provided setup scripts for reproducible results

### Getting Help

If you continue to experience issues:

1. Check that all dependencies are installed correctly
2. Verify Java and Maven versions match requirements
3. Ensure Docker is running and accessible
4. Review service logs in tmux sessions
5. Try running a single service first: `python3 run_service.py features-service 11000 blackbox`
