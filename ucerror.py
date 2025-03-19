"""
ucerror.py.

This file defines the error-handling function used by the uC compiler.

Project UID c49e54971d13f14fbc634d7a0fe4b38d421279e7
"""

# use colors if available
try:
    from termcolor import colored
except ImportError:
    def colored(string, *_args, **_kwargs):
        """Return the given string uncolored."""
        return string


def error(phase, position, message):
    """Print an error message if error checking is enabled.

    If error checking is enabled, prints an error message for the
    given phase at the given source position, with the given message
    content. Increments the number of errors encountered. If error
    checking is disabled, does nothing.
    """
    if not error.disabled:
        string = colored(f'{error.source_name}:{position}: ',
                         attrs=('bold',))
        string += colored(f'error ({phase}): ', 'red', attrs=('bold',))
        string += colored(message, attrs=('bold',))
        print(string)
        print_source_line(position)
        error.num_errors += 1


def print_source_line(position):
    """Print the source line and highlight position in it."""
    if position.line <= len(error.source_lines):
        print(error.source_lines[position.line-1].rstrip())
    else:
        print()
    print(' ' * (position.column - 1), end='')
    print(colored('^', 'green', attrs=('bold',)), end='')
    if position.start() != position.end():
        end = (position.end_column - 2
               if position.end_line == position.line
               else len(error.source_lines[position.line-1].rstrip()))
        print(colored('~' * (end - position.column), 'green',
                      attrs=('bold',)), end='')
        if (
                position.end_line == position.line
                and position.end_column > position.column + 1
        ):
            print(colored('^', 'green', attrs=('bold',)), end='')
    print()


error.disabled = False
error.num_errors = 0
# the following are filled in by the parser
error.source_name = ''
error.source_lines = []
error.source = ''


def error_count():
    """Return the number of errors detected in static analysis."""
    return error.num_errors


def disable_errors():
    """Disable error checking."""
    error.disabled = True
