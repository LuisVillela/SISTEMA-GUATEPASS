import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function para manejar notificaciones
    """
    logger.info(f"Received notification event: {json.dumps(event)}")
    
    try:
        # El evento de SNS viene en un formato específico
        for record in event.get('Records', []):
            if record.get('EventSource') == 'aws:sns':
                message = json.loads(record['Sns']['Message'])
                notification_type = message.get('notification_type')
                
                if notification_type == 'payment_success':
                    send_payment_notification(message)
                elif notification_type == 'invoice_generated':
                    send_invoice_notification(message)
                elif notification_type == 'registration_invitation':
                    send_registration_invitation(message)
                else:
                    logger.warning(f"Unknown notification type: {notification_type}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Notifications processed'})
        }
        
    except Exception as e:
        logger.error(f"Error processing notifications: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

def send_payment_notification(message):
    """Simula envío de notificación de pago exitoso"""
    user_email = message.get('user_email')
    user_phone = message.get('user_phone')
    amount = message.get('amount')
    peaje_id = message.get('peaje_id')
    
    notification_text = f"Pago exitoso: Q{amount} en {peaje_id}"
    logger.info(f"SIMULATING NOTIFICATION - Email to {user_email}: {notification_text}")
    logger.info(f"SIMULATING NOTIFICATION - SMS to {user_phone}: {notification_text}")

def send_invoice_notification(message):
    """Simula envío de notificación de factura"""
    user_email = message.get('user_email')
    user_phone = message.get('user_phone')
    amount = message.get('amount')
    invoice_number = message.get('invoice_number')
    
    notification_text = f"Factura generada: #{invoice_number} - Q{amount}. Pague dentro de 15 días."
    logger.info(f"SIMULATING INVOICE NOTIFICATION - Email to {user_email}: {notification_text}")
    logger.info(f"SIMULATING INVOICE NOTIFICATION - SMS to {user_phone}: {notification_text}")

def send_registration_invitation(message):
    """Simula envío de invitación a registrarse"""
    user_email = message.get('user_email')
    user_phone = message.get('user_phone')
    
    invitation_text = "¡Regístrese en GuatePass! Obtenga descuentos y pague automáticamente."
    logger.info(f"SIMULATING REGISTRATION INVITATION - Email to {user_email}: {invitation_text}")
    logger.info(f"SIMULATING REGISTRATION INVITATION - SMS to {user_phone}: {invitation_text}")