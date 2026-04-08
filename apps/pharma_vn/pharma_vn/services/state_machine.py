STATE_MACHINES = {
    "batch": {
        "Draft": {"QA"},
        "QA": {"Released", "Hold", "Rejected"},
        "Hold": {"QA", "Rejected", "Released"},
        "Rejected": set(),
        "Released": {"Hold", "Recalled"},
        "Recalled": set(),
    },
    "recall": {
        "Open": {"Investigating"},
        "Investigating": {"Executing", "Closed"},
        "Executing": {"Closed"},
        "Closed": set(),
    },
}


def get_next_states(machine_name, current_state):
    machine = STATE_MACHINES[machine_name]
    return sorted(machine.get(current_state, set()))


def validate_transition(machine_name, current_state, next_state):
    current_state = str(current_state or "").strip()
    next_state = str(next_state or "").strip()
    machine = STATE_MACHINES[machine_name]

    if current_state not in machine:
        raise ValueError(f"Unknown {machine_name} state: {current_state}")
    if next_state not in machine:
        raise ValueError(f"Unknown {machine_name} state: {next_state}")
    if next_state not in machine[current_state]:
        allowed_states = ", ".join(sorted(machine[current_state])) or "none"
        raise ValueError(
            f"Invalid {machine_name} transition: {current_state} -> {next_state}. Allowed: {allowed_states}"
        )
    return next_state


def build_transition_audit(machine_name, current_state, next_state, user, note=None):
    validate_transition(machine_name, current_state, next_state)
    return {
        "machine": machine_name,
        "from_state": current_state,
        "to_state": next_state,
        "performed_by": user,
        "note": note,
    }
