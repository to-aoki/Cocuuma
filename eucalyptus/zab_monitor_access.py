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

import json
import logging
import os
import commands
from koala.settings import ZABBIX_HOST

class Zabbix_Json_Model(object):
	auth = None
	method = None
	id = None
	params = {}

class ZabbixAccess(object):

	#カスタムログ
	logger = logging.getLogger('koalalog')
	session_id = None
	zabbix_address = ''
	id = 0
	hostids = []
	debug = False

	# コンストラクタ
	def __init__(self,debug=False):
		self.zabbix_address = ZABBIX_HOST
		if self.zabbix_address == '':
			return
		self.debug = debug
		self.login()
		self.hostids = self.getHostids()

	def login(self):
		jsonData = {}
		jsonData['params'] = {}
		# TODO: settings.py 項目必要
		jsonData['params']['user'] = 'Admin'
		jsonData['params']['password'] = 'zabbix'
		jsonData['method'] = 'user.authenticate'
		jsonData['auth'] = None
		ret = self.execute(jsonData)
		self.session_id = ret['result']
		self.logger.debug("zabbix session id : %s" % (self.session_id))

	def isValid(self):
		if self.session_id:
			return True
		else:
			return False

	def getHostids(self):
		params = {}
		params['output'] = ['name']
		jsonData = {}
		jsonData['params'] = params
		jsonData['method'] = 'host.get'
		jsonData['auth'] = self.session_id
		ret = self.execute(jsonData)
		hosts = ret['result']
		return hosts

	def hostname2id(self,hostname):
		for host in self.hostids:
			if host['name'] == hostname:
				return host['hostid']
		return None

	def id2hostname(self,hostid):
		for host in self.hostids:
			if host['hostid'] == hostid:
				return host['name']
		return None

	def itemByHostname(self,item,hostname):
		for i in item:
			if i['hostid'] == self.hostname2id(hostname):
				return i['lastvalue']
		return None

	def getItem(self, itemkey, hostname=None, discovery=None):
		params = {}
		if hostname:
			params['hostids'] = self.hostname2id(hostname)
		params['filter'] = {}
		params['filter']['key_'] = itemkey
		params['output'] = ['lastvalue','hostid']
		jsonData = {}
		jsonData['params'] = params
		jsonData['method'] = 'item.get'
		if discovery == "discovery":
			jsonData['method'] = 'discoveryrule.get'
		jsonData['auth'] = self.session_id
		ret = self.execute(jsonData)
		item = None
		if ret.has_key('result'):
			item = ret['result']
		return item

	def hasItem(self, itemkey, hostname):
		params = {}
		params['hostids'] = self.hostname2id(hostname)
		params['filter'] = {}
		params['filter']['key_'] = itemkey
		jsonData = {}
		jsonData['params'] = params
		jsonData['method'] = 'item.exists'
		jsonData['auth'] = self.session_id
		ret = self.execute(jsonData)
		has_item = False
		if ret.has_key('result'):
			has_item = ret['result']
		return has_item

	def updateItemDelay(self, itemkey, hostname, delay, discovery=None):
		item = self.getItem(itemkey, hostname, discovery)
		if item:
			params = {}
			params['itemid'] = item[0]['itemid']
			params['delay'] = delay
			jsonData = {}
			jsonData['params'] = params
			jsonData['method'] = 'item.update'
			if discovery == "discovery":
				jsonData['method'] = 'discoveryrule.update'
			jsonData['auth'] = self.session_id
			ret = self.execute(jsonData)
			if ret.has_key('result'):
				return ret['result']['itemids'][0]
		return None

	def getGroupId(self, group):
		params = {}
		params['output'] = ['groupid']
		params['filter'] = {}
		params['filter']['name'] = group
		jsonData = {}
		jsonData['params'] = params
		jsonData['method'] = 'hostgroup.get'
		jsonData['auth'] = self.session_id
		ret = self.execute(jsonData)
		if ret['result']:
			return ret['result'][0]['groupid']
		else:
			return None

	def getTemplateId(self, template):
		params = {}
		params['output'] = ['templateid']
		params['filter'] = {}
		params['filter']['host'] = template
		jsonData = {}
		jsonData['params'] = params
		jsonData['method'] = 'template.get'
		jsonData['auth'] = self.session_id
		ret = self.execute(jsonData)
		if ret['result']:
			return ret['result'][0]['templateid']
		else:
			return None

	def addHost(self, hostname, template, ip, group):
		groupid = self.getGroupId(group)
		templateid = self.getTemplateId(template)
		if groupid and templateid:
			params = {}
			params['host'] = hostname
			interface = {}
			interface['type'] = 1
			interface['main'] = 1
			interface['useip'] = 1
			interface['ip'] = ip
			interface['port'] = 10050
			interface['dns'] = ""
			params['interfaces'] = [interface]
			params['groups'] = [{ 'groupid':groupid }]
			params['templates'] = [{ 'templateid':templateid }]
			jsonData = {}
			jsonData['params'] = params
			jsonData['method'] = 'host.create'
			jsonData['auth'] = self.session_id
			ret = self.execute(jsonData)
			if ret.has_key('result'):
				hostid = ret['result']['hostids'][0]
				newhost = { 'name':hostname, 'hostid':hostid }
				self.hostids.append(newhost)
				return hostid
			else:
				return None
		else:
			return None

	def deleteHost(self, hostname):
		hostid = self.hostname2id(hostname)
		if hostid:
			params = [ {"hostid":hostid} ]
			jsonData = {}
			jsonData['params'] = params
			jsonData['method'] = 'host.delete'
			jsonData['auth'] = self.session_id
			ret = self.execute(jsonData)
			if ret.has_key('result'):
				hostid = ret['result']['hostids'][0]
				deletedhost = { 'name':hostname, 'hostid':hostid }
				if deletedhost in self.hostids:
					self.hostids.remove(deletedhost)
				return hostid
			else:
				return None
		else:
			return None

	# execute query to zabbix server:
	def execute(self,jsonData):

		jsonDataReturn = None
		jsonData['id'] = self.id
		jsonData['jsonrpc'] = "2.0"
		#try:
		cmd_ch = "curl -s -d '" + json.dumps(jsonData)
		cmd_ch += "' -H 'Content-Type:application/json-rpc'"
		cmd_ch += " http://" + self.zabbix_address + "/zabbix/api_jsonrpc.php"
		if self.debug:
			self.logger.debug('zabbix api request : %s' % (cmd_ch))
		ret_ch = commands.getstatusoutput(cmd_ch)
		if ret_ch[0] != 0:
			self.logger.error('zabbix API 実行エラー. response=%s' % ret_ch[0])
			#raise Exception('zabbix API 実行エラー')
			ret = {}
			ret['result'] = None
			return ret
		if self.debug:
			self.logger.debug('zabbix api response : %s' % (ret_ch[1]))
		jsonDataReturn = json.loads(ret_ch[1])

		#except Exception, ex:
		#	raise ex

		self.id = jsonDataReturn['id'] + 1
		return jsonDataReturn

