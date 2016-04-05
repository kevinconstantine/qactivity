import os
import sys
from sqlalchemy import Column, Integer, BigInteger, String, Interval
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()

class Iops(Base):
    __tablename__ = 'iops'
    id = Column(Integer, primary_key=True)
    # ts represents int # of seconds between op datetime and 1/1/1970
    ts = Column(BigInteger, index=True)
    ip = Column(String, index=True)
    path = Column(String, index=True)
    iops = Column(String)

    def __repr__(self):
        return '<Iops %r>' % str(self.id)

class Capacity(Base):
    __tablename__ = 'capacity'
    id = Column(Integer, primary_key=True)
    # ts represents int # of seconds between op datetime and 1/1/1970
    ts = Column(BigInteger, index=True)
    path = Column(String, index=True)
    size = Column(BigInteger)

    def __repr__(self):
        return '<Capacity %r>' % str(self.id)


# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
engine = create_engine('sqlite:///qactivity.sqlite')

# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)