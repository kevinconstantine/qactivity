from config import Config
import os
import re
import smtplib
import threading
import time

from qumulo_client import QumuloClient
from qactivity_tables import Iops, Capacity

class Worker(threading.Thread):

    def __init__(self, cfg):
        threading.Thread.__init__(self)
        self._cfg = cfg
        self.setDaemon(True)
        self.client = QumuloClient(cfg) # only one cluster for now

    def get_iops(self):
        # iops = client.get_iops()
        pass

    def get_capacity(self):
        # capacity = client.get_capacity()
        pass

    def get_cluster_metrics(self):
        self.get_iops()
        self.get_capacity()

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
