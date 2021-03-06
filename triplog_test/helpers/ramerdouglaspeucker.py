#!/usr/bin/python
"""Ramer-Douglas-Peucker line simplification demo.
Dmitri Lebedev, detail@ngs.ru

http://ryba4.com/python/ramer-douglas-peucker
2010-04-17"""


def reduce_trackpoints(trackpoints, epsilon):
    points = list()
    reduced_trackpoints = list()
    for pt in trackpoints:
        points.append(Vec2D( float(pt.longitude) , float(pt.latitude) ))
    line = Line(points)
    rdp_trkpts_reduced = line.simplify(epsilon) #simplified douglas peucker line
    for trackpoint in rdp_trkpts_reduced.points:
        reduced_trackpoints.append([trackpoint.coords[0],trackpoint.coords[1]]) #list of simplified trackpoints
    return reduced_trackpoints


def ramerdouglas(line, dist):
    """Does Ramer-Douglas-Peucker simplification of
    a line with `dist` threshold.
    `line` must be a list of Vec objects,
    all of the same type (either 2d or 3d)."""
    if len(line) < 3:
        return line

    begin, end = line[0], line[-1]
    distSq = [begin.distSq(curr) -
        ((end - begin) * (curr - begin)) ** 2 /
        begin.distSq(end) for curr in line[1:-1]]

    maxdist = max(distSq)
    if maxdist < dist ** 2:
        return [begin, end]

    pos = distSq.index(maxdist)
    return (ramerdouglas(line[:pos + 2], dist) + 
            ramerdouglas(line[pos + 1:], dist)[1:])

class Line:
    """Polyline. Contains a list of points and outputs
    a simplified version of itself."""
    def __init__(self, points):
        pointclass = points[0].__class__
        for i in points[1:]:
            if i.__class__ != pointclass:
                raise TypeError("""All points in a Line
                                must have the same type""")
        self.points = points

    def simplify(self, dist):
        if self.points[0] != self.points[-1]:
            points = ramerdouglas(self.points, dist)
        else:
            points = ramerdouglas(
                self.points[:-1], dist) + self.points[-1:]
        return self.__class__(points)

    def __repr__(self):
        return '{0}{1}'.format(self.__class__.__name__,
            tuple(self.points))

class Vec:
    """Generic vector class for n-dimensional vectors
    for any natural n."""
    def __eq__(self, obj):
        """Equality check."""
        if self.__class__ == obj.__class__:
            return self.coords == obj.coords
        return False

    def __repr__(self):
        """String representation. The string is executable as Python
        code and makes the same vector."""
        return '{0}{1}'.format(self.__class__.__name__, self.coords)

    def __add__(self, obj):
        """Add a vector."""
        if not isinstance(obj, self.__class__):
            raise TypeError

        return self.__class__(*list(map(sum, list(zip(self.coords, obj.coords)))))

    def __neg__(self):
        """Reverse the vector."""
        return self.__class__(*[-i for i in self.coords])

    def __sub__(self, obj):
        """Substract object from self."""
        if not isinstance(obj, self.__class__):
            raise TypeError

        return self + (- obj)

    def __mul__(self, obj):
        """If obj is scalar, scales the vector.
        If obj is vector returns the scalar product."""
        if isinstance(obj, self.__class__):
            return sum([a * b for (a, b) in zip(self.coords, obj.coords)])

        return self.__class__(*[i * obj for i in self.coords])

    def dist(self, obj = None):
        """Distance to another object. Leave obj empty to get
        the length of vector from point 0."""
        return self.distSq(obj) ** 0.5

    def distSq(self, obj = None):
        """ Square of distance. Use this method to save
        calculations if you don't need to calculte an extra square root."""
        if obj is None:
            obj = self.__class__(*[0]*len(self.coords))
        elif not isinstance(obj, self.__class__):
            raise TypeError('Parameter must be of the same class')

        # simple memoization to save extra calculations
        if obj.coords not in self.distSqMem:
            self.distSqMem[obj.coords] = sum([(s - o) ** 2 for (s, o) in
                zip(self.coords, obj.coords)])
        return self.distSqMem[obj.coords]

