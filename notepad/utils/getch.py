class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            pass
        #print('('+str(ord(ch))+')')
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


getch1 = _Getch()

CSI = "\033["
#CSI = "["

def getch():
  ch = getch1()
  if ord(ch) == 27:
    ch = ch + getch1()
    if (ch == ""):
      return ""
    else:
      ch = ch + getch1()
  return ch


if __name__ == "__main__":
  test = getch()
  print('\r\n<<'+test+'>>\r\n')
  if test == '\r': print('\\r')
  if test == '\n': print('\\n')
  if test == '': print('<ESC>')