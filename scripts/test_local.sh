#!/bin/bash
# Run local development server
# Usage: ./scripts/test_local.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "========================================"
echo "Mock Meraki API - Local Testing"
echo "========================================"
echo ""

# Create env.json for local testing
cat > env.json << EOF
{
    "MerakiMockFunction": {
        "CONFIG_TABLE": "MerakiMock_Config_dev",
        "DATA_TABLE": "MerakiMock_Data_dev",
        "DEFAULT_TOPOLOGY": "hub_spoke",
        "LOG_LEVEL": "DEBUG",
        "STRICT_AUTH": "false",
        "DYNAMODB_LOCAL_ENDPOINT": "http://host.docker.internal:8000"
    }
}
EOF

echo "Environment configuration created: env.json"
echo ""

# Start local DynamoDB if not running
echo "Checking local DynamoDB..."
if ! curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "Starting local DynamoDB..."
    docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local 2>/dev/null || true
    sleep 2
    echo "Local DynamoDB started on port 8000"
else
    echo "Local DynamoDB already running"
fi

# Seed local data
echo ""
echo "Seeding local DynamoDB..."
./scripts/seed_data.sh --local

# Build SAM app
echo ""
echo "Building SAM application..."
sam build

# Start local API
echo ""
echo "Starting local API server..."
echo "API will be available at: http://localhost:3000"
echo ""
echo "Test commands:"
echo "  curl -H 'X-Cisco-Meraki-API-Key: test' http://localhost:3000/health"
echo "  curl -H 'X-Cisco-Meraki-API-Key: test' http://localhost:3000/api/v1/organizations"
echo "  curl -H 'X-Cisco-Meraki-API-Key: test' -H 'X-Mock-Topology: mesh' http://localhost:3000/api/v1/organizations"
echo ""

sam local start-api --env-vars env.json --docker-network host
