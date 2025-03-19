"""
ucccheck.py.

Simple check for correct output on a test for the frontend.

Project UID c49e54971d13f14fbc634d7a0fe4b38d421279e7
"""

import sys
import re
import os
import difflib
import collections


ERROR_PATTERN = re.compile(r'^.*\.uc:(\d*):\d*: error \((\d*)\): (.*)')


def check_file(filename, error=True):
    """Check if the given file exists.

    Exits with non-zero code if error is true and the file does not
    exist.
    """
    if os.path.isfile(filename):
        return True
    if error:
        print(f'Error: required file {filename} not found')
        sys.exit(1)
    print(f'{"%" * 70}\nWARNING: missing expected output file '
          f'{filename}\n{"%" * 70}')
    return False


def extract_info(line):
    """Extract phase and line information from an error message."""
    match = ERROR_PATTERN.match(line)
    return match.group(2, 1, 3) if match else None


def get_errors(filename):
    """Extract errors from the given file."""
    with open(filename, encoding="utf8") as result_file:
        results_all = collections.defaultdict(list)
        for line in result_file.readlines():
            info = extract_info(line)
            if info:
                results_all[info[:2]].append(info[2])
        return results_all, set(results_all)


def check_output(filename):
    """Compare standard output from frontend with expected output.

    Returns whether or not the types output should be compared.
    """
    output = filename.replace('.uc', '.out')
    check_file(output)
    if not check_file(output + '.correct', error=False):
        return False
    actual_all, actual = get_errors(output)
    correct_all, correct = get_errors(output + '.correct')
    missing = correct - actual
    extra = actual - correct
    failed = len(missing) + len(extra)
    if missing:
        print('Missing errors:')
        for i, item in enumerate(missing):
            print(f'{i+1}) Phase {item[0]}, line {item[1]}'
                  f' ({correct_all[item][0]})')
    if extra:
        print('Extraneous errors:')
        for i, item in enumerate(extra):
            print(f'{i+1}) Phase {item[0]}, line {item[1]}'
                  f' [{actual_all[item][0]}]')
    if failed:
        print(f'Test {filename} failed.')
        sys.exit(1)
    return not correct


def check_types(filename):
    """Compare types output from frontend with expected output."""
    types = filename.replace('.uc', '.types')
    check_file(types)
    if not check_file(types + '.correct', error=False):
        return
    with open(types, encoding="utf8") as actual_file, \
            open(types + '.correct', encoding="utf8") as correct_file:
        actual = actual_file.readlines()
        correct = correct_file.readlines()
        if actual != correct:
            print('Error: mismatch detected in types output for '
                  f'{filename}:')
            print('=' * 80)
            sys.stdout.writelines(
                difflib.context_diff(correct, actual,
                                     fromfile=f'{types}.correct',
                                     tofile=types)
            )
            print('=' * 80)
            print(f'Test {filename} failed.')
            sys.exit(1)


def main(filename):
    """Compare result of compiler frontend with expected output.

    filename is the name of the uC file for which to check output.
    """
    if check_output(filename):
        try:
            check_types(filename)
        except FileNotFoundError as err:
            print(f'Error: required file not found: {err.filename}')
            sys.exit(1)
    print(f'Test {filename} passed.')


if __name__ == '__main__':
    main(sys.argv[1])
