import json
import boto3
import os
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function que procesa notificaciones de SNS y simula envio de emails/SMS
    """
    logger.info(f"Evento SNS recibido: {json.dumps(event)}")
    
    try:
        for record in event.get('Records', []):
            if record.get('EventSource') == 'aws:sns':
                message = json.loads(record['Sns']['Message'])
                logger.info(f"Procesando notificacion: {message.get('placa')}")
                process_notification(message)
        
        logger.info("Todas las notificaciones procesadas exitosamente")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Notifications processed successfully'})
        }
        
    except Exception as e:
        logger.error(f"Error procesando notificacion: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

def process_notification(notification_data):
    """
    Procesa y simula el envio de notificaciones segun el tipo de usuario y escenario
    """
    placa = notification_data.get('placa')
    escenario = notification_data.get('escenario')
    user_type = notification_data.get('user_type')
    email = notification_data.get('email')
    telefono = notification_data.get('telefono')
    monto = notification_data.get('monto')
    resultado = notification_data.get('resultado', {})
    peaje_id = notification_data.get('peaje_id')
    
    logger.info(f"Procesando: {placa} - {escenario} - Email: {email} - Tel: {telefono}")
    
    if escenario == 'no_registrado_tradicional':
        send_invoice_notification(placa, email, telefono, monto, resultado, peaje_id)
    elif escenario in ['registrado_digital', 'tag_express']:
        if resultado.get('pago', {}).get('exitoso', True):
            send_payment_success_notification(placa, email, telefono, monto, escenario, resultado, peaje_id)
        else:
            send_payment_failed_notification(placa, email, telefono, monto, resultado, peaje_id)
    else:
        logger.warning(f"Escenario no reconocido: {escenario}")

def send_invoice_notification(placa, email, telefono, monto, resultado, peaje_id):
    """
    Simula envio de FACTURA e INVITACION A REGISTRO para usuarios no registrados
    """
    factura = resultado.get('factura', {})
    factura_id = factura.get('factura_id', 'N/A')
    
    invoice_message = f"""
    FACTURA GUATEPASS - {factura_id}
    
    Detalles de la Factura:
    - Placa del vehiculo: {placa}
    - Peaje: {peaje_id}
    - Monto total: Q{monto:.2f}
    - Tarifa base: {factura.get('cargo_premium', 'Incluye 50% recargo')}
    - Multa por no registro: {factura.get('multa_tardia', 'Q15.00')}
    - Fecha de emision: {factura.get('fecha_emision', datetime.now().isoformat())}
    
    Estado: PENDIENTE DE PAGO
    Debe realizar el pago de esta factura para evitar cargos adicionales.
    """
    
    invitation_message = f"""
    EVITE RECARGOS! REGISTRESE EN GUATEPASS
    
    Beneficios al registrarse:
    - Hasta 10% de descuento con Tag fisico
    - Cobro automatico sin facturas pendientes
    - Notificaciones instantaneas
    - Sin multas por pago tardio
    - App movil para gestionar sus pagos
    
    Placa registrada: {placa}
    Ahorro estimado: Hasta 60% vs. tarifa no registrado
    
    Registrese ahora: app.guatepass.com/registro
    """
    
    if email:
        logger.info(f"[EMAIL SIMULADO] Para: {email}")
        logger.info(f"[FACTURA] Asunto: Factura GuatePass {factura_id} - Placa {placa}")
        logger.info(f"[CONTENIDO]: {invoice_message}")
        logger.info(f"[INVITACION] Asunto: Evite recargos - Registrese en GuatePass")
        logger.info(f"[CONTENIDO]: {invitation_message}")
    
    if telefono:
        sms_factura = f"FACTURA {factura_id}: Q{monto:.2f} pendiente. Placa: {placa}. GuatePass"
        sms_invitacion = f"Registre {placa} en GuatePass y ahorre hasta 60%. Evite recargos."
        
        logger.info(f"[SMS SIMULADO] Para: {telefono}")
        logger.info(f"[FACTURA]: {sms_factura}")
        logger.info(f"[INVITACION]: {sms_invitacion}")

def send_payment_success_notification(placa, email, telefono, monto, escenario, resultado, peaje_id):
    """
    Simula notificacion de pago exitoso
    """
    pago_info = resultado.get('pago', {})
    metodo_pago = pago_info.get('metodo_pago', 'tarjeta')
    codigo_autorizacion = pago_info.get('codigo_autorizacion', 'N/A')
    
    if escenario == 'tag_express':
        message = f"""
        COBRO EXPRESS EXITOSO - GUATEPASS
        
        Placa: {placa}
        Peaje: {peaje_id}
        Monto: Q{monto:.2f}
        Metodo: {metodo_pago}
        Autorizacion: {codigo_autorizacion}
        Tipo: Cobro Express con Tag
        Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Gracias por usar GuatePass!
        """
        sms_message = f"Cobro express exitoso: Q{monto:.2f} - Peaje {peaje_id} - Auth: {codigo_autorizacion}"
    else:
        message = f"""
        PAGO EXITOSO - GUATEPASS
        
        Placa: {placa}
        Peaje: {peaje_id}
        Monto: Q{monto:.2f}
        Metodo: {metodo_pago}
        Autorizacion: {codigo_autorizacion}
        Tipo: Cobro Digital
        Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Gracias por usar GuatePass!
        """
        sms_message = f"Pago exitoso: Q{monto:.2f} - Peaje {peaje_id} - Auth: {codigo_autorizacion}"
    
    if email:
        logger.info(f"[EMAIL SIMULADO] Para: {email}")
        logger.info(f"[PAGO EXITOSO] Asunto: Pago exitoso - Placa {placa}")
        logger.info(f"[CONTENIDO]: {message}")
    
    if telefono:
        logger.info(f"[SMS SIMULADO] Para: {telefono}")
        logger.info(f"[PAGO EXITOSO]: {sms_message}")

def send_payment_failed_notification(placa, email, telefono, monto, resultado, peaje_id):
    """
    Simula notificacion de pago fallido
    """
    pago_info = resultado.get('pago', {})
    error_msg = pago_info.get('error', 'Error en el procesamiento del pago')
    
    message = f"""
    PAGO FALLIDO - GUATEPASS
    
    Placa: {placa}
    Peaje: {peaje_id}
    Monto intentado: Q{monto:.2f}
    Error: {error_msg}
    Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Acciones requeridas:
    1. Verifique los fondos en su metodo de pago
    2. Actualice su metodo de pago en la app
    3. Contacte a su banco si el problema persiste
    
    Si no soluciona este problema, su vehiculo puede ser reportado.
    """
    
    sms_message = f"PAGO FALLIDO: Q{monto:.2f} - {error_msg}. Actualice metodo de pago."
    
    if email:
        logger.info(f"[EMAIL SIMULADO] Para: {email}")
        logger.info(f"[PAGO FALLIDO] Asunto: Pago fallido - Accion requerida - Placa {placa}")
        logger.info(f"[CONTENIDO]: {message}")
    
    if telefono:
        logger.info(f"[SMS SIMULADO] Para: {telefono}")
        logger.info(f"[PAGO FALLIDO]: {sms_message}")