import re
import os
import time
from collections import OrderedDict
import logging


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
        self.pwd = os.getenv('QACTIVITY_REST_PWD', 'admin')

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
            # print "Error connecting to the REST server: %s" % excpt
            # sys.exit(1)
            pass


    def path_to_paths(self, local_path):
        if local_path == "/" or local_path == "//" or local_path == "":
            return ['/']
        else:
            local_path = re.sub("//", "/", local_path)
            local_path = re.sub("/$", "", local_path)
        local_paths = []
        cur_path = ""
        for i_level, path_part in enumerate(local_path.split("/")):
            if i_level > 0:
                cur_path = cur_path + "/" + path_part
            if cur_path == "":
                cur_path = "/"
            local_paths.append(cur_path)
            if i_level == 0:
                cur_path = ""
        return local_paths


    def build_tree(self, iops_data, id_to_path, iops_dict, stop_level):
        new_big_tree = {}
        for d in iops_data['entries']:
            inode_id = int(d['id'])
            path = "/"
            try:
                for i, path in enumerate(self.path_to_paths(id_to_path[inode_id])):
                    if i not in new_big_tree:
                        new_big_tree[i] = {}
                    if path == "":
                        path = "/"
                    if path not in new_big_tree[i]:
                        new_big_tree[i][path] = iops_dict.copy()
                    new_big_tree[i][path]["path"] = path
                    new_big_tree[i][path]["counter"] += 1
                    new_big_tree[i][path][d["type"]] += d["rate"]
                    new_big_tree[i][path]["total"] += d["rate"]
                    new_big_tree[i][path][d["type"] + "-agg"] += d["rate"]
                    new_big_tree[i][path]["total-agg"] += d["rate"]
                    if i >= stop_level:
                        break
            except:
                pass
        return new_big_tree



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
                # login again
                logging.error("Error communicating with Qumulo REST server: %s" % excpt)
                retry = True

        if retry:
            attempt += 1
            time.sleep(10)

        return response_object.data


    def get_capacity(self, path):
        # return qumulo.rest.fs.read_fs_stats(self.connection, self.credentials).data
        return self.get_api_response(qumulo.rest.fs.read_dir_aggregates, path=path)


    def get_throughput(self, path):
        api_begin_time = int(time.time() - self.polling_interval)
        throughput = qumulo.rest.analytics.time_series_get(self.connection, self.credentials, api_begin_time).data
        throughput = self.get_api_response(qumulo.rest.analytics.time_series_get, api_begin_time=api_begin_time)
        # return only the last/latest reading for each indicator... not all of them.
        results = []
        for result in throughput:
            last_value = len(result["values"]) - 1

            result["times"] = [result["times"][last_value]]
            result["values"] = [result["values"][last_value]]
            results.append(result)

        return results


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



