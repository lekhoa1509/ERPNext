import frappe
from frappe.model.document import Document

from pharma_vn.dynamic_forms.service import build_schema, serialize_schema


class DynamicForm(Document):
    def validate(self):
        schema = build_schema(self)
        self.schema_json = serialize_schema(schema)
