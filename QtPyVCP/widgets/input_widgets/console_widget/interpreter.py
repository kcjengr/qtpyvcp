# -*- coding: utf-8 -*-
import os
import sys
import contextlib

try:
    import jedi
    from jedi import settings
    settings.case_insensitive_completion = False
except ImportError as ex:
    print(str(ex) + ', No completion available')

from code import InteractiveConsole

class PythonInterpreter(InteractiveConsole):
    def __init__(self, stdin, stdout, local = {}):
        InteractiveConsole.__init__(self, local)
        self.local_ns = local
        self.stdin = stdin
        self.stdout = stdout

        self._running = False
        self._last_input = ''
        self._more = False
        self._current_line = 0
        self._current_eval_buffer = ''
        self._executing = False

        self._inp = 'IN [%s]: '
        self._morep = '...: '
        self._outp = 'OUT[%s]: '
        self._p = self._inp % self._current_line
        self._print_in_prompt()

    def _update_in_prompt(self, _more, _input):
        # We need to show the more prompt of the input was incomplete
        # If the input is complete increase the input number and show
        # the in prompt
        if not _more:
            # Only increase the input number if the input was complete
            # last prompt was the more prompt (and we know that we don't have
            # more input to expect). Obviously do not increase for CR
            if _input != os.linesep or self._p == self._morep:
                self._current_line += 1

            self._p = self._inp % self._current_line
        else:
            self._p = (len(self._p) - len(self._morep)) * ' ' + self._morep

    def _print_in_prompt(self):
        self.stdout.write(self._p)

    def _format_result(self):
        # Are we at the end of a code block, not a very elegant check
        # but it works for now
        eof_cblock = self._last_input == os.linesep and self._more == True

        if self._last_input != os.linesep or eof_cblock: 
            self.stdout.write(os.linesep)

    def executing(self):
        return self._executing

    def push(self, line):
        return InteractiveConsole.push(self, line)

    def runcode(self, code):
        self._executing = True

        # Redirect IO and disable excepthook, this is the only place were we
        # redirect IO, since we don't how IO is handled within the code we
        # are running. Same thing for the except hook, we don't know what the
        # user are doing in it.
        with redirected_io(self.stdout), disabled_excepthook():
            exec_res = InteractiveConsole.runcode(self, code)

        self._executing = False        
        return exec_res

    def raw_input(self, prompt=None, timeout=None):
        line = self.stdin.readline(timeout)

        if line != os.linesep:
            line = line.strip(os.linesep)

        return line

    def write(self, data):
        self.stdout.write(data)

    def showtraceback(self):
        type_, value, tb = sys.exc_info()
        self.stdout.write(os.linesep)
        
        if type_ == KeyboardInterrupt:
            self.stdout.write('KeyboardInterrupt' + os.linesep)
        else:
            InteractiveConsole.showtraceback(self)

        self.stdout.write(os.linesep)

    def showsyntaxerror(self, filename):
        self.stdout.write(os.linesep)
        InteractiveConsole.showsyntaxerror(self, filename)
        self.stdout.write(os.linesep)

    def _rep_line(self, line):
        self._last_input = line

        if line == 'exit' or line == 'exit()':
            self._running = False
        elif line == '%%eval_buffer':
            line = self.eval_buffer()
        elif line == '%%eval_lines':
            self.eval_lines()

            # We don't want to make recursive call here, self.eval_lines
            # calls _rep_line so we return to start from scratch to not
            # 'save' the state of the current evaluation.
            return
        else:
            self._more = self.push(line)

        self._update_in_prompt(self._more, self._last_input)
        self._print_in_prompt()

    def repl(self):
        self._running = True

        while self._running:
            try:
                line = self.raw_input(timeout = None)

                if line:
                    self._rep_line(line)
            except KeyboardInterrupt:
                pass

    def repl_nonblock(self):
        line = self.raw_input(timeout = 0)

        if line:
            self._rep_line(line)

    def exit(self):
        self.stdin.write('exit\n')

    def set_buffer(self, _buffer):
        self._current_eval_buffer = _buffer.strip(os.linesep)

    def eval_buffer(self):
        if self._current_eval_buffer:
            try:
                code = compile(self._current_eval_buffer,'<string>', 'exec')
            except (OverflowError, SyntaxError):
                InteractiveConsole.showsyntaxerror(self)
            else:
                self.runcode(code)

        return False

    def eval_lines(self):
        if self._current_eval_buffer:
            lines = self._current_eval_buffer.split(os.linesep)

            for line in lines:
                if line:
                    # Remove the any remaining more prompt, to make it easier
                    # to copy/paste within the interpreter.
                    if line.startswith(self._morep):
                        line = line[len(self._morep):]

                    self.stdout.write(line)
                    self._rep_line(line + os.linesep)

    def get_completions(self, line):
        words = []

        if 'jedi' in globals():
            script = jedi.Interpreter(line, [self.local_ns])

            for completion in script.completions():
                words.append(completion.name)

        return words


@contextlib.contextmanager
def disabled_excepthook():
    """Run code with the exception hook temporarily disabled."""
    old_excepthook = sys.excepthook
    sys.excepthook = sys.__excepthook__

    try:
        yield
    finally:
        # If the code we did run did change sys.excepthook, we leave it
        # unchanged. Otherwise, we reset it.
        if sys.excepthook is sys.__excepthook__:
            sys.excepthook = old_excepthook


@contextlib.contextmanager
def redirected_io(stdout):
    sys.stdout = stdout
    sys.stderr = stdout

    try:
        yield
    finally:

        # Only reset if stdout or stderr was unchanged in the code that was
        # executed within the context
        if sys.stdout == stdout:
            sys.stdout = sys.__stdout__

        if sys.stderr == stdout:
            sys.stderr = sys.__stderr__
