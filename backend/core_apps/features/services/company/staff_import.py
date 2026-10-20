"""Bounded, nonpersistent CSV parsing. Confirmation uses existing staff batches."""

import csv
import io
from uuid import uuid4

from rest_framework.exceptions import ValidationError
from ...company_staff_serializers import StaffFields

FIELDS = (
    "display_name",
    "work_email",
    "employee_code",
    "mobile",
    "job_title",
    "department",
    "project_code",
)
MAX_BYTES = 200_000


def preview(company, text):
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_BYTES:
        raise ValidationError(
            {"csv_text": "Use a UTF-8 CSV file of at most 200000 bytes."}
        )
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")), strict=True)
    try:
        headers = reader.fieldnames or []
    except csv.Error:
        raise ValidationError(
            {"csv_text": "The CSV quoting or header structure is invalid."}
        )
    if (
        len(headers) != len(set(headers))
        or set(headers) - set(FIELDS)
        or not {"display_name", "work_email"} <= set(headers)
    ):
        raise ValidationError(
            {
                "csv_text": "Use unique supported headers including display_name and work_email. Roles cannot be imported."
            }
        )
    rows, emails, codes = [], set(), set()
    try:
        for number, raw in enumerate(reader, start=2):
            if len(rows) >= 50:
                raise ValidationError({"csv_text": "Import at most 50 staff rows."})
            if None in raw or any(v is None for v in raw.values()):
                raise ValidationError(
                    {"csv_text": f"Row {number} has a different number of columns."}
                )
            values = {k: raw.get(k, "").strip() for k in FIELDS}
            values["roles"] = ["employee"]
            serializer = StaffFields(data=values)
            valid = serializer.is_valid()
            errors = {
                k: [str(v) for v in items] for k, items in serializer.errors.items()
            }
            email, code = values["work_email"].casefold(), values["employee_code"]
            if (
                email in emails
                or company.staff_records.filter(work_email__iexact=email).exists()
            ):
                errors["work_email"] = [
                    "This contact already appears in this import or company staff."
                ]
            if code and (
                code in codes
                or company.staff_records.filter(employee_code=code).exists()
            ):
                errors["employee_code"] = [
                    "This employee code already appears in this import or company staff."
                ]
            emails.add(email)
            if code:
                codes.add(code)
            rows.append(
                {
                    "row_key": str(uuid4()),
                    "line": number,
                    "values": values,
                    "errors": errors,
                    "messages": [
                        f"{key}: {message}"
                        for key, messages in errors.items()
                        for message in messages
                    ],
                    "valid": valid and not errors,
                }
            )
    except csv.Error:
        raise ValidationError(
            {"csv_text": "The CSV quoting or row structure is invalid."}
        )
    if not rows:
        raise ValidationError({"csv_text": "The file contains no staff rows."})
    return {
        "company_id": str(company.id),
        "rows": rows,
        "persisted": False,
        "activation_sent": False,
        "supported_columns": list(FIELDS),
        "maximum_rows": 50,
    }
