import re
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import boto3
import os

class WebhookValidator:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.tags_table = self.dynamodb.Table(os.environ['TAGS_TABLE'])
        self.users_table = self.dynamodb.Table(os.environ['USERS_TABLE'])
    
    @staticmethod
    def validate_structure(event: Dict) -> Tuple[bool, str]:
        if 'body' not in event:
            return False, "Missing body in request"
        if not event.get('body'):
            return False, "Empty body"
        return True, "OK"
    
    @staticmethod
    def validate_json_body(body: str) -> Tuple[bool, str, Dict]:
        try:
            import json
            data = json.loads(body)
            return True, "OK", data
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}", {}
    
    def validate_required_fields(self, data: Dict) -> Tuple[bool, str]:
        """Valida que haya placa O tag_id, pero al menos uno"""
        has_placa = 'placa' in data and data['placa']
        has_tag_id = 'tag_id' in data and data['tag_id']
        
        if not has_placa and not has_tag_id:
            return False, "Either 'placa' or 'tag_id' must be provided"
        
        if not data.get('peaje_id'):
            return False, "Missing required field: peaje_id"
            
        if not data.get('timestamp'):
            return False, "Missing required field: timestamp"
            
        return True, "OK"
    
    @staticmethod
    def validate_placa_format(placa: str) -> Tuple[bool, str]:
        if not placa:
            return True, "OK"  # Placa es opcional si hay tag_id
        
        pattern = r'^[A-Z0-9]{1,3}-[A-Z0-9]{3,6}$'
        if not re.match(pattern, placa):
            return False, "Invalid placa format. Expected: P-123ABC"
        return True, "OK"
    
    @staticmethod
    def validate_timestamp(timestamp: str) -> Tuple[bool, str]:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now(dt.tzinfo)
            
            if dt > now:
                return False, "Timestamp cannot be in the future"
            
            time_diff = now - dt
            if time_diff.total_seconds() > 86400:
                return False, "Timestamp too old"
                
            return True, "OK"
        except ValueError as e:
            return False, f"Invalid timestamp format: {str(e)}"
    
    @staticmethod
    def validate_peaje_id(peaje_id: str) -> Tuple[bool, str]:
        valid_peajes = ['PEAJE_ZONA10', 'PEAJE_ZONA11', 'PEAJE_ZONA12', 'PEAJE_ZONA13']
        if peaje_id not in valid_peajes:
            return False, f"Invalid peaje_id. Must be one of: {valid_peajes}"
        return True, "OK"
    
    def validate_tag_id_format(self, tag_id: str) -> Tuple[bool, str]:
        """Valida solo el formato del tag_id"""
        if not tag_id:
            return True, "OK"
            
        if not re.match(r'^TAG-\d{1,3}$', tag_id):
            return False, "Invalid tag_id format. Expected: TAG-001"
        
        return True, "OK"
    
    def resolve_placa_from_tag(self, tag_id: str) -> Tuple[bool, str, Optional[str]]:
        """Resuelve la placa a partir del tag_id"""
        if not tag_id:
            return False, "No tag_id provided", None
        
        try:
            response = self.tags_table.get_item(Key={'tag_id': tag_id})
            if 'Item' not in response:
                return False, f"Tag ID not found: {tag_id}", None
            
            tag_info = response['Item']
            placa = tag_info.get('placa')
            
            if not placa:
                return False, f"Tag {tag_id} is not associated with any vehicle", None
            
            # Verificar que la placa existe
            user_response = self.users_table.get_item(Key={'placa': placa})
            if 'Item' not in user_response:
                return False, f"Associated placa {placa} not found in system", None
            
            return True, "Placa resolved successfully", placa
            
        except Exception as e:
            return False, f"Error resolving placa from tag: {str(e)}", None
    
    def validate_tag_association(self, tag_id: str, placa: str) -> Tuple[bool, str, Dict]:
        """Valida que el tag esté asociado a la placa correcta"""
        if not tag_id:
            return True, "OK", {}
        
        try:
            # Buscar el tag en la tabla de tags
            response = self.tags_table.get_item(Key={'tag_id': tag_id})
            if 'Item' not in response:
                return False, f"Tag ID not found: {tag_id}", {}
            
            tag_info = response['Item']
            
            # Verificar si el tag está activo
            if tag_info.get('estado') != 'activo':
                return False, f"Tag is not active: {tag_id}", {}
            
            # Obtener la placa asociada al tag
            tag_placa = tag_info.get('placa')
            if not tag_placa:
                return False, f"Tag {tag_id} is not associated with any vehicle", {}
            
            # Verificar que el tag esté asociado a la placa proporcionada
            if placa != tag_placa:
                return False, f"Tag {tag_id} is associated with placa {tag_placa}, not {placa}", {}
            
            # Verificar que la placa existe en la tabla de usuarios
            user_response = self.users_table.get_item(Key={'placa': placa})
            if 'Item' not in user_response:
                return False, f"Placa {placa} not found in system", {}
            
            user_info = user_response['Item']
            
            return True, "Tag validation successful", {
                'tag_info': tag_info,
                'user_info': user_info
            }
            
        except Exception as e:
            return False, f"Error validating tag association: {str(e)}", {}
    
    def validate_complete(self, event: Dict) -> Tuple[bool, str, Dict]:
        # Validar estructura HTTP
        is_valid, message = self.validate_structure(event)
        if not is_valid:
            return False, message, {}
        
        # Validar JSON
        is_valid, message, data = self.validate_json_body(event['body'])
        if not is_valid:
            return False, message, {}
        
        # Validar campos requeridos (placa O tag_id)
        is_valid, message = self.validate_required_fields(data)
        if not is_valid:
            return False, message, {}
        
        # Extraer datos
        original_placa = data.get('placa')
        tag_id = data.get('tag_id')
        
        # CASO 1: Solo tag_id (sin placa)
        if not original_placa and tag_id:
            # Resolver la placa desde el tag
            is_valid, message, resolved_placa = self.resolve_placa_from_tag(tag_id)
            if not is_valid:
                return False, f"Cannot process with tag: {message}", {}
            
            # Usar la placa resuelta del tag
            placa = resolved_placa
            data['placa'] = placa
            
        # CASO 2: Solo placa (sin tag_id)
        elif original_placa and not tag_id:
            # Solo validar que la placa existe
            placa = original_placa
            try:
                user_response = self.users_table.get_item(Key={'placa': placa})
                if 'Item' not in user_response:
                    return False, f"Placa {placa} not found in system", {}
            except Exception as e:
                return False, f"Error validating placa: {str(e)}", {}
        
        # CASO 3: Ambos (placa y tag_id)
        elif original_placa and tag_id:
            placa = original_placa
            # Validar que el tag esté asociado a esta placa específica
            is_valid, message, validation_result = self.validate_tag_association(tag_id, placa)
            if not is_valid:
                # ERROR: Tag no está asociado a esta placa - NO permitir
                return False, f"Tag validation failed: {message}", {}
        
        # CASO 4: Ninguno (ya fue validado arriba)
        else:
            return False, "Either 'placa' or 'tag_id' must be provided", {}
        
        # Validar formatos individuales
        validations = [
            (self.validate_placa_format, placa),
            (self.validate_timestamp, data['timestamp']),
            (self.validate_peaje_id, data['peaje_id']),
            (self.validate_tag_id_format, tag_id)
        ]
        
        for validation_func, value in validations:
            if value is not None:
                is_valid, message = validation_func(value)
                if not is_valid:
                    return False, message, {}
        
        # Preparar datos finales
        final_data = {
            **data,
            'placa': placa,
            'tag_id': tag_id,  # Mantener el tag_id original si existe
            'user_type': 'unknown'  # Será determinado en el procesador
        }
        
        # Si hay tag_id válido, agregar información adicional
        if tag_id:
            try:
                tag_response = self.tags_table.get_item(Key={'tag_id': tag_id})
                if 'Item' in tag_response:
                    final_data['tag_info'] = tag_response['Item']
            except Exception:
                pass  # No crítico si falla aquí
        
        return True, "Validation successful", final_data