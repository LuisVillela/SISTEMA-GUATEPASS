import re
from datetime import datetime
from typing import Dict, Any, Tuple
import boto3
import os

class WebhookValidator:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.tags_table = self.dynamodb.Table(os.environ['TAGS_TABLE'])
    
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
    
    @staticmethod
    def validate_required_fields(data: Dict) -> Tuple[bool, str]:
        required_fields = ['placa', 'peaje_id', 'timestamp']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Missing required field: {field}"
        return True, "OK"
    
    @staticmethod
    def validate_placa_format(placa: str) -> Tuple[bool, str]:
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
    
    def validate_tag_id(self, tag_id: str) -> Tuple[bool, str, Dict]:
        """Valida formato Y EXISTENCIA del tag_id"""
        if tag_id is None or tag_id == "":
            return True, "OK", {}  # Tag opcional
        
        if not re.match(r'^TAG-\d{1,3}$', tag_id):
            return False, "Invalid tag_id format. Expected: TAG-001", {}
        
        # Verificar si el tag existe y está activo en DynamoDB
        try:
            response = self.tags_table.get_item(Key={'tag_id': tag_id})
            if 'Item' not in response:
                return False, f"Tag ID not found: {tag_id}", {}
            
            tag_info = response['Item']
            if tag_info.get('estado') != 'activo':
                return False, f"Tag is not active: {tag_id}", {}
            
            return True, "OK", tag_info
            
        except Exception as e:
            return False, f"Error validating tag: {str(e)}", {}
    
    def validate_complete(self, event: Dict) -> Tuple[bool, str, Dict]:
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
            (self.validate_peaje_id, data['peaje_id'])
        ]
        
        for validation_func, value in validations:
            if value is not None:
                is_valid, message = validation_func(value)
                if not is_valid:
                    return False, message, {}
        
        # Validar tag_id (especial - puede retornar info adicional)
        tag_info = {}
        if 'tag_id' in data and data['tag_id']:
            is_valid, message, tag_info = self.validate_tag_id(data['tag_id'])
            if not is_valid:
                return False, message, {}
        
        return True, "Validation successful", {**data, 'tag_info': tag_info}
