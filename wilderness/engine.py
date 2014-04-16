import sys
import time
import random
import curses
from itertools import cycle
from wilderness.maps import Tile, Map
from wilderness.entities import Entity

class Mode(object):
	PLAYER = "Play"
	DRAW = "Draw"
	LOOK = "Look"

class DisplayArea(object):
	MAIN = 0
	MAP = 1
	STATUS = 2

class Engine(object):

	def __init__(self, screen):
		self.directions = ["N", "S", "E", "W"]
		self.mode = Mode.PLAYER
		self.modes = cycle([Mode.DRAW, Mode.LOOK, Mode.PLAYER])
		self.draw_cursor = False
		self.player = None
		self.cursor = None
		self.the_map = None
		self.lines = 0
		self.cols = 0
		self.inputs = []
		self.displays = []
		self.ignore_input = True
		self.input_dispatcher = InputDispatcher(screen)
		self.step = 0

	def inc_step(self, n):
		self.step += n

	def add_display(self, display):
		self.displays.append(display)

	def add_input(self, input):
		self.inputs.append(input)

	def next_mode(self):
		self.mode = next(self.modes)
		if self.mode == Mode.PLAYER:
			self.draw_cursor = False
		else:
			self.draw_cursor = True

	def reset_mode(self):
		while self.mode != self.Mode.PLAYER:
			self.next_mode()

	def move(self, dir, entity, incrememts_step=False):
		if dir == "N":
			self.the_map.move_n(entity)
		if dir == "S":
			self.the_map.move_s(entity)
		if dir == "E":
			self.the_map.move_e(entity)
		if dir == "W":
			self.the_map.move_w(entity)
		if incrememts_step:
			self.inc_step(entity.step_factor)

	def random_move(self, entity):
		self.move(random.choice(self.directions), entity)

	def rove(self, entity):
		while True:
			if self.mode == Mode.PLAYER:
				time.sleep(.25)
				self.random_move(entity)

	def draw_map(self):
		for display in self.displays:
			display.draw_map(self.the_map)

	def register_input_handler(self, handler):
		for in_method in self.inputs:
			in_method.register_handler(handler)

	def loop(self):

		self.register_input_handler(self._ui_input_handler)
		self.the_map = Map(self.displays[0].cols-3, self.displays[0].lines-6)
		self.the_map.array[0][0] = Tile((0,0), 'marker')
		self.cursor = self.create_cursor()
		self.player = self.create_player()
		self.draw_map()
		self.update_displays()
		self.ignore_input = False

		while True:
			ocols, olines = self.cols, self.lines
			cols = curses.tigetnum('cols')
			lines = curses.tigetnum('lines')
			if not (ocols, olines) == (cols, lines):
				the_map = Map(cols-3, lines-6)
				the_map.array[0][0] = Tile((0,0), 'marker')
			self.draw_map()
			self.handle_input()
			self.update_displays()

	def _cursor_input_handler(self, ch):
		try:
			d = CursesInput.ch_to_dir(ch)
		except ValueError:
			pass
		else:
			if self.mode == Mode.PLAYER:
				self.cursor.y = self.player.y
				self.cursor.x = self.player.x
			self.move(d, self.cursor)

	def _player_input_handler(self, ch):
		if self.mode == Mode.PLAYER:
			try:
				d = CursesInput.ch_to_dir(ch)
			except ValueError:
				pass
			else:
				self.move(d, self.player, incrememts_step=True)

	def _ui_input_handler(self, ch):
		if ch == ord('a'):
			self.the_map.selected_terrain = self.the_map.terrain_cycle.next()
		if ch == ord('q'):
			sys.exit(0)
		if ch == ord('\t'):
			self.next_mode()
		if ch == 27:
			self.reset_mode()
		# Need to figure out a suitable way to get the mouse position from
		# the display.
		#
		# The display should be able to return the mouse position, and then
		# also all the rest of the mouse positioning and which button information
		# needs to be done in a input/display independent way.
		#
		# if ch == CursesInput.MOUSE_CLICK:
		# 	_, mx, my, _, bstate = curses.getmouse()
		# 	y, x = self.screen.getyx()
		# 	if (bstate & curses.BUTTON1_CLICKED):
		# 		if (-1 < mx-1 < self.the_map.cols) and (-1 < my-1 < self.the_map.lines):
		# 			tile = Tile((my-1, mx-1), self.the_map.selected_terrain)
		# 			self.the_map.array[my-1][mx-1] = tile
		# 			self.draw(DisplayArea.MAP, tile)
		if ch == ord(' '):
			if self.mode == Mode.DRAW:
				tile = Tile((self.cursor.y, self.cursor.x), self.the_map.selected_terrain)
				self.the_map.array[self.cursor.y][self.cursor.x] = tile

	def handle_input(self):
		ch = self.input_dispatcher.get_input()
		for inp in self.inputs:
			inp.handle_input(ch)

	def update_displays(self):
		for display in self.displays:
			display.update(self.the_map)

	def create_cursor(self):
		cursor = Entity(self.the_map.starting_coords, "Cursor", self.displays[0].colors['wall'])
		cursor.ghost = True
		self.register_input_handler(self._cursor_input_handler)
		return cursor

	def create_player(self):
		player = Entity(self.the_map.starting_coords, "Player", self.displays[0].colors['wall'])
		self.register_input_handler(self._player_input_handler)
		return player

