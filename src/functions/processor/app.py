import json
import boto3
import os
import traceback
import uuid
from decimal import Decimal
from datetime import datetime

# Configuración de tarifas
TARIFAS_BASE = {
    'PEAJE_ZONA10': Decimal('25.00'),
    'PEAJE_ZONA11': Decimal('30.00'), 
    'PEAJE_ZONA12': Decimal('20.00'),
    'PEAJE_ZONA13': Decimal('35.00')
}

RECARGO_NO_REGISTRADO = Decimal('1.5')
MULTA_TARDIA = Decimal('15.00')
DESCUENTO_TAG = Decimal('0.9')

# Clients de AWS
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Tablas DynamoDB
users_table = dynamodb.Table(os.environ['USERS_TABLE'])
transactions_table = dynamodb.Table(os.environ['TRANSACTIONS_TABLE'])
tags_table = dynamodb.Table(os.environ['TAGS_TABLE'])

# SNS Topic
notifications_topic_arn = os.environ['NOTIFICATIONS_TOPIC_ARN']

def calcular_monto(peaje_id, user_type, has_tag):
    tarifa_base = TARIFAS_BASE.get(peaje_id, Decimal('25.00'))
    
    if user_type == 'no_registrado':
        return (tarifa_base * RECARGO_NO_REGISTRADO + MULTA_TARDIA).quantize(Decimal('0.01'))
    elif user_type == 'registrado' and has_tag:
        return (tarifa_base * DESCUENTO_TAG).quantize(Decimal('0.01'))
    else:
        return tarifa_base.quantize(Decimal('0.01'))

def simular_procesamiento_pago(placa, monto, metodo_pago):
    """Simula el procesamiento de pago con tarjeta"""
    # Simulamos una probabilidad de 95% de éxito
    import random
    exito = random.random() > 0.05  # 95% de éxito
    
    if exito:
        return {
            'exitoso': True,
            'codigo_autorizacion': f"AUTH-{uuid.uuid4().hex[:8].upper()}",
            'mensaje': 'Pago procesado exitosamente',
            'metodo_pago': metodo_pago
        }
    else:
        return {
            'exitoso': False,
            'error': 'Fondos insuficientes',
            'mensaje': 'El pago no pudo ser procesado',
            'metodo_pago': metodo_pago
        }

def procesar_usuario_con_tag(data):
    """Procesamiento para usuario con tag activo"""
    placa = data['placa']
    peaje_id = data['peaje_id']
    tag_id = data.get('tag_id')
    tag_info = data.get('tag_info', {})
    
    print(f"Procesando usuario con TAG: {placa}, Tag: {tag_id}")
    
    # Calcular monto con descuento por tag
    monto = calcular_monto(peaje_id, 'registrado', True)
    
    # Simular procesamiento de pago
    metodo_pago = tag_info.get('metodo_pago')
    resultado_pago = simular_procesamiento_pago(placa, monto, metodo_pago)
    
    resultado = {
        'tipo_escenario': 'tag_express',
        'monto': Decimal(monto),
        'tag_id': tag_id,
        'procesamiento_rapido': True,
        'pago': resultado_pago
    }
    
    return monto, resultado

def procesar_usuario_registrado(data):
    """Procesamiento para usuario registrado sin tag"""
    placa = data['placa']
    peaje_id = data['peaje_id']
    metodo_pago = data.get('metodo_pago')
    
    print(f"Procesando usuario registrado: {placa}")
    
    # Calcular monto normal
    monto = calcular_monto(peaje_id, 'registrado', False)
    
    # Simular procesamiento de pago
    resultado_pago = simular_procesamiento_pago(placa, monto, metodo_pago)
    
    resultado = {
        'tipo_escenario': 'registrado_digital',
        'monto': Decimal(monto),
        'pago': resultado_pago,
        'metodo_pago': metodo_pago
    }
    
    return monto, resultado

