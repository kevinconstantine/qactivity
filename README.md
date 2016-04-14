# Qumulo Activity Reporting Tool (qactivity): Show IOPS+Throughput+Capacity Growth for a job

qactivity/ daemon is a command-line tool that does the following:

1. Runs a daemon that pulls IOPs and Capacity data for specified folders from a cluster. 
2. Provides a command like tool to search and filter the retried data, so the values can be 
piped to other tools etc.

The canonical scenario for this sample app is as follows:

A workflow application moves files to/from certain folders while doing work, and possibly spins up
workers on particular machines in order to perform the work involved.

The qactivity daemon (daemon.py) is configured to retrieve capacity and IOPs data for these folders from 
the cluster, and the daemon is started.

As the worfklow application runs, the daemon collects data from the cluster and stores it in a local
sqlite database.

Once the workflow application has completed, the command line qactivity tool can be used to
filter IOPs and workflow by folder, IP address (for IOPs), date/time and more.

## License

Licensed under the Educational Community License, Version 2.0 (ECL-2.0) (the "License"); 
you may not use this file except in compliance with the License.  Please refer to LICENSE
file as part of this project for details.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.

## Requirements

* Qumulo cluster and API credentials for the cluster
* Linux or Mac with continuous access to the Qumulo cluster
* python
* python libraries: argparse, sqlite, others (see requirements.txt file)


## Installation Steps

### 1. Download from GitHub
```shell
git clone git clone https://github.com/Qumulo/qactivity.git
```
Or, download the zip file (https://github.com/Qumulo/qactivity/archive/master.zip) and unzip it to 
your machine where you will be running this tool.

### 2. Install Prerequisites

We currently support Linux or MacOSX for running qactivity (it should also work in Windows environments with 
python 2.7.x and sqlite DB support but has not been tested).

You will need Python 2.7 and pip in order to install dependencies.

NOTE that we strongly recommend using python virtual environments to isolate the libaries used
for this and other python applications from your system versions of python and libraries.  If
you are unfamiliar with the use of virtual environments, please have a look at this Qumulo Community 
article that we created on the subject:

https://community.qumulo.com/qumulo/topics/virtual-environments-when-using-qumulo-rest-api

if you don't have access to the above, please see

http://docs.python-guide.org/en/latest/dev/virtualenvs/


A virtual environment for this app and python is not a requirement but it is a best practice and helps isolate
your system from your application's installed libraries and vice-versa.

### 3. Install the prerequisite python libraries

From a terminal window, `cd` to the folder where you cloned/installed file_transfer_tool and then run
    
```
pip install -r requirements.txt
```

to install the python prerequisites including the SQLite database and the Qumulo REST API
wrapper.  *NOTE* that qactivity requires Qumulo REST API version 2.0.0 or later.  You can 
potentially use qactivity with Qumulo Core versions earlier than 2.0.0 but we have not tested earlier versions.  

As always, you'll want to be sure that the version of Qumulo REST API specified in `requirements.txt' matches
your Qumulo Cluster version.

### 4. Set up the configuration file
There are a few settings you'll need to set up in `qactivity.cfg` before you can run  
qactivity. Specifically you'll need to set up cluster info and paths to monitor, like this example 
(please customize to match your environment):

    # paths to monitor
    paths:
    [
      "/users_foo/",
      "/rendering/bar/"
    ]

    cluster: {
        hostname: "cluster"
        port: 8000
    }
    
    

You could of course add "/" to monitored paths, but then you'd be seeing the same information as the 'Analytics'
tab in the Qumulo cluster UI.


In addition, qactivity daemon and qactivity shell apps are looking for two environment variables that specify the 
username and password used to access the cluster via the REST API: QACTIVITY_USER and QACTIVITY_PWD.  So for example 
if your cluster uses 'api_user' as the username and 'special1!' as the account and password used to access
the API, your shell environment for the user account running qactivity should define these vars like this:

export QACTIVITY_USER=api_user
export QACTIVITY_PWD=special1!

*NOTE* Don't forget to `source` your shell script, restart a new session or otherwise pick up settings 
such as `QACTIVITY_USER` after you change them; Typically you'll need to restart the application
after making any config changes.


### 5. Create local Sql database for qactivity
Qactivity uses SqLite to store data.  To initialize the sqlite DB for qactivity, run

    python qactivity_tables.py
    
to set up the DB.  

If you want to place some test data in the DB  (./qactivity.sqlite) to peruse/browse, you can run

    python add_test_data.py
    
to install some sample data.

To clear out the contents of the sqlite DB, run

    python clear_tables.py
    
To peruse data in the sqlite db directly, I'd recommend using DB Browser for Sqlite, which you can find here:

http://sqlitebrowser.org/
 

