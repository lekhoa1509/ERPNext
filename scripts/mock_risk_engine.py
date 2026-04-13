#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer


def build_response(tax_code):
    normalized = str(tax_code or "").strip().upper()

    if normalized.startswith("HIGH"):
        return {
            "risk_score": 85,
            "risk_level": "HIGH",
            "reasons": [
                "Late payment history",
                "High outstanding debt",
            ],
        }

    if normalized.startswith("WARN"):
        return {
            "risk_score": 54,
            "risk_level": "WARNING",
            "reasons": [
                "Outstanding balance is rising",
                "Recent payment delays detected",
            ],
        }

    return {
        "risk_score": 18,
        "risk_level": "SAFE",
        "reasons": [
            "Healthy payment behavior",
            "No major contract risk signals",
        ],
    }


def build_business_profile(tax_code):
    normalized = str(tax_code or "").strip().upper() or "UNKNOWN"
    company_name = {
        "HIGH001": "Cong Ty TNHH RUI RO CAO",
        "WARN001": "Cong Ty Co Phan Canh Bao",
        "SAFE001": "Cong Ty Co Phan Viet An Pharma",
    }.get(normalized, f"Cong Ty MST {normalized}")
    established_date = {
        "HIGH001": "2025-11-12",
        "WARN001": "2023-06-04",
        "SAFE001": "2014-03-18",
    }.get(normalized, "2020-01-15")
    business_lines = {
        "HIGH001": ["Real Estate Investment", "Construction Services"],
        "WARN001": ["Logistics Services", "Import Export"],
        "SAFE001": ["Pharmaceutical Distribution"],
    }.get(normalized, ["General Trading"])

    status = "Dang hoat dong"
    if normalized.startswith("HIGH"):
        status = "Dang hoat dong, can theo doi no"

    return {
        "data": {
            "company_name": company_name,
            "tax_code": normalized,
            "address": "123 Nguyen Hue, Quan 1, TP. Ho Chi Minh",
            "status": status,
            "representative": "Nguyen Van A",
            "established_date": established_date,
            "business_lines": business_lines,
            "source": "Mock Tax Business API",
        }
    }


class RiskHandler(BaseHTTPRequestHandler):
    server_version = "MockRiskEngine/1.0"

    def _send_json(self, status_code, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in {"/", "/health"}:
            self._send_json(
                200,
                {
                    "ok": True,
                    "service": "mock-risk-engine",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            return

        if self.path.startswith("/api/tax/business/"):
            tax_code = self.path.rsplit("/", 1)[-1]
            self._send_json(200, build_business_profile(tax_code))
            return

        if self.path.startswith("/api/tax/business"):
            tax_code = ""
            if "?" in self.path:
                query = self.path.split("?", 1)[1]
                for part in query.split("&"):
                    if part.startswith("tax_code="):
                        tax_code = part.split("=", 1)[1]
                        break
            self._send_json(200, build_business_profile(tax_code))
            return

        self._send_json(404, {"ok": False, "message": "Not found"})

    def do_POST(self):
        if self.path not in {"/api/risk/check", "/api/tax/business"}:
            self._send_json(404, {"ok": False, "message": "Not found"})
            return

        content_length = int(self.headers.get("Content-Length", "0") or 0)
        raw_body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send_json(400, {"ok": False, "message": "Invalid JSON payload"})
            return

        tax_code = payload.get("tax_code")
        if self.path == "/api/tax/business":
            self._send_json(200, build_business_profile(tax_code))
            return

        customer = payload.get("customer")
        result = build_response(tax_code)
        result.update(
            {
                "customer": customer,
                "tax_code": tax_code,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "engine": "mock",
            }
        )
        self._send_json(200, result)

    def log_message(self, format, *args):
        return


def main():
    parser = argparse.ArgumentParser(description="Local mock risk engine for ERPNext integration testing.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=5051, type=int)
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), RiskHandler)
    print(f"Mock risk engine listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
