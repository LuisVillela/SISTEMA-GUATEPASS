#!/usr/bin/env python
import boto3
import json
from decimal import Decimal

def test_processor():
    # Simular un mensaje que llegaría de SQS
    test_message = {
        "placa": "P-123ABC",
        "peaje_id": "PEAJE_ZONA10",
        "tag_id": "TAG-001",
        "timestamp": "2025-01-20T10:30:00Z",
        "user_type": "registrado",
        "user_email": "juan@email.com",
        "user_phone": "50212345678",
        "has_tag": True,
        "available_balance": 100.00
    }
    
    # Verificar DynamoDB antes
    dynamodb = boto3.resource('dynamodb')
    users_table = dynamodb.Table('guatepass-users-dev')
    transactions_table = dynamodb.Table('guatepass-transactions-dev')
    
    print("=== ESTADO INICIAL ===")
    user_before = users_table.get_item(Key={'placa': 'P-123ABC'})
    if 'Item' in user_before:
        print(f"Saldo inicial: {user_before['Item'].get('saldo_disponible', 'N/A')}")
    
    # Verificar transacciones existentes
    response = transactions_table.scan()
    print(f"Transacciones existentes: {len(response.get('Items', []))}")
    
    print("\n=== EJECUTANDO TEST ===")
    print("Mensaje de prueba enviado a SQS")
    print("Revisa CloudWatch para ver si el Processor lo procesó")
    
    # Enviar mensaje real a SQS para prueba
    sqs = boto3.client('sqs')
    queue_url = sqs.list_queues(QueueNamePrefix='guatepass-processing-dev')['QueueUrls'][0]
    
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(test_message)
    )
    
    print(f" Mensaje enviado a SQS: {response['MessageId']}")
    print("Espera 1-2 minutos y ejecuta la verificación de nuevo")

if __name__ == "__main__":
    test_processor()