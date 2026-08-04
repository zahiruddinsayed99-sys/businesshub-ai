#!/usr/bin/env bash
# ==============================================================================
# BusinessHub AI - Local WSL Environment Verification Script
# This script verifies that Docker, container services, and mapped network ports
# (PostgreSQL, Redis, MinIO) are fully active and reachable within WSL.
# ==============================================================================

# Text Formatting Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}        BusinessHub AI - WSL Local Infrastructure Verifier           ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# Helper function to print status
print_status() {
    local service_name=$1
    local status=$2
    local message=$3
    if [ "$status" = "SUCCESS" ]; then
        echo -e "[ ${GREEN}OK${NC} ] ${service_name}: ${message}"
    elif [ "$status" = "WARNING" ]; then
        echo -e "[ ${YELLOW}WARN${NC} ] ${service_name}: ${message}"
    else
        echo -e "[ ${RED}FAIL${NC} ] ${service_name}: ${message}"
    fi
}

# 1. Verify Docker Daemon is running
if ! docker info >/dev/null 2>&1; then
    print_status "Docker Daemon" "FAIL" "Docker is not running. Please start Docker Desktop and ensure WSL integration is enabled."
    exit 1
else
    print_status "Docker Daemon" "SUCCESS" "Docker service is active."
fi

# 2. Check running docker-compose containers
echo -e "\n${BLUE}Checking active Docker containers...${NC}"
CONTAINERS=("businesshub-db" "businesshub-redis" "businesshub-minio")

for container in "${CONTAINERS[@]}"; do
    if [ "$(docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null)" = "true" ]; then
        print_status "Container [$container]" "SUCCESS" "Running and healthy."
    else
        print_status "Container [$container]" "FAIL" "Container is stopped or does not exist."
        docker_failed=true
    fi
done

if [ "$docker_failed" = true ]; then
    echo -e "${YELLOW}Hint: Try running 'docker-compose up -d' in the project root to start services.${NC}"
fi

# 3. Verify Local TCP Port Availability (WSL localhost bindings)
echo -e "\n${BLUE}Verifying localhost port bindings...${NC}"

check_port() {
    local port=$1
    local service=$2
    # Use bash built-in socket check (highly portable in WSL bash)
    timeout 2 bash -c "</dev/tcp/127.0.0.1/$port" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_status "Port $port ($service)" "SUCCESS" "Reachable."
    else
        print_status "Port $port ($service)" "FAIL" "Unreachable. Ensure container is healthy or check port conflicts."
    fi
}

# Database Port
check_port 5432 "PostgreSQL"

# Redis Cache Port
check_port 6379 "Redis"

# MinIO Storage API Port
check_port 9000 "MinIO API"

# MinIO Admin Dashboard Port
check_port 9001 "MinIO Console"

# 4. Environment Check (Checking if local .env exists)
echo -e "\n${BLUE}Verifying local configuration...${NC}"
if [ -f ".env" ]; then
    print_status "Local Configuration" "SUCCESS" ".env file detected in the current directory."
else
    print_status "Local Configuration" "WARNING" ".env file not found in current directory. Ensure you have copied env.example to .env."
fi

echo -e "${BLUE}====================================================================${NC}"
echo -e "Verification check completed."
echo -e "${BLUE}====================================================================${NC}"
