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
    logger.info("Evento SNS recibido: %s", json.dumps(event))
    
    try:
        for record in event.get('Records', []):
            if record.get('EventSource') == 'aws:sns':
                message = json.loads(record['Sns']['Message'])
                logger.info("Procesando notificacion: %s", message.get('placa'))
                process_notification(message)
        
        logger.info("Todas las notificaciones procesadas exitosamente")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Notifications processed successfully'})
        }
        
    except Exception as e:
        logger.error("Error procesando notificacion: %s", str(e))
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
    
    logger.info("Procesando: %s - %s - Email: %s - Tel: %s", placa, escenario, email, telefono)
    
    if escenario == 'no_registrado_tradicional':
        send_invoice_notification(placa, email, telefono, monto, resultado, peaje_id)
    elif escenario in ['registrado_digital', 'tag_express']:
        if resultado.get('pago', {}).get('exitoso', True):
            send_payment_success_notification(placa, email, telefono, monto, escenario, resultado, peaje_id)
        else:
            send_payment_failed_notification(placa, email, telefono, monto, resultado, peaje_id)
    else:
        logger.warning("Escenario no reconocido: %s", escenario)

def send_invoice_notification(placa, email, telefono, monto, resultado, peaje_id):
    """
    Simula envio de FACTURA e INVITACION A REGISTRO para usuarios no registrados
    """
    factura = resultado.get('factura', {})
    factura_id = factura.get('factura_id', 'N/A')
    
    # Convertir monto a float si es string, o usar directamente
    try:
        monto_float = float(monto) if monto else 0.0
    except (ValueError, TypeError):
        monto_float = 0.0
    
    invoice_message = f"""
    FACTURA GUATEPASS - {factura_id}
    
    Detalles de la Factura:
    - Placa del vehiculo: {placa}
    - Peaje: {peaje_id}
    - Monto total: Q{monto_float:.2f}
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
        logger.info("[EMAIL SIMULADO] Para: %s", email)
        logger.info("[FACTURA] Asunto: Factura GuatePass %s - Placa %s", factura_id, placa)
        logger.info("[CONTENIDO FACTURA]: %s", invoice_message)
        logger.info("[INVITACION] Asunto: Evite recargos - Registrese en GuatePass")
        logger.info("[CONTENIDO INVITACION]: %s", invitation_message)
    
    if telefono:
        sms_factura = "FACTURA %s: Q%s pendiente. Placa: %s. GuatePass" % (factura_id, monto, placa)
        sms_invitacion = "Registre %s en GuatePass y ahorre hasta 60%%. Evite recargos." % placa
        
        logger.info("[SMS SIMULADO] Para: %s", telefono)
        logger.info("[FACTURA SMS]: %s", sms_factura)
        logger.info("[INVITACION SMS]: %s", sms_invitacion)

def send_payment_success_notification(placa, email, telefono, monto, escenario, resultado, peaje_id):
    """
    Simula notificacion de pago exitoso
    """
    pago_info = resultado.get('pago', {})
    metodo_pago = pago_info.get('metodo_pago', 'tarjeta')
    codigo_autorizacion = pago_info.get('codigo_autorizacion', 'N/A')
    
    # Convertir monto a float si es string
    try:
        monto_float = float(monto) if monto else 0.0
    except (ValueError, TypeError):
        monto_float = 0.0
    
    if escenario == 'tag_express':
        message = """
        COBRO EXPRESS EXITOSO - GUATEPASS
        
        Placa: %s
        Peaje: %s
        Monto: Q%s
        Metodo: %s
        Autorizacion: %s
        Tipo: Cobro Express con Tag
        Fecha: %s
        
        Gracias por usar GuatePass!
        """ % (placa, peaje_id, monto, metodo_pago, codigo_autorizacion, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        sms_message = "Cobro express exitoso: Q%s - Peaje %s - Auth: %s" % (monto, peaje_id, codigo_autorizacion)
    else:
        message = """
        PAGO EXITOSO - GUATEPASS
        
        Placa: %s
        Peaje: %s
        Monto: Q%s
        Metodo: %s
        Autorizacion: %s
        Tipo: Cobro Digital
        Fecha: %s
        
        Gracias por usar GuatePass!
        """ % (placa, peaje_id, monto, metodo_pago, codigo_autorizacion, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        sms_message = "Pago exitoso: Q%s - Peaje %s - Auth: %s" % (monto, peaje_id, codigo_autorizacion)
    
    if email:
        logger.info("[EMAIL SIMULADO] Para: %s", email)
        logger.info("[PAGO EXITOSO] Asunto: Pago exitoso - Placa %s", placa)
        logger.info("[CONTENIDO PAGO EXITOSO]: %s", message)
    
    if telefono:
        logger.info("[SMS SIMULADO] Para: %s", telefono)
        logger.info("[PAGO EXITOSO SMS]: %s", sms_message)

def send_payment_failed_notification(placa, email, telefono, monto, resultado, peaje_id):
    """
    Simula notificacion de pago fallido
    """
    pago_info = resultado.get('pago', {})
    error_msg = pago_info.get('error', 'Error en el procesamiento del pago')
    
    message = """
    PAGO FALLIDO - GUATEPASS
    
    Placa: %s
    Peaje: %s
    Monto intentado: Q%s
    Error: %s
    Fecha: %s
    
    Acciones requeridas:
    1. Verifique los fondos en su metodo de pago
    2. Actualice su metodo de pago en la app
    3. Contacte a su banco si el problema persiste
    
    Si no soluciona este problema, su vehiculo puede ser reportado.
    """ % (placa, peaje_id, monto, error_msg, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    sms_message = "PAGO FALLIDO: Q%s - %s. Actualice metodo de pago." % (monto, error_msg)
    
    if email:
        logger.info("[EMAIL SIMULADO] Para: %s", email)
        logger.info("[PAGO FALLIDO] Asunto: Pago fallido - Accion requerida - Placa %s", placa)
        logger.info("[CONTENIDO PAGO FALLIDO]: %s", message)
    
    if telefono:
        logger.info("[SMS SIMULADO] Para: %s", telefono)
        logger.info("[PAGO FALLIDO SMS]: %s", sms_message)