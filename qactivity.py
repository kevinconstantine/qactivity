#!/usr/bin/env python
# Copyright (c) 2016 Qumulo, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

'''
== Description:

Qactivity (pronounced "quack-tivity") is the command line interface for interacting
with and filtering the results of data stored by qactivity/daemon.py

Credentials for accessing the cluster come from environment variables QACTIVITY_USER and QACTIVITY_PWD.
If these variables are not defined, we default to 'admin' / 'admin' for cluster credentials.

Usage:

qactivity

- divide a qumulo cluster into N equal partitions based on . A partition is a list of paths.
The partitioning is based on the block count, which is obtained from
fs_read_dir_aggregates

- feed each partition to an rsync client

== Typical Script Usage:

qfiles.py --host ip_address|hostname [options] SRC DEST

=== Required:

One or more paths and/or IP addresses must be specified to filter the data in the database.

[ -i | -ips]  One or more IP addresses, comma-separated. Only makes sense for fetching

and/or

[ -p | -paths] One or more paths, comma-separated

=== Options:

[-s | --start] starting date-time to filter events from DB
[-e | --end] ending date-time to filter events from DB; If start is specified but not end,
             we get all events since start
[-i | --iops]  get only iops data
[-c | --capacity] get only capacity data
[-l | --latest] return only the latest entry for specified type
[-v ] return the results in CSV format

(If neither iops nor capacity are specified, both are return for specified IPs or paths)

-h | --help                         Print out the script usage/help

=== Examples:

# Get latest capacity reading for path
qactivity.py -c -p /users/test/foo

# Get latest IOPs reading for path
qactivity.py -l -i -p /users

# Get latest capacity entry for any path (don't specify a path)
qactivity.py -l -c

# Get latest IOPs entry in CSV format
qactivity.py -l -i -v

# Get capacity entries for path between start and end datetime
qactivity.py -c -p /users/test/foo -s 2016/04/13 13:30 -e 2016/04/13 17:30

# Get iops for ipbetween specified datetimes in CSV format
qactivity.py




'''

# Import python libraries
import argparse
import datetime
import sys

# Import Qumulo REST libraries
# Leaving in the 'magic file path' for customers who want to run these scripts
# from cust_demo as before
import qumulo.lib.auth
import qumulo.lib.request
import qumulo.rest.fs as fs

