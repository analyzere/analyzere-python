import sys

from flake8.main import main


def test_code_style():
    try:
        sys.argv = []
        main()
    except SystemExit:
        raise AssertionError('flake8 found code style issues.')
