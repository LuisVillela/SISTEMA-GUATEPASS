#!/usr/bin/env python3
import boto3
import json
from decimal import Decimal

def verify_data():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('guatepass-users-dev')
    
    print("Verificando datos en DynamoDB...")
    
    # Escanear toda la tabla
    response = table.scan()
    items = response.get('Items', [])
    
    print(f"\nTotal de usuarios cargados: {len(items)}")
    
    for item in items:
        print(f"Placa: {item['placa']}, Nombre: {item['nombre']}, Tipo: {item['tipo_usuario']}, Saldo: {item['saldo_disponible']}")
    
    # Verificar usuarios específicos
    test_placas = ['P-123ABC', 'P-456DEF', 'P-789GHI']
    
    print(f"\nVerificando usuarios de prueba:")
    for placa in test_placas:
        try:
            response = table.get_item(Key={'placa': placa})
            if 'Item' in response:
                user = response['Item']
                print(f"{placa}: {user['nombre']} ({user['tipo_usuario']}) - Saldo: {user['saldo_disponible']}")
            else:
                print(f"{placa}: NO ENCONTRADO")
        except Exception as e:
            print(f"{placa}: ERROR - {str(e)}")

if __name__ == "__main__":
    verify_data()
