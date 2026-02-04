#!/bin/bash
# Deploy Mock Meraki API to AWS
# Usage: ./scripts/deploy.sh [--guided]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "========================================"
echo "Mock Meraki API - AWS Deployment"
echo "========================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v sam &> /dev/null; then
    echo "ERROR: AWS SAM CLI is not installed."
    echo "Install with: pip install aws-sam-cli"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI is not installed."
    exit 1
fi

# Verify SSO session
echo "Verifying AWS credentials (okta-sso profile)..."
if ! aws sts get-caller-identity --profile okta-sso &> /dev/null; then
    echo "AWS SSO session expired. Logging in..."
    aws sso login --profile okta-sso
fi

echo "Building SAM application..."
sam build

echo ""
echo "Deploying to AWS (eu-west-1)..."

if [ "$1" == "--guided" ]; then
    sam deploy --guided --profile okta-sso
else
    sam deploy --profile okta-sso --no-confirm-changeset
fi

echo ""
echo "========================================"
echo "Deployment complete!"
echo "========================================"

# Get outputs
echo ""
echo "API Endpoint:"
aws cloudformation describe-stacks \
    --stack-name meraki-mock-api \
    --profile okta-sso \
    --region eu-west-1 \
    --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
    --output text

echo ""
echo "Next steps:"
echo "1. Seed the database:"
echo "   cd seed_data && python seed_dynamodb.py --profile okta-sso --region eu-west-1"
echo ""
echo "2. Test the API:"
echo "   curl -H 'X-Cisco-Meraki-API-Key: test123' <API_ENDPOINT>/api/v1/organizations"
