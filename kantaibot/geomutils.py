import math

def lines_intersect(p1, q1, p2, q2):
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)
    if (o1 != o2 and o3 != o4):
        return True
    if (o1 == 0 and on_segment(p1, p2, q1)):
        return True
    if (o2 == 0 and on_segment(p1, q2, q1)):
        return True
    if (o3 == 0 and on_segment(p2, p1, q2)):
        return True
    if (o4 == 0 and on_segment(p2, q1, q2)):
        return True
    return False

def on_segment(p, q, r):
    return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
        q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))

def orientation(p, q, r):
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if (val == 0):
        return 0
    return 1 if val > 0 else 2

def dist_sq(p, q):
    return ((p[0] - q[0]) * (p[0] - q[0])) + ((p[1] - q[1]) * (p[1] - q[1]))

def distance_to_line(q, p1, p2):
    x_diff = p2[0] - p1[0]
    y_diff = p2[1] - p1[1]
    num = abs(y_diff * q[0] - x_diff * q[1] + p2[0] * p1[1] - p2[1] * p1[0])
    den = math.sqrt(y_diff ** 2 + x_diff ** 2)
    return num / den
