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

import logging
#import os
import re
import commands
from koala.settings import SERVER_PRIV_KEY
#from models import Host

class FileData(object):
	filename = None
	size = None
	valid = None

class ServerAccess(object):

	#カスタムログ
	logger = logging.getLogger('koalalog')
	server_address = None
	server_hostname = None
	server_key_path = None
	debug = False

	# コンストラクタ
	def __init__(self,ip,debug=False):
		# only for admin@eucalyptus on frontends:
		#if not user.resource_admin:
		#	return None
		self.server_key_path = SERVER_PRIV_KEY
		if self.server_key_path == '':
			return
		self.debug = debug
		self.server_address = ip
		(ret,result) = self.sshComannd("hostname")
		if ret == 0:
			self.server_hostname = result

	def hostname(self):
		return self.server_hostname

	def getFileList(self,path,prefix=None):
		com = "ls -l " + path
		if prefix:
			com = com + " | grep " + prefix
		file_list = []
		(ret,result) = self.sshComannd(com)
		if ret == 0:
			lines = result.splitlines()
			for line in lines:
				columns = line.strip().split()
				if len(columns) <= 2:
					continue
				f = FileData()
				f.filename = columns[8]
				f.size = columns[4]
				file_list.append(f)
		return file_list

	def getDiskFree(self,path):
		com = "df -P " + path
		total = 0
		free = 0
		mount_path = None
		(ret,result) = self.sshComannd(com)
		if ret == 0:
			lines = result.splitlines()
			for line in lines:
				columns = line.strip().split()
				if columns[0] == "Filesystem":
					continue
				total = int(columns[1])*1024
				free = int(columns[3])*1024
				mount_path = columns[5]
		return (total, free, mount_path)

	def getCpuPercent(self,key=None):
		if not key:
			key = "idle"
		com = "vmstat -s | grep cpu"
		total = 0
		keyValue = 0
		(ret,result) = self.sshComannd(com)
		if ret == 0:
			lines = result.splitlines()
			for line in lines:
				columns = line.strip().split()
				if re.search(key,columns[1]):
					keyValue = int(columns[0])
				total += int(columns[0])
				self.logger.debug("%s:%s" % (columns[0], columns[1]))	
		return float(keyValue*100)/float(total)

	def getMemFree(self):
		com = "free"
		total = 0
		free = 0
		(ret,result) = self.sshComannd(com)
		if ret == 0:
			lines = result.splitlines()
			for line in lines:
				columns = line.strip().split()
				if columns[0] != "Mem:":
					continue
				total = int(columns[1])*1024
				free = (int(columns[3])+int(columns[5])+int(columns[6]))*1024
		return (total, free)

	def deleteFile(self,path):
		com = "rm -f " + path
		(ret,result) = self.sshComannd(com)
		if ret:
			return result
		return None

	def sshComannd(self,com):
		cmd_ch = 'ssh -i ' + self.server_key_path + ' root@' + self.server_address + ' ' + com
		ret_ch = commands.getstatusoutput(cmd_ch)
		if self.debug:
			self.logger.debug("ssh command:%s" % com)
		if ret_ch[0] != 0:
			self.logger.error('sshコマンド:%s 実行エラー. response=%s' % (com, ret_ch[0]))
		if self.debug:
			self.logger.debug("ssh result:%s" % ret_ch[1])
		return ret_ch[0], ret_ch[1]
