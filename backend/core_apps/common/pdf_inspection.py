"""Bounded subprocess: document bytes are never included in diagnostics."""

import io
import json
import sys


def limit_process():
    if sys.platform != "win32":
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
        if sys.platform.startswith("linux"):
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        return
    # Windows has no resource module. A nested job limits this child process;
    # failure to establish the limits remains a rejected inspection.
    import ctypes
    from ctypes import wintypes

    class BasicLimits(ctypes.Structure):
        _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
            ("flags", wintypes.DWORD), ("minimum_working_set", ctypes.c_size_t),
            ("maximum_working_set", ctypes.c_size_t), ("active_processes", wintypes.DWORD),
            ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD), ("scheduling", wintypes.DWORD)]
    class IoCounters(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in ("read", "write", "other", "read_bytes", "write_bytes", "other_bytes")]
    class ExtendedLimits(ctypes.Structure):
        _fields_ = [("basic", BasicLimits), ("io", IoCounters), ("process_memory", ctypes.c_size_t),
            ("job_memory", ctypes.c_size_t), ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    job = kernel.CreateJobObjectW(None, None)
    limits = ExtendedLimits()
    limits.basic.process_time = 8 * 10_000_000
    limits.basic.flags = 0x2 | 0x100  # Per-process CPU time and memory.
    limits.process_memory = 512 * 1024 * 1024
    if (not job or not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits))
            or not kernel.AssignProcessToJobObject(job, kernel.GetCurrentProcess())):
        raise OSError("PDF inspection limits could not be established")
    # The process owns the handle until exit; closing it early would remove
    # resource enforcement while parsing.
    global _process_limit_job
    _process_limit_job = job


def main():
    limit_process()
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
