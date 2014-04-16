# -*- encoding: utf-8 -*-
import random
import itertools
import wilderness

def weighted_choice(lst):
	n = random.uniform(0, 1)
	for item, weight in lst:
		if n < weight:
			break
		n = n - weight
	return item

class Tile(object):
	import curses

	terrain_types = {
		# this is super hacky and needs to be changed to
		# avoid using curses-- it needs to be abstract
		# enough that I can drop different front ends over it.
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
		"marker": True
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
		terrain = random.choice(tset)
		t = Tile(y_x, terrain, tileset)
		return t

	def __repr__(self):
		return Tile.get_symbol(self.terrain)

class Map(object):

	def __init__(self, cols, lines, default_terrain="dirt", tileset="default", starting_coords=(1,1)):
		"""
		Procedurally generate a map consisting of different biomes.

		"""
		self.cols = cols
		self.lines = lines
		self.array = []
		self.entities = {}
		self.tileset = tileset
		self.default_terrain = default_terrain
		self.terrain_cycle = itertools.cycle(Tile.terrain_types['default'])
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
			if not entity.ghost:
				self.entities[(entity.y, entity.x)] = None
			entity.y -= 1
			if not entity.ghost:
				self.entities[(entity.y, entity.x)] = entity

	def move_s(self, entity):
		if (entity.y+1 < self.lines and (self.array[entity.y+1][entity.x].is_passable() or entity.ghost)):
			if not entity.ghost:
				self.entities[(entity.y, entity.x)] = None
			entity.y += 1
			if not entity.ghost:
				self.entities[(entity.y, entity.x)] = entity

	def move_w(self, entity):
		if (entity.x-1 >= 0 and (self.array[entity.y][entity.x-1].is_passable() or entity.ghost)):
			if not entity.ghost:
				self.entities[(entity.y, entity.x)] = None
			entity.x -= 1
			if not entity.ghost:
				self.entities[(entity.y, entity.x)] = entity

	def move_e(self, entity):
		if (entity.x+1 < self.cols and (self.array[entity.y][entity.x+1].is_passable() or entity.ghost)):
			if not entity.ghost:
				self.entities[(entity.y, entity.x)] = None
			entity.x += 1
			if not entity.ghost:
				self.entities[(entity.y, entity.x)] = entity