from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from qactivity_tables import Iops, Capacity

engine = create_engine('sqlite:///qactivity.sqlite')
DBSession = sessionmaker(bind=engine)
session = DBSession()


session.query(Iops).delete()
session.query(Capacity).delete()

session.commit()