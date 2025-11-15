#!/usr/bin/env python3
import boto3

def verify_dashboard_exists():
    """Verifica que el dashboard existe"""
    cloudwatch = boto3.client('cloudwatch')
    
    print("VERIFICANDO DASHBOARD CLOUDWATCH")
    print("=" * 50)
    
    try:
        response = cloudwatch.list_dashboards()
        dashboards = response['DashboardEntries']
        guatepass_dashboards = [d for d in dashboards if 'guatepass' in d['DashboardName'].lower()]
        
        if guatepass_dashboards:
            print("Dashboard encontrado:")
            for dashboard in guatepass_dashboards:
                print(" - Nombre: " + dashboard['DashboardName'])
                print(" - Ultima modificacion: " + str(dashboard['LastModified']))
            return True
        else:
            print("No se encontro el dashboard de GuatePass")
            return False
            
    except Exception as e:
        print("Error verificando dashboard: " + str(e))
        return False

def verify_lambda_functions():
    """Verifica que las funciones Lambda existen"""
    lambda_client = boto3.client('lambda')
    
    print("\nVERIFICANDO FUNCIONES LAMBDA")
    print("=" * 50)
    
    expected_functions = [
        "tags-management-dev",
        "transaction-processor-dev",
        "webhook-validator-dev",
        "notification-handler-dev", 
        "payment-history-dev",
        "invoice-history-dev"
    ]
    
    try:
        response = lambda_client.list_functions()
        functions = response['Functions']
        
        existing_functions = [func['FunctionName'] for func in functions]
        guatepass_functions = [func for func in existing_functions if any(name in func for name in expected_functions)]
        
        print("Funciones Lambda de GuatePass encontradas:")
        for func in sorted(guatepass_functions):
            print(" - " + func)
        
        missing_functions = [func for func in expected_functions if func not in existing_functions]
        
        if missing_functions:
            print("Funciones faltantes:")
            for func in missing_functions:
                print(" - " + func)
            return False
        else:
            print("Todas las funciones Lambda estan desplegadas")
            return True
            
    except Exception as e:
        print("Error verificando funciones Lambda: " + str(e))
        return False

def verify_metrics_available():
    """Verifica que las metricas estan disponibles"""
    cloudwatch = boto3.client('cloudwatch')
    
    print("\nVERIFICANDO METRICAS DISPONIBLES")
    print("=" * 50)
    
    namespaces = ['AWS/Lambda', 'AWS/ApiGateway', 'AWS/DynamoDB']
    
    for namespace in namespaces:
        try:
            response = cloudwatch.list_metrics(Namespace=namespace)
            metrics = response['Metrics']
            print(namespace + ": " + str(len(metrics)) + " metricas disponibles")
        except Exception as e:
            print("Error obteniendo metricas para " + namespace + ": " + str(e))

if __name__ == "__main__":
    verify_dashboard_exists()
    verify_lambda_functions()
    verify_metrics_available()