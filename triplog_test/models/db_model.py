from sqlalchemy import (
    Table,
    ForeignKey,
    Column,
    Integer,
    Text,
    types,
    UniqueConstraint,
    Unicode,
    and_,
    func
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.dialects import postgresql
from sqlalchemy.types import UserDefinedType

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref,
    exc
    )


from zope.sqlalchemy import ZopeTransactionExtension

from triplog_test.helpers.ramerdouglaspeucker import reduce_trackpoints

import hashlib
from os import urandom
from base64 import b64encode, b64decode
from itertools import izip
import uuid as uuidlib
import datetime
from decimal import Decimal


from triplog_test.helpers import timetools

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


SALT_LENGTH = 12
KEY_LENGTH = 24
HASH_FUNCTION = 'sha256'  # Must be in hashlib.
# Linear to the hashing time. Adjust to be high but take a reasonable
# amount of time on your server. Measure with:
# python -m timeit -s 'import passwords as p' 'p.make_hash("something")'
COST_FACTOR = 10000

def now():
    return datetime.datetime.now()


class Geometry(UserDefinedType):
    def get_col_spec(self):
        return "GEOMETRY"

    def bind_expression(self, bindvalue):
        return func.ST_GeomFromText(bindvalue, 4326, type_=self)

    def column_expression(self, col):
        return func.ST_AsText(col, type_=self)


class Mode(Base):
    __tablename__ = 'mode'
    id = Column(Integer, primary_key=True)
    type = Column("type", Text, unique=True)
    track = relationship("Track", backref="mode_ref", order_by="desc(Track.start_timestamp)")

    def __init__(self, type):
        self.type = type


class Tour(Base):
    __tablename__ = 'tour'
    id = Column(Integer, primary_key=True)
    name = Column("name", Text)
    description = Column("description", Text)
    start_timestamp = Column("start_timestamp", types.TIMESTAMP(timezone=False))
    end_timestamp = Column("end_timestamp", types.TIMESTAMP(timezone=False))
    reduced_trackpoints = Column("reduced_trackpoints", Text)
    extent = Column("extent", Geometry)
    center = Column("center", postgresql.ARRAY(types.Float(), dimensions=1))
    uuid = Column("uuid", postgresql.UUID, unique=True)
    etappes = relationship("Etappe", backref="tour_ref", order_by="desc(Etappe.start_timestamp)")

    def __init__(self, name, description, start_timestamp=timetools.now(), end_timestamp=timetools.now(), 
                center=None, uuid=str(uuidlib.uuid4())):
        self.name = name
        self.description = description
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.reduced_trackpoints = reduce_trackpoints(trackpoints, epsilon)
        self.extent = extent
        self.center = center
        self.uuid = uuid

    def reprGeoJSON(self): #returns own columns only
        start_timestamp = self.start_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        end_timestamp = self.end_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        children = [etappe.id for etappe in self.etappes]
        return dict(id=self.id, name=self.name, description=self.description,
                    start_timestamp=start_timestamp, end_timestamp=end_timestamp, 
                    extent=self.extent, center=self.center, uuid=self.uuid,
                    parent = None, children = children)



class Etappe(Base):
    __tablename__ = 'etappe'
    id = Column(Integer, primary_key=True)
    tour = Column(Integer, ForeignKey('tour.id', onupdate="CASCADE", ondelete="CASCADE"))
    name = Column(Text)
    description = Column(Text)
    start_timestamp = Column(types.TIMESTAMP(timezone=False),default=timetools.now())
    end_timestamp = Column(types.TIMESTAMP(timezone=False),default=timetools.now())
    reduced_trackpoints = Column("reduced_trackpoints", Text)
    extent = Column("extent", Geometry)
    center = Column("center", postgresql.ARRAY(types.Float(), dimensions=1))
    uuid = Column(Text, unique=True)
    tracks = relationship('Track', backref='etappe_ref', order_by="desc(Track.start_timestamp)")
    __table_args__ = (
        UniqueConstraint('start_timestamp', 'end_timestamp', name='etappe_start_end'),
        {}
        )

    def __init__(self, tour, name, description, start_timestamp=timetools.now(), 
                end_timestamp=timetools.now(), trackpoints=None, epsilon=Decimal(0.0005), 
                extent=None, center=None, uuid=str(uuidlib.uuid4())):
        self.tour = tour.id
        self.description = description
        self.name = name
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.reduced_trackpoints = reduce_trackpoints(trackpoints, epsilon)
        self.extent = extent
        self.center = center
        self.uuid = uuid

    def reprGeoJSON(self): #returns own columns only
        start_timestamp = self.start_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        end_timestamp = self.end_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        children = [track.id for track in self.tracks]
        return dict(id=self.id, name=self.name, description=self.description,
                    start_timestamp=start_timestamp, end_timestamp=end_timestamp, 
                    extent=self.extent, center=self.center, uuid=self.uuid,
                    parent = self.tour, children = children)





