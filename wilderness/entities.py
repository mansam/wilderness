class Entity(object):

	def __init__(self, coords, name, color, symbol='@', hp=10, mp=10, ac=10, st=8, it=8, dx=8, exp=0):
		y, x = coords
		self.y = y
		self.x = x
		self.hp = hp
		self.mp = mp
		self.ac = ac
		self.str = st
		self.int = it
		self.dex = dx
		self.exp = exp
		self.ghost = False
		self.cursor = False
		self.name = name
		self.color = color
		self.symbol = symbol
		self.step_factor = 1