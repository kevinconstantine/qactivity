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
from __future__ import print_function
import argparse
from datetime import date, datetime, time, timedelta
import decimal
import json
from pprint import pprint
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from qactivity_tables import Iops, Capacity

from qumulo_client import QumuloClient

#### SQLAlchemy encoding helper function
def alchemyencoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


#### Classes
class QumuloActivityCommand(object):
    ''' class wrapper for cmd so that we can new them up in tests '''
    def __init__(self, argv=None):

        parser = argparse.ArgumentParser()
        parser.add_argument("-s", "--start", dest="start", required=False,  help="Specify start date for activity")
        parser.add_argument("-e", "--end", dest="end", required=False, help="Specify end date for activity")
        parser.add_argument("-i", "--iops", dest="iops", required=False, action="store_true", help="Show IOPs data")
        parser.add_argument("-c","--capacity", dest="capacity", required=False, action="store_true", help="Show Capacity data")
        parser.add_argument("-j","--json", dest="json", action="store_true", required=False, help="Output results as raw JSON")
        parser.add_argument("-l", "--latest", dest="latest", action="store_true", required=False, help="Show only latest data")
        parser.add_argument("-v","--csv", dest="csv", action="store_true", required=False, help="Output results in comma-separated lines")

        self.dt_1970 = datetime(1970,1,1)
        args = parser.parse_args()
        start = args.start
        end = args.end

        self.use_date_range = False

        if args.start:
            self.use_date_range = True
            self.start, self.start_ts = self.coerce_datetime(args.start)

        if args.end:
            self.use_date_range = True
            self.end, self.end_ts = self.coerce_datetime(args.end)

        self.iops= args.iops
        self.capacity = args.capacity

        if (not(self.iops or self.capacity)): # Neither specified; do both
            self.iops = True
            self.capacity = True

        self.json = args.json
        self.csv = args.csv
        self.latest= args.latest

        engine = create_engine('sqlite:///qactivity.sqlite')
        DBSession = sessionmaker(bind=engine)
        self.session = DBSession()


    def dt_seconds(self, dt):
        return int((dt - self.dt_1970).total_seconds())

    def seconds_dt(self, seconds):
        return self.dt_1970 + timedelta(seconds=seconds)

    def coerce_datetime(self, strdatetime):
        num_colons = strdatetime.count(':')
        new_datetime = datetime.now()
        if num_colons == 2:
            new_datetime = datetime.strptime(strdatetime, "%Y.%m.%d %H:%M:%S")
        elif num_colons == 1:
            new_datetime = datetime.strptime(strdatetime, "%Y.%m.%d %H:%M")
        else:
            new_datetime = datetime.strptime(strdatetime, "%Y.%m.%d")

        return new_datetime, self.dt_seconds(new_datetime)

    def print_capacity_summary(self, results):
        maxCapacity = max(results, key=lambda x:x['size'])
        minCapacity = min(results, key=lambda x:x['size'])
        avgSize = sum(d['size'] for d in results)/ len(results)

        print('Capacity summary from {0} to {1}'.format(str(self.start), str(self.end)))
        print('Max Usage: Size:{0} Path:{1}'.format(maxCapacity['size'], maxCapacity['path']))
        print('Min Usage: Size:{0} Path:{1}'.format(minCapacity['size'], minCapacity['path']))
        print('Avg Usage: Size:{0}'.format(avgSize))

    def print_iops_summary(self, results):
        pass

    def print_summary(self, operations, results):


        for idx, operation in enumerate(operations):

            if self.json:
                # dump them out as JSON for now
                print("$s data from %1 to %2:", operation, str(self.start), str(self.end))
                list_json = json.dumps([dict(e) for e in results[idx]], default=alchemyencoder)
                pprint(list_json)
            elif self.csv:
                print("TODO: CSV output")
                pass
            else:
                # Just a summary based on the type of data
                if operation == "Capacity":
                    self.print_capacity_summary(results[idx])
                else:
                    self.print_iops_summary(results[idx])
                pass

    def get_activity(self):
        operations = []
        results = []

        # IOPs and/or Capacity
        if self.iops:
            operations.append("IOPs")
        if self.capacity:
            operations.append("Capacity")

        if "Capacity" in operations:
            cd = self.session.query(Capacity)\
            .filter((Capacity.ts >= self.start_ts) & (Capacity.ts <= self.end_ts))
            cd_list = [ { "id":c.id, "cluster":c.cluster, "dt":self.dt_1970+timedelta(seconds=c.ts), "path":c.path, "size":c.size} for c in iter(cd) ]
            results.append(cd_list)

        if "IOPs" in operations:
            iops = self.session.query(Iops)\
            .filter((Iops.ts >= self.start_ts) & (Iops.ts <= self.end_ts))
            iops_list = [ { "id":i.id, "cluster":i.cluster, "dt":self.dt_1970 + timedelta(seconds=i.ts), "path":i.path, "iops":i.iops} for i in iter(iops) ]
            results.append(iops_list)

        self.print_summary(operations, results)

### Main subroutine
def main():
    ''' Main entry point '''
    command = QumuloActivityCommand(sys.argv)
    command.get_activity()


# Main
if __name__ == '__main__':
    main()
