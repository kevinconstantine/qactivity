from config import Config
import json
import threading
import time

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from qumulo_client import QumuloClient
from qactivity_tables import Iops, Capacity

class Worker(threading.Thread):

    def __init__(self, cfg):
        threading.Thread.__init__(self)
        self.cfg = cfg
        self.setDaemon(True)
        self.client = QumuloClient(cfg) # only one cluster for now

        engine = create_engine('sqlite:///qactivity.sqlite')
        DBSession = sessionmaker(bind=engine)
        self.session = DBSession()

    def get_iops(self, ts):
        iops = self.client.get_iops()
        for entry in iops:
            self.session.add(\
                Iops(ts=ts,\
                     cluster=self.cfg.cluster.hostname,\
                     path=entry['path'],\
                     ip=entry['ip'],\
                     iops = json.dumps(entry)))
            self.session.commit()

    def get_capacity(self, ts):

        for path in self.cfg.paths:
            capacity = self.client.get_capacity(path)
            # add a Capacity record
            self.session.add(Capacity(ts=ts, cluster=self.cfg.cluster.hostname, \
                path=path, size=  long(capacity['total_capacity'])))
            self.session.commit()


    def get_cluster_metrics(self):
        for path in self.cfg.paths:
            ts = int((datetime.now() - datetime(1970, 1, 1)).total_seconds())
            self.get_iops(ts)
            self.get_capacity(ts)

    def run(self):
        try:
            while True:
                print("Getting data....")
                time.sleep(10)
                self.get_cluster_metrics()
        except KeyboardInterrupt:
            print "Shutting down"

if __name__ == '__main__':

    # see if we can read config
    f = file('qactivity.cfg')
    cfg = Config(f)

    Worker(cfg).run()
