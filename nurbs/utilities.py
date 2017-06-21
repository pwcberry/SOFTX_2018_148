"""
.. module:: utilities
    :platform: Unix, Windows
    :synopsis: A helper module for Curve and Surface classes

.. moduleauthor:: Onur Rauf Bingol

"""

import decimal
import math


# A float range function, implementation of http://stackoverflow.com/a/7267280
def frange(x, y, step):
    """ An implementation of a ``range()`` function which works with decimals.

    Reference to this implementation: http://stackoverflow.com/a/7267280

    :param x: start value
    :type x: integer or float
    :param y: end value
    :type y: integer or float
    :param step: increment
    :type step: integer or float
    :return: float
    :rtype: generator
    """
    step_str = str(step)
    while x <= y:
        yield float(x)
        x += decimal.Decimal(step_str)


# Normalizes knot vector (internal functionality)
def knotvector_normalize(knotvector=()):
    """ Normalizes the input knot vector between 0 and 1.

    :param knotvector: input knot vector
    :type knotvector: tuple
    :return: normalized knot vector
    :rtype: list
    """
    if len(knotvector) == 0:
        return knotvector

    first_knot = float(knotvector[0])
    last_knot = float(knotvector[-1])

    knotvector_out = []
    for kv in knotvector:
        knotvector_out.append((float(kv) - first_knot) / (last_knot - first_knot))

    return knotvector_out


# Autogenerates a uniform knot vector using the given degree and the number of control points
def knotvector_autogen(degree=0, num_ctrlpts=0):
    """ Generates a uniformly-spaced knot vector using the degree and the number of control points.

    :param degree: degree of the knot vector direction
    :type degree: integer
    :param num_ctrlpts: number of control points on that direction
    :type num_ctrlpts: integer
    :return: knot vector
    :rtype: list
    """
    if degree == 0 or num_ctrlpts == 0:
        raise ValueError("Input values should be different than zero.")

    # Min and max knot vector values
    knot_min = 0.0
    knot_max = 1.0

    # Equation to use: m = n + p + 1
    # p: degree, n+1: number of ctrlpts; m+1: number of knots
    m = degree + num_ctrlpts + 1

    # Initialize return value and counter
    knotvector = []
    i = 0

    # First degree+1 knots are "knot_min"
    while i < degree+1:
        knotvector.append(knot_min)
        i += 1

    # Calculate a uniform interval for middle knots
    num_segments = (m - (degree+1)*2)+1  # number of segments in the middle
    spacing = (knot_max - knot_min) / num_segments  # spacing between the knots (uniform)
    midknot = knot_min + spacing  # first middle knot
    # Middle knots
    while i < m-(degree+1):
        knotvector.append(midknot)
        midknot += spacing
        i += 1

    # Last degree+1 knots are "knot_max"
    while i < m:
        knotvector.append(knot_max)
        i += 1

    # Return autogenerated knot vector
    return knotvector


# Algorithm A2.1 (internal functionality)
def find_span(degree=0, knotvector=(), num_ctrlpts=0, knot=0, tol=0.001):
    """ Algorithm A2.1 of The NURBS Book by Piegl & Tiller."""
    # Number of knots; m + 1
    # Number of control points; n + 1
    # n = m - p - 1; where p = degree
    #m = len(knotvector) - 1
    #n = m - degree - 1
    n = num_ctrlpts - 1
    if abs(knotvector[n + 1] - knot) <= tol:
        return n

    low = degree
    high = n + 1
    mid = int((low + high) / 2)

    while (knot < knotvector[mid]) or (knot >= knotvector[mid + 1]):
        if knot < knotvector[mid]:
            high = mid
        else:
            low = mid
        mid = int((low + high) / 2)

    return mid


# Finds knot multiplicity (internal functionality)
def find_multiplicity(knot=-1, knotvector=(), tol=0.001):
    """ Finds knot multiplicity."""
    # Find and return the multiplicity of the input knot in the given knot vector
    mult = 0  # initial multiplicity
    # Loop through the knot vector
    for kv in knotvector:
        # Float equality should be checked w.r.t a tolerance value
        if abs(knot - kv) <= tol:
            mult += 1
    return mult


