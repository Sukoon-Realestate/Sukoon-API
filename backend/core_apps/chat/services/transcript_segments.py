"""Untrusted provider timestamps are optional; invalid sets fall back to text."""


def validated_segments(value, duration_ms):
    if (not isinstance(value, list) or not 1 <= len(value) <= 500
            or type(duration_ms) is not int or duration_ms <= 0):
        return []
    result, previous_end, characters = [], 0, 0
    for row in value:
        if not isinstance(row, dict):
            return []
        start, end, text = row.get("start_ms"), row.get("end_ms"), row.get("text")
        if (type(start) is not int or type(end) is not int or not previous_end <= start < end <= duration_ms
                or not isinstance(text, str) or not text.strip()):
            return []
        characters += len(text)
        if characters > 16000:
            return []
        result.append({"start_ms": start, "end_ms": end, "text": text})
        previous_end = end
    return result
