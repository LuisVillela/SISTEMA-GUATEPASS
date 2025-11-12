import json
import boto3
import os
import uuid
from datetime import datetime

# Clients de AWS
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Tablas DynamoDB
users_table = dynamodb.Table(os.environ['USERS_TABLE'])
transactions_table = dynamodb.Table(os.environ['TRANSACTIONS_TABLE'])

# SNS Topic
notifications_topic_arn = os.environ['NOTIFICATIONS_TOPIC_ARN']

# Tarifas de peajes
TOLL_RATES = {
    'PEAJE_ZONA10': 25.00,
    'PEAJE_ZONA11': 30.00,
    'PEAJE_ZONA12': 20.00,
    'PEAJE_ZONA13': 35.00
}

def lambda_handler(event, context):
    """
    Lambda function para procesar transacciones desde SQS
    """
    print(f"Received SQS event: {json.dumps(event)}")
    
    for record in event['Records']:
        try:
            message_body = json.loads(record['body'])
            process_transaction(message_body)
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            # En un entorno real, podrías enviar a una DLQ aquí
            continue
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Transactions processed'})
    }

def process_transaction(transaction_data):
    """
    Procesa una transacción según el tipo de usuario
    """
    placa = transaction_data['placa']
    user_type = transaction_data['user_type']
    peaje_id = transaction_data['peaje_id']
    
    # Calcular monto base
    base_amount = TOLL_RATES.get(peaje_id, 25.00)
    
    # Aplicar lógica según tipo de usuario
    if user_type == 'no_registrado':
        process_unregistered_user(transaction_data, base_amount)
    elif user_type == 'registrado':
        process_registered_user(transaction_data, base_amount)
    else:
        print(f"Unknown user type: {user_type}")

def process_unregistered_user(transaction_data, base_amount):
    """
    Procesa usuario no registrado - genera factura con recargos
    """
    placa = transaction_data['placa']
    
    # Aplicar recargos (50% premium + 10% multa)
    premium_amount = base_amount * 1.5
    final_amount = premium_amount * 1.10
    
    # Generar factura simulada
    invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
    
    # Guardar transacción
    transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    
    transaction_item = {
        'transaction_id': transaction_id,
        'placa': placa,
        'peaje_id': transaction_data['peaje_id'],
        'monto': final_amount,
        'modalidad': 'no_registrado',
        'timestamp': transaction_data['timestamp'],
        'estado': 'factura_generada',
        'invoice_number': invoice_number,
        'base_amount': base_amount,
        'premium_charge': premium_amount - base_amount,
        'late_fee': final_amount - premium_amount
    }
    
    transactions_table.put_item(Item=transaction_item)
    
    # Enviar notificación de factura
    send_notification({
        'notification_type': 'invoice_generated',
        'placa': placa,
        'user_email': transaction_data.get('user_email'),
        'user_phone': transaction_data.get('user_phone'),
        'amount': final_amount,
        'invoice_number': invoice_number,
        'peaje_id': transaction_data['peaje_id']
    })
    
    # Enviar invitación a registrarse si tiene contacto
    if transaction_data.get('user_email') or transaction_data.get('user_phone'):
        send_notification({
            'notification_type': 'registration_invitation',
            'placa': placa,
            'user_email': transaction_data.get('user_email'),
            'user_phone': transaction_data.get('user_phone')
        })
    
    print(f"Factura generada para {placa}: Q{final_amount} (Invoice: {invoice_number})")

def process_registered_user(transaction_data, base_amount):
    """
    Procesa usuario registrado - cobro instantáneo
    """
    placa = transaction_data['placa']
    available_balance = transaction_data.get('available_balance', 0)
    
    # Verificar saldo suficiente
    if available_balance >= base_amount:
        # Procesar pago
        new_balance = available_balance - base_amount
        
        # Actualizar saldo en base de datos
        try:
            users_table.update_item(
                Key={'placa': placa},
                UpdateExpression='SET saldo_disponible = :new_balance',
                ExpressionAttributeValues={':new_balance': new_balance}
            )
            
            # Guardar transacción
            transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
            
            transaction_item = {
                'transaction_id': transaction_id,
                'placa': placa,
                'peaje_id': transaction_data['peaje_id'],
                'monto': base_amount,
                'modalidad': 'digital',
                'timestamp': transaction_data['timestamp'],
                'estado': 'completado',
                'previous_balance': available_balance,
                'new_balance': new_balance
            }
            
            # Si tiene tag, usar modalidad express
            if transaction_data.get('has_tag'):
                transaction_item['modalidad'] = 'express'
            
            transactions_table.put_item(Item=transaction_item)
            
            # Enviar notificación de pago exitoso
            send_notification({
                'notification_type': 'payment_success',
                'placa': placa,
                'user_email': transaction_data.get('user_email'),
                'user_phone': transaction_data.get('user_phone'),
                'amount': base_amount,
                'peaje_id': transaction_data['peaje_id'],
                'new_balance': new_balance
            })
            
            print(f"Pago exitoso para {placa}: Q{base_amount} (Nuevo saldo: Q{new_balance})")
            
        except Exception as e:
            print(f"Error updating balance for {placa}: {str(e)}")
            # En caso de error, generar factura
            process_unregistered_user(transaction_data, base_amount)
    
    else:
        # Saldo insuficiente - tratar como no registrado
        print(f"Saldo insuficiente para {placa}. Generando factura...")
        process_unregistered_user(transaction_data, base_amount)

def send_notification(notification_data):
    """
    Envía notificación a través de SNS
    """
    try:
        response = sns.publish(
            TopicArn=notifications_topic_arn,
            Message=json.dumps(notification_data),
            MessageAttributes={
                'NotificationType': {
                    'DataType': 'String',
                    'StringValue': notification_data['notification_type']
                }
            }
        )
        print(f"Notification sent: {response['MessageId']}")
    except Exception as e:
        print(f"Error sending notification: {str(e)}")