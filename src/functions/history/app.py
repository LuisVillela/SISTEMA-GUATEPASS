import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
transactions_table = dynamodb.Table(os.environ['TRANSACTIONS_TABLE'])

def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")
    
    # Extraer placa del path
    placa = event.get('pathParameters', {}).get('placa', '').upper()
    
    if not placa:
        return error_response(400, "MISSING_PLACA", "Placa parameter is required")
    
    # Validar formato de placa
    if not is_valid_placa(placa):
        return error_response(400, "INVALID_PLACA", "Invalid placa format")
    
    try:
        # Consultar transacciones de la placa
        response = transactions_table.scan(
            FilterExpression='placa = :placa',
            ExpressionAttributeValues={':placa': placa}
        )
        
        transactions = response.get('Items', [])
        
        # Filtrar solo pagos exitosos (excluir facturas de no registrados)
        payments = [
            {
                'transaction_id': tx['transaction_id'],
                'peaje_id': tx['peaje_id'],
                'timestamp': tx['timestamp'],
                'monto': float(tx['monto']),
                'user_type': tx['user_type'],
                'tipo_escenario': tx.get('tipo_escenario', 'unknown'),
                'fecha_procesado': tx.get('fecha_procesado')
            }
            for tx in transactions
            if tx.get('user_type') != 'no_registrado' and tx.get('resultado', {}).get('pago', {}).get('exitoso', True)
        ]
        
        # Ordenar por timestamp descendente
        payments.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return success_response({
            'placa': placa,
            'total_payments': len(payments),
            'payments': payments
        })
        
    except Exception as e:
        print(f"Error querying payments: {str(e)}")
        return error_response(500, "INTERNAL_ERROR", "Error retrieving payment history")

def is_valid_placa(placa):
    """Valida formato de placa guatemalteca"""
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
        'body': json.dumps(data, default=decimal_default)
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

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError