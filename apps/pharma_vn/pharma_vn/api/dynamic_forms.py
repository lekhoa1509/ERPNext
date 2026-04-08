import frappe

from pharma_vn.dynamic_forms.service import build_schema, parse_payload, validate_submission


@frappe.whitelist()
def get_form_schema(form_name):
    form = frappe.get_doc("Dynamic Form", form_name)
    return {"data": build_schema(form)}


@frappe.whitelist()
def submit_form(form_name, payload=None):
    form = frappe.get_doc("Dynamic Form", form_name)
    schema = build_schema(form)
    cleaned_payload = validate_submission(schema, parse_payload(payload))

    submission = frappe.get_doc(
        {
            "doctype": "Dynamic Form Submission",
            "dynamic_form": form.name,
            "submitted_by": frappe.session.user,
            "payload_json": frappe.as_json(cleaned_payload),
        }
    )
    submission.insert()

    return {
        "message": form.success_message or "Submission saved successfully.",
        "submission_name": submission.name,
        "data": cleaned_payload,
    }
