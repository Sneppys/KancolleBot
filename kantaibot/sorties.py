import random
import geomutils

def random_sortie():
    difficulty = random.randrange(1, 4)
    map_w, map_h = (600, 400)
    node_count = random.randrange(difficulty * 2 + 1, difficulty * 3 + 1)
    node_positions = []
    nodes = []
    # stage 1: create nodes
    start_node = Node(NODE_TYPE_START, 0, [])
    node_positions.append((random.randrange(0, map_w // 2), random.randrange(map_h)))
    nodes.append(start_node)
    start_node._gen_connections = []
    nid = 1
    for n in range(node_count + 1):
        if (n == node_count):
            ntype = NODE_TYPE_BOSS
        else:
            ntype = random_node_type()
        node = Node(ntype, nid, [])
        nodes.append(node)
        node._gen_connections = []
        conn_weight = random.randrange(10)
        num_connections = 1 if conn_weight < 6 else (2 if conn_weight < 8 else 3)
        for i in range(num_connections):
            gen_min = 0
            if (ntype == NODE_TYPE_BOSS):
                gen_min = 1 # let's not connect boss nodes to the start
            node_connect = random.randrange(gen_min, nid)
            if (not node in nodes[node_connect]._gen_connections):
                nodes[node_connect]._gen_connections.append(node)
        nid += 1
    # stage 2: create routes
    for n in nodes:
        connected = list(n._gen_connections)
        if (len(connected) > 0):
            random.shuffle(connected)
            num_routes = random.randrange(1, len(connected) + 1)
            for i in range(num_routes):
                r = Route([])
                r.nodes_to.append(connected.pop().nid) # make sure one node in each route
                n.routes.append(r)
            while (len(connected) > 0):
                rand_route = random.choice(n.routes)
                rand_route.nodes_to.append(connected.pop().nid)
    # stage 3: positioning
    for nid in range(1, len(nodes)):
        n = nodes[nid]
        pos_n = None
        timeout_limit = 15000
        allowed_intersections = 0
        while timeout_limit > 0:
            undesireable_position = False
            found_intersections = 0
            pos_n = (random.randrange(map_w), random.randrange(map_h))
            # check if too close to any points
            for npos in node_positions:
                if (geomutils.dist_sq(npos, pos_n) < 35 * 35):
                    undesireable_position = True
                    break
            # check if paths intersect
            for nf_i in range(len(node_positions)):
                if (undesireable_position):
                    break
                node_from = nodes[nf_i]
                for route in node_from.routes:
                    if (undesireable_position):
                        break
                    if (n.nid in route.nodes_to): # all routes that end with current node
                        q1 = node_positions[nf_i]

                        for node_check_from in range(len(node_positions)):
                            node_check1 = nodes[node_check_from]
                            p2 = node_positions[node_check_from]
                            for route_check in node_check1.routes:
                                if (undesireable_position):
                                    break
                                for node_check_to in route_check.nodes_to:
                                    if (node_check_from != nf_i and node_check_to != nf_i and node_check_to < len(node_positions)):
                                        q2 = node_positions[node_check_to]
                                        if (geomutils.lines_intersect(pos_n, q1, p2, q2)):
                                            found_intersections += 1
                                            if (found_intersections > allowed_intersections):
                                                undesireable_position = True
                                                break
            # check if too close to any paths
            for node_check_from in range(len(node_positions)):
                if (undesireable_position):
                    break
                node_check1 = nodes[node_check_from]
                p1 = node_positions[node_check_from]
                for route_check in node_check1.routes:
                    if (undesireable_position):
                        break
                    for node_check_to in route_check.nodes_to:
                        if (undesireable_position):
                            break
                        if (node_check_to < len(node_positions)):
                            p2 = node_positions[node_check_to]
                            if (geomutils.distance_to_line(pos_n, p1, p2) < 30):
                                undesireable_position = True
            # check if paths too close to any points
            for nf_i in range(len(node_positions)):
                if (undesireable_position):
                    break
                node_from = nodes[nf_i]
                for route in node_from.routes:
                    if (undesireable_position):
                        break
                    if (n.nid in route.nodes_to):
                        q1 = node_positions[nf_i]
                        for chk_ind in range(len(node_positions)):
                            if (chk_ind != nf_i):
                                pos_chk = node_positions[chk_ind]
                                if (geomutils.distance_to_line(pos_chk, pos_n, q1) < 30):
                                    undesireable_position = True
                                    break
            if (undesireable_position): # this is an undesireable position
                if (timeout_limit < 4000 and timeout_limit % 1000 == 0):
                    allowed_intersections += 1
                timeout_limit -= 1
                continue
            break

        node_positions.append(pos_n)

    return Sortie(difficulty, (map_w, map_h), node_positions, nodes)

def random_node_type():
    weight = sum(map(lambda x: x.pick_weight, NODE_TYPES))
    targ_weight = random.randrange(weight)
    for t in NODE_TYPES:
        targ_weight -= t.pick_weight
        if (targ_weight < 0):
            return t
    return NODE_TYPE_BATTLE

class Sortie:
    def __init__(self, difficulty, map_size, node_positions, nodes):
        self.difficulty = difficulty
        self.map_size = map_size
        self.nodes = list(zip(node_positions, nodes))

class NodeType:
    def __init__(self, tid, color, pick_weight=0):
        self.tid = tid
        self.color = color
        self.pick_weight = pick_weight
        NODE_TYPES.append(self)

NODE_TYPES = []
NODE_TYPE_START = NodeType(0, (0, 0, 255))
NODE_TYPE_BATTLE = NodeType(1, (255, 0, 0), 100)
NODE_TYPE_AVOIDED = NodeType(2, (0, 255, 255), 20)
NODE_TYPE_RESOURCE_FUEL = NodeType(3, (0, 255, 0), 15)
NODE_TYPE_RESOURCE_AMMO = NodeType(4, (0, 255, 0), 15)
NODE_TYPE_RESOURCE_STEEL = NodeType(5, (0, 255, 0), 15)
NODE_TYPE_RESOURCE_BAUXITE = NodeType(6, (0, 255, 0), 15)
NODE_TYPE_MAELSTROM = NodeType(7, (220, 200, 220), 10)
NODE_TYPE_NIGHTBATTLE = NodeType(8, (150, 0, 255), 5)
NODE_TYPE_AIR_RAID = NodeType(9, (255, 150, 0), 2)
NODE_TYPE_BOSS = NodeType(10, (150, 0, 0))

class Node:
    def __init__(self, ntype, nid, routes, enemies=[]):
        self.ntype = ntype
        self.nid = nid
        self.routes = routes
        self.enemies = enemies

    def symbol(self):
        syms = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        if (self.nid < 1):
            return "*"
        if (self.nid > len(syms)):
            return "".join(["Z"] * (self.nid - len(syms) + 1))
        return syms[self.nid - 1]


class Route:
    def __init__(self, nodes_to):
        self.nodes_to = nodes_to
