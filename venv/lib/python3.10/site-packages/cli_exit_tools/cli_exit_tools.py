import sys
import traceback
from typing import Any, Optional, TextIO


class _Config(object):
    traceback: bool = False


config = _Config()


# get_system_exit_code{{{
def get_system_exit_code(exc: BaseException) -> int:
    """
    Return the exit code for linux or Windows os, based on the exception.
    If, on windows, the winerror code is passed with the Exception, we return that winerror code.


    Parameter
    ---------
    exc
        the exception to analyze


    Result
    ------
    exit_code
        as integer


    Examples
    --------

    >>> try:
    ...     raise RuntimeError()
    ... except RuntimeError as my_exc:
    ...     assert get_system_exit_code(my_exc) == 1
    ...     setattr(my_exc, 'winerror', 42)
    ...     assert get_system_exit_code(my_exc) == 42
    ...     setattr(my_exc, 'winerror', None)
    ...     assert get_system_exit_code(my_exc) == 1
    >>> try:
    ...     exit(99)
    ... except SystemExit as my_exc:
    ...     assert get_system_exit_code(my_exc) == 99

    """
    # get_system_exit_code}}}

    # from https://www.thegeekstuff.com/2010/10/linux-error-codes
    # dict key sorted from most specific to unspecific
    posix_exceptions = {FileNotFoundError: 2, PermissionError: 13, FileExistsError: 17, TypeError: 22, ValueError: 22, RuntimeError: 1, BaseException: 1}
    windows_exceptions = {FileNotFoundError: 2, PermissionError: 5, ValueError: 13, FileExistsError: 80, TypeError: 87, RuntimeError: 1, BaseException: 1}

    # Handle SystemExit
    if isinstance(exc, SystemExit):
        exit_code = int(exc.args[0])
        return exit_code

    if hasattr(exc, "winerror"):
        try:
            exit_code = int(exc.winerror)  # type: ignore
            return exit_code
        except (AttributeError, TypeError):
            pass

    if "posix" in sys.builtin_module_names:
        exceptions = posix_exceptions
    else:
        exceptions = windows_exceptions     # pragma: no cover

    # Handle all other Exceptions
    for exception in exceptions:
        if isinstance(exc, exception):
            return exceptions[exception]

    # this should never happen
    return 1  # pragma: no cover


# print_exception_message{{{
def print_exception_message(trace_back: bool = config.traceback, length_limit: int = 500, stream: Optional[TextIO] = None) -> None:
    """
    Prints the Exception Message to stderr. If trace_back is True, it also prints the traceback information.
    If the exception has stdout, stderr attributes (like subprocess.CalledProcessError), those will also be printed.

    Parameters
    ----------
    trace_back : bool, optional
        Whether to print traceback information. Default is False.
    length_limit : int, optional
        Maximum length of the exception message to be printed. Default is 500.
    stream : Optional[TextIO], optional
        The stream to print to. Default is sys.stderr.

    Examples
    --------

    >>> # test with exc_info = None
    >>> print_exception_message()

    >>> # test with exc_info
    >>> try:
    ...     raise FileNotFoundError('unknown_command_test1')
    ... except Exception:       # noqa
    ...     print_exception_message(True, length_limit=15, stream=sys.stdout)
    ...     print_exception_message(False, stream=sys.stdout)
    ...     print_exception_message(True, stream=sys.stdout)
    Traceback Info...

    >>> # test with subprocess to get stdout, stderr
    >>> import subprocess
    >>> try:
    ...     discard=subprocess.run('unknown_command_test2', shell=True, check=True)
    ... except subprocess.CalledProcessError:
    ...     print_exception_message(False, stream=sys.stdout)
    ...     print_exception_message(True, stream=sys.stdout)
    ...     print_exception_message(True, stream=sys.stdout)
    CalledProcessError...

    """
    # print_exception_message}}}
    flush_streams()

    if stream is None:
        stream = sys.stderr

    exc_info = sys.exc_info()[1]  # Get the current exception
    if exc_info is not None:
        exc_info_type = type(exc_info).__name__
        exc_info_msg = f"{exc_info_type}: {str(exc_info)}"

        # Print traceback if trace_back is True
        if trace_back:
            exc_info_msg = f"Traceback Information:\n{traceback.format_exc()}"

        # If message exceeds length limit, truncate it
        if len(exc_info_msg) > length_limit:
            exc_info_msg = f"{exc_info_msg[:length_limit]} ...[TRUNCATED at {length_limit} characters]"

        # Print stdout/stderr if they exist in the exception
        _print_output(exc_info, "stdout", stream)
        _print_output(exc_info, "stderr", stream)

        # Print the exception message
        print(exc_info_msg, file=stream)
        flush_streams()


def _print_output(exc_info: Any, attr: str, stream: Optional[TextIO] = None) -> None:
    """
    Helper function to print an attribute (stdout, stderr) of the exc_info if it exists.

    Parameters
    ----------
    exc_info : Any
        The exception object that may contain stdout or stderr.
    attr : str
        The attribute name ('stdout' or 'stderr').
    stream : Optional[TextIO]
        The stream to print to. Default is sys.stderr.

    >>> class ExcInfo(object):
    ...    pass

    >>> my_exc_info = ExcInfo()

    >>> # test no stdout attribute
    >>> _print_output(my_exc_info, 'stdout')

    >>> # test stdout=None
    >>> my_exc_info.stdout=None
    >>> _print_output(my_exc_info, 'stdout')

    >>> # test stdout
    >>> my_exc_info.stdout=b'test'
    >>> _print_output(my_exc_info, 'stdout', stream=sys.stdout)
    STDOUT: test

    >>> my_exc_info = ExcInfo()

    >>> # test no stderr attribute
    >>> _print_output(my_exc_info, 'stderr')

    >>> # test stderr=None
    >>> my_exc_info.stderr=None
    >>> _print_output(my_exc_info, 'stderr')

    >>> # test stderr
    >>> my_exc_info.stderr=b'test'
    >>> _print_output(my_exc_info, 'stderr', stream=sys.stdout)
    STDERR: test

    """
    if stream is None:
        stream = sys.stderr

    if hasattr(exc_info, attr):
        output = getattr(exc_info, attr)
        if output is not None:
            assert isinstance(output, bytes), f"{attr} must be of type bytes"
            print(f"{attr.upper()}: {output.decode()}", file=stream)


# flush_streams{{{
def flush_streams() -> None:
    """
    flush the streams - make sure the output is written early,
    otherwise the output might be printed even after another CLI
    command is launched


    Examples
    --------


    >>> flush_streams()

    """
    # flush_streams}}}
    try:
        sys.stdout.flush()
    except Exception:  # pragma: no cover
        pass  # pragma: no cover
    try:
        sys.stderr.flush()
    except Exception:  # pragma: no cover
        pass  # pragma: no cover
