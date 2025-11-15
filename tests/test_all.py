#!/usr/bin/env python3
import boto3
import json
import requests
import time
from datetime import datetime, timezone

class GuatePassTester:
    def __init__(self, api_url):
        self.api_url = api_url
        self.dynamodb = boto3.resource('dynamodb')
        self.transactions_table = self.dynamodb.Table('guatepass-transactions-dev')
        
    def test_scenario_1_no_registrado(self):
        """
        Prueba Modalidad 1: Usuario No Registrado (Cobro Tradicional)
        """
        print("=" * 70)
        print("PRUEBA 1: USUARIO NO REGISTRADO (Cobro Tradicional)")
        print("=" * 70)
        
        test_data = {
            "placa": "P-789GHI",
            "peaje_id": "PEAJE_ZONA10",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print("Enviando transaccion de usuario no registrado...")
        print(f"Datos: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(
            f"{self.api_url}/webhook/toll",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_data)
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        # Esperar procesamiento
        time.sleep(10)
        
        # Verificar en base de datos
        self.verify_transaction_in_db("P-789GHI", "no_registrado_tradicional")
        
        print("RESULTADOS ESPERADOS:")
        print("- Debe generar una FACTURA con recargo premium")
        print("- Debe enviar invitacion a registro por correo/SMS")
        print("- No debe realizar cobro a tarjeta")
        print("- Debe guardarse como tipo 'no_registrado_tradicional'")
        print("=" * 70)
        
    def test_scenario_2_registrado_digital(self):
        """
        Prueba Modalidad 2: Usuario Registrado en App (Cobro Digital)
        """
        print("=" * 70)
        print("PRUEBA 2: USUARIO REGISTRADO (Cobro Digital)")
        print("=" * 70)
        
        test_data = {
            "placa": "P-123ABC",
            "peaje_id": "PEAJE_ZONA11",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print("Enviando transaccion de usuario registrado...")
        print(f"Datos: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(
            f"{self.api_url}/webhook/toll",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_data)
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        # Esperar procesamiento
        time.sleep(10)
        
        # Verificar en base de datos
        self.verify_transaction_in_db("P-123ABC", "registrado_digital")
        
        print("RESULTADOS ESPERADOS:")
        print("- Debe realizar cobro a tarjeta de credito/debito")
        print("- Debe enviar notificacion de pago exitoso")
        print("- No debe generar factura")
        print("- Debe guardarse como tipo 'registrado_digital'")
        print("- Monto debe ser tarifa normal (sin recargos)")
        print("=" * 70)
        
    def test_scenario_3_tag_express(self):
        """
        Prueba Modalidad 3: Usuario con Dispositivo Tag (Cobro Express)
        """
        print("=" * 70)
        print("PRUEBA 3: USUARIO CON TAG (Cobro Express)")
        print("=" * 70)
        
        test_data = {
            "placa": "P-456DEF",
            "peaje_id": "PEAJE_ZONA12",
            "tag_id": "TAG-002",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print("Enviando transaccion de usuario con tag...")
        print(f"Datos: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(
            f"{self.api_url}/webhook/toll",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_data)
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        # Esperar procesamiento
        time.sleep(10)
        
        # Verificar en base de datos
        self.verify_transaction_in_db("P-456DEF", "tag_express")
        
        print("RESULTADOS ESPERADOS:")
        print("- Debe aplicar descuento del 10% por tag")
        print("- Debe usar metodo de pago configurado en el tag")
        print("- Debe ser procesamiento mas rapido (express)")
        print("- Debe enviar notificacion de cobro express")
        print("- Debe guardarse como tipo 'tag_express'")
        print("=" * 70)
        
    def test_scenario_4_pago_fallido(self):
        """
        Prueba adicional: Pago fallido para usuario registrado
        """
        print("=" * 70)
        print("PRUEBA 4: PAGO FALLIDO (Escenario de error)")
        print("=" * 70)
        
        test_data = {
            "placa": "P-111JKL",
            "peaje_id": "PEAJE_ZONA13",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print("Enviando transaccion que puede fallar (5% probabilidad)...")
        print(f"Datos: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(
            f"{self.api_url}/webhook/toll",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_data)
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        # Esperar procesamiento
        time.sleep(10)
        
        # Verificar en base de datos
        transactions = self.get_transactions_by_placa("P-111JKL")
        if transactions:
            last_tx = transactions[0]
            pago_exitoso = last_tx.get('resultado', {}).get('pago', {}).get('exitoso', True)
            
            if not pago_exitoso:
                print("PAGO FALLIDO DETECTADO - Comportamiento correcto")
                print("RESULTADOS ESPERADOS:")
                print("- Debe enviar notificacion de pago fallido")
                print("- Debe indicar error en el resultado")
                print("- No debe generar factura")
            else:
                print("PAGO EXITOSO - Comportamiento normal")
        else:
            print("No se encontraron transacciones para verificar")
            
        print("=" * 70)
    
    def verify_transaction_in_db(self, placa, expected_scenario):
        """
        Verifica que la transaccion se guardo correctamente en DynamoDB
        """
        print("Verificando transaccion en base de datos...")
        
        transactions = self.get_transactions_by_placa(placa)
        
        if transactions:
            last_tx = transactions[0]
            print("Transaccion encontrada en DynamoDB:")
            print(f"- Transaction ID: {last_tx.get('transaction_id')}")
            print(f"- Tipo Escenario: {last_tx.get('tipo_escenario')}")
            print(f"- User Type: {last_tx.get('user_type')}")
            print(f"- Monto: {last_tx.get('monto')}")
            print(f"- Peaje: {last_tx.get('peaje_id')}")
            
            if last_tx.get('tipo_escenario') == expected_scenario:
                print("VERIFICACION: CORRECTA - Escenario coincide")
            else:
                print(f"VERIFICACION: ERROR - Esperado {expected_scenario}, obtenido {last_tx.get('tipo_escenario')}")
                
            # Verificar detalles especificos por escenario
            if expected_scenario == "no_registrado_tradicional":
                factura = last_tx.get('resultado', {}).get('factura', {})
                if factura:
                    print(f"- Factura ID: {factura.get('factura_id')}")
                    print(f"- Cargo Premium: {factura.get('cargo_premium')}")
                else:
                    print("VERIFICACION: ERROR - No se genero factura")
                    
            elif expected_scenario in ["registrado_digital", "tag_express"]:
                pago = last_tx.get('resultado', {}).get('pago', {})
                if pago:
                    print(f"- Pago Exitoso: {pago.get('exitoso')}")
                    print(f"- Metodo Pago: {pago.get('metodo_pago')}")
                else:
                    print("VERIFICACION: ERROR - No hay info de pago")
                    
        else:
            print("VERIFICACION: ERROR - No se encontro transaccion en la base de datos")
    
    def get_transactions_by_placa(self, placa):
        """
        Obtiene transacciones de una placa especifica
        """
        try:
            response = self.transactions_table.scan(
                FilterExpression='placa = :placa',
                ExpressionAttributeValues={':placa': placa}
            )
            transactions = response.get('Items', [])
            # Ordenar por timestamp descendente
            transactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return transactions
        except Exception as e:
            print(f"Error consultando base de datos: {e}")
            return []
    
    def check_notification_logs(self):
        """
        Verifica los logs de notificaciones en CloudWatch
        """
        print("=" * 70)
        print("VERIFICANDO LOGS DE NOTIFICACIONES")
        print("=" * 70)
        
        print("Para ver las notificaciones simuladas, revisa los logs de CloudWatch:")
        print("1. Ve a AWS Console > CloudWatch > Log groups")
        print("2. Busca: /aws/lambda/notification-handler-dev")
        print("3. Revisa los log streams mas recientes")
        print("")
        print("Deberias ver mensajes como:")
        print("- [EMAIL SIMULADO] Para: email@ejemplo.com")
        print("- [SMS SIMULADO] Para: 50212345678")
        print("- Contenido de facturas, pagos exitosos, pagos fallidos, etc.")
        print("=" * 70)

def main():
    # Obtener URL de la API
    try:
        cloudformation = boto3.client('cloudformation')
        stacks = cloudformation.describe_stacks(StackName='guatepass-stack')
        outputs = stacks['Stacks'][0]['Outputs']
        
        api_url = None
        for output in outputs:
            if output['OutputKey'] == 'ApiUrl':
                api_url = output['OutputValue']
                break
                
        if not api_url:
            print("No se pudo obtener la URL de la API. Usando valor por defecto.")
            api_url = "https://tu-api-id.execute-api.us-east-1.amazonaws.com/dev"
            
    except Exception as e:
        print(f"Error obteniendo URL de la API: {e}")
        api_url = "https://tu-api-id.execute-api.us-east-1.amazonaws.com/dev"
    
    print(f"Usando API URL: {api_url}")
    print("")
    
    tester = GuatePassTester(api_url)
    
    # Ejecutar pruebas
    tester.test_scenario_1_no_registrado()
    time.sleep(5)
    
    tester.test_scenario_2_registrado_digital()
    time.sleep(5)
    
    tester.test_scenario_3_tag_express()
    time.sleep(5)
    
    tester.test_scenario_4_pago_fallido()
    
    # Verificar logs
    tester.check_notification_logs()
    
    print("")
    print("PRUEBAS COMPLETADAS")
    print("Revisa los logs de CloudWatch para ver las notificaciones simuladas")

if __name__ == "__main__":
    main()