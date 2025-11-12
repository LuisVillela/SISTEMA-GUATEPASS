import re
from datetime import datetime
from typing import Dict, Any, Tuple

class WebhookValidator:
    @staticmethod
    def validate_structure(event: Dict) -> Tuple[bool, str]:
        """Valida la estructura básica del evento HTTP"""
        if 'body' not in event:
            return False, "Missing body in request"
        
        if not event.get('body'):
            return False, "Empty body"
            
        return True, "OK"
    
    @staticmethod
    def validate_json_body(body: str) -> Tuple[bool, str, Dict]:
        """Valida y parsea el JSON body"""
        try:
            import json
            data = json.loads(body)
            return True, "OK", data
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}", {}
    
    @staticmethod
    def validate_required_fields(data: Dict) -> Tuple[bool, str]:
        """Valida campos obligatorios"""
        required_fields = ['placa', 'peaje_id', 'timestamp']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        
        return True, "OK"
    
    @staticmethod
    def validate_placa_format(placa: str) -> Tuple[bool, str]:
        """Valida formato de placa guatemalteca"""
        pattern = r'^[A-Z0-9]{1,3}-[A-Z0-9]{3,6}$'
        if not re.match(pattern, placa):
            return False, "Invalid placa format. Expected: P-123ABC"
        return True, "OK"
    
    @staticmethod
    def validate_timestamp(timestamp: str) -> Tuple[bool, str]:
        """Valida formato de timestamp ISO 8601"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now(dt.tzinfo)
            
            # Verificar que no sea en el futuro
            if dt > now:
                return False, "Timestamp cannot be in the future"
            
            # Verificar que no sea muy antiguo (últimas 24 horas)
            time_diff = now - dt
            if time_diff.total_seconds() > 86400:  # 24 horas
                return False, "Timestamp too old"
                
            return True, "OK"
        except ValueError as e:
            return False, f"Invalid timestamp format: {str(e)}"
    
    @staticmethod
    def validate_peaje_id(peaje_id: str) -> Tuple[bool, str]:
        """Valida ID del peaje"""
        valid_peajes = ['PEAJE_ZONA10', 'PEAJE_ZONA11', 'PEAJE_ZONA12', 'PEAJE_ZONA13']
        if peaje_id not in valid_peajes:
            return False, f"Invalid peaje_id. Must be one of: {valid_peajes}"
        return True, "OK"
    
    @staticmethod
    def validate_tag_id(tag_id: str) -> Tuple[bool, str]:
        """Valida formato del tag_id"""
        if tag_id is None or tag_id == "":
            return True, "OK"  # Tag opcional
        
        if not re.match(r'^TAG-\d{3}$', tag_id):
            return False, "Invalid tag_id format. Expected: TAG-001"
        return True, "OK"
    
    def validate_complete(self, event: Dict) -> Tuple[bool, str, Dict]:
        """Ejecuta todas las validaciones"""
        # Validar estructura HTTP
        is_valid, message = self.validate_structure(event)
        if not is_valid:
            return False, message, {}
        
        # Validar JSON
        is_valid, message, data = self.validate_json_body(event['body'])
        if not is_valid:
            return False, message, {}
        
        # Validar campos requeridos
        is_valid, message = self.validate_required_fields(data)
        if not is_valid:
            return False, message, {}
        
        # Validar formatos individuales
        validations = [
            (self.validate_placa_format, data['placa']),
            (self.validate_timestamp, data['timestamp']),
            (self.validate_peaje_id, data['peaje_id']),
            (self.validate_tag_id, data.get('tag_id'))
        ]
        
        for validation_func, value in validations:
            if value is not None:  # Solo validar si el valor existe
                is_valid, message = validation_func(value)
                if not is_valid:
                    return False, message, {}
        
        return True, "Validation successful", data