# -*- encoding: utf-8 -*-
import random
import curses
import time
import sys
import threading
from itertools import cycle

MOVE_KEYS = {}
MOVE_KEYS['N'] = [ord('k'), curses.KEY_UP]
MOVE_KEYS['S'] = [ord('j'), curses.KEY_DOWN]
MOVE_KEYS['W'] = [ord('h'), curses.KEY_LEFT]
MOVE_KEYS['E'] = [ord('l'), curses.KEY_RIGHT]

def weighted_choice(lst):
	n = random.uniform(0, 1)
	for item, weight in lst:
		if n < weight:
			break
		n = n - weight
	return item

class Tile(object):

	terrain_types = {

		"default":{
			"tree":[curses.COLOR_GREEN, (0,20,0), '∆', True],
			"hill":[curses.COLOR_WHITE,(50,50,50), '☗', False],
			"water":[curses.COLOR_BLUE, (0,0,255), 'w', False],
			"dirt":[curses.COLOR_YELLOW, (200,200,200), '░', True],
			"grass":[curses.COLOR_GREEN, (0,200,0), '░', True],
			"wall":[curses.COLOR_WHITE, (200,200,200), "#", False],
			"road":[curses.COLOR_YELLOW, (255,255,0), "|", True],
			"marker":[curses.COLOR_RED, (200,0,0), ".", True]
		},

		"moon":{
			"tree":[(75,75,75), (255,255,255), '^^', True],
			"hill":[(150,75,75),(50,0,0), '))', False],
			"water":[(100,20,20), (200,0,0), '  ', False],
			"dirt":[(155,100,100), (200,200,200), '  ', True],
			"grass":[(100,100,100), (20,20,20), '..', True],
			"wall":[(20,20,20), (200,200,200), "##", False],
			"road":[(30,30,30), (255,255,0), "| ", True],
			"marker":[(0,0,0), (200,0,0), "..", True]
		}
	}

	passable = {
		"grass": True,
		"dirt": True,
		"gravel": True,
		"stone": True,
		"road": True,
	}

	regional_probabilities = {
		"water":[("water", .3), ("dirt", .35), ("tree", .2), ("grass", .1), ("hill", .05)],
		"dirt":[("dirt", .4), ("grass", .25), ("hill", .2), ("water", .1), ("tree", .05)],
		"grass":[("tree", .4), ("grass", .25), ("dirt", .2), ("water", .1), ("hill", .05)],
		"hill":[("tree", .5), ("hill", .15), ("dirt", .2), ("water", .1), ("grass", .05)],
		"tree":[("tree", .4), ("hill", .25), ("grass", .2), ("water", .1), ("dirt", .05)]
	}

	def __init__(self, y_x, terrain, tileset="default"):
		y, x = y_x
		self.y = y
		self.x = x
		self.terrain = terrain
		self.tileset = tileset

	def is_passable(self):
		return self.passable.get(self.terrain, False)

	@classmethod
	def get_symbol(cls, terrain, tileset='default'):
		return cls.terrain_types[tileset][terrain][2]
	
	@classmethod
	def random_tile(cls, y_x, tileset="default"):
		tset = cls.terrain_types[tileset]
		terrain = random.choice(cls.tset)
		t = Tile(y_x, terrain, tileset)
		return t

	def __repr__(self):
		return Tile.get_symbol(self.terrain)

class Entity(object):

	def __init__(self, coords):
		y, x = coords
		self.y = y
		self.x = x
		self.ghost = False

class Map(object):

	def __init__(self, cols, lines, default_terrain="dirt", tileset="default", starting_coords=(1,1)):
		"""
		Procedurally generate a map consisting of different biomes.

		"""
		self.cols = cols
		self.lines = lines
		self.array = []
		self.entities = []
		self.tileset = tileset
		self.default_terrain = default_terrain
		self.terrain_cycle = cycle(Tile.terrain_types['default'])
		self.selected_terrain = self.default_terrain
		self.starting_coords = starting_coords
		for y in range(0, lines):
			row = []
			for x in range(0, cols):
				row.append(None)
			self.array.append(row)
		modifier = .10
		curr_tile = (0,0)
		draw_prob = 4
		self._paint(curr_tile, default_terrain, draw_prob, modifier)
		# while queue:
		# 	y_x = queue.pop(0)
		# 	remaining, last_terrain, draw_prob, modifier = paint(new_map, y_x, last_terrain, draw_prob, modifier)
		# 	queue += remaining

	def _paint(self, y_x, terrain, prob, mod, iteration=0, queue=[], visited=[]):
		y, x = y_x
		if random.random() <= prob:
			t = Tile((y, x), terrain)
			self.array[y][x] = t
			prob -= mod
			mod += .01
			if mod < 0:
				mod = 0
		else:
			terrain = weighted_choice(Tile.regional_probabilities[terrain])
			t = Tile((y,x), terrain)
			self.array[y][x] = t
			prob = 4
			mod = .01
		adj_list = self.get_adjacent((y, x), self.cols, self.lines)
		random.shuffle(adj_list)
		iteration += 1
		for pair in adj_list:
			if not self.array[pair[0]][pair[1]]:
				self._paint(pair, terrain, prob, mod, iteration)
				
	def get_adjacent(self, y_x, cols, lines):
		"""

		"""

		coords = []
		y, x = y_x
		for pair in ((y-1, x), (y, x-1), (y+1, x), (y, x+1)):
				if pair[0] >= 0 and pair[0] < lines and pair[1] >= 0 and pair[1] < cols and pair != (y, x):
					coords.append(pair)
		return coords

	def move_n(self, entity):
		if (entity.y-1 >= 0 and (self.array[entity.y-1][entity.x].is_passable() or entity.ghost)):
			entity.y -= 1

	def move_s(self, entity):
		if (entity.y+1 < self.lines and (self.array[entity.y+1][entity.x].is_passable() or entity.ghost)):
			entity.y += 1

	def move_w(self, entity):
		if (entity.x-1 >= 0 and (self.array[entity.y][entity.x-1].is_passable() or entity.ghost)):
			entity.x -= 1

	def move_e(self, entity):
		if (entity.x+1 < self.cols and (self.array[entity.y][entity.x+1].is_passable() or entity.ghost)):
			entity.x += 1

