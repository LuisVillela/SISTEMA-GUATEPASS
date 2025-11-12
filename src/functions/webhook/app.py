import json
import boto3
import os
from validation import WebhookValidator

# Clients de AWS
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

# Tablas DynamoDB
users_table = dynamodb.Table(os.environ['USERS_TABLE'])

# Cola SQS
processing_queue_url = os.environ['PROCESSING_QUEUE_URL']

validator = WebhookValidator()

def lambda_handler(event, context):
    """
    Lambda function para validar webhook de peajes
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Validar request completo
        is_valid, message, transaction_data = validator.validate_complete(event)
        
        if not is_valid:
            return error_response(400, "VALIDATION_ERROR", message)
        
        # Consultar información del usuario
        user_info = get_user_info(transaction_data['placa'], transaction_data.get('tag_id'))
        
        # Preparar mensaje para procesamiento
        processing_message = {
            **transaction_data,
            'user_type': user_info['tipo_usuario'],
            'user_email': user_info.get('email'),
            'user_phone': user_info.get('telefono'),
            'has_tag': user_info.get('tiene_tag', False),
            'available_balance': user_info.get('saldo_disponible', 0)
        }
        
        # Enviar a cola de procesamiento
        response = sqs.send_message(
            QueueUrl=processing_queue_url,
            MessageBody=json.dumps(processing_message),
            MessageAttributes={
                'UserType': {
                    'DataType': 'String',
                    'StringValue': user_info['tipo_usuario']
                },
                'PeajeId': {
                    'DataType': 'String', 
                    'StringValue': transaction_data['peaje_id']
                }
            }
        )
        
        print(f"Message sent to SQS: {response['MessageId']}")
        
        # Respuesta exitosa inmediata
        return success_response({
            "status": "processing",
            "message": "Transaction received and queued for processing",
            "user_type": user_info['tipo_usuario'],
            "message_id": response['MessageId']
        })
        
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return error_response(500, "INTERNAL_ERROR", "Internal server error")

def get_user_info(placa, tag_id):
    """
    Consulta información del usuario basado en placa o tag_id
    """
    try:
        # Primero intentar por tag_id si existe
        if tag_id:
            # Buscar usuario por tag_id (necesitaríamos un índice global secundario)
            # Por simplicidad, busquemos directamente por placa
            pass
        
        # Buscar por placa
        response = users_table.get_item(Key={'placa': placa})
        
        if 'Item' in response:
            user_data = response['Item']
            return {
                'tipo_usuario': user_data.get('tipo_usuario', 'no_registrado'),
                'email': user_data.get('email'),
                'telefono': user_data.get('telefono'),
                'tiene_tag': user_data.get('tiene_tag', False),
                'saldo_disponible': float(user_data.get('saldo_disponible', 0))
            }
        else:
            # Usuario no encontrado - tratar como no registrado
            return {
                'tipo_usuario': 'no_registrado',
                'email': None,
                'telefono': None, 
                'tiene_tag': False,
                'saldo_disponible': 0
            }
            
    except Exception as e:
        print(f"Error querying user info: {str(e)}")
        # En caso de error, tratar como no registrado
        return {
            'tipo_usuario': 'no_registrado',
            'email': None,
            'telefono': None,
            'tiene_tag': False,
            'saldo_disponible': 0
        }

def success_response(data):
    """Respuesta HTTP exitosa"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }

def error_response(status_code, error_code, message):
    """Respuesta HTTP de error"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json', 
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': {
                'code': error_code,
                'message': message,
                'timestamp': None  # Se agregaría timestamp real
            }
        })
    }