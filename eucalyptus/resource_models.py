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

# Instance_informationモデルを定義
class Instance_information(object):
	instanceid = None
	accountid = None
	imageid = None
	privateipaddress = None
	ipaddress = None
	keyname = None
	vmtype = None
	status = None
	launchtime = None
	rootdevicetype = None
	# related data
	attachedvolumes = []
	account = None
	node = None
	cpu = None
	mem = None
	disk = None
	@property
	def num_volumes(self):
		return len(self.attachedvolumes)
	def using_resources(self):
		if self.status == "stopped" or self.status == "terminated":
			return False
		else:
			return True

	def __getitem__(self, key):
		return self.__dict__[key]
	def __setitem__(self, key, value):
		self.__dict__[key] = value

# Account_informationモデルを定義
class Account_information(object):
	accountname = None
	accountid = None
	# related data
	num_instances = None
	num_all_instances = None
	cpu = None
	mem = None
	total_volume_size = None

	def __getitem__(self, key):
		return self.__dict__[key]
	def __setitem__(self, key, value):
		self.__dict__[key] = value

# Node_informationモデルを定義
class Node_information(object):
	node_ip = None
	instanceids = []
	cpu = None
	mem = None
	max_cpu = None
	max_mem = None
	monitored_ip = None
	hostname = None
	monitored_hostname = None
	monitoring = None
	num_ins = None

	def num_instances(self):
		return len(self.instanceids)

	def __getitem__(self, key):
		return self.__dict__[key]
	def __setitem__(self, key, value):
		self.__dict__[key] = value

class Service_information(object):
	service = None
	partition = None
	server_ip = None
	state = None

	def __getitem__(self, key):
		return self.__dict__[key]
	def __setitem__(self, key, value):
		self.__dict__[key] = value

class Frontend_information(object):
	server_ip = None
	monitored_ip = None
	hostname = None
	monitored_hostname = None
	services = []
	monitoring = None
	volume_path = None
	walrus_path = None
	volume_mount_path = None
	walrus_mount_path = None

	def num_services(self):
		return len(self.services)

	def has_sc(self):
		for s in self.services:
			if s.service == "Storage Controller" and s.state == "ENABLED":
				return True
		return False

	def getScPartition(self):
		for s in self.services:
			if s.service == "Storage Controller":
				return s.partition
		return None

	def has_walrus(self):
		for s in self.services:
			if s.service == "Walrus" and s.state == "ENABLED":
				return True
		return False

	def has_storage(self):
		if self.has_sc() or self.has_walrus():
			return True
		else:
			return False

	def __getitem__(self, key):
		return self.__dict__[key]
	def __setitem__(self, key, value):
		self.__dict__[key] = value

# Volumes_informationモデルを定義
class Volume_information(object):
	volumeid = None
	status = None
	instanceid = None
	snapshotid = None
	accountid = None
	accountnumber = None
	partition = None
	size = None
	rootdevice = None
	filefound = True

	def __getitem__(self, key):
		return self.__dict__[key]
	def __setitem__(self, key, value):
		self.__dict__[key] = value
	def deletingOrDeleted(self):
		if self.status == "deleting" or self.status == "deleted":
			return True
		else:
			return False

class Volume_owner(object):
	volumeid = None
	account_number = None
	user_name = None

# Properties_informationモデルを定義
class Properties_information(object):
	name = None
	value = None

	def __getitem__(self, key):
		return self.__dict__[key]
	def __setitem__(self, key, value):
		self.__dict__[key] = value

# Snapshots_informationモデルを定義
class Snapshots_information(object):
	snapshotid = None
	volumeid = None
	status = None
	starttime= None
	progress= None
	accountid = None
	size = None
	#related data
	accountname = None

	def __getitem__(self, key):
		return self.__dict__[key]
	def __setitem__(self, key, value):
		self.__dict__[key] = value

