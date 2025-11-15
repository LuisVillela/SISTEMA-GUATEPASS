#!/usr/bin/env python3
import boto3
import json
from datetime import datetime

def create_guatepass_dashboard():
    """Crea el dashboard de CloudWatch para GuatePass con los nombres correctos"""
    
    cloudwatch = boto3.client('cloudwatch')
    
    dashboard_name = "GuatePass-Dashboard"
    
    # Definir los widgets del dashboard con los nombres reales
    dashboard_body = {
        "widgets": [
            # LAMBDA FUNCTIONS - Invocaciones
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/Lambda", "Invocations", "FunctionName", "webhook-validator-dev" ],
                        [ ".", ".", ".", "transaction-processor-dev" ],
                        [ ".", ".", ".", "notification-handler-dev" ],
                        [ ".", ".", ".", "tags-management-dev" ],
                        [ ".", ".", ".", "payment-history-dev" ],
                        [ ".", ".", ".", "invoice-history-dev" ]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Lambda - Invocaciones por Funcion",
                    "period": 300,
                    "stat": "Sum"
                }
            },
            # LAMBDA FUNCTIONS - Errores
            {
                "type": "metric",
                "x": 8,
                "y": 0,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/Lambda", "Errors", "FunctionName", "webhook-validator-dev" ],
                        [ ".", ".", ".", "transaction-processor-dev" ],
                        [ ".", ".", ".", "notification-handler-dev" ],
                        [ ".", ".", ".", "tags-management-dev" ],
                        [ ".", ".", ".", "payment-history-dev" ],
                        [ ".", ".", ".", "invoice-history-dev" ]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Lambda - Errores por Funcion",
                    "period": 300,
                    "stat": "Sum"
                }
            },
            # LAMBDA FUNCTIONS - Duracion
            {
                "type": "metric",
                "x": 16,
                "y": 0,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/Lambda", "Duration", "FunctionName", "webhook-validator-dev", { "stat": "Average" } ],
                        [ ".", ".", ".", "transaction-processor-dev", { "stat": "Average" } ],
                        [ ".", ".", ".", "notification-handler-dev", { "stat": "Average" } ],
                        [ ".", ".", ".", "tags-management-dev", { "stat": "Average" } ],
                        [ ".", ".", ".", "payment-history-dev", { "stat": "Average" } ],
                        [ ".", ".", ".", "invoice-history-dev", { "stat": "Average" } ]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Lambda - Duracion Promedio (ms)",
                    "period": 300,
                    "stat": "Average"
                }
            },
            # LAMBDA FUNCTIONS - Throttles
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/Lambda", "Throttles", "FunctionName", "webhook-validator-dev" ],
                        [ ".", ".", ".", "transaction-processor-dev" ],
                        [ ".", ".", ".", "notification-handler-dev" ],
                        [ ".", ".", ".", "tags-management-dev" ],
                        [ ".", ".", ".", "payment-history-dev" ],
                        [ ".", ".", ".", "invoice-history-dev" ]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Lambda - Throttles",
                    "period": 300,
                    "stat": "Sum"
                }
            },
            # API GATEWAY - Numero de Requests
            {
                "type": "metric",
                "x": 8,
                "y": 6,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/ApiGateway", "Count", "ApiName", "guatepass-api-dev" ]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "API Gateway - Numero de Requests",
                    "period": 300,
                    "stat": "Sum"
                }
            },
            # API GATEWAY - Latencia y Errores
            {
                "type": "metric",
                "x": 16,
                "y": 6,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/ApiGateway", "Latency", "ApiName", "guatepass-api-dev", { "stat": "Average", "label": "Latencia" } ],
                        [ ".", "4XXError", ".", ".", { "stat": "Sum", "label": "Errores 4XX" } ],
                        [ ".", "5XXError", ".", ".", { "stat": "Sum", "label": "Errores 5XX" } ]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "API Gateway - Latencia y Errores",
                    "period": 300
                }
            },
            # DYNAMODB - Users Table
            {
                "type": "metric",
                "x": 0,
                "y": 12,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "guatepass-users-dev", { "label": "Lectura Users" } ],
                        [ ".", "ConsumedWriteCapacityUnits", ".", ".", { "label": "Escritura Users" } ]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "DynamoDB - Tabla Users",
                    "period": 300,
                    "stat": "Sum"
                }
            },
            # DYNAMODB - Transactions Table
            {
                "type": "metric",
                "x": 8,
                "y": 12,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "guatepass-transactions-dev", { "label": "Lectura Transactions" } ],
                        [ ".", "ConsumedWriteCapacityUnits", ".", ".", { "label": "Escritura Transactions" } ]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "DynamoDB - Tabla Transactions",
                    "period": 300,
                    "stat": "Sum"
                }
            },
            # DYNAMODB - Throttles
            {
                "type": "metric",
                "x": 16,
                "y": 12,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/DynamoDB", "ReadThrottleEvents", "TableName", "guatepass-users-dev", { "label": "Throttle Lectura Users" } ],
                        [ ".", "WriteThrottleEvents", ".", ".", { "label": "Throttle Escritura Users" } ],
                        [ ".", "ReadThrottleEvents", "TableName", "guatepass-transactions-dev", { "label": "Throttle Lectura Transactions" } ],
                        [ ".", "WriteThrottleEvents", ".", ".", { "label": "Throttle Escritura Transactions" } ]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "DynamoDB - Throttle Events",
                    "period": 300,
                    "stat": "Sum"
                }
            },
            # RESUMEN DE FUNCIONES LAMBDA
            {
                "type": "text",
                "x": 0,
                "y": 18,
                "width": 12,
                "height": 6,
                "properties": {
                    "markdown": "# GuatePass - Funciones Lambda\n\n**webhook-validator-dev:** Valida webhooks de peajes\n**transaction-processor-dev:** Procesa transacciones\n**notification-handler-dev:** Maneja notificaciones\n**tags-management-dev:** Gestion de tags\n**payment-history-dev:** Historial de pagos\n**invoice-history-dev:** Historial de facturas\n\n**Ultima actualizacion:** " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            },
            # METRICAS CLAVE
            {
                "type": "text",
                "x": 12,
                "y": 18,
                "width": 12,
                "height": 6,
                "properties": {
                    "markdown": "# Metricas Principales\n\n## Lambda Functions\n- Invocaciones\n- Errores\n- Duracion\n- Throttles\n\n## API Gateway\n- Numero de requests\n- Latencia\n- Errores 4XX/5XX\n\n## DynamoDB\n- Capacidad consumida\n- Throttle events"
                }
            }
        ]
    }
    
    try:
        response = cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print("Dashboard 'GuatePass-Dashboard' creado exitosamente!")
        print("URL del Dashboard: https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=GuatePass-Dashboard")
        
        return True
        
    except Exception as e:
        print("Error creando dashboard: " + str(e))
        return False