#### Classes
class QumuloActivityCommand(object):
    ''' class wrapper for REST API cmd so that we can new them up in tests '''
    def __init__(self, argv=None):

        parser = argparse.ArgumentParser()
        parser.add_argument("-H", "--host", default="dev", dest="host", required=False,  help="specify host for sync source")
        parser.add_argument("-P", "--port", type=int, dest="port", default=30157, required=False, help="specify port on sync source to use for sync")
        parser.add_argument("-u", "--user", default="admin", dest="user", required=False, help="specify user credentials for login")
        parser.add_argument("-mp","--mountpoint", dest="mountpoint", required=True, help="This is where Rsync starts the sync.  You MUST mount your share at this path before running this tool!")
        parser.add_argument("--pass", default="admin", dest="passwd", required=False, help="specify user pwd for login")
        parser.add_argument("-n", "--notreally", required=False, dest="notreally", help="don't actually sync but generate files", action="store_true")
        parser.add_argument("-v", "--verbose", required=False, dest="verbose", help="Echo stuff to ", action="store_true")
        parser.add_argument("-t", "--threads", type=int, default=1, dest="threads", required=False, help="specify number of threads/workers for sync")
        parser.add_argument("start_path", action="store", help="This is the root path on the cluster for syn")
        parser.add_argument("target_path", action="store")


        args = parser.parse_args()
        self.notreally_mode = args.notreally
        self.port = args.port
        self.user = args.user
        self.passwd = args.passwd
        self.host = args.host
        self.num_buckets = args.threads
        self.start_path = args.start_path
        self.target_path = args.target_path
        self.mountpoint = args.mountpoint
        self.verbose_mode = args.verbose

        self.connection = None
        self.credentials = None
        self.current_bucket_number = 0
        self.current_bucket_size = 0
        self.total_buckets_size = 0
        self.buckets = []
        self.buckets.append([])

        self.login()
        self.total_size = self.get_size(self.start_path)
        self.max_bucket_size = self.total_size / self.num_buckets

        if (self.total_size % self.num_buckets) > 0:
            # add a bucket for the remainder
            self.num_buckets += 1

        self.remaining_data = self.total_size
        self.start_time = datetime.datetime.now()

    def login(self):
        try:
            self.connection = qumulo.lib.request.Connection(\
                                self.host, int(self.port))
            login_results, _ = qumulo.rest.auth.login(\
                    self.connection, None, self.user, self.passwd)

            self.credentials = qumulo.lib.auth.Credentials.\
                    from_login_response(login_results)
        except Exception, excpt:
            print "Error connecting to the REST server: %s" % excpt
            print __doc__
            sys.exit(1)


    def get_size(self, path):
        ''' return n lists of files for path, where n is the # of threads specified '''
        try:
            result = fs.read_dir_aggregates(self.connection, self.credentials, path=path)
        except qumulo.lib.request.RequestError, excpt:
            print "Error: %s" % excpt
            sys.exit(1)

        return int(result.data['files'][0]['data_usage'])

    def get_folder_contents(self, path):

        # todo: handle paging in folder contents
        response = fs.read_dir_aggregates(self.connection, self.credentials, path=path)
        return response.data['files']

    def launch_rsync(self, bucket_filename):
        ''' start rsync with the specified list of paths '''
        # rsync -av --files-from=DirectoriesToCopy.txt ./nfstest /tmp/junk/

        # use ‘-n’ or ‘-dry-run’ to simulate the run before copying

        pass


    def process_bucket(self, bucket):
        ''' depending upon start params, spit bucket contents to console or
            fire off rsync with the list of paths in the bucket '''

        if self.verbose_mode:
            print("\nCurrent Bucket is: " + str(self.current_bucket_number) + " with size " + str(self.current_bucket_size) + "\n")


        # create a file for bucket path entries
        filename = "qsync_" + self.start_time.strftime("%Y%m%d%H%M_bucket") + str(self.current_bucket_number) + ".txt"
        bucket_file = open(filename, 'w+')

        for entry in bucket:
            if self.verbose_mode:
                print(entry['path'].encode('utf-8') + '\t' + str(entry['size']))
            bucket_file.write(entry['path'].encode('utf-8') + '\n')

        bucket_file.close()

        if not self.notreally_mode:
            self.launch_rsync(filename)


    def kick_the_bucket(self):
        ''' process current bucket, create a new one '''
        self.total_buckets_size += self.current_bucket_size
        self.process_bucket(self.buckets[self.current_bucket_number])
        self.current_bucket_number += 1
        self.current_bucket_size = 0
        self.buckets.append([])

    def add_to_bucket(self, path, entry):
        ''' add an entry to the current bucket.  If there isn't space for the entry
            in the bucket such that we'll exceed max_bucket_size, create a new bucket
            and make it the current one. '''

        #if path != self.start_path:
        #    relative_filename = path + entry['name']
        #else:
        relative_filename = path + '/' + entry['name']

        relative_filename = relative_filename.lstrip(self.start_path)


        size = int(entry['data_usage'])
        bucket_entry = { "path" : relative_filename, "size" : size }

        if (size + self.current_bucket_size) >= self.max_bucket_size:
            self.kick_the_bucket()

        self.buckets[self.current_bucket_number].append(bucket_entry)
        self.current_bucket_size += size

        # if we're done, handle the bucket
        # if self.current_bucket_size == self.total_size:
        #     self.process_bucket(self.buckets[self.current_bucket_number])



    def process_files(self, path):
        ''' return n lists of files for path, where n is the # of threads specified '''

        print("path is " + path)
        contents = self.get_folder_contents(path)
        paths_to_process = []


        # BUGBUG this never seems to come back to top-level entries after the first one, not sure why...
        for filesystem_entry in contents:
            # add to bucket if <= max_bucket_size and there's room.
            # if its a folder and <= max_bucket_size, add it, no need to crawl contents.
            # if it's a file and > bucket_size, it gets its own bucket
            size = int(filesystem_entry['data_usage'])


            if (size <= self.max_bucket_size or filesystem_entry['type'] == "FS_FILE_TYPE_FILE"):
                self.add_to_bucket(path, filesystem_entry)
            else:
                if path == '/':
                    new_path = path + filesystem_entry['name']
                else:
                    new_path = path + '/' + filesystem_entry['name']

                self.process_files(new_path)

### Main subroutine
def main():
    ''' Main entry point '''
    command = QumuloFilesCommand(sys.argv)
    command.process_files(command.start_path)

    if command.verbose_mode:
        print("\nTotal size is: " + str(command.total_size))
        print("Total size of buckets is: " + str(command.total_buckets_size) + "\n")



# Main
if __name__ == '__main__':
    main()
gg