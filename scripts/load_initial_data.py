#!/usr/bin/env python3
import boto3
import csv
import os
import sys
from decimal import Decimal

def load_initial_data():
    dynamodb = boto3.resource('dynamodb')
    
    table_name = 'guatepass-users-dev'
    
    try:
        table = dynamodb.Table(table_name)
        
        # Verificar que el archivo existe
        if not os.path.exists('data/clientes.csv'):
            print("ERROR: Archivo data/clientes.csv no encontrado")
            sys.exit(1)
        
        with open('data/clientes.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Verificar que el CSV tiene las columnas esperadas
            if not reader.fieldnames:
                print("ERROR: CSV vacío o sin columnas")
                sys.exit(1)
                
            print(f"Columnas detectadas: {reader.fieldnames}")
            
            for row_num, row in enumerate(reader, 1):
                # Limpiar y validar datos
                placa = row['placa'].strip()
                nombre = row['nombre'].strip()
                
                # Convertir saldo a Decimal (NO float)
                try:
                    saldo = Decimal(str(row['saldo_disponible']).strip())
                except:
                    print(f"Advertencia: Saldo inválido para {placa}, usando 0.0")
                    saldo = Decimal('0.0')
                
                # Preparar item para DynamoDB
                item = {
                    'placa': placa,
                    'nombre': nombre,
                    'email': row['email'].strip() if row['email'].strip() else None,
                    'telefono': row['telefono'].strip() if row['telefono'].strip() else None,
                    'tipo_usuario': row['tipo_usuario'].strip(),
                    'tiene_tag': row['tiene_tag'].strip().lower() == 'true',
                    'tag_id': row['tag_id'].strip() if row['tag_id'].strip() else None,
                    'metodo_pago' : row['metodo_pago'].strip() if row['metodo_pago'].strip() else None,
                }
                
                # Insertar en DynamoDB
                table.put_item(Item=item)
                print(f"[{row_num}] Cargado: {placa} - {nombre} - Saldo: {saldo}")
        
        print("\n¡Datos iniciales cargados exitosamente!")
        
    except Exception as e:
        print(f"Error cargando datos: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    load_initial_data()