def configure_colors(tileset):
	color_map = {}
	n = 1
	k = 1
	for terrain in Tile.terrain_types[tileset]:
		t = Tile.terrain_types[tileset][terrain]
		curses.init_pair(k, t[0], curses.COLOR_BLACK)
		color_map[terrain] = curses.color_pair(k)
		k += 1
	return color_map

def main(screen):

	screen.leaveok(1)
	screen.nodelay(11)
	curses.curs_set(0)

	colors = configure_colors('default')
	curses.mousemask(curses.BUTTON1_CLICKED | curses.BUTTON1_DOUBLE_CLICKED)

	cols = curses.tigetnum('cols')
	lines = curses.tigetnum('lines')
	w =  curses.newwin(lines-2, cols-2, 1, 1)
	the_map = Map(cols-3, lines-2)
	the_map.array[0][0] = Tile((0,0), 'marker')
	for row in the_map.array:
		for tile in row:
			w.addstr(tile.y, tile.x, repr(tile), colors[tile.terrain])
	# w.refresh()

	game = GameState()
	screen.border()

	last_mouse = (0,0)
	player = Entity(the_map.starting_coords)
	cursor = Entity(the_map.starting_coords)
	cursor.ghost = True
	test_beast = Entity((4,4))
	beast_thread = threading.Thread(target=rove, args=(test_beast, the_map))
	beast_thread.daemon = True
	beast_thread.start()

	while True:
		ocols, olines = cols, lines
		cols = curses.tigetnum('cols')
		lines = curses.tigetnum('lines')
		if not (ocols, olines) == (cols, lines):
			the_map = Map(cols-3, lines-2)
			the_map.array[0][0] = Tile((0,0), 'marker')

		for row in the_map.array:
			for tile in row:
				w.addstr(tile.y, tile.x, repr(tile), colors[tile.terrain])
	
		ch = screen.getch()
		if ch == curses.KEY_MOUSE:
			_, mx, my, _, bstate = curses.getmouse()
			y, x = screen.getyx()
			if (bstate & curses.BUTTON1_CLICKED):
				if (-1 < mx-1 < the_map.cols) and (-1 < my-1 < the_map.lines):
					tile = Tile((my-1, mx-1), the_map.selected_terrain) 
					the_map.array[my-1][mx-1] = tile
					w.addstr(tile.y, tile.x, repr(tile), colors[tile.terrain])
			last_mouse = (my, mx)
		if ch == ord(' '):
			if game.mode == game.MODE_DRAW:
				tile = Tile((cursor.y, cursor.x), the_map.selected_terrain) 
				the_map.array[cursor.y][cursor.x] = tile
				w.addstr(tile.y, tile.x, repr(tile), colors[tile.terrain])			
		if ch == ord('a'):
			the_map.selected_terrain = the_map.terrain_cycle.next()
		if ch == ord('q'):
			sys.exit(0)
		if ch == ord('\t'):
			game.next_mode()
		if ch == 27:
			game.reset_mode()

		if game.mode == game.MODE_PLAYER:
			cursor.y = player.y
			cursor.x = player.x
			move(the_map, ch, player)
		move(the_map, ch, cursor)
		
		w.addstr(player.y, player.x, '@', curses.color_pair(0) | curses.A_BOLD)
		w.addstr(test_beast.y, test_beast.x, 'h', colors['water'])

		screen.addstr(0,1, "%dx%d" % (player.y, player.x))
		screen.addstr(0,8, game.MODE_LABELS[game.mode])
		screen.addstr(0, cols-2, Tile.get_symbol(the_map.selected_terrain), colors[the_map.selected_terrain])
		if game.draw_cursor:
			w.chgat(cursor.y, cursor.x, 1, curses.A_STANDOUT)

		w.refresh()
		screen.refresh()

def move(the_map, dir, entity):
	if dir in MOVE_KEYS['N']:
		the_map.move_n(entity)
	if dir in MOVE_KEYS['S']:
		the_map.move_s(entity)
	if dir in MOVE_KEYS['E']:
		the_map.move_e(entity)
	if dir in MOVE_KEYS['W']:
		the_map.move_w(entity)

def rove(entity, the_map):
	directions = [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]
	while True:
		time.sleep(.25)
		move(the_map, random.choice(directions), entity)

class GameState(object):

	MODE_PLAYER = 0
	MODE_DRAW = 1
	MODE_LOOK = 2

	MODE_LABELS = {
		MODE_PLAYER: "Play",
		MODE_DRAW: "Draw",
		MODE_LOOK: "Look"
	}

	def __init__(self):
		self.mode = self.MODE_PLAYER
		self.modes = cycle([self.MODE_DRAW, self.MODE_LOOK, self.MODE_PLAYER])
		self.draw_cursor = False

	def next_mode(self):
		self.mode = next(self.modes)
		if self.mode == self.MODE_PLAYER:
			self.draw_cursor = False
		else:
			self.draw_cursor = True

	def reset_mode(self):
		while self.mode != self.MODE_PLAYER:
			self.next_mode()

if __name__ == '__main__':
	import locale
	sys.setrecursionlimit(2**20)
	locale.setlocale(locale.LC_ALL,"")
	curses.wrapper(main)