def procesar_usuario_no_registrado(data):
    """Procesamiento para usuario no registrado"""
    placa = data['placa']
    peaje_id = data['peaje_id']
    
    print(f"Procesando usuario no registrado: {placa}")
    
    # Calcular monto con recargo
    monto = calcular_monto(peaje_id, 'no_registrado', False)
    
    # Generar factura simulada
    factura_id = f"FACT-{uuid.uuid4().hex[:8].upper()}"
    factura = {
        'factura_id': factura_id,
        'placa': placa,
        'peaje_id': peaje_id,
        'monto': Decimal(monto),
        'fecha_emision': datetime.utcnow().isoformat() + 'Z',
        'concepto': f'Cobro de peaje {peaje_id} - Usuario no registrado',
        'cargo_premium': '50%',
        'multa_tardia': 'Q15.00',
        'mensaje_invitacion': 'Registrese en GuatePass para evitar recargos'
    }
    
    resultado = {
        'tipo_escenario': 'no_registrado_tradicional',
        'monto': Decimal(monto),
        'factura': factura,
        'enviar_invitacion': True
    }
    
    return monto, resultado

def guardar_transaccion(transaction_data, monto, resultado):
    """Guarda la transacción en DynamoDB"""
    try:
        transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        
        item = {
            'transaction_id': transaction_id,
            'placa': transaction_data['placa'],
            'peaje_id': transaction_data['peaje_id'],
            'timestamp': transaction_data['timestamp'],
            'monto': monto,
            'user_type': transaction_data['user_type'],
            'has_tag': transaction_data.get('has_tag', False),
            'tag_id': transaction_data.get('tag_id'),
            'tipo_escenario': resultado['tipo_escenario'],
            'resultado': resultado,
            'fecha_procesado': datetime.utcnow().isoformat() + 'Z'
        }
        
        transactions_table.put_item(Item=item)
        print(f"Transaccion guardada: {transaction_id} - Escenario: {resultado['tipo_escenario']}")
        return True
    except Exception as e:
        print(f"Error guardando transaccion: {e}")
        traceback.print_exc()
        return False

def enviar_notificacion_sns(transaction_data, monto, resultado):
    """Envía notificación a SNS"""
    try:
        notification_data = {
            'placa': transaction_data['placa'],
            'peaje_id': transaction_data['peaje_id'],
            'monto': Decimal(monto),
            'user_type': transaction_data['user_type'],
            'escenario': resultado['tipo_escenario'],
            'resultado': resultado,
            'email': transaction_data.get('user_email'),
            'telefono': transaction_data.get('user_phone'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        sns.publish(
            TopicArn=notifications_topic_arn,
            Message=json.dumps(notification_data, default=str),
            Subject=f"GuatePass - {resultado['tipo_escenario']} - {transaction_data['peaje_id']}"
        )
        
        print(f"Notificacion enviada a SNS para {transaction_data['placa']}")
        
    except Exception as e:
        print(f"Error enviando notificacion: {e}")

def lambda_handler(event, context):
    print(f"Procesando {len(event['Records'])} mensajes de SQS")
    
    for record in event['Records']:
        try:
            data = json.loads(record['body'])
            placa = data['placa']
            user_type = data['user_type']
            has_tag = data.get('has_tag', False)
            
            print(f"Iniciando procesamiento para: {placa} - {user_type} - Tag: {has_tag}")
            
            # Seleccionar escenario basado en tipo de usuario y tag
            if has_tag and data.get('tag_id'):
                monto, resultado = procesar_usuario_con_tag(data)
            elif user_type == 'registrado':
                monto, resultado = procesar_usuario_registrado(data)
            else:
                monto, resultado = procesar_usuario_no_registrado(data)
            
            # Guardar transacción en base de datos
            guardado_exitoso = guardar_transaccion(data, monto, resultado)
            
            if guardado_exitoso:
                # Enviar notificación
                enviar_notificacion_sns(data, monto, resultado)
                print(f"Procesamiento completado para {placa}")
            else:
                print(f"Procesamiento fallo al guardar para {placa}")
            
        except Exception as e:
            print(f"Error procesando mensaje: {e}")
            traceback.print_exc()
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f"Procesamiento completado para {len(event['Records'])} mensajes",
            'procesados': len(event['Records'])
        })
    }