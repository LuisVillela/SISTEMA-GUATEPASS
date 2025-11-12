#!/bin/bash

echo " VERIFICANDO LAMBDA PROCESSOR..."

# 1. Verificar que la función existe
LAMBDA_NAME=$(aws lambda list-functions --query "Functions[?contains(FunctionName, 'transaction-processor-dev')].FunctionName" --output text)

if [ -z "$LAMBDA_NAME" ]; then
    echo "Lambda Processor no encontrado"
    exit 1
fi

echo "Lambda encontrado: $LAMBDA_NAME"

# 2. Verificar triggers de SQS
echo "Verificando trigger de SQS..."
aws lambda get-function --function-name $LAMBDA_NAME --query "Configuration.[FunctionName, Runtime, LastModified]" --output table

# 3. Verificar métricas recientes
echo "Verificando métricas..."
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=$LAMBDA_NAME \
    --start-time $(date -u -d "1 hour ago" +"%Y-%m-%dT%H:%M:%SZ") \
    --end-time $(date -u +"%Y-%m-%dT%H:%M:%SZ") \
    --period 300 \
    --statistics Sum \
    --query "Datapoints[].Sum" \
    --output table

# 4. Verificar mensajes en SQS
echo "Verificando cola SQS..."
SQS_URL=$(aws sqs list-queues --queue-name-prefix guatepass-processing-dev --query "QueueUrls[0]" --output text)

if [ -n "$SQS_URL" ]; then
    MSG_COUNT=$(aws sqs get-queue-attributes \
        --queue-url $SQS_URL \
        --attribute-names ApproximateNumberOfMessages \
        --query "Attributes.ApproximateNumberOfMessages" \
        --output text)
    
    echo "Mensajes en cola: $MSG_COUNT"
else
    echo "Cola SQS no encontrada"
fi

echo "Verificación completada"