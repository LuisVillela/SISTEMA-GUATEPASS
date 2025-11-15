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
        
        # Filtrar solo facturas de no registrados
        invoices = [
            {
                'factura_id': tx.get('resultado', {}).get('factura', {}).get('factura_id', 'N/A'),
                'peaje_id': tx['peaje_id'],
                'timestamp': tx['timestamp'],
                'monto': float(tx['monto']),
                'fecha_emision': tx.get('resultado', {}).get('factura', {}).get('fecha_emision'),
                'concepto': tx.get('resultado', {}).get('factura', {}).get('concepto', ''),
                'cargo_premium': tx.get('resultado', {}).get('factura', {}).get('cargo_premium', ''),
                'multa_tardia': tx.get('resultado', {}).get('factura', {}).get('multa_tardia', ''),
                'estado': 'pendiente'
            }
            for tx in transactions
            if tx.get('user_type') == 'no_registrado' and tx.get('resultado', {}).get('factura')
        ]
        
        # Ordenar por timestamp descendente
        invoices.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return success_response({
            'placa': placa,
            'total_invoices': len(invoices),
            'invoices': invoices
        })
        
    except Exception as e:
        print(f"Error querying invoices: {str(e)}")
        return error_response(500, "INTERNAL_ERROR", "Error retrieving invoice history")

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