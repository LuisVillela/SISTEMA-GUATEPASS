#!/bin/bash

API_URL=$(aws cloudformation describe-stacks --stack-name guatepass-stack --query 'Stacks[0].Outputs[?OutputKey==`WebhookUrl`].OutputValue' --output text)

echo "Testing GuatePass Webhook at: $API_URL"
echo "Current time: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# Test case 1: Request válido con tag
echo "=== Test 1: Request válido con tag ==="
curl -X POST $API_URL \
  -H "Content-Type: application/json" \
  -d '{
    "placa": "P-123ABC",
    "peaje_id": "PEAJE_ZONA10", 
    "tag_id": "TAG-001",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }'
echo -e "\n"

# Test case 2: Request válido sin tag
echo "=== Test 2: Request válido sin tag ==="
curl -X POST $API_URL \
  -H "Content-Type: application/json" \
  -d '{
    "placa": "P-456DEF",
    "peaje_id": "PEAJE_ZONA11",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }'
echo -e "\n"

# Test case 3: Request inválido - placa mal formada
echo "=== Test 3: Request inválido - placa mal formada ==="
curl -X POST $API_URL \
  -H "Content-Type: application/json" \
  -d '{
    "placa": "123ABC",
    "peaje_id": "PEAJE_ZONA10",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }'
echo -e "\n"

# Test case 4: Request con timestamp en futuro (debería fallar)
echo "=== Test 4: Timestamp en futuro (debería fallar) ==="
curl -X POST $API_URL \
  -H "Content-Type: application/json" \
  -d '{
    "placa": "P-123ABC",
    "peaje_id": "PEAJE_ZONA10",
    "timestamp": "2026-01-20T10:30:00Z"
  }'
echo -e "\n"