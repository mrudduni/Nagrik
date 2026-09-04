import json
import os
from typing import Dict, List, Any

SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "schemas")

class SchemaParser:
    def __init__(self, schema_id: str):
        self.schema_id = schema_id
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        path = os.path.join(SCHEMAS_DIR, f"{self.schema_id}.json")
        if not os.path.exists(path):
            # Fallback for old schema if name is just public_grievance without .json
            # Wait, schemas are usually .json
            pass
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _is_condition_met(self, condition: Dict[str, Any], state_data: Dict[str, Any]) -> bool:
        field_name = condition.get("field")
        if not field_name or field_name not in state_data:
            return False
            
        field_state = state_data[field_name]
        
        # Only evaluate dependencies if the field is VALID
        if field_state.get("status") != "VALID":
            return False
            
        value = field_state.get("value")

        if "equals" in condition:
            eq_val = condition["equals"]
            if isinstance(eq_val, list):
                return value in eq_val
            return value == eq_val
            
        if "in" in condition:
            return value in condition["in"]
            
        return False

    def get_required_fields(self, state_data: Dict[str, Any]) -> List[str]:
        required_fields = set()
        fields = {f.get("id", f.get("name")): f for f in self.schema.get("fields", [])} # Fallback to "name" for old schemas
        
        # 1. Base required fields
        for field_id, field in fields.items():
            if field.get("required") is True:
                required_fields.add(field_id)
                
        # 2. Inline dependencies (depends_on)
        for field_id, field in fields.items():
            depends_on = field.get("depends_on")
            if depends_on:
                if self._is_condition_met(depends_on, state_data):
                    if depends_on.get("becomes") == "required":
                        required_fields.add(field_id)
                        
        # 3. Global dependencies
        for dep in self.schema.get("dependencies", []):
            condition = dep.get("if")
            if condition and self._is_condition_met(condition, state_data):
                for req_field in dep.get("then_required", []):
                    required_fields.add(req_field)
                    
        return list(required_fields)

    def get_missing_fields(self, state_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        required_ids = self.get_required_fields(state_data)
        missing = []
        
        for field in self.schema.get("fields", []):
            field_id = field.get("id", field.get("name"))
            if field_id in required_ids:
                # Missing if not in state_data or not VALID
                field_state = state_data.get(field_id)
                if not field_state or field_state.get("status") != "VALID":
                    missing.append(field)
                    
        return missing

    def get_field_metadata(self, field_id: str) -> Dict[str, Any]:
        for field in self.schema.get("fields", []):
            if field.get("id", field.get("name")) == field_id:
                return field
        return {}
