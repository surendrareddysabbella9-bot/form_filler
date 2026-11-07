import re
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

class FieldValidator:
    """Deterministic backend validator enforcing data types, formats, and conditional rules."""

    @staticmethod
    def validate_field(
        field_key: str,
        label: str,
        field_type: str,
        value: Optional[str],
        required: bool,
        all_field_values: Optional[Dict[str, str]] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Validates a single field value against its schema constraints.
        Returns: (validation_status, validation_error)
        Possible statuses: 'confirmed', 'extracted', 'needs_review', 'missing', 'invalid'
        """
        clean_val = value.strip() if value is not None else ""

        # Check conditional requirements to dynamically promote required flag
        is_conditionally_required = False
        conditional_err = None
        if all_field_values:
            marital_status = all_field_values.get("marital_status", "").lower()
            if marital_status in ["married", "yes"] and field_key == "spouse_name":
                is_conditionally_required = True
                conditional_err = "Spouse name is required when marital status is Married."

        effective_required = required or is_conditionally_required

        # 1. Missing check
        if not clean_val:
            if effective_required:
                return "missing", conditional_err or f"Mandatory field '{label}' is required."
            return "missing", None

        # 2. Format validation by field_type or field_key
        # Date check
        if field_type == "date" or "date" in field_key or "dob" in field_key:
            date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"]
            valid_date = False
            for fmt in date_formats:
                try:
                    datetime.strptime(clean_val, fmt)
                    valid_date = True
                    break
                except ValueError:
                    continue
            if not valid_date:
                return "invalid", f"Invalid date format '{clean_val}'. Expected YYYY-MM-DD or DD/MM/YYYY."

        # Email check
        elif field_type == "email" or field_key == "email":
            email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            if not re.match(email_regex, clean_val):
                return "invalid", f"Invalid email format: '{clean_val}'."

        # Phone check
        elif field_type == "phone" or "phone" in field_key or "mobile" in field_key:
            digits = re.sub(r"\D", "", clean_val)
            if len(digits) < 10 or len(digits) > 13:
                return "invalid", f"Phone number '{clean_val}' must contain 10 to 13 digits."

        # Number / Currency check
        elif field_type == "number" or "income" in field_key or "salary" in field_key or "amount" in field_key:
            num_clean = clean_val.replace(",", "").replace("₹", "").replace("$", "").replace("Rs.", "").strip()
            try:
                float(num_clean)
            except ValueError:
                return "invalid", f"Numeric value expected for '{label}', received: '{clean_val}'."

        # PAN Number check
        elif field_key == "pan_number":
            if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", clean_val.upper()):
                return "invalid", f"PAN must follow format: 5 letters, 4 numbers, 1 letter (e.g. ABCDE1234F)."

        # Bank IFSC check
        elif field_key == "bank_ifsc_code":
            if not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", clean_val.upper()):
                return "invalid", f"IFSC must be 11 characters starting with 4 letters followed by 0 (e.g. HDFC0001234)."

        # Postal code check
        elif field_key == "postal_code" or "pin" in field_key or "zip" in field_key:
            digits = re.sub(r"\D", "", clean_val)
            if len(digits) not in [5, 6]:
                return "invalid", f"Postal code '{clean_val}' should be 5 or 6 digits."

        return "extracted", None
