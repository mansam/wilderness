def chunks(l, n):
	"""
	Divide map into evenly sized chunks.

	"""

	for i in xrange(0, len(l), n):
		yield l[i:i + n]

def load_config(config_file_name):
	config_dict = {}
	config_file = open(config_file_name).readlines()
	for config_entry in config_file:
		config = config_entry[:-1].split(" ")
		config_dict[config[0]] = config[1:]
	return config_dict

def is_passable(matrix, y_x):
	y, x = y_x
	tile = matrix[y][x]
	if hasattr(tile, "is_passable"):
		return tile.is_passable()
	elif isinstance(tile, (tuple, list)):
		# a tile with nothing in it is passable
		return not tile
	else:
		return True

def get_neighbors(y_x, map, radius=1, check_passable=True):
	"""
	Return the neighbor tiles within a radius surrounding a center tile.
	Optionally considers whether a tile is passable when considering
	whether it is a neighbor.

	"""

	y, x = y_x

	vals = [0]
	for i in range(1, radius+1):
		vals.append(i)
		vals.append(-i)

	neighbors = set()
	for i in vals:
		for j in vals:
			new_x = x+i
			new_y = y+j
			if (new_x >= 0 and new_x < len(map[0])
		    	and new_y >= 0 and new_y < len(map)
		    	and (new_x, new_y) != (x, y)
		    	and (is_passable(map, (new_y, new_x)) or not check_passable)):
				neighbors.add((new_y, new_x))
	return neighbors

def calculate_distance(x1_y1, x2_y2, ceiling=True):
	"""
	Calculate the distance between two
	tiles on the map. Returns the ceiling
	of the distance by default.

	"""

	x1, y1 = x1_y1
	x2, y2 = x2_y2

	import math
	distance = math.sqrt(math.pow(x2 -x1, 2) + math.pow(y2 - y1, 2))
	if ceiling:
		return math.ceil(distance)
	else:
		return distance

def reconstruct_path(came_from, current_node):
	"""
	:param came_from:
	:type came_from: dict

	:param current_node:
	:type current_node: tuple

	:rtype: list:
	
	"""

	if came_from.has_key(current_node):
		p = reconstruct_path(came_from, came_from[current_node])
		p.append(current_node)
		return p
	else:
		return [current_node]

def a_star(start, goal, matrix, check_passable=True):
	"""
	Perform an A* search for the best path across a matrix.

	"""

	import operator

	closedset = set()	# The set of nodes already evaluated.
	openset = set([start])	# The set of tentative nodes to be evaluated, initially containing the start node
	came_from = {}   # The map of navigated nodes.

	g_score = {}
	h_score = {}
	f_score = {}

	g_score[start] = 0	# Cost from start along best known path.
	h_score[start] = calculate_distance(start, goal)
	f_score[start] = g_score[start] + h_score[start] # Estimated total cost from start to goal through y.

	while openset:
		sorted_fscore = sorted(f_score.iteritems(), key=operator.itemgetter(1))
		current = sorted_fscore[0][0]
		if current == goal:
			return reconstruct_path(came_from, goal)

		openset.remove(current)
		del f_score[current]
		closedset.add(current)
		for neighbor in get_neighbors(current, matrix, check_passable=check_passable):
			if neighbor in closedset:
				continue
			tentative_g_score = g_score[current] + calculate_distance(current, neighbor, ceiling=False)

			if neighbor not in openset:
				openset.add(neighbor)
				h_score[neighbor] = calculate_distance(neighbor, goal, ceiling=False)
				tentative_is_better = True
			elif tentative_g_score < g_score[neighbor]:
				tentative_is_better = True
			else:
				tentative_is_better = False

			if tentative_is_better:
				came_from[neighbor] = current
				g_score[neighbor] = tentative_g_score
				f_score[neighbor] = g_score[neighbor] + h_score[neighbor]

	return False