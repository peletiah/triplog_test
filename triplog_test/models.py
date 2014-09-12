from sqlalchemy import (
    Table,
    ForeignKey,
    Column,
    Integer,
    Text,
    types,
    UniqueConstraint,
    Unicode,
    and_
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.dialects import postgresql

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref,
    exc
    )

from zope.sqlalchemy import ZopeTransactionExtension

from poab.helpers import timetools

import hashlib
from poab.helpers.pbkdf2.pbkdf2 import pbkdf2_bin
from os import urandom
from base64 import b64encode, b64decode
from itertools import izip
import uuid as uuidlib
import datetime


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


class Mode(Base):
    __tablename__ = 'mode'
    id = Column(Integer, primary_key=True)
    type = Column("type", Text, unique=True)
    track = relationship("Track", backref="tracks", order_by="desc(Track.start_time)")

    def __init__(self, type):
        self.type = type


class Track(Base):
    __tablename__ = 'track'
    id = Column(Integer, primary_key=True)
    reduced_trackpoints = Column("reduced_trackpoints", postgresql.ARRAY(types.Float(), dimensions=2))
    distance = Column("distance", Text)
    timespan = Column("timespan", types.Interval)
    trackpoint_count = Column(Integer)
    start_time = Column("start_time", types.TIMESTAMP(timezone=False))
    end_time = Column("end_time", types.TIMESTAMP(timezone=False))
    uuid = Column("uuid", postgresql.UUID, unique=True)
    mode_id = Column("mode_id", types.Integer, ForeignKey('mode.id'))
    trackpoints = relationship("Trackpoint", backref="tracks", order_by="desc(Trackpoint.timestamp)")

    def __init__(self, reduced_trackpoints, distance, timespan, trackpoint_count,
                start_time, end_time, etappe, uuid):
        self.reduced_trackpoints = reduced_trackpoints
        self.distance = distance
        self.timespan = timespan
        self.trackpoint_count = trackpoint_count
        self.start_time = start_time
        self.end_time = end_time
        self.uuid = uuid

    def reprJSON(self): #returns own columns only
        start_time = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time = self.end_time.strftime("%Y-%m-%d %H:%M:%S")
        return dict(id=self.id, reduced_trackpoints=self.reduced_trackpoints, distance=str(self.distance),
                    timespan=str(self.timespan), trackpoint_count=self.trackpoint_count, start_time=start_time,
                    end_time=end_time, uuid=self.uuid)
                    #TODO:distance is a decimal, string is not a proper conversion

    
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
    def get_track_by_reduced_trackpoints(self, reduced_trackpoints):
        try:
            track = DBSession.query(Track).filter(Track.reduced_trackpoints == reduced_trackpoints).one()
            return track
        except Exception, e:
            print "Error retrieving track %s: ",e
            return None

class Trackpoint(Base):
    __tablename__ = 'trackpoint'
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    track_id = Column("track_id", types.Integer, ForeignKey('track.id'))
    latitude = Column("latitude", types.Numeric(9,7))
    longitude = Column("longitude", types.Numeric(10,7))
    altitude = Column("altitude", types.Integer)
    velocity = Column("velocity", types.Integer)
    temperature = Column("temperature", types.Integer)
    direction = Column("direction", types.Integer)
    pressure = Column("pressure", types.Integer)
    timestamp = Column("timestamp", types.TIMESTAMP(timezone=False))
    uuid = Column("uuid", postgresql.UUID, unique=True)

    def __init__(self, track_id, latitude, longitude, altitude, velocity, temperature, direction, pressure, \
                timestamp, uuid):
        self.track_id = track_id
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
    def get_trackpoint_by_lat_lon_time(self, latitude, longitude, timestamp):
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

