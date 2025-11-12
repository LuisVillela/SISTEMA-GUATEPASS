#!/usr/bin/env python3
import boto3
import json

def debug_processor():
    print("=== DIAGNÓSTICO LAMBDA PROCESSOR ===\n")
    
    # 1. Verificar tablas existentes
    dynamodb = boto3.client('dynamodb')
    tables = dynamodb.list_tables()['TableNames']
    guatepass_tables = [t for t in tables if 'guatepass' in t]
    
    print(" TABLAS DYNAMODB EXISTENTES:")
    for table in guatepass_tables:
        print(f"   {table}")
    
    # 2. Verificar contenido de cada tabla
    dynamodb_resource = boto3.resource('dynamodb')
    
    print("\n CONTENIDO DE TABLAS:")
    for table_name in guatepass_tables:
        try:
            table = dynamodb_resource.Table(table_name)
            response = table.scan(Limit=5)
            count = len(response.get('Items', []))
            print(f"  {table_name}: {count} registros")
            
            if count > 0 and 'transaction' in table_name.lower():
                print("  └─ Primeras transacciones:")
                for item in response['Items'][:2]:
                    print(f"     - {item.get('transaction_id', 'N/A')}")
                    
        except Exception as e:
            print(f"  {table_name}: ERROR - {str(e)}")
    
    # 3. Verificar configuración Lambda
    print("\n CONFIGURACIÓNDE LAMBDA:")
    lambda_client = boto3.client('lambda')
    try:
        response = lambda_client.get_function(FunctionName='transaction-processor-dev')
        env_vars = response['Configuration'].get('Environment', {}).get('Variables', {})
        print("  Variables de entorno:")
        for key, value in env_vars.items():
            print(f"    {key}: {value}")
    except Exception as e:
        print(f"  Error: {str(e)}")

if __name__ == "__main__":
    debug_processor()
