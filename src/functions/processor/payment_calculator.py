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
        
        # Aplicar lógica según tipo de usuario
        if user_type == 'no_registrado':
            # Modalidad 1: No registrado - tarifa premium + multa
            monto = (tarifa_base * self.recargo_no_registrado) + self.multa_tardia
            
        elif user_type == 'registrado':
            if has_tag:
                # Modalidad 3: Con Tag - descuento
                monto = tarifa_base * self.descuento_tag
            else:
                # Modalidad 2: Registrado app - tarifa normal
                monto = tarifa_base
        else:
            # Por defecto, tarifa base
            monto = tarifa_base
        
        return monto.quantize(Decimal('0.01'))

    def procesar_pago(self, placa: str, monto: Decimal, user_type: str, dynamodb_table) -> bool:
        """Procesa el pago deduciendo del saldo disponible - USANDO DECIMAL"""
        
        try:
            if user_type == 'no_registrado':
                # No registrados no tienen saldo, se genera factura
                return True
                
            # Para usuarios registrados, verificar y deducir saldo
            response = dynamodb_table.get_item(Key={'placa': placa})
            
            if 'Item' not in response:
                print(f" Usuario no encontrado: {placa}")
                return False
                
            usuario = response['Item']
            saldo_actual = usuario.get('saldo_disponible', Decimal('0'))
            
            print(f"💰 Saldo actual {placa}: {saldo_actual}, Monto a deducir: {monto}")
            
            if saldo_actual >= monto:
                # Actualizar saldo - USANDO DECIMAL directamente
                nuevo_saldo = saldo_actual - monto
                print(f" Actualizando saldo {placa}: {saldo_actual} -> {nuevo_saldo}")
                
                dynamodb_table.update_item(
                    Key={'placa': placa},
                    UpdateExpression='SET saldo_disponible = :nuevo_saldo',
                    ExpressionAttributeValues={':nuevo_saldo': nuevo_saldo}
                )
                print(f" Pago exitoso: {placa} - {monto}Q")
                return True
            else:
                # Saldo insuficiente
                print(f" Saldo insuficiente para {placa}. Saldo: {saldo_actual}, Requerido: {monto}")
                return False
                
        except Exception as e:
            print(f" Error procesando pago para {placa}: {str(e)}")
            return False
