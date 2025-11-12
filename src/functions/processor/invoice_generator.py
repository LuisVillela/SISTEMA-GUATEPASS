import uuid
from datetime import datetime
from decimal import Decimal

class InvoiceGenerator:
    def generar_factura(self, placa: str, peaje_id: str, monto: Decimal, user_type: str) -> dict:
        """Genera una factura simulada para usuarios no registrados"""
        
        factura_id = f"FACT-{uuid.uuid4().hex[:8].upper()}"
        
        factura = {
            'factura_id': factura_id,
            'placa': placa,
            'peaje_id': peaje_id,
            'monto': monto,
            'fecha_emision': datetime.utcnow().isoformat() + 'Z',
            'concepto': f'Cobro de peaje {peaje_id}',
            'estado': 'pendiente',
            'tipo_usuario': user_type,
            'datos_contribuyente': {
                'nombre': 'SISTEMA GUATEPASS',
                'nit': 'CF-00000000',
                'direccion': 'Ciudad de Guatemala'
            }
        }
        
        # Agregar detalles específicos por tipo de usuario
        if user_type == 'no_registrado':
            factura['detalles'] = {
                'tarifa_base': self._obtener_tarifa_base(peaje_id),
                'recargo_premium': '50%',
                'multa_tardia': 'Q15.00',
                'mensaje': 'Regístrese en GuatePass para evitar recargos'
            }
        
        return factura
    
    def _obtener_tarifa_base(self, peaje_id: str) -> Decimal:
        """Obtiene tarifa base para el peaje"""
        tarifas = {
            'PEAJE_ZONA10': Decimal('25.00'),
            'PEAJE_ZONA11': Decimal('30.00'),
            'PEAJE_ZONA12': Decimal('20.00'),
            'PEAJE_ZONA13': Decimal('35.00')
        }
        return tarifas.get(peaje_id, Decimal('25.00'))