# Algorithm A2.2 (internal functionality)
def basis_functions(degree=0, knotvector=(), span=0, knot=0):
    """ Algorithm A2.2 of The NURBS Book by Piegl & Tiller."""
    left = [None for x in range(degree+1)]
    right = [None for x in range(degree+1)]
    N = [None for x in range(degree + 1)]

    # N[0] = 1.0 by definition
    N[0] = 1.0

    for j in range(1, degree+1):
        left[j] = knot - knotvector[span+1-j]
        right[j] = knotvector[span+j] - knot
        saved = 0.0
        for r in range(0, j):
            temp = N[r] / (right[r+1] + left[j-r])
            N[r] = saved + right[r+1] * temp
            saved = left[j-r] * temp
        N[j] = saved

    return N


# Algorithm A2.2 - modified (internal functionality)
def basis_functions_all(degree=0, knotvector=(), span=0, knot=0):
    """ A modified version of Algorithm A2.2 of The NURBS Book by Piegl & Tiller."""
    N = [[None for x in range(degree+1)] for y in range(degree+1)]
    for i in range(0, degree+1):
        bfuns = basis_functions(i, knotvector, span, knot)
        for j in range(0, i+1):
            N[j][i] = bfuns[j]
    return N


# Algorithm A2.3 (internal functionality)
def basis_functions_ders(degree=0, knotvector=(), span=0, knot=0, order=0):
    """ Algorithm A2.3 of The NURBS Book by Piegl & Tiller."""
    # Initialize variables for easy access
    left = [None for x in range(degree+1)]
    right = [None for x in range(degree+1)]
    ndu = [[None for x in range(degree+1)] for y in range(degree+1)]

    # N[0][0] = 1.0 by definition
    ndu[0][0] = 1.0

    for j in range(1, degree+1):
        left[j] = knot - knotvector[span+1-j]
        right[j] = knotvector[span+j] - knot
        saved = 0.0
        r = 0
        for r in range(r, j):
            # Lower triangle
            ndu[j][r] = right[r+1] + left[j-r]
            temp = ndu[r][j-1] / ndu[j][r]
            # Upper triangle
            ndu[r][j] = saved + (right[r+1] * temp)
            saved = left[j-r] * temp
        ndu[j][j] = saved

    # Load the basis functions
    ders = [[None for x in range(degree+1)] for y in range((min(degree, order)+1))]
    for j in range(0, degree+1):
        ders[0][j] = ndu[j][degree]

    # Start calculating derivatives
    a = [[None for x in range(degree+1)] for y in range(2)]
    # Loop over function index
    for r in range(0, degree+1):
        # Alternate rows in array a
        s1 = 0
        s2 = 1
        a[0][0] = 1.0
        # Loop to compute k-th derivative
        for k in range(1, order+1):
            d = 0.0
            rk = r - k
            pk = degree - k
            if r >= k:
                a[s2][0] = a[s1][0] / ndu[pk+1][rk]
                d = a[s2][0] * ndu[rk][pk]
            if rk >= -1:
                j1 = 1
            else:
                j1 = -rk
            if (r - 1) <= pk:
                j2 = k - 1
            else:
                j2 = degree - r
            for j in range(j1, j2+1):
                a[s2][j] = (a[s1][j] - a[s1][j-1]) / ndu[pk+1][rk+j]
                d += (a[s2][j] * ndu[rk+j][pk])
            if r <= pk:
                a[s2][k] = -a[s1][k-1] / ndu[pk+1][r]
                d += (a[s2][k] * ndu[r][pk])
            ders[k][r] = d

            # Switch rows
            j = s1
            s1 = s2
            s2 = j

    # Multiply through by the the correct factors
    r = float(degree)
    for k in range(1, order+1):
        for j in range(0, degree+1):
            ders[k][j] *= r
        r *= (degree - k)

    # Return the basis function derivatives list
    return ders


