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
    node_positions.append((random.randrange(map_w // 5, map_w // 3), random.randrange(map_h // 5, map_h * 4 // 5)))
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
        num_connections = 1 if conn_weight < 7 else (2 if conn_weight < 9 else 3)
        for i in range(num_connections):
            gen_min = 0
            if (ntype == NODE_TYPE_BOSS):
                gen_min = 1 # let's not connect boss nodes to the start
            while True:
                node_connect = random.randrange(gen_min, nid)
                if (len(nodes[node_connect]._gen_connections) < 2):
                    break
            # prevent boss node from being directly connected from start to a 'free' node (no battle)
            # will raise the chances of requiring at least one battle
            # if it is connected, change it to a battle node
            disallow_boss_connect = [NODE_TYPE_AVOIDED, NODE_TYPE_RESOURCE_FUEL,
                                     NODE_TYPE_RESOURCE_AMMO, NODE_TYPE_RESOURCE_STEEL,
                                     NODE_TYPE_RESOURCE_BAUXITE, NODE_TYPE_MAELSTROM]
            if (ntype == NODE_TYPE_BOSS and nodes[node_connect].ntype in disallow_boss_connect):
                if (nodes[node_connect] in start_node._gen_connections):
                    nodes[node_connect].ntype = NODE_TYPE_BATTLE
            if (not node in nodes[node_connect]._gen_connections):
                nodes[node_connect]._gen_connections.append(node)
        nid += 1
    # stage 2: create routes
    gen_exclusions = set()
    for n in nodes:
        connected = list(n._gen_connections)
        if (len(connected) > 0):
            for i in range(len(connected)):
                r = Route([])
                r.node_to = connected.pop().nid
                n.routing_rules.routes.append(r)
    for n in nodes:
        n.routing_rules.generate_random(difficulty, exclusions=list(gen_exclusions))
        for r in n.routing_rules.routes:
            if (r.routing_type):
                gen_exclusions.update(r.routing_type.excludes)
                gen_exclusions.add(r.routing_type.tid)
    # stage 3: positioning
    for nid in range(1, len(nodes)):
        n = nodes[nid]

        search_radius_l = map_w // 20
        search_radius_r = map_w // 2
        search_radius_v = map_h // 3

        past_node_pos = [node_positions[cn.nid] for cn in nodes if cn.routing_rules.routes_to(cn.nid)]
        if (len(past_node_pos) > 0):
            cx = sum(x[0] for x in past_node_pos) // len(past_node_pos)
            cy = sum(x[1] for x in past_node_pos) // len(past_node_pos)
        else:
            cx, cy = node_positions[0]
        pos_n = None
        timeout_limit = 15000
        allowed_intersections = 0
        while timeout_limit > 0:
            undesireable_position = False
            found_intersections = 0
            pos_n = (cx + random.randrange(-search_radius_l, search_radius_r), cy + random.randrange(-search_radius_v, search_radius_v))
            pos_n = (min(max(pos_n[0], 0), map_w), min(max(pos_n[1], 0), map_h))
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
                for route in node_from.routing_rules.routes:
                    if (undesireable_position):
                        break
                    if (n.nid == route.node_to): # all routes that end with current node
                        q1 = node_positions[nf_i]

                        for node_check_from in range(len(node_positions)):
                            node_check1 = nodes[node_check_from]
                            p2 = node_positions[node_check_from]
                            for route_check in node_check1.routing_rules.routes:
                                if (undesireable_position):
                                    break
                                node_check_to = route_check.node_to
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
                for route_check in node_check1.routing_rules.routes:
                    if (undesireable_position):
                        break
                    node_check_to = route_check.node_to
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
                for route in node_from.routing_rules.routes:
                    if (undesireable_position):
                        break
                    if (n.nid == route.node_to):
                        q1 = node_positions[nf_i]
                        for chk_ind in range(len(node_positions)):
                            if (chk_ind != nf_i):
                                pos_chk = node_positions[chk_ind]
                                if (geomutils.distance_to_line(pos_chk, pos_n, q1) < 30):
                                    undesireable_position = True
                                    break
            if (undesireable_position): # this is an undesireable position
                if (timeout_limit < 4000 and timeout_limit % 1000 == 0):
                    search_radius_r += map_w // 8
                    search_radius_v += map_h // 10
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
NODE_TYPE_AVOIDED = NodeType(2, (0, 255, 255), 10)
NODE_TYPE_RESOURCE_FUEL = NodeType(3, (0, 150, 0), 10)
NODE_TYPE_RESOURCE_AMMO = NodeType(4, (0, 150, 0), 10)
NODE_TYPE_RESOURCE_STEEL = NodeType(5, (0, 150, 0), 10)
NODE_TYPE_RESOURCE_BAUXITE = NodeType(6, (0, 150, 0), 10)
NODE_TYPE_MAELSTROM = NodeType(7, (220, 200, 220), 10)
NODE_TYPE_NIGHTBATTLE = NodeType(8, (150, 0, 255), 5)
NODE_TYPE_AIR_RAID = NodeType(9, (255, 150, 0), 2)
NODE_TYPE_BOSS = NodeType(10, (150, 0, 0))

# TODO: For abyssal generation
# Take into account number of possible offroutes, and number of routing rules
# Generate relative complexity for the node based on that, and spawn accordingly
class Node:
    def __init__(self, ntype, nid, enemies=[]):
        self.ntype = ntype
        self.nid = nid
        self.routing_rules = RoutingRules([])
        self.enemies = enemies

    def symbol(self):
        syms = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        if (self.nid < 1):
            return "*"
        if (self.nid > len(syms)):
            return "".join(["Z"] * (self.nid - len(syms) + 1))
        return syms[self.nid - 1]

class RoutingRules:
    def __init__(self, routes):
        self.routes = routes
        self.rtype = 0

    def routes_to(self, nid):
        return nid in [x.node_to for x in self.routes]

    def generate_random(self, difficulty, exclusions=[]):
        if (len(self.routes) < 2):
            return
        rtype_gen = random.random()
        if (rtype_gen < (1.0 - difficulty * 0.2)):
            self.rtype = 0 # normal random, no condition
        elif (rtype_gen < (1.0 - difficulty * 0.125)):
            self.rtype = 1 # weighted if condition true, random otherwise
        else:
            self.rtype = 2 # forced if condition true, never otherwise

        if (self.rtype != 0):
            valid_types = [x for x in ROUTING_TYPES if not x.tid in exclusions]
            if (len(valid_types) > 0):
                total_weight = sum(map(lambda x: x.weight, valid_types))
                targ = random.randrange(total_weight)
                type = None
                for n in valid_types:
                    targ -= n.weight
                    if (targ < 0):
                        type = n
                        break
                route_limit = random.choice(self.routes)
                route_limit.set_type(type)

                if (self.rtype == 2):
                    route_limit.routing_weight = 0
            else:
                self.rtype = 0
        else:
            route_limit = None
        for r in self.routes:
            if (not r == route_limit):
                r.set_type(None)
                if (self.rtype == 1):
                    r.routing_weight_if_other_true = int(21.42 / (len(self.routes) - 1))
                elif (self.rtype == 2):
                    r.routing_weight_if_other_true = 0

    def format(self):
        nodes = {}
        for r in self.routes:
            req = r.format()
            if (len(self.routes) < 2):
                req = "Fixed route"
            else:
                if (not req):
                    req = ""
                    if (self.rtype in [0, 1] or len(self.routes) > 2):
                        req += "random"
                    if (self.rtype == 2):
                        if (len(self.routes) > 2):
                            req += " if "
                        req += "no other requirements are met"
                    req = req.capitalize()
                elif (self.rtype == 1):
                    req = "70% if {0}, Random otherwise".format(req)
            nodes[r.node_to] = req
        return nodes

    def get_route_to(self, fleet):
        # TODO given fleet comp, determine route to go to
        pass

class Route:
    def __init__(self, node_to):
        self.node_to = node_to
        self.routing_type = None
        self.routing_value = 0
        self.routing_weight = 50 # default routing weight
        self.routing_weight_if_other_true = 50 # routing weight if other condition in node is true

    def set_type(self, routing_type):
        self.routing_type = routing_type
        if (routing_type):
            self.routing_value = random.randrange(routing_type.min, routing_type.max + 1)

    def format(self):
        if (self.routing_type):
            return self.routing_type.format(self.routing_value)
        else:
            return None

class RoutingType:
    def __init__(self, tid, infostring, infostring_zero=None, min=0, max=0, weight=5, excludes=[]):
        self.tid = tid
        self.infostring = infostring
        if (not infostring_zero):
            self.infostring_zero = infostring
        else:
            self.infostring_zero = infostring_zero
        self.min = min
        self.max = max
        self.weight = weight
        self.excludes = excludes
        ROUTING_TYPES.append(self)

    def format(self, val):
        if (val == 0):
            return self.infostring_zero
        if (self.infostring.count('{0}') > 0):
            return self.infostring.format(val)
        return self.infostring

ROUTING_TYPES = []
ROUTING_TYPE_LIMIT_DESTROYER = RoutingType(10, "Amount of DD/DE ≤{0}", infostring_zero="Fleet does not contain DD/DE", max=3, excludes=[11, 20])
ROUTING_TYPE_LIMIT_DD = RoutingType(11, "Amount of DD ≤{0}", infostring_zero="Fleet does not contain DD", max=3, excludes=[10, 20])
ROUTING_TYPE_LIMIT_CARRIER = RoutingType(12, "Amount of carriers ≤{0}", infostring_zero="Fleet does not contain carriers", max=2, excludes=[13, 21, 22])
ROUTING_TYPE_LIMIT_CV = RoutingType(13, "Amount of CV(B) ≤{0}", infostring_zero="Fleet does not contain CV(B)", max=2, excludes=[12, 21, 22])
ROUTING_TYPE_LIMIT_BATTLESHIP = RoutingType(14, "Amount of (F)BB(V) ≤{0}", infostring_zero="Fleet does not contain (F)BB(V)", max=2, excludes=[15, 16, 22, 23, 24])
ROUTING_TYPE_LIMIT_BBV = RoutingType(15, "Amount of BBV ≤{0}", infostring_zero="Fleet does not contain BBV", max=2, weight=3, excludes=[14, 16, 22, 23, 24])
ROUTING_TYPE_LIMIT_FBB = RoutingType(16, "Amount of FBB ≤{0}", infostring_zero="Fleet does not contain FBB", max=2, weight=2, excludes=[13, 14, 22, 23, 24])
ROUTING_TYPE_LIMIT_SUBMARINE = RoutingType(17, "Amount of SS(V) ≤{0}", infostring_zero="Fleet does not contain SS(V)", max=2, excludes=[26])
ROUTING_TYPE_LIMIT_CA = RoutingType(18, "Amount of CA(V) ≤{0}", infostring_zero="Fleet contains no CA(V)", max=2, excludes=[25])
ROUTING_TYPE_MIN_DESTROYER = RoutingType(20, "Fleet contains ≥{0} DD/DE", min=1, max=2, excludes=[10, 11])
ROUTING_TYPE_MIN_CARRIER = RoutingType(21, "Fleet contains ≥{0} carriers", min=1, max=2, excludes=[12, 13])
ROUTING_TYPE_MIN_BATTLESHIP = RoutingType(22, "Fleet contains ≥{0} (F)BB(V)", min=1, max=2, excludes=[23, 24, 14, 15, 16])
ROUTING_TYPE_MIN_FBB = RoutingType(23, "Fleet contains ≥{0} FBB", min=1, max=2, weight=2, excludes=[22, 24, 14, 15, 16])
ROUTING_TYPE_MIN_BBV = RoutingType(24, "Fleet contains ≥{0} BBV", min=1, max=2, weight=3, excludes=[22, 23, 14, 15, 16])
ROUTING_TYPE_MIN_CA = RoutingType(25, "Fleet contains ≥{0} CA(V)", min=1, max=2, excludes=[18])
ROUTING_TYPE_MIN_SUBMARINE = RoutingType(26, "Fleet contains ≥{0} SS(V)", min=1, max=2, excludes=[17])
