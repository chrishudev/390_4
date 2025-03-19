"""
uccontext.py.

This file defines the PhaseContext type that is used by both the
frontend and backend.

Project UID c49e54971d13f14fbc634d7a0fe4b38d421279e7
"""

import sys


class PhaseContext:
    """Contains contextual information required in a compiler phase.

    Contextual information can be added to this context using the
    dictionary interface (e.g. ctx['is_return'] = False).
    """

    # Hardcoded field set. Do NOT modify or add to this.
    __slots__ = ('phase', 'global_env', 'out', 'indent', '__info')

    def __init__(self, phase=0, global_env=None, out=sys.stdout,
                 indent='', info=None):
        """Initialize this context.

        out is the output stream for writing an AST representation or
        for code generation. The internal dictionary is set to be a
        copy of info, if it is not None.
        """
        self.phase = phase
        self.global_env = global_env
        self.out = out
        self.indent = indent
        self.__info = dict(info) if info else {}

    def clone(self, indent='', **new_entries):
        """Return a shallow copy of this context, plus new entries.

        indent specifies the additional indentation for the copy over
        this context's indentation. new_entries specifies additional
        entries to add to the copy. The values in new_entries take
        priority if this context and new_entries share keys.
        """
        return PhaseContext(self.phase, self.global_env, self.out,
                            self.indent + indent,
                            self.__info | new_entries)

    def __copy__(self):
        """Return a shallow copy of this context."""
        return self.clone()

    def __getitem__(self, key):
        """Return the value associated with the key in this context."""
        return self.__info[key]

    def __setitem__(self, key, value):
        """Set the value associated with the key in this context."""
        self.__info[key] = value

    def __contains__(self, key):
        """Return whether the given key exists in this context."""
        return key in self.__info

    def print(self, *args, **kwargs):
        """Print to the context's output.

        Indents with this context's indent string if indent=True is
        provided. The trailing newline can be suppressed by end='',
        as with the standard print() function.
        """
        if 'indent' in kwargs:
            if kwargs['indent']:
                print(self.indent, file=self.out, end='')
            del kwargs['indent']
        print(*args, file=self.out, **kwargs)
