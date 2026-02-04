#!/bin/bash
# Seed DynamoDB with mock data
# Usage: ./scripts/seed_data.sh [--local]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "========================================"
echo "Mock Meraki API - Seed DynamoDB"
echo "========================================"
echo ""

if [ "$1" == "--local" ]; then
    echo "Seeding LOCAL DynamoDB..."
    echo ""

    # Check if local DynamoDB is running
    if ! curl -s http://localhost:8000 > /dev/null 2>&1; then
        echo "Starting local DynamoDB..."
        docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local 2>/dev/null || true
        sleep 2
    fi

    python seed_data/seed_dynamodb.py --local --config-table MerakiMock_Config_dev --data-table MerakiMock_Data_dev

else
    echo "Seeding AWS DynamoDB (eu-west-1)..."
    echo ""

    # Verify SSO session
    if ! aws sts get-caller-identity --profile okta-sso &> /dev/null; then
        echo "AWS SSO session expired. Logging in..."
        aws sso login --profile okta-sso
    fi

    python seed_data/seed_dynamodb.py --profile okta-sso --region eu-west-1

fi

echo ""
echo "========================================"
echo "Seeding complete!"
echo "========================================"
