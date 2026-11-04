"""Local processor lease; database job claims remain authoritative."""
import errno
import os


def claim_process_lock(stream):
    if os.name != 'nt':
        import fcntl
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return
    import msvcrt
    # Lock the same byte regardless of the append stream's current position.
    position = stream.tell()
    try:
        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                raise BlockingIOError(exc.errno, 'Processor lease is held') from exc
            raise
    finally:
        stream.seek(position)