class CursesTerminal(object):

	def __init__(self, engine, scr, tileset="default"):
		self.engine = engine
		self.screen = scr
		self.colors = self.set_colors(tileset=tileset)
		self.set_term_size()
		self._create_windows()
		self.screen.border()

	def set_term_size(self):
		self.cols = curses.tigetnum('cols')
		self.lines = curses.tigetnum('lines')

	def set_colors(self, tileset="default"):
		from wilderness.maps import Tile
		color_map = {}
		k = 1
		for terrain in Tile.terrain_types[tileset]:
			t = Tile.terrain_types[tileset][terrain]
			curses.init_pair(k, t[0], curses.COLOR_BLACK)
			color_map[terrain] = curses.color_pair(k)
			k += 1
		return color_map

	def draw_map(self, the_map):
		for row in the_map.array:
			for tile in row:
				self.main_window.addstr(tile.y, tile.x, repr(tile), self.colors[tile.terrain])

	def update(self, the_map):
		self.draw_map(the_map)
		self.draw_main_window()
	 	self.draw_status_window()
		self.screen.refresh()

	def draw_status_window(self):
		self.status_window.erase()
	 	self.status_window.border()
		if self.engine.mode == Mode.PLAYER:
			self.draw_entity_status(self.status_window, self.engine.player)
		elif self.engine.mode == Mode.LOOK:
			entity = self.engine.the_map.entities.get((self.engine.cursor.y, self.engine.cursor.x), None)
			if entity:
				self.draw_entity_status(self.status_window, entity)
			else:
				self.status_window.addstr(1,1, "Nothing Selected")
		self.status_window.refresh()

	def draw_entity_status(self, window, entity):
		window.addstr(1,2, "HP:")
		window.addstr(1,6, ("%d" % entity.hp).rjust(2), self.colors['grass'])
		window.addstr(1,10, "STR:", self.colors['dirt'])
		window.addstr(1,15, ("%d" % entity.str).rjust(2), self.colors['wall'])
		window.addstr(1,18, "INT:", self.colors['dirt'])
		window.addstr(1,23, ("%d" % entity.int).rjust(2), self.colors['wall'])
		window.addstr(1,26, "DEX:", self.colors['dirt'])
		window.addstr(1,31, ("%d" % entity.dex).rjust(2), self.colors['wall'])
		window.addstr(1,34, "TURN: %s" % self.engine.step, self.colors['wall'])
		window.addstr(2,2, "MP:")
		window.addstr(2,6, ("%d" % entity.mp).rjust(2), self.colors['water'])
		window.addstr(2,11, "AC:", self.colors['dirt'])
		window.addstr(2,15, ("%d" % entity.ac).rjust(2), self.colors['wall'])
		window.addstr(2,18, "EXP:", self.colors['dirt'])
		window.addstr(2,23, (" %d" % entity.exp), self.colors['wall'])

	def draw_main_window(self):
		player = self.engine.player
		cursor = self.engine.cursor
		if self.engine.mode == Mode.PLAYER:
			self.draw(self.screen, (0,1), "%sx%s" % (str(player.y).zfill(3), str(player.x).zfill(3)), self.colors['wall'])
		else:
			self.draw(self.screen, (0,1), "%sx%s" % (str(cursor.y).zfill(3), str(cursor.x).zfill(3)), self.colors['wall'])		
		self.draw(self.screen, (0,15), self.engine.mode, self.colors['wall'])


		if self.engine.mode == Mode.DRAW:
			# draw the current selected drawing tile
			symbol = Tile.get_symbol(self.engine.the_map.selected_terrain)
			self.draw(self.screen, (0, self.cols-2), symbol, self.colors[self.engine.the_map.selected_terrain])

		# draw player
		py_px = (player.y+1, player.x+1)
		self.draw(self.screen, (0, 20), player.symbol, player.color)
		self.draw(self.screen, py_px, player.symbol, player.color | curses.A_BOLD)

		if self.engine.draw_cursor:
			self.main_window.chgat(cursor.y, cursor.x, 1, curses.A_STANDOUT)

		self.main_window.refresh()

	def get_mouse(self):
		return (curses.getmouse(), self.screen.getyx())

	def draw(self, screen, y_x, string, color):
		y, x = y_x
		screen.addstr(y, x, string, color)

	def _create_windows(self):
		self.main_window = curses.newwin(self.lines-6, self.cols-2, 1, 1)
		self.status_window = curses.newwin(4, self.cols-2, self.lines-5, 1)