class Track(Base):
    __tablename__ = 'track'
    id = Column(Integer, primary_key=True)
    etappe = Column(Integer, ForeignKey('etappe.id', onupdate="CASCADE", ondelete="CASCADE"))
    mode = Column("mode", types.Integer, ForeignKey('mode.id'))
    distance = Column("distance", Text)
    timespan = Column("timespan", types.Interval)
    trackpoint_count = Column(Integer)
    start_timestamp = Column("start_timestamp", types.TIMESTAMP(timezone=False))
    end_timestamp = Column("end_timestamp", types.TIMESTAMP(timezone=False))
    reduced_trackpoints = Column("reduced_trackpoints", Text)
    extent = Column("extent", Geometry)
    center = Column("center", postgresql.ARRAY(types.Float(), dimensions=1))
    uuid = Column("uuid", postgresql.UUID, unique=True)
    trackpoints = relationship("Trackpoint", backref="tracks", order_by="desc(Trackpoint.timestamp)")
    #reduced_trackpoints = relationship("ReducedTrackpoints", backref="tracks")
    __table_args__ = (
        UniqueConstraint("start_timestamp", "end_timestamp", name="track_start_end_timestamp"),
        {}
        )


    def __init__(self, etappe, mode, distance, timespan, trackpoint_count,
                start_timestamp, end_timestamp, trackpoints, epsilon, 
                extent=None, center=None, uuid=str(uuidlib.uuid4())):
        self.etappe = etappe.id
        self.distance = distance
        self.mode = mode
        self.timespan = timespan
        self.trackpoint_count = trackpoint_count
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.reduced_trackpoints = reduce_trackpoints(trackpoints, epsilon)
        self.extent = extent
        self.center = center
        self.uuid = uuid

    def reprJSON(self): #returns own columns only
        start_timestamp = self.start_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        end_timestamp = self.end_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return dict(id=self.id, distance=str(self.distance),
                    timespan=str(self.timespan), trackpoint_count=self.trackpoint_count, 
                    start_timestamp=start_timestamp, end_timestamp=end_timestamp, uuid=self.uuid)
                    #TODO:distance is a decimal, string is not a proper conversion


    def reprGeoJSON(self): #returns own columns only
        start_timestamp = self.start_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        end_timestamp = self.end_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return dict(id=self.id, start_timestamp=start_timestamp, end_timestamp=end_timestamp, 
                    extent=self.extent, center=self.center, uuid=self.uuid,
                    parent = self.etappe, children = None)




    
    @classmethod
    def get_tracks(self):
        tracks = DBSession.query(Track).all()
        return tracks

    @classmethod
    def get_track_by_id(self, id):
        track = DBSession.query(Track).filter(Track.id == id).one()
        return track

    @classmethod
    def get_track_by_uuid(self, uuid):
        try:
            track = DBSession.query(Track).filter(Track.uuid == uuid).one()
            return track
        except Exception, e:
            print "Error retrieving track %s: ",e
            return None


    @classmethod
    def get_track_by_time(self, start_timestamp, end_timestamp):
        try:
            track = DBSession.query(Track).filter(and_(Track.start_timestamp == start_timestamp, Track.end_timestamp == end_timestamp)).one()
            return track
        except Exception, e:
            print "Error retrieving track %s: ",e
            return None


class ReducedTrackpoints(Base):
    __tablename__ = 'reduced_trackpoints'
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    track = Column("track", types.Integer, ForeignKey('track.id'))
    reduced_trackpoints = Column("reduced_trackpoints", postgresql.ARRAY(types.Float(), dimensions=2))
    epsilon = Column("epsilon", types.Numeric(11,4))
    zoomlevel = Column("zoomlevel", Text)
    __table_args__ = (
        UniqueConstraint("track", "epsilon", name="reduced_trackpoints_track_epsilon"),
        {}
        )


    def __init__(self, track, trackpoints, epsilon, zoomlevel):
        self.track = track.id
        self.reduced_trackpoints = reduce_trackpoints(trackpoints, epsilon)
        self.epsilon = epsilon
        self.zoomlevel = zoomlevel


class Trackpoint(Base):
    __tablename__ = 'trackpoint'
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    track = Column("track", types.Integer, ForeignKey('track.id'))
    latitude = Column("latitude", types.Numeric(9,7))
    longitude = Column("longitude", types.Numeric(10,7))
    altitude = Column("altitude", types.Integer)
    velocity = Column("velocity", types.Integer)
    temperature = Column("temperature", types.Integer)
    direction = Column("direction", types.Integer)
    pressure = Column("pressure", types.Integer)
    timestamp = Column("timestamp", types.TIMESTAMP(timezone=False))
    uuid = Column("uuid", postgresql.UUID, unique=True)
    __table_args__ = (
        UniqueConstraint('latitude', 'longitude','timestamp', name='trackpoint_lat_lon_timestamp'),
        {}
        )


    def __init__(self, track, latitude, longitude, altitude, velocity, temperature, direction, pressure, \
                timestamp, uuid):
        self.track = track.id
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.velocity = velocity
        self.temperature = temperature
        self.direction = direction
        self.pressure = pressure
        self.timestamp = timestamp
        self.uuid = uuid

    @classmethod
    def get_trackpoint_by_lat_lon_timestamp(self, latitude, longitude, timestamp):
        try:
            trackpoint = DBSession.query(Trackpoint).filter(and_(Trackpoint.latitude == latitude, Trackpoint.longitude == longitude, Trackpoint.timestamp == timestamp)).one()
            return trackpoint
        except Exception, e:
            print ("Error retrieving trackpoint by lat(%s), lon(%s), time(%s) :\n %s ") % (latitude, longitude, timestamp, e)
            return None

    @classmethod
    def get_trackpoint_by_uuid(self, uuid):
        try:
            trackpoint = DBSession.query(Trackpoint).filter(Trackpoint.uuid == uuid).one()
            return trackpoint
        except Exception, e:
            print "Error retrieving trackpoint %s: ",e
            return None

