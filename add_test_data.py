from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from qactivity_tables import Iops, Capacity

engine = create_engine('sqlite:///qactivity.sqlite')
DBSession = sessionmaker(bind=engine)
session = DBSession()


ts = int((datetime.now() - datetime(1970,1,1)).total_seconds())
ip = "192.168.0.7"
path = "/users/mmurray/music"
iops = "{ 'a': 1, 'b': 2 }"

# Insert an Iops Record
new_iops = Iops(ts=ts, ip=ip, path=path, iops=iops)
session.add(new_iops)
session.commit()

# Insert a capacity record
new_capacity =  Capacity(ts=ts, path=path, size=12345678901112)
session.add(new_capacity)
session.commit()
