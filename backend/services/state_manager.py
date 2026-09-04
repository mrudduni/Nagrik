from sqlalchemy.orm import Session
from typing import Dict, Any, Tuple
from backend.db.models import FormSession
from backend.services.schema_parser import SchemaParser
from backend.services.validation_service import ValidationService

class StateManager:
    def __init__(self, db: Session, session_id: str):
        self.db = db
        self.session_id = session_id
        self.session = self.db.query(FormSession).filter(FormSession.id == session_id).first()
        if not self.session:
            raise ValueError(f"Session {session_id} not found")
        self.schema_parser = SchemaParser(self.session.schema_id)

    def get_missing_fields(self):
        """Returns the list of fields still required."""
        return self.schema_parser.get_missing_fields(self.session.state_data)

    def update_field(self, field_id: str, value: Any, confidence: float = 1.0) -> Tuple[bool, str]:
        """
        Updates a field in the form state. 
        Returns (success, message).
        """
        field_metadata = self.schema_parser.get_field_metadata(field_id)
        if not field_metadata:
            return False, f"Field '{field_id}' does not exist in schema."

        # Integrate ValidationService
        is_valid, msg, normalized_value = ValidationService.validate(field_metadata, value)
        if not is_valid:
            return False, msg
            
        value = normalized_value

        # Check for confirmation requirements
        requires_conf = field_metadata.get("requires_confirmation", False)
        
        # Check global confirmation fields
        conf_req_fields = self.schema_parser.schema.get("confirmation_required_fields", [])
        if field_id in conf_req_fields:
            requires_conf = True

        threshold = field_metadata.get("confidence_threshold", 0.8)

        status = "VALID"
        if requires_conf or confidence < threshold:
            status = "UNCONFIRMED"

        # Update state data
        # We need to explicitly copy and reassign so SQLAlchemy detects the JSON change
        state_data = dict(self.session.state_data)
        state_data[field_id] = {
            "value": value,
            "status": status,
            "confidence": confidence
        }
        self.session.state_data = state_data

        # Recalculate missing fields
        # Note: missing_fields in DB just stores IDs, but our get_missing_fields returns full metadata.
        # It's better to store just the IDs or not store it at all (calculate on the fly).
        # We'll calculate on the fly when needed, but we can store required_fields IDs.
        self.session.missing_fields = self.schema_parser.get_required_fields(state_data)
        
        self.db.commit()

        if status == "UNCONFIRMED":
            return True, f"Value recorded but requires explicit user confirmation."
            
        return True, "Field updated successfully."

    def confirm_field(self, field_id: str) -> Tuple[bool, str]:
        state_data = dict(self.session.state_data)
        if field_id not in state_data:
            return False, "Field not found in state."
            
        if state_data[field_id]["status"] != "UNCONFIRMED":
            return False, "Field does not require confirmation."

        state_data[field_id]["status"] = "VALID"
        self.session.state_data = state_data
        
        # We must recalculate missing fields because making a field VALID might trigger new dependencies
        self.session.missing_fields = self.schema_parser.get_required_fields(state_data)
        self.db.commit()
        return True, "Field confirmed."
