#-*- coding: utf-8 -*-
#
# COPYRIGHT FUJITSU SOCIAL SCIENCE LABORATORY LIMITED 2012
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# + Redistributions of source code must retain the above copyright notice, this list of conditions
# and the following disclaimer.
# + Redistributions in binary form must reproduce the above copyright notice, this list of conditions
# and the following disclaimer in the documentation and/or other materials provided with the distribution.
# + Neither the name of the FUJITSU SOCIAL SCIENCE LABORATORY LIMITED nor the names of its contributors
# may be used to endorse or promote products derived from this software without specific prior written
# permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

class Report_Instance_Model(object):

    def __init__(self):
        self.start_time = None
        self.last_seen_time = None
        self.duration = None
        self.duration_hour = None
        self.running_time = None
        self.running_hour = None
        self.instance_id = None
        self.instance_type = None
        self.cores = None
        self.mem_gigabytes = None
        self.disk_io = None
        self.network_io = None

class Report_Volume_Model(object):

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.duration_hour = None
        self.ebs_megabytes = None
        self.snapshot_megabytes = None

class Report_Walrus_Model(object):

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.duration_hour = None
        self.objects_megabytes = None
        self.objects_num = None

class Report_Volume_History_Model(object):

    def __init__(self):
        self.user_id = None
        self.account_name = None
        self.history = None
        self.ebs_gigabytes_by_hours = 0
        self.snapshot_gigabytes_by_hours = 0

class Report_Walrus_History_Model(object):

    def __init__(self):
        self.user_id = None
        self.account_name = None
        self.history = None
        self.walrus_gigabytes_by_hours = 0

class Report_User_Model(object):

    def __init__(self):
        self.user_id = None
        self.user_internal_id = None

class Report_Account_Model(object):

    def __init__(self):
        self.name = None
        self.id_number = None

class Charge_Instance_Model(object):

    def __init__(self):
        self.bootups = 0
        self.cores_by_hours = 0
        self.memgigabytes_by_hours = 0
        self.disk_io_gigabytes = 0
        self.network_io_gigabytes = 0

class Charge_Volume_Model(object):

    def __init__(self):
        self.ebs_gigabytes_by_hours = 0
        self.snapshot_gigabytes_by_hours = 0

class Charge_Walrus_Model(object):

    def __init__(self):
        self.walrus_gigabytes_by_hours = 0

class Charge_Model(object):

    def __init__(self):
        self.bootups = 0
        self.cores = 0
        self.mem = 0
        self.disk_io = 0
        self.network_io = 0
        self.ebs = 0
        self.snapshots = 0
        self.walrus = 0

    def total(self):
        return self.bootups + self.cores + self.disk_io + self.ebs + self.mem + self.network_io + self.snapshots + self.walrus
