import re
import os
import time
from collections import OrderedDict
import logging
import sys


import qumulo.lib.auth
import qumulo.lib.request
import qumulo.rest

class QumuloClient(object):
    ''' class wrapper for REST API cmd so that we can new them up in tests '''
    def __init__(self, cfg):

        self.hostname = cfg.cluster.hostname
        self.port = cfg.cluster.port
        self.paths = cfg.paths
        self.user = os.getenv('QACTIVITY_USER', 'admin')
        self.pwd = os.getenv('QACTIVITY_PWD', 'admin')

        self.connection = None
        self.credentials = None
        self.polling_interval = 60

        self.login()

    def login(self):
        try:
            self.connection = qumulo.lib.request.Connection(\
                                self.hostname, self.port)
            login_results, _ = qumulo.rest.auth.login(\
                    self.connection, None, self.user, self.pwd)

            self.credentials = qumulo.lib.auth.Credentials.\
                    from_login_response(login_results)
        except Exception, excpt:
            print "Error connecting to the REST server: %s" % excpt
            sys.exit(1)


    def get_api_response(self, api_call, **kwargs):

        attempt = 0
        response_object = None
        retry = True

        while retry and (attempt <= 10):
            try:
                if len(kwargs) > 0:
                    # TODO: fix.  This call is not really general-purpose yet
                    response_object = api_call(self.connection, self.credentials, kwargs.values()[0])
                else:
                    response_object = api_call(self.connection, self.credentials)

                if len(response_object) == 0:
                    retry = True
                else:
                    retry = False
            except Exception, excpt:
               if excpt.status_code == 401 or excpt.status_code == 307:
                 # is it a 307 or 401?  Try to get a new access token
                # by logging in again
                self.login()
                logging.error("Error communicating with Qumulo REST server: %s" % excpt)
                retry = True

        if retry:
            attempt += 1
            time.sleep(10)

        return response_object.data


    def get_capacity(self, path):
        # return qumulo.rest.fs.read_fs_stats(self.connection, self.credentials).data
        return self.get_api_response(qumulo.rest.fs.read_dir_aggregates, path=path)


    def get_iops(self):

        try:
            iops_data = self.get_api_response(qumulo.rest.analytics.iops_get)

            entries = iops_data['entries']
            ids = [ entry['id'] for entry in entries ]
            id_map = map(str, ids)
            unique_ids = sorted(list(set(ids)))

            id_path_arr = \
                self.get_api_response(qumulo.rest.fs.resolve_paths, \
                                      ids=unique_ids)

            results = []
            for entry in entries:
                g = [ d for d in id_path_arr if d["id"] == entry["id"]]
                entry['path'] = g[0]["path"]
                # if it is one of the paths we're watching,
                # add to results
                for path in self.paths:
                    if entry['path'].startswith(path):
                        results.append(entry)

        except:
            pass

        return results



