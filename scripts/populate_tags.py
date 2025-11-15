#!/usr/bin/env python3
import boto3
import json
from decimal import Decimal

def populate_tags():
    dynamodb = boto3.resource('dynamodb')
    tags_table = dynamodb.Table('guatepass-tags-dev')
    
    tags_data = [
        {
            'tag_id': 'TAG-001',
            'placa': 'P-456DEF',
            'estado': 'activo',
            'fecha_activacion': '2025-01-15T00:00:00Z',
            'metodo_pago': 'tarjeta_debito',
            'configuracion': {
                'notificaciones': True,
                'cobro_automatico': True
            }
        },
        {
            'tag_id': 'TAG-002', 
            'placa': 'P-333PQR',
            'estado': 'activo',
            'fecha_activacion': '2025-01-10T00:00:00Z',
            'metodo_pago': 'tarjeta_credito',
            'configuracion': {
                'notificaciones': False,
                'cobro_automatico': True
            }
        },
        {
            'tag_id': 'TAG-003',
            'placa': 'P-999ZZZ',
            'estado': 'inactivo',
            'fecha_activacion': '2025-01-05T00:00:00Z',
            'fecha_desactivacion': '2025-01-20T00:00:00Z',
            'metodo_pago': 'tarjeta_debito',
            'configuracion': {
                'notificaciones': True,
                'cobro_automatico': False
            }
        }
    ]
    
    print("Poblando tabla de tags...")
    
    for tag in tags_data:
        try:
            tags_table.put_item(Item=tag)
            print(f"Tag creado: {tag['tag_id']} - {tag['placa']} - Estado: {tag['estado']}")
        except Exception as e:
            print(f"Error creando tag {tag['tag_id']}: {str(e)}")
    
    print("Población de tags completada!")

if __name__ == "__main__":
    populate_tags()
