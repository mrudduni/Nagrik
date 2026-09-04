"""
Dynamic form schemas for application creation. In a real build these would
likely be loaded from a DB/config per scheme; here we define representative
examples plus the extraction schema doc-understanding produces.
"""
from typing import Optional
from pydantic import BaseModel, Field


class FormField(BaseModel):
    name: str
    label: str
    type: str = "string"          # string | number | date | enum
    required: bool = True
    enum_values: Optional[list[str]] = None


class FormSchema(BaseModel):
    form_id: str
    title: str
    fields: list[FormField]


# Example: a generic scholarship-style application form used in tests/demos.
SAMPLE_SCHOLARSHIP_FORM = FormSchema(
    form_id="scholarship_app_v1",
    title="Student Scholarship Application",
    fields=[
        FormField(name="full_name", label="Full name"),
        FormField(name="aadhaar_number", label="Aadhaar number"),
        FormField(name="date_of_birth", label="Date of birth", type="date"),
        FormField(name="category", label="Category", type="enum",
                   enum_values=["General", "OBC", "SC", "ST", "EWS"]),
        FormField(name="annual_family_income", label="Annual family income", type="number"),
        FormField(name="institution_name", label="Institution name"),
    ],
)


class ExtractedDocFields(BaseModel):
    """Structured output schema for the doc/image understanding node."""
    doc_type: Optional[str] = None
    fields: dict[str, str] = Field(default_factory=dict)
    text: Optional[str] = Field(
        default=None,
        description="Any reliably extracted plain text from the document/image.",
    )
    confidence: float = 0.0
