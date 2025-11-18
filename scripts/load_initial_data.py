#!/usr/bin/env python3
import boto3
import csv
import os
import sys
from decimal import Decimal

def load_initial_data():
    # Especificar región explícitamente
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    table_name = 'guatepass-users-dev'
    
    try:
        table = dynamodb.Table(table_name)
        
        # Verificar que el archivo existe
        if not os.path.exists('data/clientes.csv'):
            print("ERROR: Archivo data/clientes.csv no encontrado")
            print(f"Directorio actual: {os.getcwd()}")
            sys.exit(1)
        
        with open('data/clientes.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            if not reader.fieldnames:
                print("ERROR: CSV vacío o sin columnas")
                sys.exit(1)
                
            print(f"Columnas detectadas: {reader.fieldnames}")
            
            has_metodo_pago = 'metodo_pago' in reader.fieldnames
            print(f"Columna 'metodo_pago' encontrada: {has_metodo_pago}")
            
            for row_num, row in enumerate(reader, 1):
                try:
                    placa = row['placa'].strip()
                    nombre = row['nombre'].strip()
                    
                    if not placa:
                        print(f"Advertencia: Placa vacía en fila {row_num}, saltando...")
                        continue
                    
                    # Convertir saldo
                    try:
                        saldo = Decimal(str(row['saldo_disponible']).strip())
                    except:
                        saldo = Decimal('0.0')
                    
                    # Crear item
                    item = {
                        'placa': placa,
                        'nombre': nombre,
                        'email': row['email'].strip() or None,
                        'telefono': row['telefono'].strip() or None,
                        'tipo_usuario': row['tipo_usuario'].strip(),
                        'tiene_tag': row['tiene_tag'].strip().lower() == 'true',
                        'tag_id': row['tag_id'].strip() or None,
                        'saldo_disponible': saldo
                    }
                    
                    # Agregar metodo_pago si existe
                    if has_metodo_pago and row['metodo_pago'].strip():
                        item['metodo_pago'] = row['metodo_pago'].strip()
                    else:
                        print(f"Info: No se agregó metodo_pago para {placa}")
                    
                    # Insertar con manejo de errores específico
                    table.put_item(Item=item)
                    print(f"[{row_num}] Cargado: {placa} - {nombre} - Saldo: {saldo}")
                    
                except Exception as e:
                    print(f"ERROR en fila {row_num}: {str(e)}")
                    continue
        
        print("\n¡Proceso completado!")
        
        # Verificar carga
        response = table.scan(Select='COUNT')
        print(f"Registros en tabla: {response['Count']}")
        
    except Exception as e:
        print(f"Error general: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    load_initial_data()