# Checks if the input (u, v) values are valid (internal functionality)
def check_uv(u=-1, v=-1, test_normal=False, delta=0.1):
    """ Checks if the input (u, v) values are valid."""
    # Check u value
    if u < 0.0 or u > 1.0:
        raise ValueError('"u" value should be between 0 and 1.')
    # Check v value
    if v < 0.0 or v > 1.0:
        raise ValueError('"v" value should be between 0 and 1.')

    if test_normal:
        # Check if we are on any edge of the surface
        if u + delta > 1.0 or u + delta < 0.0 or v + delta > 1.0 or v + delta < 0.0:
            raise ValueError("Cannot calculate normal on an edge.")


# Computes vector cross-product
def vector_cross(vect1=(), vect2=()):
    """ Computes the cross-product of the input vectors.

    :param vect1: input vector 1
    :type vect1: tuple
    :param vect2: input vector 2
    :type vect2: tuple
    :return: result of the cross-product
    :rtype: list
    """
    if not vect1 or not vect2:
        raise ValueError("Input arguments are empty.")

    if len(vect1) != 3 or len(vect2) != 3:
        raise ValueError("Input tuples should contain 3 elements representing (x,y,z).")

    # Compute cross-product
    retval = [(vect1[1] * vect2[2]) - (vect1[2] * vect2[1]),
              (vect1[2] * vect2[0]) - (vect1[0] * vect2[2]),
              (vect1[0] * vect2[1]) - (vect1[1] * vect2[0])]

    # Return the cross product of the input vectors
    return retval


# Computes vector dot-product
def vector_dot(vect1=(), vect2=()):
    """ Computes the dot-product of the input vectors.

    :param vect1: input vector 1
    :type vect1: tuple
    :param vect2: input vector 2
    :type vect2: tuple
    :return: result of the cross-product
    :rtype: list
    """
    if not vect1 or not vect2:
        raise ValueError("Input arguments are empty.")

    # Compute dot-product
    retval = (vect1[0] * vect2[0]) + (vect1[1] * vect2[1])
    if len(vect1) == 3 and len(vect2) == 3:
        retval += (vect1[2] * vect2[2])

    # Return the dot product of the input vectors
    return retval


# Normalizes the input vector
def vector_normalize(vect=()):
    """ Generates a unit vector from the input.

    :param vect: vector to be normalized
    :type vect: tuple
    :return: the normalized vector (i.e. the unit vector)
    :rtype: list
    """
    if not vect:
        raise ValueError("Input argument is empty.")

    sq_sum = math.pow(vect[0], 2) + math.pow(vect[1], 2)
    if len(vect) == 3:
        sq_sum += math.pow(vect[2], 2)

    # Calculate magnitude of the vector
    magnitude = math.sqrt(sq_sum)

    if magnitude != 0:
        # Normalize the vector
        if len(vect) == 3:
            retval = [vect[0] / magnitude,
                      vect[1] / magnitude,
                      vect[2] / magnitude]
        else:
            retval = [vect[0] / magnitude,
                      vect[1] / magnitude]
        # Return the normalized vector
        return retval
    else:
        raise ValueError("The magnitude of the vector is zero.")

# Returnd control points and weigths(optional) from json dict representation
def parse_json(jsonrepr):
    """ Deserializes control points from json representation - weigths are used if present, else
    a unity vector is used.

    :param jsonrepr: json representation
    :type jsonrepr: dict
    :return: tuple of control points and weights
    """
    # Control points are required
    try:
        ctrlpts = jsonrepr['controlpoints']
        ctrlptsx = ctrlpts['x']
        ctrlptsy = ctrlpts['y']
    except KeyError:
        print('Unable to parse control points')
        sys.exit(1)

    # Weigths are optional
    ctrlptsw = [1.0] * len(ctrlptsx)
    try:
        ctrlptsw = jsonrepr['weights']            
    except KeyError:
        pass

    ctrlpts = [[float(ctrlptx), float(ctrlpty)] for ctrlptx, ctrlpty in zip(ctrlptsx, ctrlptsy)]
    weights = [float(ctrlptw) for ctrlptw in ctrlptsw]

    return ctrlpts, weights
