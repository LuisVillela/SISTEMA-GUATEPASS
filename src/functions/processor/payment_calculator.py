import os
from decimal import Decimal

class PaymentCalculator:
    def __init__(self):
        # Tarifas base por peaje (en quetzales) - USANDO DECIMAL
        self.tarifas_base = {
            'PEAJE_ZONA10': Decimal('25.00'),
            'PEAJE_ZONA11': Decimal('30.00'),
            'PEAJE_ZONA12': Decimal('20.00'),
            'PEAJE_ZONA13': Decimal('35.00')
        }
        
        # Recargos y descuentos - USANDO DECIMAL
        self.recargo_no_registrado = Decimal('1.5')  # 50% más
        self.multa_tardia = Decimal('15.00')         # Multa fija
        self.descuento_tag = Decimal('0.9')          # 10% descuento

    def calcular_monto(self, peaje_id: str, user_type: str, has_tag: bool) -> Decimal:
        """Calcula el monto a cobrar según el tipo de usuario"""
        
        # Obtener tarifa base
        tarifa_base = self.tarifas_base.get(peaje_id, Decimal('25.00'))
        
        print(f"🔧 CALCULANDO MONTO: peaje={peaje_id}, user_type={user_type}, has_tag={has_tag}, tarifa_base={tarifa_base}")
        
        # Aplicar lógica según tipo de usuario
        if user_type == 'no_registrado':
            # Modalidad 1: No registrado - tarifa premium + multa
            monto = (tarifa_base * self.recargo_no_registrado) + self.multa_tardia
            print(f"   💰 No registrado: {tarifa_base} * 1.5 + {self.multa_tardia} = {monto}")
            
        elif user_type == 'registrado':
            if has_tag:
                # Modalidad 3: Con Tag - descuento
                monto = tarifa_base * self.descuento_tag
                print(f"   💰 Registrado con tag: {tarifa_base} * 0.9 = {monto}")
            else:
                # Modalidad 2: Registrado app - tarifa normal
                monto = tarifa_base
                print(f"   💰 Registrado sin tag: {tarifa_base}")
        else:
            # Por defecto, tarifa base
            monto = tarifa_base
            print(f"   💰 Tipo desconocido, usando tarifa base: {tarifa_base}")
        
        monto_final = monto.quantize(Decimal('0.01'))
        print(f"   ✅ MONTO FINAL: {monto_final}")
        return monto_final

    def procesar_pago(self, placa: str, monto: Decimal, user_type: str, dynamodb_table) -> bool:
        """Procesa el pago deduciendo del saldo disponible - USANDO DECIMAL"""
        
        print(f"🔄 INICIANDO PROCESO DE PAGO: {placa}, monto={monto}, user_type={user_type}")
        
        try:
            # Para TODOS los usuarios, verificar y deducir saldo
            response = dynamodb_table.get_item(Key={'placa': placa})
            
            if 'Item' not in response:
                print(f"❌ Usuario no encontrado: {placa}")
                return False
                
            usuario = response['Item']
            saldo_actual = usuario.get('saldo_disponible', Decimal('0'))
            
            # Asegurarnos que saldo_actual es Decimal
            if not isinstance(saldo_actual, Decimal):
                saldo_actual = Decimal(str(saldo_actual))
            
            print(f"💰 VERIFICANDO SALDO: {placa}")
            print(f"   Saldo actual: {saldo_actual}")
            print(f"   Monto a deducir: {monto}")
            print(f"   Tipo de saldo: {type(saldo_actual)}")
            print(f"   Tipo de monto: {type(monto)}")
            
            if saldo_actual >= monto:
                # Actualizar saldo - USANDO DECIMAL directamente
                nuevo_saldo = saldo_actual - monto
                print(f"✅ SALDO SUFICIENTE")
                print(f"   Actualizando saldo: {saldo_actual} - {monto} = {nuevo_saldo}")
                
                # Actualizar en DynamoDB
                dynamodb_table.update_item(
                    Key={'placa': placa},
                    UpdateExpression='SET saldo_disponible = :nuevo_saldo',
                    ExpressionAttributeValues={
                        ':nuevo_saldo': nuevo_saldo
                    },
                    ReturnValues='UPDATED_NEW'
                )
                
                # Verificar que se actualizó
                response_verificacion = dynamodb_table.get_item(Key={'placa': placa})
                saldo_verificado = response_verificacion['Item'].get('saldo_disponible', Decimal('0'))
                print(f"✅ PAGO EXITOSO: {placa} - {monto}Q")
                print(f"   Saldo verificado después: {saldo_verificado}")
                return True
            else:
                # Saldo insuficiente
                print(f"❌ SALDO INSUFICIENTE")
                print(f"   Saldo actual: {saldo_actual}")
                print(f"   Monto requerido: {monto}")
                print(f"   Diferencia: {monto - saldo_actual}")
                return False
                
        except Exception as e:
            print(f"❌ ERROR PROCESANDO PAGO: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def verificar_saldo_actual(self, placa: str, dynamodb_table) -> Decimal:
        """Verifica el saldo actual de un usuario (para debugging)"""
        try:
            response = dynamodb_table.get_item(Key={'placa': placa})
            if 'Item' in response:
                saldo = response['Item'].get('saldo_disponible', Decimal('0'))
                if not isinstance(saldo, Decimal):
                    saldo = Decimal(str(saldo))
                print(f"📊 SALDO ACTUAL {placa}: {saldo}")
                return saldo
            else:
                print(f"📊 USUARIO NO ENCONTRADO: {placa}")
                return Decimal('0')
        except Exception as e:
            print(f"❌ ERROR VERIFICANDO SALDO: {e}")
            return Decimal('0')