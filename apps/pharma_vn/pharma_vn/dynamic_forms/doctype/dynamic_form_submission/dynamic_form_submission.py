import frappe
from frappe.model.document import Document

from pharma_vn.dynamic_forms.service import build_schema, parse_payload, validate_submission


class DynamicFormSubmission(Document):
    def validate(self):
        if self.dynamic_form:
            form = frappe.get_doc("Dynamic Form", self.dynamic_form)
            schema = build_schema(form)
            payload = parse_payload(self.payload_json)
            cleaned_payload = validate_submission(schema, payload)
            self.payload_json = frappe.as_json(cleaned_payload)

        if not self.submitted_by:
            self.submitted_by = frappe.session.user
