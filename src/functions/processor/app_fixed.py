import json
import boto3
import os
import traceback
import uuid
from decimal import Decimal
from datetime import datetime

# Configuración de tarifas - TODO EN DECIMAL
TARIFAS_BASE = {
    'PEAJE_ZONA10': Decimal('25.00'),
    'PEAJE_ZONA11': Decimal('30.00'), 
    'PEAJE_ZONA12': Decimal('20.00'),
    'PEAJE_ZONA13': Decimal('35.00')
}

RECARGO_NO_REGISTRADO = Decimal('1.5')  # 50% más
MULTA_TARDIA = Decimal('15.00')         # Multa fija
DESCUENTO_TAG = Decimal('0.9')          # 10% descuento

# Clients de AWS
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Tablas DynamoDB
users_table = dynamodb.Table(os.environ['USERS_TABLE'])
transactions_table = dynamodb.Table(os.environ['TRANSACTIONS_TABLE'])

# SNS Topic
notifications_topic_arn = os.environ['NOTIFICATIONS_TOPIC_ARN']

def calcular_monto(peaje_id, user_type, has_tag):
    """Calcula monto usando SOLO Decimal"""
    tarifa_base = TARIFAS_BASE.get(peaje_id, Decimal('25.00'))
    
    if user_type == 'no_registrado':
        return (tarifa_base * RECARGO_NO_REGISTRADO + MULTA_TARDIA).quantize(Decimal('0.01'))
    elif user_type == 'registrado' and has_tag:
        return (tarifa_base * DESCUENTO_TAG).quantize(Decimal('0.01'))
    else:
        return tarifa_base.quantize(Decimal('0.01'))

def procesar_pago(placa, monto, user_type):
    """Procesa pago usando SOLO Decimal"""
    if user_type == 'no_registrado':
        return True
        
    try:
        response = users_table.get_item(Key={'placa': placa})
        if 'Item' not in response:
            return False
            
        usuario = response['Item']
        saldo_actual = usuario.get('saldo_disponible', Decimal('0'))
        
        if saldo_actual >= monto:
            nuevo_saldo = saldo_actual - monto
            users_table.update_item(
                Key={'placa': placa},
                UpdateExpression='SET saldo_disponible = :ns',
                ExpressionAttributeValues={':ns': nuevo_saldo}
            )
            return True
        return False
    except Exception as e:
        print(f"Error en pago: {e}")
        return False

def guardar_transaccion(transaction_data, monto, resultado):
    """Guarda transacción usando SOLO Decimal"""
    try:
        transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        
        # ITEM 100% COMPATIBLE CON DYNAMODB - SIN FLOAT
        item = {
            'transaction_id': transaction_id,
            'placa': transaction_data['placa'],
            'peaje_id': transaction_data['peaje_id'], 
            'timestamp': transaction_data['timestamp'],
            'monto': monto,  # DECIMAL DIRECTAMENTE
            'user_type': transaction_data['user_type'],
            'has_tag': transaction_data.get('has_tag', False),
            'fecha_procesado': datetime.utcnow().isoformat() + 'Z'
        }
        
        transactions_table.put_item(Item=item)
        print(f" Transacción guardada: {transaction_id}")
        return True
    except Exception as e:
        print(f" Error guardando: {e}")
        return False

def lambda_handler(event, context):
    """Lambda handler simplificado y corregido"""
    print(f" Mensajes a procesar: {len(event['Records'])}")
    
    for record in event['Records']:
        try:
            data = json.loads(record['body'])
            placa = data['placa']
            peaje_id = data['peaje_id']
            user_type = data['user_type']
            has_tag = data.get('has_tag', False)
            
            print(f" Procesando: {placa} ({user_type})")
            
            # 1. Calcular monto (Decimal)
            monto = calcular_monto(peaje_id, user_type, has_tag)
            print(f" Monto: {monto}")
            
            # 2. Procesar pago
            if user_type == 'no_registrado':
                resultado = {'tipo': 'factura', 'exitoso': True}
            else:
                exitoso = procesar_pago(placa, monto, user_type)
                resultado = {'tipo': 'cobro', 'exitoso': exitoso}
            
            # 3. Guardar transacción
            guardar_transaccion(data, monto, resultado)
            
            print(f" Completado: {placa}")
            
        except Exception as e:
            print(f" Error: {e}")
            traceback.print_exc()
    
    return {'statusCode': 200, 'body': 'OK'}
