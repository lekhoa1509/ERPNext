from frappe.model.document import Document

from pharma_vn.hrm.payroll import DEFAULT_SETTINGS, FORMULA_FIELDS, validate_payroll_formula


class PayrollAutomationSettings(Document):
    def validate(self):
        self.tax_slabs = sorted(self.tax_slabs or [], key=lambda row: row.from_amount or 0)
        for fieldname in FORMULA_FIELDS:
            formula = (getattr(self, fieldname, None) or "").strip()
            if not formula:
                formula = DEFAULT_SETTINGS[fieldname]
            validate_payroll_formula(fieldname, formula)
            setattr(self, fieldname, formula)