class InputDispatcher(object):

	def __init__(self, screen):
		self.screen = screen

	def get_input(self):
		return self.screen.getch()

class CursesInput(object):

	# MOVE_KEYS = {}
	# MOVE_KEYS['N'] = [ord('k'), curses.KEY_UP]
	# MOVE_KEYS['S'] = [ord('j'), curses.KEY_DOWN]
	# MOVE_KEYS['W'] = [ord('h'), curses.KEY_LEFT]
	# MOVE_KEYS['E'] = [ord('l'), curses.KEY_RIGHT]

	VIM_KEYS = [ord(c) for c in "yubnhjkl"]
	ARROW_KEYS = [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]
	MOVE_KEYS = VIM_KEYS + ARROW_KEYS
	UI_KEYS = [ord(' '), '\t', 27, ord('a'), ord('q'), ord('x')]

	def __init__(self, engine, screen, listens_to=MOVE_KEYS + UI_KEYS):
		self.engine = engine
		self.screen = screen
		self.listens_to = listens_to
		self.handlers = []

	def register_handler(self, callback):
		self.handlers.append(callback)

	def handle_input(self, ch):
		if not ch in self.listens_to:
			return
		for handler in self.handlers:
			handler(ch)

	@classmethod
	def ch_to_dir(cls, ch):
		if ch in [ord('k'), curses.KEY_UP]: return "N"
		if ch in [ord('j'), curses.KEY_DOWN]: return "S"
		if ch in [ord('h'), curses.KEY_LEFT]: return "W"
		if ch in [ord('l'), curses.KEY_RIGHT]: return "E"
		if ch in [ord('y')]: return "NW"
		if ch in [ord('u')]: return "NE"
		if ch in [ord('b')]: return "SW"
		if ch in [ord('n')]: return "SE"
		raise ValueError

def initialize(screen):
	screen.leaveok(1)
	# screen.nodelay(11)
	curses.curs_set(0)
	curses.mousemask(curses.BUTTON1_CLICKED | curses.BUTTON1_DOUBLE_CLICKED)
	engine = Engine(screen)
	term = CursesTerminal(engine, screen)
	kbd = CursesInput(engine, screen)
	engine.add_display(term)
	engine.add_input(kbd)
	engine.loop()
