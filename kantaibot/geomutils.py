"""Miscellaneous utility functions for 2d geometry."""
import math


def lines_intersect(p1, q1, p2, q2):
    """Return True if the lines intersect.

    Parameters
    ----------
    p1 : tuple
        Point of the start of the first line.
    q1 : tuple
        Point of the end of the first lines.
    p2 : tuple
        Point of the start of the second line.
    q2 : tuple
        Point of the end of the second line.
    """
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
    """Return True if the point r is on the line (p, q)."""
    return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
            q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))


def orientation(p, q, r):
    """Return the orientation of point r on the line (p, q).

    Returns 0 if the point is or would be on the line if the line was infinite.
    Returns 1 or 2 if the line is on one side or the other.
    """
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if (val == 0):
        return 0
    return 1 if val > 0 else 2


def dist_sq(p, q):
    """Return squared distance between point p and point q."""
    return ((p[0] - q[0]) * (p[0] - q[0])) + ((p[1] - q[1]) * (p[1] - q[1]))


def distance_to_line(q, p1, p2):
    """Return the distance of point q to line (p1, p2)."""
    x_diff = p2[0] - p1[0]
    y_diff = p2[1] - p1[1]
    num = abs(y_diff * q[0] - x_diff * q[1] + p2[0] * p1[1] - p2[1] * p1[0])
    den = math.sqrt(y_diff ** 2 + x_diff ** 2)
    return num / den
