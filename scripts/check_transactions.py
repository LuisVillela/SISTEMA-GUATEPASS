#!/usr/bin/env python3
import boto3
import json
from decimal import Decimal

def check_transactions():
    dynamodb = boto3.resource('dynamodb')
    
    print("=== VERIFICACIÓN DETALLADA ===")
    
    # 1. Verificar saldos de usuarios de prueba
    users_table = dynamodb.Table('guatepass-users-dev')
    test_users = ['P-123ABC', 'P-456DEF', 'P-789GHI']
    
    print("\n SALDOS ACTUALIZADOS:")
    for placa in test_users:
        try:
            response = users_table.get_item(Key={'placa': placa})
            if 'Item' in response:
                user = response['Item']
                print(f"  {placa}: {user.get('saldo_disponible', 'N/A')} Q - {user.get('tipo_usuario')}")
        except Exception as e:
            print(f"  {placa}: Error - {e}")
    
    # 2. Verificar transacciones registradas
    transactions_table = dynamodb.Table('guatepass-transactions-dev')
    
    try:
        response = transactions_table.scan()
        transactions = response.get('Items', [])
        
        print(f"\n TRANSACCIONES REGISTRADAS: {len(transactions)}")
        
        # Ordenar por timestamp más reciente
        transactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        for tx in transactions[:5]:  # Mostrar 5 más recientes
            print(f"  ├─ {tx.get('transaction_id')}")
            print(f"  │  Placa: {tx.get('placa')}")
            print(f"  │  Monto: {tx.get('monto')}Q")
            print(f"  │  Tipo: {tx.get('user_type')}")
            print(f"  │  Peaje: {tx.get('peaje_id')}")
            print(f"  └─ Timestamp: {tx.get('timestamp')[:19]}")
            
    except Exception as e:
        print(f"Error accediendo a transacciones: {e}")

if __name__ == "__main__":
    check_transactions()
