def ok(message, data=None):
    return {
        "ok": True,
        "message": message,
        "data": data or {},
    }

