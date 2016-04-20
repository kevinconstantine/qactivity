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


== Typical Script Usage:

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
qactivity.py -c -p /users/test/foo -s 2016.04.13 13:30 -e 2016.04.13 17:30

# Get iops for ipbetween specified datetimes in CSV format
qactivity.py -i 10.8.12.34 -s 2016.04.20 09:00 -e 2016.04.20 12:30 -v




'''

# Import python libraries
import argparse
from datetime import datetime
import sys

from qumulo_client import QumuloClient

#### Classes
class QumuloActivityCommand(object):
    ''' class wrapper for cmd so that we can new them up in tests '''
    def __init__(self, argv=None):

        parser = argparse.ArgumentParser()
        parser.add_argument("-s", "--start", dest="start", required=False,  help="Specify start date for activity")
        parser.add_argument("-e", "--end", dest="end", required=False, help="Specify end date for activity")
        parser.add_argument("-i", "--iops", dest="iops", required=False, help="Show IOPs data")
        parser.add_argument("-c","--capacity", dest="capacity", required=False, help="Show Capacity data")
        parser.add_argument("-l", "--latest", dest="latest", type=bool, default=False, required=False, help="Show only latest data")


        args = parser.parse_args()

        self.use_date_range = False

        if args.start:
            self.start = datetime.strptime(args.start, "%Y.%m.%d %H:%M:%S")
            self.start_ts = int((self.start - datetime(1970, 1, 1)).total_seconds())
            self.use_date_range = True

        if args.end:
            self.end= datetime.strptime(args.end, "%Y.%m.%d %H:%M:%S")
            self.use_date_range = True
            self.end_ts = int((self.end - datetime(1970, 1, 1)).total_seconds())
        elif self.use_date_range is True:
            self.end = datetime.now()
            self.end_ts = int((self.end - datetime(1970, 1, 1)).total_seconds())


        self.end = args.end
        self.iops= args.iops
        self.capacity = args.capacity
        self.latest= args.latest


    def get_activity(self):
        print "get activity"
        import ipdb; ipdb.set_trace()
        pass

### Main subroutine
def main():
    ''' Main entry point '''
    command = QumuloActivityCommand(sys.argv)
    command.get_activity()


# Main
if __name__ == '__main__':
    main()
