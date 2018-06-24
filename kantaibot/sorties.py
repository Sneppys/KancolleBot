"""Handles sortie generation and rules."""
import random
import geomutils


def random_sortie():
    """Generate a random sortie and return the Sortie object."""
    difficulty = random.randrange(1, 4)
    map_w, map_h = (600, 400)
    node_count = random.randrange(difficulty * 2 + 1, difficulty * 3 + 1)
    node_positions = []
    nodes = []
    # stage 1: create nodes
    start_node = Node(NODE_TYPE_START, 0, [])
    node_positions.append((random.randrange(
        map_w // 5, map_w // 3), random.randrange(map_h // 5, map_h * 4 // 5)))
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
        num_connections = 1 if conn_weight < 7 else (
            2 if conn_weight < 9 else 3)
        for i in range(num_connections):
            gen_min = 0
            if (ntype == NODE_TYPE_BOSS):
                gen_min = 1  # let's not connect boss nodes to the start
            while True:
                node_connect = random.randrange(gen_min, nid)
                if (len(nodes[node_connect]._gen_connections) < 2):
                    break
            # prevent boss node from being directly connected from start to a
            #   'free' node (no battle)
            # will raise the chances of requiring at least one battle
            # if it is connected, change it to a battle node
            disallow_boss_connect = [NODE_TYPE_AVOIDED,
                                     NODE_TYPE_RESOURCE_FUEL,
                                     NODE_TYPE_RESOURCE_AMMO,
                                     NODE_TYPE_RESOURCE_STEEL,
                                     NODE_TYPE_RESOURCE_BAUXITE,
                                     NODE_TYPE_MAELSTROM]
            if (ntype == NODE_TYPE_BOSS and nodes[node_connect].ntype
                    in disallow_boss_connect):
                if (nodes[node_connect] in start_node._gen_connections):
                    nodes[node_connect].ntype = NODE_TYPE_BATTLE
            if (node not in nodes[node_connect]._gen_connections):
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
        n.routing_rules.generate_random(
            difficulty, exclusions=list(gen_exclusions))
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

        past_node_pos = [node_positions[cn.nid]
                         for cn in nodes if cn.routing_rules.routes_to(cn.nid)]
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
            pos_n = (cx + random.randrange(-search_radius_l, search_radius_r),
                     cy + random.randrange(-search_radius_v, search_radius_v))
            pos_n = (min(max(pos_n[0], 0), map_w),
                     min(max(pos_n[1], 0), map_h))
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
                    # all routes that end with current node
                    if (n.nid == route.node_to):
                        q1 = node_positions[nf_i]

                        for node_check_from in range(len(node_positions)):
                            node_check1 = nodes[node_check_from]
                            p2 = node_positions[node_check_from]
                            for route_check in \
                                    node_check1.routing_rules.routes:
                                if (undesireable_position):
                                    break
                                node_check_to = route_check.node_to
                                if (node_check_from != nf_i and node_check_to
                                    != nf_i and node_check_to <
                                        len(node_positions)):
                                    q2 = node_positions[node_check_to]
                                    if (geomutils.lines_intersect(pos_n, q1,
                                                                  p2, q2)):
                                        found_intersections += 1
                                        if (found_intersections >
                                                allowed_intersections):
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
                                if (geomutils.distance_to_line(pos_chk, pos_n,
                                                               q1) < 30):
                                    undesireable_position = True
                                    break
            if (undesireable_position):  # this is an undesireable position
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
    """Return a random node type based on the weights of the node types."""
    weight = sum(map(lambda x: x.pick_weight, NODE_TYPES))
    targ_weight = random.randrange(weight)
    for t in NODE_TYPES:
        targ_weight -= t.pick_weight
        if (targ_weight < 0):
            return t
    return NODE_TYPE_BATTLE


class Sortie:
    """Represents a sortie."""

    def __init__(self, difficulty, map_size, node_positions, nodes):
        """Initialize the sortie.

        Parameters
        ----------
        difficulty : int
            An integer representation of the difficulty during generation.
        map_size : tuple
            2-tuple of ints representing the size of the map of nodes.
        node_positions : list
            List of 2-tuples representing the positions of each node.
        nodes : list
            List of Node objects the sortie contains.
        """
        self.difficulty = difficulty
        self.map_size = map_size
        self.nodes = list(zip(node_positions, nodes))


class NodeType:
    """Represents a type of node that can be generated."""

    def __init__(self, tid, color, pick_weight=0):
        """Initialize the type.

        Parameters
        ----------
        tid : int
            The ID of the node type.
        color : tuple
            A 3-tuple giving the colour of the node in (R, G, B) form.
        pick_weight : int
            The weight this node type has in being generated.
        """
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
# Generate relative complexity for the node based on that, and spawn
#   accordingly


class Node:
    """Represents a node in the sortie graph."""

    def __init__(self, ntype, nid, enemies=[]):
        """Initialize the node.

        Parameters
        ----------
        ntype : NodeType
            The type of node this is.
        nid : int
            The index of this node in the sortie graph.
        enemies : list
            (Unused) The enemies that are on this node.
        """
        self.ntype = ntype
        self.nid = nid
        self.routing_rules = RoutingRules([])
        self.enemies = enemies

    def symbol(self):
        """Return the symbol to use for the node on the map, as a string."""
        syms = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        if (self.nid < 1):
            return "*"
        if (self.nid > len(syms)):
            return "".join(["Z"] * (self.nid - len(syms) + 1))
        return syms[self.nid - 1]


class RoutingRules:
    """Contains information detailing a node's routing information."""

    def __init__(self, routes):
        """Initialize the routing.

        Parameters
        ----------
        routes : list
            List of Route objects that the routing rules uses.
        """
        self.routes = routes
        self.rtype = 0

    def routes_to(self, nid):
        """Return a list of node IDs that the routing rules can route to."""
        return nid in (x.node_to for x in self.routes)

    def generate_random(self, difficulty, exclusions=[]):
        """Generate random routes and rules.

        Parameters
        ----------
        difficulty : int
            Integer representation of the difficulty.
        exclusions : list
            List of routing type IDs that this object should not generate.
        """
        if (len(self.routes) < 2):
            return
        rtype_gen = random.random()
        if (rtype_gen < (1.0 - difficulty * 0.2)):
            self.rtype = 0  # normal random, no condition
        elif (rtype_gen < (1.0 - difficulty * 0.125)):
            self.rtype = 1  # weighted if condition true, random otherwise
        else:
            self.rtype = 2  # forced if condition true, never otherwise

        if (self.rtype != 0):
            valid_types = [x for x in ROUTING_TYPES if x.tid not in exclusions]
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
                    route_limit.routing_weight_if_true = 50
            else:
                self.rtype = 0
        else:
            route_limit = None
        for r in self.routes:
            if (not r == route_limit):
                r.set_type(None)
                if (self.rtype == 1):
                    r.routing_weight_if_other_true = int(
                        21.42 / (len(self.routes) - 1))
                elif (self.rtype == 2):
                    r.routing_weight_if_other_true = 0

    def format(self):
        """Return a list of formatted routing rules by node.

        Returns
        -------
        dict
            A dictionary where the key is the node ID, and the value is a
            string giving information about the route.
        """
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
        """Return a random weighted route given the current fleet.

        Takes into account the fleet composition and the routing rules of
        each node to generate a weighted random result.
        """
        weights = {x: x.routing_weight for x in self.routes}
        if (self.rtype in (1, 2)):
            is_true = [r for r in self.routes if r.matches_rule(fleet)]
            if (len(is_true) > 0):
                for r in self.routes:
                    if (r not in is_true):
                        weights[r] = r.routing_weight_if_other_true
                    else:
                        weights[r] = r.routing_weight_if_true

        total_weight = sum(weights.values())
        targ = random.randrange(total_weight)
        for k, v in weights.items():
            targ -= v
            if (targ < 0):
                return k
        return None


class Route:
    """Represents a route to a certain node."""

    def __init__(self, node_to):
        """Initialize the node.

        Parameters
        ----------
        node_to : int
            The node ID of the node to route to.
        """
        self.node_to = node_to
        self.routing_type = None
        self.routing_value = 0
        # default routing weight
        self.routing_weight = 50
        # routing weight if condition is true
        self.routing_weight_if_true = 50
        # routing weight if other condition in node is true
        self.routing_weight_if_other_true = 50

    def set_type(self, routing_type):
        """Set the type of this route to the given RoutingType."""
        self.routing_type = routing_type
        if (routing_type):
            self.routing_value = random.randrange(
                routing_type.min, routing_type.max + 1)

    def format(self):
        """Return a formatted string giving information about the requirements.

        Will return None if the route has no type (Random).
        """
        if (self.routing_type):
            return self.routing_type.format(self.routing_value)
        else:
            return None

    def matches_rule(self, fleet):
        """Return true if the fleet matches the routing type requirements.

        Returns False if the routing type is None (Random).
        """
        if (self.routing_type):
            return self.routing_type.valid_func(fleet, self.routing_value)
        return False


class RoutingType:
    """Represents a routing type."""

    def __init__(self, tid, infostring, infostring_zero=None, min=0, max=0,
                 weight=5, excludes=[]):
        """Initialize the routing type.

        Parameters
        ----------
        tid : int
            The ID of this type.
        infostring : str
            A string giving information about routing.
            Replaces {0} with the routing value.
        infostring_zero : str
            A string giving information about routing if the routing value
            is 0.
        min : int
            The minimum the routing value can be.
        max : int
            The maximum the routing value can be.
        weight : int
            The weight the routing type takes in generation.
        excludes : list
            A list of routing type IDs incompatible with this one.
        """
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

    def valid_func(self, fleet, val):
        """Return true if the fleet matches the rule. False by default."""
        return False

    def format(self, val):
        """Return the infostring formatted to match the given value."""
        if (val == 0):
            return self.infostring_zero
        if (self.infostring.count('{0}') > 0):
            return self.infostring.format(val)
        return self.infostring


def count(fleet, types):
    """Return the total number in the fleet of ships matching the given types.

    Parameters
    ----------
    fleet : list
        List of ShipInstance representing the fleet.
    types : list
        List of ship type discriminators to count.
    """
    c = 0
    for si in fleet:
        if (si.base().stype in types):
            c += 1
    return c


ROUTING_INFO_MIN = "Fleet contains at least {0} %s"


class RoutingTypeMinimum(RoutingType):
    """A routing type based on having a minimum number of certain ships."""

    def __init__(self, tid, info, stypes, min=1, max=2, weight=5, excludes=[]):
        """Initialize the routing type.

        Parameters
        ----------
        tid : int
            The ID of this type.
        info : str
            A string representing the ship types this routing type handles.
        stypes : list
            A list of ship type IDs that this routing type handles.
        min : int
            The minimum the routing value can be.
        max : int
            The maximum the routing value can be.
        weight : int
            The weight the routing type takes in generation.
        excludes : list
            A list of routing type IDs incompatible with this one.
        """
        super().__init__(tid, ROUTING_INFO_MIN %
                         info, min=min, max=max, weight=weight,
                         excludes=excludes)
        self.stypes = stypes

    def valid_func(self, fleet, val):
        """Return true if the number of ships is larger than the minimum."""
        return count(fleet, self.stypes) >= val


ROUTING_INFO_MAX = "Amount of %s ≤{0}"
ROUTING_INFO_MAX_ZERO = "Fleet does not contain any %s"


class RoutingTypeMaximum(RoutingType):
    """A routing type based on having a maximum number of certain ships."""

    def __init__(self, tid, info, stypes, min=0, max=2, weight=5, excludes=[]):
        """Initialize the routing type.

        Parameters
        ----------
        tid : int
            The ID of this type.
        info : str
            A string representing the ship types this routing type handles.
        stypes : list
            A list of ship type IDs that this routing type handles.
        min : int
            The minimum the routing value can be.
        max : int
            The maximum the routing value can be.
        weight : int
            The weight the routing type takes in generation.
        excludes : list
            A list of routing type IDs incompatible with this one.
        """
        super().__init__(tid, ROUTING_INFO_MAX % info,
                         infostring_zero=ROUTING_INFO_MAX_ZERO %
                         info, min=min, max=max, weight=weight,
                         excludes=excludes)
        self.stypes = stypes

    def valid_func(self, fleet, val):
        """Return true if the number of ships is smaller than the maximum."""
        return count(fleet, self.stypes) <= val


ROUTING_TYPES = []
ROUTING_TYPE_LIMIT_DESTROYER = RoutingTypeMaximum(10, "DD/DE", ["DD", "DE"], max=3, excludes=[20])
ROUTING_TYPE_LIMIT_DD = RoutingTypeMaximum(11, "DD", ["DD"], max=3, excludes=[20])
ROUTING_TYPE_LIMIT_CARRIER = RoutingTypeMaximum(12, "carriers", ["CV", "CVB", "CVL"], max=2, excludes=[21, 22])
ROUTING_TYPE_LIMIT_CV = RoutingTypeMaximum(13, "CV(B)", ["CV", "CVB"], max=2, excludes=[21, 22])
ROUTING_TYPE_LIMIT_BATTLESHIP = RoutingTypeMaximum(14, "(F)BB(V)", ["FBB", "BB", "BBV"], max=2, excludes=[22, 23, 24])
ROUTING_TYPE_LIMIT_BBV = RoutingTypeMaximum(15, "BBV", ["BBV"], max=2, weight=3, excludes=[22, 23, 24])
ROUTING_TYPE_LIMIT_FBB = RoutingTypeMaximum(16, "FBB", ["FBB"], max=2, weight=2, excludes=[22, 23, 24])
ROUTING_TYPE_LIMIT_SUBMARINE = RoutingTypeMaximum(17, "SS(V)", ["SS", "SSV"], max=2, excludes=[26])
ROUTING_TYPE_LIMIT_CA = RoutingTypeMaximum(18, "CA(V)", ["CA", "CAV"], max=2, excludes=[25])
ROUTING_TYPE_MIN_DESTROYER = RoutingTypeMinimum(20, "DD/DE", ["DD", "DE"], min=1, max=2, excludes=[10, 11])
ROUTING_TYPE_MIN_CARRIER = RoutingTypeMinimum(21, "carriers", ["CV", "CVL", "CVB"], min=1, max=2, excludes=[12, 13])
ROUTING_TYPE_MIN_BATTLESHIP = RoutingTypeMinimum(22, "(F)BB(V)", ["FBB", "BB", "BBV"], min=1, max=2, excludes=[14, 15, 16])
ROUTING_TYPE_MIN_FBB = RoutingTypeMinimum(23, "FBB", ["FBB"], min=1, max=2, weight=2, excludes=[14, 15, 16])
ROUTING_TYPE_MIN_BBV = RoutingTypeMinimum(24, "BBV", ["BBV"], min=1, max=2, weight=3, excludes=[14, 15, 16])
ROUTING_TYPE_MIN_CA = RoutingTypeMinimum(25, "CA(V)", ["CA", "CAV"], min=1, max=2, excludes=[18])
ROUTING_TYPE_MIN_SUBMARINE = RoutingTypeMinimum(26, "SS(V)", ["SS", "SSV"], min=1, max=2, excludes=[17])
