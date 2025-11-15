import json
import boto3
import os
from validation import WebhookValidator

# Clients de AWS
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

# Tablas DynamoDB
users_table = dynamodb.Table(os.environ['USERS_TABLE'])
tags_table = dynamodb.Table(os.environ['TAGS_TABLE'])

# Cola SQS
processing_queue_url = os.environ['PROCESSING_QUEUE_URL']

validator = WebhookValidator()

def lambda_handler(event, context):
    """
    Lambda function para validar webhook de peajes - ACTUALIZADO CON TAGS
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Validar request completo (incluye validación de tag)
        is_valid, message, transaction_data = validator.validate_complete(event)
        
        if not is_valid:
            return error_response(400, "VALIDATION_ERROR", message)
        
        # Consultar información del usuario Y del tag
        user_info = get_user_info(transaction_data['placa'])
        tag_info = get_tag_info(transaction_data.get('tag_id'))
        
        # Determinar tipo de usuario REAL basado en tag válido
        user_type_final = determine_user_type(user_info, tag_info)
        has_active_tag = tag_info is not None and tag_info.get('estado') == 'activo'
        
        # Preparar mensaje para procesamiento
        processing_message = {
            **{k: v for k, v in transaction_data.items() if k != 'tag_info'},
            'user_type': user_type_final,
            'user_email': user_info.get('email'),
            'user_phone': user_info.get('telefono'),
            'has_tag': has_active_tag,
            'tag_id': transaction_data.get('tag_id'),
            'tag_info': tag_info,
            'metodo_pago': user_info.get('metodo_pago')
        }
        
        # Enviar a cola de procesamiento
        response = sqs.send_message(
            QueueUrl=processing_queue_url,
            MessageBody=json.dumps(processing_message),
            MessageAttributes={
                'UserType': {
                    'DataType': 'String',
                    'StringValue': user_type_final
                },
                'HasActiveTag': {
                    'DataType': 'String', 
                    'StringValue': str(has_active_tag)
                },
                'PeajeId': {
                    'DataType': 'String',
                    'StringValue': transaction_data['peaje_id']
                }
            }
        )
        
        print(f"Message sent to SQS: {response['MessageId']}")
        print(f"User type determined: {user_type_final}, Active tag: {has_active_tag}")
        
        # Respuesta exitosa inmediata
        return success_response({
            "status": "processing",
            "message": "Transaction received and queued for processing",
            "user_type": user_type_final,
            "has_active_tag": has_active_tag,
            "message_id": response['MessageId']
        })
        
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return error_response(500, "INTERNAL_ERROR", "Internal server error")

def get_user_info(placa):
    """Consulta información del usuario basado en placa"""
    try:
        response = users_table.get_item(Key={'placa': placa})
        
        if 'Item' in response:
            user_data = response['Item']
            return {
                'tipo_usuario': user_data.get('tipo_usuario', 'no_registrado'),
                'email': user_data.get('email'),
                'telefono': user_data.get('telefono'),
                'tiene_tag': user_data.get('tiene_tag', False),
                'metodo_pago': user_data.get('metodo_pago')
            }
        else:
            # Usuario no encontrado - tratar como no registrado
            return {
                'tipo_usuario': 'no_registrado',
                'email': None,
                'telefono': None, 
                'tiene_tag': False,
                'metodo_pago': None
            }
            
    except Exception as e:
        print(f"Error querying user info: {str(e)}")
        return {
            'tipo_usuario': 'no_registrado',
            'email': None,
            'telefono': None,
            'tiene_tag': False,
            'metodo_pago': None
        }

def get_tag_info(tag_id):
    """Consulta información del tag si existe"""
    if not tag_id:
        return None
        
    try:
        response = tags_table.get_item(Key={'tag_id': tag_id})
        if 'Item' in response:
            return response['Item']
        return None
    except Exception as e:
        print(f"Error querying tag info: {str(e)}")
        return None

def determine_user_type(user_info, tag_info):
    """Determina el tipo de usuario final basado en usuario Y tag"""
    
    # Si hay tag activo válido, es usuario con Tag (aunque en DB diga otra cosa)
    if tag_info and tag_info.get('estado') == 'activo':
        return 'registrado'  # Con tag implica registro
    
    # Si no hay tag, usar lo que está en la base de datos
    return user_info.get('tipo_usuario', 'no_registrado')

def success_response(data):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }

def error_response(status_code, error_code, message):
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
                'timestamp': None
            }
        })
    }
