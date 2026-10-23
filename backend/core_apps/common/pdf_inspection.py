"""Bounded subprocess: document bytes are never included in diagnostics."""

import io
import json
import sys


def main():
    import resource

    resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
    if sys.platform.startswith("linux"):
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    from pypdf import PdfReader

    content = sys.stdin.buffer.read(25 * 1024 * 1024 + 1)
    if not content.startswith(b"%PDF-") or len(content) > 25 * 1024 * 1024:
        raise ValueError()
    reader = PdfReader(io.BytesIO(content), strict=True)
    if reader.is_encrypted or not 0 < len(reader.pages) <= 500:
        raise ValueError()
    root = reader.trailer["/Root"]
    names = root.get("/Names", {})
    if hasattr(names, "get_object"):
        names = names.get_object()
    if any(key in names for key in ("/JavaScript", "/EmbeddedFiles")) or "/AA" in root:
        raise ValueError()
    action = root.get("/OpenAction")
    if hasattr(action, "get_object"):
        action = action.get_object()
    if isinstance(action, dict) and action.get("/S") in {"/JavaScript", "/Launch"}:
        raise ValueError()
    # Actions can also live in annotations, forms or nested /Next dictionaries.
    # Traverse references with a bound and cycle detection instead of checking
    # only the catalog. Parsing success does not replace the malware scanner.
    from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject

    pending, seen, visited = [reader.trailer], set(), 0
    forbidden = {
        "/AA",
        "/JavaScript",
        "/JS",
        "/EmbeddedFiles",
        "/RichMedia",
        "/RichMediaContent",
        "/XFA",
    }
    while pending:
        value = pending.pop()
        visited += 1
        if visited > 100000:
            raise ValueError()
        if isinstance(value, IndirectObject):
            identity = (value.idnum, value.generation)
            if identity in seen:
                continue
            seen.add(identity)
            value = value.get_object()
        if isinstance(value, DictionaryObject):
            if forbidden.intersection(value) or value.get("/S") in {
                "/JavaScript",
                "/Launch",
                "/SubmitForm",
                "/ImportData",
            }:
                raise ValueError()
            pending.extend(value.values())
        elif isinstance(value, ArrayObject):
            pending.extend(value)
    print(json.dumps({"page_count": len(reader.pages)}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(1)
