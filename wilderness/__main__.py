import sys
import curses
import locale
import wilderness

sys.setrecursionlimit(2**20)
locale.setlocale(locale.LC_ALL,"")
curses.wrapper(wilderness.engine.initialize)