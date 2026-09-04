import re
from datetime import datetime
from typing import Tuple, Any, Dict

class ValidationService:
    @staticmethod
    def validate(field_metadata: Dict[str, Any], value: Any) -> Tuple[bool, str, Any]:
        """
        Validates the value against field metadata.
        Returns (is_valid, error_message, normalized_value).
        """
        field_type = field_metadata.get("type", "string")
        
        # 1. Type Validation
        if field_type == "enum":
            options = field_metadata.get("options", [])
            # Be forgiving with case
            val_str = str(value).strip().lower()
            matched = False
            for opt in options:
                if opt.lower() == val_str:
                    value = opt # Normalize to exact case defined in options
                    matched = True
                    break
            if not matched:
                return False, f"Value must be one of: {', '.join(options)}", value
                
        elif field_type == "boolean":
            if not isinstance(value, bool):
                val_str = str(value).strip().lower()
                if val_str in ["true", "1", "yes", "y"]:
                    value = True
                elif val_str in ["false", "0", "no", "n"]:
                    value = False
                else:
                    return False, "Value must be a boolean (yes/no)", value

        elif field_type == "date":
            # For simplicity, expect YYYY-MM-DD from LLM (ISO format)
            try:
                date_val = datetime.strptime(str(value).strip(), "%Y-%m-%d")
            except ValueError:
                return False, "Date must be in YYYY-MM-DD format", value
                
        # 2. Validation Constraints (regex, not_future, min_age_years, etc)
        val_rules = field_metadata.get("validation", {})
        
        if "regex" in val_rules:
            if not re.match(val_rules["regex"], str(value)):
                return False, "Value does not match the required format", value
                
        if "max_length" in val_rules:
            if len(str(value)) > val_rules["max_length"]:
                return False, f"Value exceeds maximum length of {val_rules['max_length']} characters", value
                
        if "no_titles" in val_rules:
            titles = val_rules["no_titles"] if isinstance(val_rules["no_titles"], list) else ["Mr", "Mrs", "Dr", "Shri", "Smt", "Kumari"]
            for title in titles:
                # Basic check using word boundaries
                if re.search(rf"\b{title}\b", str(value), re.IGNORECASE):
                    return False, f"Name should not contain titles like '{title}'", value
                    
        if field_type == "date":
            # date_val is guaranteed to be a datetime object here
            if val_rules.get("not_future"):
                if date_val > datetime.now():
                    return False, "Date cannot be in the future", value
                    
            if "min_age_years" in val_rules:
                min_age = val_rules["min_age_years"]
                age = (datetime.now() - date_val).days / 365.25
                if age < min_age:
                    return False, f"Must be at least {min_age} years old", value
                    
        return True, "Valid", value
