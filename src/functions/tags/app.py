import json
import boto3
import os
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ['USERS_TABLE'])
tags_table = dynamodb.Table(os.environ['TAGS_TABLE'])

def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")
    
    # Determinar método HTTP y ruta
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    placa = event.get('pathParameters', {}).get('placa', '').upper()
    
    if not placa:
        return error_response(400, "MISSING_PLACA", "Placa parameter is required")
    
    if not is_valid_placa(placa):
        return error_response(400, "INVALID_PLACA", "Invalid placa format")
    
    try:
        if http_method == 'POST' and '/tag' in path:
            return associate_tag(event, placa)
        elif http_method == 'GET' and '/tag' in path:
            return get_tag_info(placa)
        elif http_method == 'PUT' and '/tag' in path:
            return update_tag_config(event, placa)
        elif http_method == 'DELETE' and '/tag' in path:
            return delete_tag_association(event, placa)
        else:
            return error_response(404, "NOT_FOUND", "Endpoint not found")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response(500, "INTERNAL_ERROR", "Internal server error")

def associate_tag(event, placa):
    """Asocia un tag a un vehículo"""
    body = json.loads(event.get('body', '{}'))
    tag_id = body.get('tag_id')
    metodo_pago = body.get('metodo_pago')
    configuracion = body.get('configuracion', {})
    
    if not tag_id:
        return error_response(400, "MISSING_TAG_ID", "tag_id is required")
    
    # Verificar que el tag no esté en uso
    try:
        existing_tag = tags_table.get_item(Key={'tag_id': tag_id})
        if 'Item' in existing_tag:
            return error_response(400, "TAG_IN_USE", "Tag ID already in use")
    except Exception as e:
        print(f"Error checking tag: {e}")
    
    # Verificar que el usuario existe
    user_response = users_table.get_item(Key={'placa': placa})
    if 'Item' not in user_response:
        return error_response(404, "USER_NOT_FOUND", "Usuario no encontrado")
    
    # Crear registro del tag
    tag_item = {
        'tag_id': tag_id,
        'placa': placa,
        'estado': 'activo',
        'fecha_activacion': datetime.now(timezone.utc).isoformat(),
        'metodo_pago': metodo_pago,
        'configuracion': configuracion
    }
    
    # Actualizar usuario para indicar que tiene tag
    users_table.update_item(
        Key={'placa': placa},
        UpdateExpression='SET tiene_tag = :has_tag, tag_id = :tag_id',
        ExpressionAttributeValues={
            ':has_tag': True,
            ':tag_id': tag_id
        }
    )
    
    # Guardar tag
    tags_table.put_item(Item=tag_item)
    
    return success_response({
        'message': 'Tag asociado exitosamente',
        'tag': tag_item
    })

def get_tag_info(placa):
    """Obtiene información del tag asociado a un vehículo"""
    # Buscar usuario primero
    user_response = users_table.get_item(Key={'placa': placa})
    if 'Item' not in user_response:
        return error_response(404, "USER_NOT_FOUND", "Usuario no encontrado")
    
    user = user_response['Item']
    
    if not user.get('tiene_tag') or not user.get('tag_id'):
        return success_response({
            'placa': placa,
            'tiene_tag': False,
            'message': 'El usuario no tiene tag asociado'
        })
    
    # Obtener información del tag
    tag_response = tags_table.get_item(Key={'tag_id': user['tag_id']})
    if 'Item' not in tag_response:
        return error_response(404, "TAG_NOT_FOUND", "Tag no encontrado")
    
    tag_info = tag_response['Item']
    
    return success_response({
        'placa': placa,
        'tag_info': tag_info
    })

def update_tag_config(event, placa):
    """Actualiza configuración del tag"""
    body = json.loads(event.get('body', '{}'))
    configuracion = body.get('configuracion')
    metodo_pago = body.get('metodo_pago')
    
    # Obtener tag_id del usuario
    user_response = users_table.get_item(Key={'placa': placa})
    if 'Item' not in user_response:
        return error_response(404, "USER_NOT_FOUND", "Usuario no encontrado")
    
    user = user_response['Item']
    tag_id = user.get('tag_id')
    
    if not tag_id:
        return error_response(400, "NO_TAG_ASSOCIATED", "El usuario no tiene tag asociado")
    
    # Preparar update expression
    update_expr = []
    expr_values = {}
    
    if configuracion:
        update_expr.append('configuracion = :config')
        expr_values[':config'] = configuracion
    
    if metodo_pago:
        update_expr.append('metodo_pago = :mp')
        expr_values[':mp'] = metodo_pago
    
    if not update_expr:
        return error_response(400, "NO_UPDATES", "No se proporcionaron campos para actualizar")
    
    # Actualizar tag
    tags_table.update_item(
        Key={'tag_id': tag_id},
        UpdateExpression='SET ' + ', '.join(update_expr),
        ExpressionAttributeValues=expr_values
    )
    
    # Obtener tag actualizado
    updated_tag = tags_table.get_item(Key={'tag_id': tag_id})['Item']
    
    return success_response({
        'message': 'Tag actualizado exitosamente',
        'tag': updated_tag
    })

def delete_tag_association(event, placa):
    """Desasocia un tag de un vehículo"""
    body = json.loads(event.get('body', '{}'))
    razon = body.get('razon', 'Sin razón especificada')
    
    # Obtener usuario
    user_response = users_table.get_item(Key={'placa': placa})
    if 'Item' not in user_response:
        return error_response(404, "USER_NOT_FOUND", "Usuario no encontrado")
    
    user = user_response['Item']
    tag_id = user.get('tag_id')
    
    if not tag_id:
        return error_response(400, "NO_TAG_ASSOCIATED", "El usuario no tiene tag asociado")
    
    # Actualizar tag a inactivo
    tags_table.update_item(
        Key={'tag_id': tag_id},
        UpdateExpression='SET estado = :estado, fecha_desactivacion = :fecha, razon_desactivacion = :razon REMOVE placa',
        ExpressionAttributeValues={
            ':estado': 'inactivo',
            ':fecha': datetime.now(timezone.utc).isoformat(),
            ':razon': razon
        }
    )
    
    # Actualizar usuario
    users_table.update_item(
        Key={'placa': placa},
        UpdateExpression='REMOVE tag_id SET tiene_tag = :has_tag',
        ExpressionAttributeValues={':has_tag': False}
    )
    
    return success_response({
        'message': 'Tag desasociado exitosamente',
        'placa': placa,
        'tag_id': tag_id,
        'razon': razon
    })

def is_valid_placa(placa):
    import re
    pattern = r'^[A-Z0-9]{1,3}-[A-Z0-9]{3,6}$'
    return re.match(pattern, placa) is not None

def success_response(data):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data, default=str)
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
                'message': message
            }
        })
    }