def verify_log_groups():
    """Verifica que los Log Groups esten organizados correctamente"""
    logs = boto3.client('logs')
    
    print("\nVERIFICANDO LOG GROUPS")
    print("=" * 50)
    
    expected_log_groups = [
        "/aws/lambda/tags-management-dev",
        "/aws/lambda/transaction-processor-dev",
        "/aws/lambda/webhook-validator-dev", 
        "/aws/lambda/notification-handler-dev",
        "/aws/lambda/payment-history-dev",
        "/aws/lambda/invoice-history-dev"
    ]
    
    try:
        response = logs.describe_log_groups(logGroupNamePrefix="/aws/lambda/")
        existing_groups = [lg['logGroupName'] for lg in response['logGroups']]
        
        # Filtrar solo los de GuatePass
        guatepass_groups = [group for group in existing_groups if any(name in group for name in [
            "tags-management-dev",
            "transaction-processor-dev", 
            "webhook-validator-dev",
            "notification-handler-dev",
            "payment-history-dev",
            "invoice-history-dev"
        ])]
        
        print("Log Groups de GuatePass encontrados:")
        for group in sorted(guatepass_groups):
            print(" - " + group)
        
        # Verificar que todos los esperados existen
        missing_groups = [group for group in expected_log_groups if group not in guatepass_groups]
        
        if missing_groups:
            print("Log Groups faltantes:")
            for group in missing_groups:
                print(" - " + group)
            return False
        else:
            print("Todos los Log Groups estan organizados correctamente")
            return True
            
    except Exception as e:
        print("Error verificando log groups: " + str(e))
        return False

def check_cloudwatch_alarms():
    """Verifica si existen alarmas basicas configuradas"""
    cloudwatch = boto3.client('cloudwatch')
    
    print("\nVERIFICANDO ALARMAS CLOUDWATCH")
    print("=" * 50)
    
    try:
        response = cloudwatch.describe_alarms()
        alarms = response['MetricAlarms']
        
        guatepass_alarms = []
        for alarm in alarms:
            alarm_name_lower = alarm['AlarmName'].lower()
            if any(keyword in alarm_name_lower for keyword in ['guatepass', 'lambda', 'apigateway', 'dynamodb']):
                guatepass_alarms.append(alarm)
        
        if guatepass_alarms:
            print("Alarmas relacionadas encontradas:")
            for alarm in guatepass_alarms:
                print(" - " + alarm['AlarmName'] + " (" + alarm['StateValue'] + ")")
        else:
            print("No se encontraron alarmas configuradas para GuatePass")
            print("Recomendacion: Configurar alarmas para errores Lambda y alta latencia")
            
    except Exception as e:
        print("Error verificando alarmas: " + str(e))

if __name__ == "__main__":
    print("INICIANDO CONFIGURACION DE MONITOREO GUATEPASS")
    print("=" * 60)
    
    # Crear dashboard
    success = create_guatepass_dashboard()
    
    # Verificar log groups
    verify_log_groups()
    
    # Verificar alarmas
    check_cloudwatch_alarms()
    
    if success:
        print("\nRESUMEN: Dashboard creado exitosamente")
        print("Accede al dashboard en la consola de AWS CloudWatch")
    else:
        print("\nRESUMEN: Hubo problemas en la configuracion")
        print("Revisa los errores anteriores")