class Vec3D(Vec):
    """3D vector"""
    def __init__(self, x, y, z):
        self.coords = x, y, z
        self.distSqMem = {}

class Vec2D(Vec):
    """2D vector"""
    def __init__(self, x, y):
        self.coords = x, y
        self.distSqMem = {}

if __name__ == '__main__':
    coast = Line([
    Vec2D( 6.247872 , 11.316756 ),
    Vec2D( 6.338566 , 11.316756 ),
    Vec2D( 6.633323 , 11.205644 ),
    Vec2D( 6.724018 , 11.205644 ),
    Vec2D( 6.792039 , 11.205644 ),
    Vec2D( 7.154817 , 11.372311 ),
    Vec2D( 7.313532 , 11.400089 ),
    Vec2D( 7.381553 , 11.344533 ),
    Vec2D( 7.336206 , 11.288978 ),
    Vec2D( 7.200164 , 11.288978 ),
    Vec2D( 7.154817 , 11.261200 ),
    Vec2D( 7.132143 , 11.233422 ),
    Vec2D( 7.154817 , 11.150089 ),
    Vec2D( 7.268185 , 11.177867 ),
    Vec2D( 7.313532 , 11.122311 ),
    Vec2D( 7.404227 , 11.150089 ),
    Vec2D( 7.472248 , 11.094533 ),
    Vec2D( 7.767005 , 10.900089 ),
    Vec2D( 7.758951 , 10.864989 ),
    Vec2D( 7.752684 , 10.837656 ),
    Vec2D( 7.426900 , 10.927867 ),
    Vec2D( 6.519955 , 10.927867 ),
    Vec2D( 6.429261 , 10.900089 ),
    Vec2D( 6.315893 , 10.955644 ),
    Vec2D( 6.270545 , 10.955644 ),
    Vec2D( 6.247872 , 10.927867 ),
    Vec2D( 6.111830 , 11.011200 ),
    Vec2D( 6.066483 , 11.066756 ),
    Vec2D( 5.862420 , 11.038978 ),
    Vec2D( 5.817073 , 10.955644 ),
    Vec2D( 5.771726 , 10.900089 ),
    Vec2D( 5.862420 , 10.761200 ),
    Vec2D( 5.975788 , 10.733422 ),
    Vec2D( 6.157177 , 10.566756 ),
    Vec2D( 6.247872 , 10.511200 ),
    Vec2D( 6.293219 , 10.427867 ),
    Vec2D( 6.315893 , 10.233422 ),
    Vec2D( 6.315893 , 10.177867 ),
    Vec2D( 6.542629 , 9.844533 ),
    Vec2D( 6.587976 , 9.761200 ),
    Vec2D( 6.610650 , 9.288978 ),
    Vec2D( 6.542629 , 9.066756 ),
    Vec2D( 6.565303 , 8.900089 ),
    Vec2D( 6.519955 , 8.816756 ),
    Vec2D( 6.542629 , 8.761200 ),
    Vec2D( 6.565303 , 8.733422 ),
    Vec2D( 6.429261 , 8.427867 ),
    Vec2D( 6.474608 , 8.316756 ),
    Vec2D( 6.724018 , 8.288978 ),
    Vec2D( 6.882733 , 8.538978 ),
    Vec2D( 6.973428 , 8.594533 ),
    Vec2D( 6.996101 , 8.622311 ),
    Vec2D( 7.200164 , 8.650089 ),
    Vec2D( 7.290859 , 8.650089 ),
    Vec2D( 7.426900 , 8.483422 ),
    Vec2D( 7.404227 , 8.455644 ),
    Vec2D( 7.245511 , 8.511200 ),
    Vec2D( 6.996101 , 8.427867 ),
    Vec2D( 7.041449 , 8.372311 ),
    Vec2D( 7.154817 , 8.455644 ),
    Vec2D( 7.200164 , 8.455644 ),
    Vec2D( 7.245511 , 8.455644 ),
    Vec2D( 7.381553 , 8.316756 ),
    Vec2D( 7.381553 , 8.261200 ),
    Vec2D( 7.404227 , 8.233422 ),
    Vec2D( 7.494921 , 8.205644 ),
    Vec2D( 7.767005 , 8.288978 ),
    Vec2D( 7.948394 , 8.233422 ),
    Vec2D( 8.016415 , 8.261200 ),
    Vec2D( 8.197804 , 8.094533 ),
    Vec2D( 8.084435 , 7.816756 ),
    Vec2D( 8.152456 , 7.733422 ),
    Vec2D( 8.175130 , 7.650089 ),
    Vec2D( 8.175130 , 7.511200 ),
    Vec2D( 8.311172 , 7.427867 ),
    Vec2D( 8.311172 , 7.372311 ),
    Vec2D( 8.651276 , 7.372311 ),
    Vec2D( 8.923360 , 7.316756 ),
    Vec2D( 8.900686 , 7.261200 ),
    Vec2D( 8.809991 , 7.261200 ),
    Vec2D( 8.472735 , 7.171122 ),
    Vec2D( 8.333845 , 7.038978 ),
    Vec2D( 8.282022 , 6.981100 ),
    Vec2D( 8.254778 , 6.848911 ),
    Vec2D( 8.265824 , 6.816756 ),
    Vec2D( 8.239206 , 6.711211 ),
    Vec2D( 8.219743 , 6.612067 ),
    Vec2D( 8.130227 , 6.433044 ),
    Vec2D( 8.084435 , 6.316756 ),
    Vec2D( 8.107109 , 6.288978 ),
    Vec2D( 7.948394 , 6.177867 ),
    Vec2D( 7.925720 , 5.983422 ),
    Vec2D( 7.857699 , 5.816756 ),
    Vec2D( 7.835026 , 5.788978 ),
    Vec2D( 7.857699 , 5.511200 ),
    Vec2D( 7.812352 , 5.400089 ),
    Vec2D( 7.812352 , 5.344533 ),
    Vec2D( 7.812352 , 5.177867 ),
    Vec2D( 8.084435 , 4.733422 ),
    Vec2D( 8.107109 , 4.622311 ),
    Vec2D( 7.857699 , 4.344533 ),
    Vec2D( 7.630963 , 4.261200 ),
    Vec2D( 7.540268 , 4.177867 ),
    Vec2D( 7.494921 , 4.150089 ),
    Vec2D( 7.449574 , 4.150089 ),
    Vec2D( 7.404227 , 4.150089 ),
    Vec2D( 7.336206 , 4.094533 ),
    Vec2D( 7.313532 , 4.066756 ),
    Vec2D( 7.041449 , 4.011200 ),
    Vec2D( 6.905407 , 3.955644 ),
    Vec2D( 6.950754 , 3.900089 ),
    Vec2D( 7.200164 , 3.927867 ),
    Vec2D( 7.630963 , 3.872311 ),
    Vec2D( 7.721657 , 3.872311 ),
    Vec2D( 7.948394 , 3.788978 ),
    Vec2D( 7.993741 , 3.705644 ),
    Vec2D( 7.971067 , 3.677867 ),
    Vec2D( 7.925720 , 3.622311 ),
    Vec2D( 8.175130 , 3.705644 ),
    Vec2D( 8.401866 , 3.650089 ),
    Vec2D( 8.492561 , 3.650089 ),
    Vec2D( 8.605929 , 3.538978 ),
    Vec2D( 8.651276 , 3.566756 ),
    Vec2D( 8.855339 , 3.372311 ),
    Vec2D( 8.900686 , 3.316756 ),
    Vec2D( 8.900686 , 3.150089 ),
    Vec2D( 8.787318 , 2.900089 ),
    Vec2D( 8.787318 , 2.844533 ),
    Vec2D( 8.946033 , 2.816756 ),
    Vec2D( 8.991380 , 2.788978 ),
    Vec2D( 9.014054 , 2.705644 ),
    Vec2D( 8.886928 , 2.524989 ),
    Vec2D( 8.832665 , 2.538978 ),
    Vec2D( 8.809991 , 2.455644 ),
    Vec2D( 8.923360 , 2.538978 ),
    Vec2D( 9.014054 , 2.400089 ),
    Vec2D( 9.308811 , 2.288978 ),
    Vec2D( 9.399506 , 2.261200 ),
    Vec2D( 9.512874 , 2.122311 ),
    Vec2D( 9.535548 , 1.983422 ),
    Vec2D( 9.512874 , 1.955644 ),
    Vec2D( 9.467527 , 1.816756 ),
    Vec2D( 9.036728 , 1.816756 ),
    Vec2D( 8.991380 , 1.927867 ),
    Vec2D( 8.946033 , 1.955644 ),
    Vec2D( 8.900686 , 1.983422 ),
    Vec2D( 8.946033 , 2.122311 ),
    Vec2D( 8.968707 , 2.150089 ),
    Vec2D( 9.195443 , 1.927867 ),
    Vec2D( 9.354158 , 1.955644 ),
    Vec2D( 9.376832 , 2.038978 ),
    Vec2D( 9.376832 , 2.094533 ),
    Vec2D( 9.240790 , 2.205644 ),
    Vec2D( 9.195443 , 2.205644 ),
    Vec2D( 9.263464 , 2.150089 ),
    Vec2D( 9.240790 , 2.122311 ),
    Vec2D( 9.195443 , 2.122311 ),
    Vec2D( 9.104749 , 2.122311 ),
    Vec2D( 8.900686 , 2.316756 ),
    Vec2D( 8.787318 , 2.344533 ),
    Vec2D( 8.696623 , 2.372311 ),
    Vec2D( 8.651276 , 2.427867 ),
    Vec2D( 8.719297 , 2.455644 ),
    Vec2D( 8.787318 , 2.650089 ),
    Vec2D( 8.832665 , 2.705644 ),
    Vec2D( 8.605929 , 2.677867 ),
    Vec2D( 8.537908 , 2.788978 ),
    Vec2D( 8.333845 , 2.788978 ),
    Vec2D( 7.925720 , 2.316756 ),
    Vec2D( 7.925720 , 2.261200 ),
    Vec2D( 7.903046 , 2.233422 ),
    Vec2D( 7.857699 , 2.233422 ),
    Vec2D( 7.857699 , 2.177867 ),
    Vec2D( 7.789678 , 1.983422 ),
    Vec2D( 7.812352 , 1.788978 ),
    Vec2D( 7.948394 , 1.538978 ),
    Vec2D( 7.971067 , 1.511200 ),
    Vec2D( 8.129783 , 1.511200 ),
    Vec2D( 8.243151 , 1.594533 ),
    Vec2D( 8.333845 , 1.594533 ),
    Vec2D( 8.424540 , 1.622311 ),
    Vec2D( 8.515234 , 1.566756 ),
    Vec2D( 8.673950 , 1.400089 ),
    Vec2D( 8.771174 , 1.291756 ),
    Vec2D( 8.828938 , 1.119878 ),
    Vec2D( 8.762504 , 0.972544 ),
    Vec2D( 9.238614 , 0.759633 ),
    Vec2D( 9.492323 , 0.627022 ),
    Vec2D( 9.820891 , 0.644711 ),
    Vec2D( 10.376567 , 0.800622 ),
    Vec2D( 10.651961 , 1.085978 ),
    Vec2D( 10.762173 , 1.132022 ),
    Vec2D( 10.943045 , 1.095989 ),
    Vec2D( 11.256739 , 0.999878 ),
    Vec2D( 11.576074 , 0.761611 ),
    Vec2D( 11.768247 , 0.425211 ),
    Vec2D( 11.960165 , 0.074778 ),
    Vec2D( 11.953907 , 0.000000 ),
    Vec2D( 11.629411 , 0.258767 ),
    Vec2D( 11.229920 , 0.582278 ),
    Vec2D( 11.001633 , 0.564300 ),
    Vec2D( 10.868476 , 0.447478 ),
    Vec2D( 10.633849 , 0.541833 ),
    Vec2D( 10.513370 , 0.672133 ),
    Vec2D( 11.188700 , 0.820078 ),
    Vec2D( 11.194014 , 0.859656 ),
    Vec2D( 11.118212 , 0.905822 ),
    Vec2D( 10.874860 , 0.930311 ),
    Vec2D( 10.427319 , 0.716522 ),
    Vec2D( 10.023620 , 0.374211 ),
    Vec2D( 9.434614 , 0.360144 ),
    Vec2D( 8.455131 , 0.859544 ),
    Vec2D( 8.180481 , 0.920500 ),
    Vec2D( 7.902529 , 1.115078 ),
    Vec2D( 7.823108 , 1.269800 ),
    Vec2D( 7.830482 , 1.403778 ),
    Vec2D( 7.791937 , 1.496744 ),
    Vec2D( 7.767005 , 1.538978 ),
    Vec2D( 7.676310 , 1.622311 ),
    Vec2D( 7.653637 , 1.650089 ),
    Vec2D( 7.585616 , 1.955644 ),
    Vec2D( 7.562942 , 1.983422 ),
    Vec2D( 7.562942 , 2.233422 ),
    Vec2D( 7.608289 , 2.400089 ),
    Vec2D( 7.630963 , 2.427867 ),
    Vec2D( 7.608289 , 2.538978 ),
    Vec2D( 7.585616 , 2.566756 ),
    Vec2D( 7.653637 , 2.705644 ),
    Vec2D( 7.630963 , 2.816756 ),
    Vec2D( 7.336206 , 3.011200 ),
    Vec2D( 7.290859 , 3.011200 ),
    Vec2D( 7.245511 , 3.011200 ),
    Vec2D( 7.041449 , 2.955644 ),
    Vec2D( 6.928081 , 2.816756 ),
    Vec2D( 6.928081 , 2.733422 ),
    Vec2D( 6.905407 , 2.622311 ),
    Vec2D( 6.860060 , 2.677867 ),
    Vec2D( 6.814712 , 2.677867 ),
    Vec2D( 6.678671 , 2.677867 ),
    Vec2D( 6.678671 , 2.733422 ),
    Vec2D( 6.769365 , 2.733422 ),
    Vec2D( 6.814712 , 2.733422 ),
    Vec2D( 6.792039 , 2.788978 ),
    Vec2D( 6.293219 , 3.066756 ),
    Vec2D( 6.225198 , 3.122311 ),
    Vec2D( 6.202525 , 3.233422 ),
    Vec2D( 6.134504 , 3.344533 ),
    Vec2D( 5.907767 , 3.261200 ),
    Vec2D( 5.862420 , 3.288978 ),
    Vec2D( 6.043809 , 3.427867 ),
    Vec2D( 6.021136 , 3.483422 ),
    Vec2D( 5.975788 , 3.483422 ),
    Vec2D( 5.930441 , 3.511200 ),
    Vec2D( 5.953115 , 3.566756 ),
    Vec2D( 5.975788 , 3.594533 ),
    Vec2D( 5.749052 , 3.788978 ),
    Vec2D( 5.703705 , 3.788978 ),
    Vec2D( 5.635684 , 3.788978 ),
    Vec2D( 5.703705 , 3.844533 ),
    Vec2D( 5.703705 , 4.011200 ),
    Vec2D( 5.499642 , 4.011200 ),
    Vec2D( 5.862420 , 4.372311 ),
    Vec2D( 5.975788 , 4.427867 ),
    Vec2D( 6.021136 , 4.427867 ),
    Vec2D( 6.089156 , 4.538978 ),
    Vec2D( 6.111830 , 4.566756 ),
    Vec2D( 6.089156 , 4.650089 ),
    Vec2D( 5.998462 , 4.650089 ),
    Vec2D( 5.817073 , 4.788978 ),
    Vec2D( 5.771726 , 4.816756 ),
    Vec2D( 5.681031 , 4.816756 ),
    Vec2D( 5.749052 , 4.927867 ),
    Vec2D( 5.749052 , 5.038978 ),
    Vec2D( 5.839747 , 5.177867 ),
    Vec2D( 5.998462 , 5.233422 ),
    Vec2D( 6.225198 , 5.233422 ),
    Vec2D( 6.270545 , 5.233422 ),
    Vec2D( 6.383914 , 5.288978 ),
    Vec2D( 6.406587 , 5.372311 ),
    Vec2D( 6.429261 , 5.400089 ),
    Vec2D( 6.587976 , 5.483422 ),
    Vec2D( 6.670626 , 5.490000 ),
    Vec2D( 6.700845 , 5.564100 ),
    Vec2D( 6.860060 , 5.927867 ),
    Vec2D( 6.860060 , 6.038978 ),
    Vec2D( 6.950754 , 6.205644 ),
    Vec2D( 6.973428 , 6.316756 ),
    Vec2D( 7.041449 , 6.344533 ),
    Vec2D( 7.064122 , 6.455644 ),
    Vec2D( 7.116072 , 6.541989 ),
    Vec2D( 7.114313 , 6.603667 ),
    Vec2D( 7.025305 , 6.741422 ),
    Vec2D( 6.736924 , 6.701367 ),
    Vec2D( 6.641658 , 6.741467 ),
    Vec2D( 6.500574 , 6.761389 ),
    Vec2D( 6.435410 , 6.733422 ),
    Vec2D( 6.224291 , 6.728556 ),
    Vec2D( 6.191759 , 6.738989 ),
    Vec2D( 6.099124 , 6.755000 ),
    Vec2D( 6.041805 , 6.749733 ),
    Vec2D( 6.001672 , 6.742967 ),
    Vec2D( 5.905382 , 6.718300 ),
    Vec2D( 5.817073 , 6.677867 ),
    Vec2D( 5.611713 , 6.686622 ),
    Vec2D( 5.401366 , 6.864333 ),
    Vec2D( 5.386274 , 6.927867 ),
    Vec2D( 5.356608 , 6.981811 ),
    Vec2D( 5.404095 , 7.111822 ),
    Vec2D( 5.561958 , 7.216133 ),
    Vec2D( 5.660643 , 7.244722 ),
    Vec2D( 5.366149 , 7.489478 ),
    Vec2D( 5.340927 , 7.511200 ),
    Vec2D( 5.114998 , 7.592867 ),
    Vec2D( 4.870667 , 7.692033 ),
    Vec2D( 4.746560 , 7.781856 ),
    Vec2D( 4.708060 , 7.760867 ),
    Vec2D( 4.692225 , 7.802500 ),
    Vec2D( 4.607090 , 7.849044 ),
    Vec2D( 4.481324 , 7.879711 ),
    Vec2D( 4.340031 , 8.093378 ),
    Vec2D( 4.181171 , 8.158044 ),
    Vec2D( 4.116415 , 8.200800 ),
    Vec2D( 4.081135 , 8.195278 ),
    Vec2D( 4.090912 , 8.272500 ),
    Vec2D( 4.032232 , 8.378311 ),
    Vec2D( 3.779566 , 8.791278 ),
    Vec2D( 3.769654 , 8.849022 ),
    Vec2D( 3.598177 , 8.955178 ),
    Vec2D( 3.576828 , 9.059633 ),
    Vec2D( 3.527037 , 9.066756 ),
    Vec2D( 3.498069 , 9.082022 ),
    Vec2D( 3.541865 , 9.174211 ),
    Vec2D( 3.542409 , 9.234411 ),
    Vec2D( 3.576275 , 9.262711 ),
    Vec2D( 3.582279 , 9.287744 ),
    Vec2D( 3.390995 , 9.316756 ),
    Vec2D( 3.209606 , 9.344533 ),
    Vec2D( 3.100836 , 9.367511 ),
    Vec2D( 2.957466 , 9.370756 ),
    Vec2D( 2.870844 , 9.366222 ),
    Vec2D( 2.777211 , 9.285222 ),
    Vec2D( 2.744851 , 9.285900 ),
    Vec2D( 2.775397 , 9.294867 ),
    Vec2D( 2.832661 , 9.341156 ),
    Vec2D( 2.868114 , 9.373300 ),
    Vec2D( 2.869502 , 9.400089 ),
    Vec2D( 2.794434 , 9.420178 ),
    Vec2D( 2.714423 , 9.440078 ),
    Vec2D( 2.641124 , 9.441944 ),
    Vec2D( 2.572096 , 9.428378 ),
    Vec2D( 2.548379 , 9.418600 ),
    Vec2D( 2.573130 , 9.388211 ),
    Vec2D( 2.563126 , 9.333567 ),
    Vec2D( 2.535855 , 9.320067 ),
    Vec2D( 2.517670 , 9.282778 ),
    Vec2D( 2.479488 , 9.260278 ),
    Vec2D( 2.483125 , 9.239067 ),
    Vec2D( 2.464034 , 9.224278 ),
    Vec2D( 2.468586 , 9.180556 ),
    Vec2D( 2.443129 , 9.168989 ),
    Vec2D( 2.439084 , 9.147456 ),
    Vec2D( 2.448389 , 9.129344 ),
    Vec2D( 2.444897 , 9.109600 ),
    Vec2D( 2.450720 , 9.097256 ),
    Vec2D( 2.444897 , 9.080389 ),
    Vec2D( 2.447808 , 9.045822 ),
    Vec2D( 2.424536 , 9.024011 ),
    Vec2D( 2.415811 , 9.000133 ),
    Vec2D( 2.442457 , 8.957422 ),
    Vec2D( 2.429887 , 8.946567 ),
    Vec2D( 2.455028 , 8.894556 ),
    Vec2D( 2.435936 , 8.879078 ),
    Vec2D( 2.413136 , 8.853411 ),
    Vec2D( 2.410805 , 8.836944 ),
    Vec2D( 2.412202 , 8.822133 ),
    Vec2D( 2.387533 , 8.789544 ),
    Vec2D( 2.386608 , 8.776044 ),
    Vec2D( 2.398706 , 8.757278 ),
    Vec2D( 2.373103 , 8.739511 ),
    Vec2D( 2.387070 , 8.769467 ),
    Vec2D( 2.375434 , 8.784611 ),
    Vec2D( 2.358674 , 8.785922 ),
    Vec2D( 2.337270 , 8.793167 ),
    Vec2D( 2.365195 , 8.790533 ),
    Vec2D( 2.399169 , 8.821478 ),
    Vec2D( 2.396376 , 8.837933 ),
    Vec2D( 2.408946 , 8.879078 ),
    Vec2D( 2.432218 , 8.894878 ),
    Vec2D( 2.414995 , 8.963022 ),
    Vec2D( 2.390961 , 8.983722 ),
    Vec2D( 2.340091 , 8.969389 ),
    Vec2D( 2.332091 , 8.946244 ),
    Vec2D( 2.340091 , 8.927722 ),
    Vec2D( 2.332091 , 8.912289 ),
    Vec2D( 2.316093 , 8.904067 ),
    Vec2D( 2.311730 , 8.874744 ),
    Vec2D( 2.288975 , 8.861244 ),
    Vec2D( 2.247727 , 8.856233 ),
    Vec2D( 2.233180 , 8.861889 ),
    Vec2D( 2.209436 , 8.859233 ),
    Vec2D( 2.231003 , 8.871144 ),
    Vec2D( 2.265911 , 8.873200 ),
    Vec2D( 2.277548 , 8.869600 ),
    Vec2D( 2.290635 , 8.873711 ),
    Vec2D( 2.299360 , 8.904578 ),
    Vec2D( 2.268088 , 8.909622 ),
    Vec2D( 2.247727 , 8.925256 ),
    Vec2D( 2.225734 , 8.920756 ),
    Vec2D( 2.208747 , 8.909622 ),
    Vec2D( 2.203768 , 8.921811 ),
    Vec2D( 2.214352 , 8.931822 ),
    Vec2D( 2.197138 , 8.933811 ),
    Vec2D( 2.148725 , 8.907478 ),
    Vec2D( 2.134577 , 8.904844 ),
    Vec2D( 2.113354 , 8.917222 ),
    Vec2D( 2.095107 , 8.918800 ),
    Vec2D( 2.079961 , 8.912944 ),
    Vec2D( 2.060761 , 8.913356 ),
    Vec2D( 2.034577 , 8.902656 ),
    Vec2D( 1.983589 , 8.895400 ),
    Vec2D( 2.033997 , 8.913356 ),
    Vec2D( 2.062502 , 8.918700 ),
    Vec2D( 2.092758 , 8.929811 ),
    Vec2D( 2.148090 , 8.928756 ),
    Vec2D( 2.168397 , 8.937878 ),
    Vec2D( 2.146421 , 8.965533 ),
    Vec2D( 2.182173 , 8.943933 ),
    Vec2D( 2.201537 , 8.951311 ),
    Vec2D( 2.239138 , 8.938400 ),
    Vec2D( 2.267063 , 8.944989 ),
    Vec2D( 2.284939 , 8.925767 ),
    Vec2D( 2.306887 , 8.926022 ),
    Vec2D( 2.311086 , 8.936356 ),
    Vec2D( 2.296312 , 8.952489 ),
    Vec2D( 2.317254 , 8.981122 ),
    Vec2D( 2.334939 , 9.003844 ),
    Vec2D( 2.374500 , 9.014044 ),
    Vec2D( 2.386136 , 9.034778 ),
    Vec2D( 2.401962 , 9.044656 ),
    Vec2D( 2.418723 , 9.044889 ),
    Vec2D( 2.426287 , 9.054878 ),
    Vec2D( 2.411739 , 9.063522 ),
    Vec2D( 2.426867 , 9.099311 ),
    Vec2D( 2.398362 , 9.125233 ),
    Vec2D( 2.373339 , 9.121944 ),
    Vec2D( 2.403595 , 9.134289 ),
    Vec2D( 2.417680 , 9.165778 ),
    Vec2D( 2.425860 , 9.192778 ),
    Vec2D( 2.423783 , 9.231400 ),
    Vec2D( 2.400330 , 9.237022 ),
    Vec2D( 2.419494 , 9.243567 ),
    Vec2D( 2.429815 , 9.246711 ),
    Vec2D( 2.449495 , 9.245489 ),
    Vec2D( 2.457676 , 9.289856 ),
    Vec2D( 2.481311 , 9.298211 ),
    Vec2D( 2.488585 , 9.334211 ),
    Vec2D( 2.520255 , 9.353822 ),
    Vec2D( 2.520400 , 9.369944 ),
    Vec2D( 2.494960 , 9.432511 ),
    Vec2D( 2.463671 , 9.469200 ),
    Vec2D( 2.406950 , 9.500578 ),
    Vec2D( 2.240907 , 9.536433 ),
    Vec2D( 2.129969 , 9.569467 ),
    Vec2D( 2.031530 , 9.607422 ),
    Vec2D( 1.932328 , 9.658044 ),
    Vec2D( 1.835167 , 9.695656 ),
    Vec2D( 1.746196 , 9.760744 ),
    Vec2D( 1.667446 , 9.789667 ),
    Vec2D( 1.575400 , 9.797622 ),
    Vec2D( 1.562104 , 9.828722 ),
    Vec2D( 1.531422 , 9.846800 ),
    Vec2D( 1.415859 , 9.888744 ),
    Vec2D( 1.315206 , 9.942167 ),
    Vec2D( 1.175573 , 10.083667 ),
    Vec2D( 1.147394 , 10.090267 ),
    Vec2D( 1.118064 , 10.086567 ),
    Vec2D( 0.990883 , 9.998400 ),
    Vec2D( 0.778930 , 9.990856 ),
    Vec2D( 0.592924 , 10.033144 ),
    Vec2D( 0.507490 , 10.125422 ),
    Vec2D( 0.419562 , 10.320811 ),
    Vec2D( 0.375403 , 10.344533 ),
    Vec2D( 0.276464 , 10.431189 ),
    Vec2D( 0.220170 , 10.534911 ),
    Vec2D( 0.181271 , 10.571000 ),
    Vec2D( 0.153745 , 10.620156 ),
    Vec2D( 0.114973 , 10.653889 ),
    Vec2D( 0.103274 , 10.707756 ),
    Vec2D( 0.097914 , 10.761511 ),
    Vec2D( 0.076256 , 10.811522 ),
    Vec2D( 0.061935 , 10.867833 ),
    Vec2D( 0.000000 , 10.960167 )
    ])

    distances = (0, .05, .1, .25) # threshold sizes in kilometres
    import csv
    for d in distances:
        simple = coast.simplify(d) if d > 0 else coast
        with open('poly-{0}.csv'.format(d), 'w') as output_doc:
            writer = csv.writer(output_doc, dialect='excel')
            for pt in simple.points:
                writer.writerow(pt.coords)
