def build_deviation_values(data, *, reported_by):
    return {
        "title": data["title"],
        "deviation_type": data.get("deviation_type") or "Process",
        "status": data.get("status") or "Open",
        "severity": data.get("severity") or "Medium",
        "description": data.get("description"),
        "detected_on_doctype": data.get("detected_on_doctype"),
        "detected_on_name": data.get("detected_on_name"),
        "batch_no": data.get("batch_no"),
        "assigned_to": data.get("assigned_to"),
        "reported_by": reported_by,
        "root_cause": data.get("root_cause"),
        "immediate_action": data.get("immediate_action"),
    }


def build_capa_values(data, *, created_by):
    return {
        "title": data["title"],
        "status": data.get("status") or "Open",
        "capa_type": data.get("capa_type") or "Corrective",
        "linked_deviation": data.get("linked_deviation"),
        "description": data.get("description"),
        "assigned_to": data.get("assigned_to"),
        "owner_user": created_by,
        "target_date": data.get("target_date"),
        "effectiveness_review": data.get("effectiveness_review"),
    }
