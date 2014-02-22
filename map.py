# -*- encoding: utf-8 -*-
import random
import curses


def weighted_choice(lst):
	n = random.uniform(0, 1)
	for item, weight in lst:
		if n < weight:
			break
		n = n - weight
	return item

class Tile(object):

	palette = [
		('tree', "dark green", "green"),
		('grass', "dark green", "green"),
		('dirt', "dark gray", "light gray"),
		('hill', "dark gray", "light gray"),
		('water', "dark blue", "dark cyan")
	]

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
	def random_tile(cls, y_x, tileset="default"):
		tset = cls.terrain_types[tileset]
		terrain = random.choice(cls.tset)
		t = Tile(y_x, terrain, tileset)
		return t

	def __repr__(self):
		return self.terrain_types[self.tileset][self.terrain][2]


def get_adjacent(y_x, cols, lines):
	"""

	"""

	coords = []
	y, x = y_x
	for pair in ((y-1, x), (y, x-1), (y+1, x), (y, x+1)):
			if pair[0] >= 0 and pair[0] < lines and pair[1] >= 0 and pair[1] < cols and pair != (y, x):
				coords.append(pair)
	return coords

def create_map(starting_terrain, cols, lines, tileset="default"):
	"""
	Procedurally generate a map consisting of different biomes.

	"""
	

	new_map = []
	for y in range(0, lines):
		row = []
		for x in range(0, cols):
			row.append(None)
		new_map.append(row)

	modifier = .10
	curr_tile = (0,0)
	draw_prob = 4

	# new_map = Map(size)

	def paint(map, y_x, terrain, prob, mod, iteration=0, queue=[], visited=[]):
		y, x = y_x
		if random.random() <= prob:
		
			t = Tile((y, x), terrain)
			map[y][x] = t

			prob -= mod
			mod += .01
			if mod < 0:
				mod = 0
		else:
			terrain = weighted_choice(Tile.regional_probabilities[terrain])
			t = Tile((y,x), terrain)
			map[y][x] = t
			prob = 4
			mod = .01
		adj_list = get_adjacent((y, x), cols, lines)
		random.shuffle(adj_list)
		iteration += 1
		for pair in adj_list:
			if not map[pair[0]][pair[1]]:
				paint(map, pair, terrain, prob, mod, iteration)
				

	# doing this iteratively results in ugly maps
	paint(new_map, curr_tile, starting_terrain, draw_prob, modifier)
	# while queue:
	# 	y_x = queue.pop(0)
	# 	remaining, last_terrain, draw_prob, modifier = paint(new_map, y_x, last_terrain, draw_prob, modifier)
	# 	queue += remaining
	return new_map

def configure_colors(tileset):
	print curses.can_change_color()
	color_map = {}
	n = 1
	k = 1
	for terrain in Tile.terrain_types[tileset]:
		t = Tile.terrain_types[tileset][terrain]
		curses.init_pair(k, t[0], curses.COLOR_BLACK)
		color_map[terrain] = k
		k += 1
	return color_map

def main(screen):

	size = int(sys.argv[1])

	colors = configure_colors('default')

	import time
	screen.leaveok(1)
	curses.curs_set(2)
	cols = curses.tigetnum('cols')
	lines = curses.tigetnum('lines')
	w =  curses.newwin(lines, cols)

	while True:
		cols = curses.tigetnum('cols')
		lines = curses.tigetnum('lines')
		the_map = create_map('dirt', cols-2, lines-1)
		for row in the_map:
			for tile in row:
				w.addstr(tile.y, tile.x, repr(tile), curses.color_pair(colors[tile.terrain]))

		w.border()
		w.addstr(0,1, "Map %d" % count)
		w.addstr(0,15, "%dx%d" % (cols, lines))
		curses.setsyx(0,0)
		w.refresh()


if __name__ == '__main__':
	import locale
	import sys
	sys.setrecursionlimit(2**20)
	locale.setlocale(locale.LC_ALL,"")
	curses.wrapper(main)