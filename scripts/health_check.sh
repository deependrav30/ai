#!/bin/bash

# Health Check Script for AI Agent System
# Verifies all services are operational

echo "🏥 AI Agent System Health Check"
echo "================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall health
ALL_HEALTHY=true

# Function to check service health
check_service() {
    local service_name=$1
    local check_command=$2
    local expected=$3
    
    echo -n "Checking $service_name... "
    
    if eval "$check_command" &> /dev/null; then
        echo -e "${GREEN}✓ Healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        ALL_HEALTHY=false
        return 1
    fi
}

# Check Docker services
echo "📦 Docker Services"
echo "─────────────────"

check_service "Redis" \
    "docker exec ai_redis redis-cli ping | grep -q PONG"

check_service "PostgreSQL" \
    "docker exec ai_postgres pg_isready -U ai_agent | grep -q 'accepting connections'"

check_service "ChromaDB" \
    "curl -sf http://localhost:8001/api/v1/heartbeat"

check_service "Prometheus" \
    "curl -sf http://localhost:9090/-/healthy | grep -q 'Prometheus is Healthy'"

check_service "Grafana" \
    "curl -sf http://localhost:3000/api/health"

check_service "AlertManager" \
    "curl -sf http://localhost:9093/-/healthy | grep -q 'OK'"

echo ""

# Check Python dependencies
echo "🐍 Python Environment"
echo "────────────────────"

check_service "OpenAI Package" \
    "python3 -c 'import openai' 2>/dev/null"

check_service "ChromaDB Package" \
    "python3 -c 'import chromadb' 2>/dev/null"

check_service "Streamlit Package" \
    "python3 -c 'import streamlit' 2>/dev/null"

check_service "Prometheus Client" \
    "python3 -c 'import prometheus_client' 2>/dev/null"

echo ""

# Check critical configurations
echo "⚙️  Configuration"
echo "────────────────"

check_service "OpenAI API Key" \
    "python3 -c 'import os; assert os.getenv(\"OPENAI_API_KEY\")' 2>/dev/null"

check_service "Knowledge Base" \
    "test -f data/uploaded/Company/General/P0/technical_support_kb.txt"

echo ""

# Database connectivity test
echo "💾 Database Connectivity"
echo "───────────────────────"

# Test PostgreSQL query
TICKET_COUNT=$(docker exec ai_postgres psql -U ai_agent -d episodic_memory -t -c "SELECT COUNT(*) FROM past_tickets;" 2>/dev/null | tr -d ' ')
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PostgreSQL Query${NC} - Found $TICKET_COUNT tickets"
else
    echo -e "${RED}✗ PostgreSQL Query Failed${NC}"
    ALL_HEALTHY=false
fi

# Test ChromaDB collection
CHROMA_STATUS=$(python3 -c "
import chromadb
try:
    client = chromadb.HttpClient(host='localhost', port=8001)
    collections = client.list_collections()
    print(f'{len(collections)} collections')
except Exception as e:
    print('error')
" 2>/dev/null)

if [[ $CHROMA_STATUS != "error" ]]; then
    echo -e "${GREEN}✓ ChromaDB Query${NC} - Found $CHROMA_STATUS"
else
    echo -e "${RED}✗ ChromaDB Query Failed${NC}"
    ALL_HEALTHY=false
fi

echo ""

# Check disk space
echo "💿 Disk Usage"
echo "────────────"

DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    echo -e "${GREEN}✓ Disk Space${NC} - ${DISK_USAGE}% used"
elif [ $DISK_USAGE -lt 90 ]; then
    echo -e "${YELLOW}⚠ Disk Space${NC} - ${DISK_USAGE}% used (warning)"
else
    echo -e "${RED}✗ Disk Space${NC} - ${DISK_USAGE}% used (critical)"
    ALL_HEALTHY=false
fi

echo ""

# Final status
echo "================================"
if [ "$ALL_HEALTHY" = true ]; then
    echo -e "${GREEN}✅ ALL SYSTEMS HEALTHY${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME SYSTEMS UNHEALTHY${NC}"
    echo "Review the output above for details"
    exit 1
fi
