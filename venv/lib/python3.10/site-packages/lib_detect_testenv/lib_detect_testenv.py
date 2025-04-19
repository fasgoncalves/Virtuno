# STDLIB
import os
import pathlib
import sys
from typing import Any, Optional, Union  # noqa

"""
set the syspath accordingly, if pytest or doctest is running
this is needed for local tests
this should be the first module which is loaded by __init__.py
to avoid frozen or partially initialized modules for pytest,
and just before the project imports (for doctest)
no other module should import or use this module,
again to avoid frozen or partially initialized modules.

"""

PathLikeOrString = Union[str, "os.PathLike[Any]"]


# is_testenv_active{{{
def is_testenv_active(arg_string: Optional[str] = None) -> bool:
    """
    returns True if test environment is detected ("pytest", "doctest", "setup.py test")


    Parameter
    ----------
    arg_string  : optional, if None : str(sys.argv())


    Result
    ----------
    True if Test environment is detected


    Exceptions
    ----------
    none


    Examples
    ----------

    >>> assert is_testenv_active() == True
    """
    # is_testenv_active}}}
    arg_string = _get_sys_argv_str(arg_string)
    return is_doctest_active(arg_string=arg_string) or is_pytest_active(arg_string=arg_string) or is_setup_test_active(arg_string=arg_string)


# is_doctest_active{{{
def is_doctest_active(arg_string: Optional[str] = None) -> bool:
    """
    returns True if pycharm "docrunner.py" or "doctest.py" is detected


    Parameter
    ----------
    arg_string  : optional, if None : str(sys.argv())


    Result
    ----------
    True if docrunner is detected


    Exceptions
    ----------
    none

    >>> assert False == is_doctest_active(arg_string="")
    >>> assert True == is_doctest_active(arg_string="docrunner.py")
    >>> assert True == is_doctest_active(arg_string="doctest.py")

    """
    # is_doctest_active}}}

    arg_string = _get_sys_argv_str(arg_string)
    if "docrunner.py" in arg_string or "doctest.py" in arg_string:
        return True
    return False


# is_pytest_active{{{
def is_pytest_active(arg_string: Optional[str] = None) -> bool:
    """
    returns True if "pytest" is detected


    Parameter
    ----------
    arg_string  : optional, if None : str(sys.argv())


    Result
    ----------
    True if pytest is detected


    Exceptions
    ----------
    none

    >>> assert True == is_pytest_active(arg_string='pytest.py')
    >>> assert True == is_pytest_active(arg_string='/pytest/__main__.py')

    """
    # is_pytest_active}}}

    arg_string = _get_sys_argv_str(arg_string)
    # this is used in our tests when we test cli-commands
    if os.getenv("PYTEST_IS_RUNNING"):
        return True
    if "pytest.py" in arg_string:
        return True
    if "/pytest/__main__.py" in arg_string:
        return True
    if "-m" in arg_string and "pytest" in arg_string:
        return True
    return False            # pragma: no cover


# is_setup_active{{{
def is_setup_active(arg_string: Optional[str] = None) -> bool:
    """
    returns True if "setup.py" is detected


    Parameter
    ----------
    arg_string  : optional, if None : str(sys.argv())


    Result
    ----------
    True if setup.py is detected


    Exceptions
    ----------
    none

    >>> assert False == is_setup_active(arg_string="")
    >>> assert True == is_setup_active(arg_string="setup.py")

    """
    # is_setup_active}}}
    arg_string = _get_sys_argv_str(arg_string)
    return "setup.py" in arg_string


# is_setup_test_active{{{
def is_setup_test_active(arg_string: Optional[str] = None) -> bool:
    """
    returns True if "setup.py test" is detected


    Parameter
    ----------
    arg_string  : optional, if None : str(sys.argv())


    Result
    ----------
    True if "setup.py test" is detected


    Exceptions
    ----------
    none

    >>> assert False == is_setup_test_active('')
    >>> assert False == is_setup_test_active('setup.py')
    >>> assert True == is_setup_test_active('setup.py test')

    """
    # is_setup_test_active}}}
    arg_string = _get_sys_argv_str(arg_string)
    if "setup.py" in arg_string:
        arg_string_remaining = arg_string.split("setup.py")[1].strip()
        if arg_string_remaining.startswith("test"):
            return True
    return False


def is_doctest_in_arg_string(arg_string: str) -> bool:
    """
    >>> assert is_doctest_in_arg_string('test') == False
    >>> assert is_doctest_in_arg_string('test/docrunner.py::::test')

    """
    if "docrunner.py" in arg_string:
        return True
    else:
        return False


# add_path_to_syspath{{{
def add_path_to_syspath(path_to_append: PathLikeOrString) -> None:
    """
    adds a path to the syspath

    Parameter
    ----------
    path_to_append
        the path to append - will be resolved by this function and added to syspath
        if path_to_append is a file, its parent directory will be added.


    Result
    ----------
    none


    Exceptions
    ----------
    none


    Examples
    ----------

    >>> add_path_to_syspath(pathlib.Path(__file__).parent)
    >>> path1 = str(sys.path)
    >>> add_path_to_syspath(pathlib.Path(__file__))
    >>> path2 = str(sys.path)
    >>> assert path1 == path2
    """
    # add_path_to_syspath}}}
    path_to_append = pathlib.Path(path_to_append).resolve()
    if path_to_append.is_file():
        path_to_append = path_to_append.parent
    sys_paths_resolved = [pathlib.Path(path).resolve() for path in sys.path]
    if path_to_append not in sys_paths_resolved:
        sys.path.append(str(path_to_append))


def _get_sys_argv_str(arg_string: Optional[str] = None) -> str:
    """
    gets the sys.argv as string. backslashes in Windows are replaced with slashes
    """
    if arg_string is None:
        arg_string = str(sys.argv)
    arg_string = arg_string.replace("\\", "/")
    arg_string = arg_string.replace("//", "/")
    return arg_string


if __name__ == "__main__":
    print(b'this is a library only, the executable is named "lib_detect_testenv_cli.py"', file=sys.stderr)
