import os
import signal
import subprocess
import tempfile
import shutil
from contextlib import contextmanager


@contextmanager
def temporary_directory(*args, **kwargs):
    directory_name = tempfile.mkdtemp(*args, **kwargs)
    try:
        yield directory_name
    finally:
        shutil.rmtree(directory_name)

def run_command(args, timeout):
    u"""
    Runs an external command and returns a ``subprocess.CompletedProcess`` with captured output,
    like ``subprocess.run(..., check=True)``. On timeout it kills the whole process group, not just
    the direct child: ``libreoffice`` is a launcher whose real worker (``soffice.bin``) otherwise
    keeps running, holds the user profile and blocks every following conversion. The raised
    ``TimeoutExpired`` and ``CalledProcessError`` always carry bytes in ``stdout`` and ``stderr``.
    """
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass
        stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(args, timeout, output=stdout or b'', stderr=stderr or b'')
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, args, output=stdout, stderr=stderr)
    return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)

def libreoffice_convert_to_pdf(filename, directory, timeout):
    u"""
    Converts ``filename`` to PDF in ``directory`` with LibreOffice. Every run uses its own user
    profile inside ``directory``, so a hung or parallel LibreOffice can never capture the request.
    """
    return run_command(
            [u'libreoffice', u'-env:UserInstallation=file://' + os.path.join(directory, u'profile'),
             u'--headless', u'--convert-to', u'pdf', u'--outdir', directory, filename],
            timeout=timeout)

def process_output(process, exception):
    u"""
    Returns decoded ``(stdout, stderr)`` of a finished ``process`` or, if it is None, of the
    ``exception`` raised while running it. Exceptions without output (or with None) give u''.
    """
    source = process if process is not None else exception
    return tuple((getattr(source, name, None) or b'').decode(u'utf-8', u'replace')
                 for name in (u'stdout', u'stderr'))
