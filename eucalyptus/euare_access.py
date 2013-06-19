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


from vmtype_model import *

from boto.ec2.regioninfo import RegionInfo
import boto.s3
import urlparse
import time
import os
import commands
import re
from koala.settings import PROJECT_PATH
from resource_models import *
from models import Host

import logging


def retry(func):
	"""Eucalyptusリクエストリトライ用デコレータ"""

	LIMIT = 5	#リトライ上限
	SIGNATURE = re.compile(r"Same signature was used")	#連続リクエストエラー時のメッセージパターン
	def _retry(*args, **keywords):
		count = 0
		while True:
			try:
				return func(*args, **keywords)
			except Exception, ex:
				count += 1
				if count >= LIMIT:
					raise		# リトライ上限に到達したらエラー終了

				msg = "%s" % ex
				if SIGNATURE.match(msg) >= 0:
					continue		#連続リクエストエラー時
				else:
					raise

	return _retry


# ユーザキーやユーザコネクションなど
# ユーザ情報を取得するクラス
#--------------------------------------------------------
class EucaEnv(object):

	#カスタムログ
	logger = logging.getLogger('koalalog')

	# ユーザーキーの取得
	def getAccessKeys(self,user_id):

		cmd_ch = 'euca-describe-users'
		ret_ch = commands.getstatusoutput(cmd_ch)

		if ret_ch[0] != 0:
			self.logger.error('euca command error. response=%s' % ret_ch[0])
			raise Exception('euca command error.')
		user_lines = ret_ch[1].splitlines()
		for i in range(0, len(user_lines)):
			columns = user_lines[i].strip().split()
			if columns[0] == 'USER-KEYS' and columns[1] == user_id:
				ret = {}
				ret['access'] = columns[2]
				ret['secret'] = columns[3]
				return ret



	# 指定されたユーザのアクセスキーとシークレットキーを取得
	# ユーザの指定がなければ、コマンドライン又は環境変数から取得
	def __init__(self,user_id=None,EC2_URL=None,S3_URL=None,EC2_ACCESS_KEY=None,EC2_SECRET_KEY=None):
		self.ec2_url = EC2_URL
		self.s3_url = S3_URL
		if user_id == None:
			# ユーザ未指定なので実行者のキーを取得する
			if EC2_ACCESS_KEY == None:
				# 指定されていない
				self.access_key = os.environ.get("EC2_ACCESS_KEY")
				if self.access_key == None:
					# 環境変数にも設定されていない
					self.logger.error('"EC2_ACCESS_KEY" is not set.')
					raise Exception('"EC2_ACCESS_KEY" is not set.')
			else:
				# 指定されていた
				self.access_key = EC2_ACCESS_KEY

			if EC2_SECRET_KEY == None:
				# 指定されていない
				self.secret_key = os.environ.get("EC2_SECRET_KEY")
				if self.secret_key == None:
					# 環境変数にも設定されていない
					self.logger.error('"EC2_SECRET_KEY" is not set.')
					raise Exception('"EC2_SECRET_KEY" is not set.')
			else:
				# 指定されていた
				self.secret_key = EC2_SECRET_KEY

		elif EC2_ACCESS_KEY and EC2_SECRET_KEY:
			#ユーザのアクセスキーとシークレットキーが指定されている
			self.access_key = EC2_ACCESS_KEY.encode('utf-8')
			self.secret_key = EC2_SECRET_KEY.encode('utf-8')
			#print type(self.access_key), self.access_key
		else:
			if EC2_ACCESS_KEY == None:
				keys = self.getAccessKeys(user_id)
				self.access_key = keys['access']
			else:
				self.access_key = EC2_ACCESS_KEY

			if EC2_SECRET_KEY == None:
				keys = self.getAccessKeys(user_id)
				self.secret_key = keys['secret']
			else:
				self.secret_key = EC2_SECRET_KEY

	# EC2connection の生成
	def getConnection(self):

		url = urlparse.urlparse(self.ec2_url)

		region = RegionInfo(name="eucalyptus", endpoint=url.hostname)
		connection = boto.connect_ec2(
			aws_access_key_id = self.access_key,
			aws_secret_access_key = self.secret_key,
			is_secure = url.scheme == "https",
			region = region,
			port = url.port,
			path = url.path
			)

		return connection

	# S3connection の生成
	def getConnection_s3(self):
		url = urlparse.urlparse(self.s3_url)
		calling_format=boto.s3.connection.OrdinaryCallingFormat()
		connection = boto.s3.Connection(
			aws_access_key_id = self.access_key,
			aws_secret_access_key = self.secret_key,
			is_secure = url.scheme == "https",
			host=url.hostname,
			port = url.port,
			calling_format=calling_format,
			path = url.path
			)
		return connection

	def getBotoVersion(self):
		return boto.__version__

# ユーザIDを指定して、Eucalyptus基盤から各種情報を取得する
# クラス
#
#--------------------------------------------------------
class Euarecmd(object):

	#カスタムログ
	logger = logging.getLogger('koalalog')
	logger.info('Euarecmd 処理１')
	#コンストラクタ
	def __init__(self,user=None):

		# URL の取得
		EC2_URL = os.environ.get('EC2_URL')

		if EC2_URL == None:
			self.logger.warning('"EC2_URL" is not set.')

		S3_URL = os.environ.get("S3_URL")

		if S3_URL == None:
			self.logger.warning('"S3_URL" is not set.')

		if user != None and user.id != ""  and user.accesskey != ""  and user.secretkey != ""  :
			# ユーザ権限でコネクションを初期化
			EC2_ACCESS_KEY = user.accesskey.encode('utf-8')
			EC2_SECRET_KEY = user.secretkey.encode('utf-8')
			user_env = EucaEnv(user.id,EC2_URL,S3_URL,EC2_ACCESS_KEY,EC2_SECRET_KEY)
			self.boto_ver = user_env.getBotoVersion()
			self.connection = user_env.getConnection()
			self.user = user
		else:
			# 管理者権限でコネクション初期化
			admin_env = EucaEnv(None,EC2_URL,S3_URL)
			self.boto_ver = admin_env.getBotoVersion()
			self.connection = admin_env.getConnection()
			self.user = user



	# 現在のコネクションのユーザがもつイメージの一覧を取得する
	# usr_conn:コネクション
	#
	# return:eucalyptus imageオブジェクトのリスト
	#--------------------------------------------------------------

	def create_group(self, user=None, group_name=None, group_path=None, account=None):

		logger = logging.getLogger('koalalog')
		"""
		TODO self.connection.get_all_zones('verbose') に置き換える
		TODO ユーザが管理者属性のときだけ実行できるようにする
		"""
		logger.info('グループ作成処理 euare-groupcreateコマンドの実行')

		cmd_ch = 'euare-groupcreate -I ' + user.accesskey + ' -S ' + user.secretkey + ' -g "' + \
 group_name + '" -p "' + group_path + '" -v '# + ' --delegate ' + account

		logger.info('euare-groupcreateコマンドの実行戻り値')
		logger.info('cmd %s' % str(cmd_ch))


		ret_ch = commands.getstatusoutput(cmd_ch)
		if ret_ch[0] != 0:
			self.logger.error('eucaツール実行エラー. response=%s' % ret_ch[0])
			raise Exception('eucaツール実行エラー')

		new_group = ret_ch[1].splitlines()

		for i in range(0, len(new_group)):
			if re.search('(W|w)arning', new_group[i]) == None:
				if re.search ('arn:ars', new_group[i]) == None:
					group_id = new_group[i]

		return group_id;



	def create_group_policy(self, user=None, group_name=None, pol_name=None, pol_cont=None, account=None):

		logger = logging.getLogger('koalalog')
		logger.info('グループポリシー作成 euare-groupuploadpolicyコマンドの実行')

		cmd_ch = "euare-groupuploadpolicy -I " + user.accesskey + " -S " + user.secretkey + " -g '" + \
 group_name + "' -p '" + pol_name + "' -o '" +  pol_cont + "'"      # + ' --delegate ' + account

		logger.info('euare-groupuploadpolicyコマンドの実行内容')
		logger.info('cmd %s' % str(cmd_ch))


		ret_ch = commands.getstatusoutput(cmd_ch)
		if ret_ch[0] != 0:
			self.logger.error('eucaツール実行エラー. response=%s' % ret_ch[0])
			raise Exception('eucaツール実行エラー')


		logger.info('グループポリシー作成チェック euare-grouplistpoliciesコマンドの実行')

		cmd_ch2 = "euare-grouplistpolicies -I " + user.accesskey + " -S " + user.secretkey + " -g '" + \
 group_name + "' -p '" + pol_name + "'"  # + ' --delegate ' + account


		ret_ch2 = commands.getstatusoutput(cmd_ch2)
		if ret_ch2[0] != 0:
			self.logger.error('eucaツール実行エラー. response=%s' % ret_ch2[0])
			raise Exception('eucaツール実行エラー')

		new_pol = ret_ch2[1].splitlines()

		for i in range(0, len(new_pol)):
			if re.search('(W|w)arning', new_pol[i]) == None:
				new_pol_name = new_pol[i]

		return new_pol_name;



class GetEucalyptusInfoBy2ool(object):

	#カスタムログ
	logger = logging.getLogger('koalalog')

	def getInstanceListVerbose(self, user=None):
		# only for admin@eucalyptus:
		if not user.resource_admin:
			return None

		cmd_ch = 'euca-describe-instances verbose -a ' + user.accesskey + ' -s ' + user.secretkey
		ret_ch = commands.getstatusoutput(cmd_ch)
		if ret_ch[0] != 0:
			self.logger.error('eucaツール実行エラー. response=%s' % ret_ch[0])
			raise Exception('eucaツール実行エラー')

		instance_list = ret_ch[1].splitlines()
		result_list = []
		account_number = '000000000000'
		for ins in instance_list:
			if re.search('(W|w)arning', ins) == None:
				columns = ins.strip().split()
				if columns[0] == "INSTANCE":
					#for item in columns:
					#	logger.debug("item:%s" % item)
					instance = Instance_information()
					instance.instanceid = columns[1]
					instance.accountid = account_number
					instance.imageid = columns[2]
					instance.ipaddress = columns[3]
					instance.privateipaddress = columns[4]
					instance.status = columns[5]
					instance.keyname = columns[6]
					offset = 0
					if instance.keyname.isdigit() and len(instance.keyname) <= 2:
						instance.keyname = ""
						offset -= 1
					#7:index
					instance.vmtype = columns[8 + offset]
					instance.launchtime = columns[9 + offset]
					#10:cluster
					#11:eki
					if columns[11 + offset][0:3] != "eki":
						offset -= 1
					#12:eri
					if columns[12 + offset][0:3] != "eri":
						offset -= 1
					#13:monitor
					#14/15:dns
					instance.rootdevicetype = columns[16 + offset]
					result_list.append(instance)
				if columns[0] == "RESERVATION":
					account_number = columns[2]

		return result_list;

	def getVolumeListVerbose(self, user=None):
		# only for admin@eucalyptus:
		if not user.resource_admin:
			return None

		cmd_ch = 'euca-describe-volumes verbose -a ' + user.accesskey + ' -s ' + user.secretkey
		ret_ch = commands.getstatusoutput(cmd_ch)
		if ret_ch[0] != 0:
			self.logger.error('eucaツール実行エラー. response=%s' % ret_ch[0])
			raise Exception('eucaツール実行エラー')

		volume_list = ret_ch[1].splitlines()
		result_list = []
		for line in volume_list:
			if re.search('(W|w)arning', line) == None:
				columns = line.strip().split()
				if columns[0] == "VOLUME":
					#for item in columns:
					#	logger.debug("item:%s" % item)
					vol = Volume_information()
					vol.volumeid = columns[1]
					vol.size = columns[2]
					if columns[3][0:4] == "snap":
						vol.snapshotid = columns[3]
						vol.partition = columns[4]
						vol.status = columns[5]
					else:
						vol.partition = columns[3]
						vol.status = columns[4]
					vol.rootdevice = False
					result_list.append(vol)

		for line in volume_list:
			if re.search('(W|w)arning', line) == None:
				columns = line.strip().split()
				if columns[0] == "ATTACHMENT":
					volumeid = columns[1]
					for vol in result_list:
						if vol.volumeid == volumeid:
							vol.instanceid = columns[2]
							if columns[3] == "/dev/sda1":
								vol.rootdevice = True
							#self.logger.debug("attached volume %s to %s" % (vol.volumeid, vol.instanceid))
							break

		return result_list;

	def getNodeList(self, user=None):
		# only for admin@eucalyptus on frontend:
		if not user.resource_admin:
			return None
		cmd_ch = 'euca-describe-nodes -I ' + user.accesskey + ' -S ' + user.secretkey
		ret_ch = commands.getstatusoutput(cmd_ch)
		if ret_ch[0] != 0:
			self.logger.error('eucaツール実行エラー. response=%s' % ret_ch[0])
			raise Exception('eucaツール実行エラー')

		node_list = ret_ch[1].splitlines()
		result_list = []
		for line in node_list:
			if re.search('(W|w)arning', line) == None:
				columns = line.strip().split()
				if columns[0] == "NODE":
					#for item in columns:
					#	logger.debug("item:%s" % item)
					node = Node_information()
					node.instanceids = []
					node.node_ip = columns[1]
					for i in range(3, len(columns)):
						node.instanceids.append(columns[i])
					if Host.objects.filter(registered_ip=node.node_ip):
						host = Host.objects.get(registered_ip=node.node_ip)
						node.hostname = host.hostname
						node.monitored_hostname = host.monitored_hostname
						node.monitored_ip = host.monitored_ip
					result_list.append(node)

		return result_list;

	def getSnapshotListVerbose(self, user=None):
		# only for admin@eucalyptus:
		if not user.resource_admin:
			return None

		cmd_ch = 'euca-describe-snapshots verbose -A ' + user.accesskey + ' -S ' + user.secretkey
		ret_ch = commands.getstatusoutput(cmd_ch)
		if ret_ch[0] != 0:
			self.logger.error('eucaツール実行エラー. response=%s' % ret_ch[0])
			raise Exception('eucaツール実行エラー')

		snap_list = ret_ch[1].splitlines()
		result_list = []
		for line in snap_list:
			if re.search('(W|w)arning', line) == None:
				columns = line.strip().split()
				if columns[0] == "SNAPSHOT":
					#for item in columns:
					#	logger.debug("item:%s" % item)
					snap = Snapshots_information()
					snap.snapshotid = columns[1]
					snap.volumeid = columns[2]
					snap.status = columns[3]
					snap.starttime = columns[4]
					snap.progress = columns[5]
					snap.accountid = columns[6]
					snap.size = columns[7]
					result_list.append(snap)

		return result_list;

	def getCloudProperties(self, user=None):
		# only for admin@eucalyptus:
		if not user.resource_admin:
			return None

		cmd_ch = 'euca-describe-properties -I ' + user.accesskey + ' -S ' + user.secretkey
		ret_ch = commands.getstatusoutput(cmd_ch)
		if ret_ch[0] != 0:
			self.logger.error('eucaツール実行エラー. response=%s' % ret_ch[0])
			raise Exception('eucaツール実行エラー')

		prop_list = ret_ch[1].splitlines()
		result_list = []
		for line in prop_list:
			if re.search('(W|w)arning', line) == None:
				columns = line.strip().split()
				if columns[0] == "PROPERTY":
					#for item in columns:
					#	logger.debug("item:%s" % item)
					prop = Properties_information()
					prop.name = columns[1]
					prop.value = columns[2]
					for i in range(3, len(columns)):
						prop.value = prop.value + " " + columns[i]
					result_list.append(prop)

		return result_list;

	def getServices(self, user=None):
		# only for admin@eucalyptus on frontend:
		if not user.resource_admin:
			return None

		result_list = []

		cmd_ch = 'euca-describe-services -I ' + user.accesskey + ' -S ' + user.secretkey
		ret_ch = commands.getstatusoutput(cmd_ch)
		if ret_ch[0] != 0:
			self.logger.error('eucaツール実行エラー. response=%s' % ret_ch[0])
			raise Exception('eucaツール実行エラー')

		service_list = ret_ch[1].splitlines()
		for line in service_list:
			if re.search('(W|w)arning', line) == None:
				columns = line.strip().split()
				if columns[0] == "SERVICE":
					#for item in columns:
					#	logger.debug("item:%s" % item)
					if columns[1] == "eucalyptus":
						service = Service_information()
						service.service = "CLC"
						service.partition = columns[2]
						service.server_ip = columns[3]
						service.state = columns[4]
						result_list.append(service)

		cmd_ch = 'euca-describe-clusters -I ' + user.accesskey + ' -S ' + user.secretkey
		ret_ch = commands.getstatusoutput(cmd_ch)
		if ret_ch[0] != 0:
			self.logger.error('eucaツール実行エラー. response=%s' % ret_ch[0])
			raise Exception('eucaツール実行エラー')

		service_list = ret_ch[1].splitlines()
		for line in service_list:
			if re.search('(W|w)arning', line) == None:
				columns = line.strip().split()
				if columns[0] == "CLUSTER":
					#for item in columns:
					#	logger.debug("item:%s" % item)
					service = Service_information()
					service.service = "CC"
					service.partition = columns[1]
					service.server_ip = columns[3]
					service.state = columns[4]
					result_list.append(service)

		cmd_ch = 'euca-describe-storage-controllers -I ' + user.accesskey + ' -S ' + user.secretkey
		ret_ch = commands.getstatusoutput(cmd_ch)
		if ret_ch[0] != 0:
			self.logger.error('eucaツール実行エラー. response=%s' % ret_ch[0])
			raise Exception('eucaツール実行エラー')

		service_list = ret_ch[1].splitlines()
		for line in service_list:
			if re.search('(W|w)arning', line) == None:
				columns = line.strip().split()
				if columns[0] == "STORAGECONTROLLER":
					#for item in columns:
					#	logger.debug("item:%s" % item)
					service = Service_information()
					service.service = "Storage Controller"
					service.partition = columns[1]
					service.server_ip = columns[3]
					service.state = columns[4]
					result_list.append(service)

		cmd_ch = 'euca-describe-walruses -I ' + user.accesskey + ' -S ' + user.secretkey
		ret_ch = commands.getstatusoutput(cmd_ch)
		if ret_ch[0] != 0:
			self.logger.error('eucaツール実行エラー. response=%s' % ret_ch[0])
			raise Exception('eucaツール実行エラー')

		service_list = ret_ch[1].splitlines()
		for line in service_list:
			if re.search('(W|w)arning', line) == None:
				columns = line.strip().split()
				if columns[0] == "WALRUS":
					#for item in columns:
					#	logger.debug("item:%s" % item)
					service = Service_information()
					service.service = "Walrus"
					service.partition = columns[1]
					service.server_ip = columns[3]
					service.state = columns[4]
					result_list.append(service)

		server_list = []
		for service in result_list:
			notfound = True
			for server in server_list:
				if server.server_ip == service.server_ip:
					notfound = False
					break
			if notfound:
				server_item = Frontend_information()
				server_item.server_ip = service.server_ip
				server_list.append(server_item)

		for server in server_list:
			server.services = []
			for service in result_list:
				if server.server_ip == service.server_ip:
					server.services.append(service)
			if Host.objects.filter(registered_ip=server.server_ip):
				host = Host.objects.get(registered_ip=server.server_ip)
				server.hostname = host.hostname
				server.monitored_hostname = host.monitored_hostname
				server.monitored_ip = host.monitored_ip

		return server_list;

#クレデンシャルファイルを取得するクラス
class GetCredential(object):

	#カスタムログ
	logger = logging.getLogger('koalalog')
	credentials_dir = 'credentials'

	#コンストラクタ
	def __init__(self,userObject=None):
		self.user = userObject

	#クレデンシャルファイルのパスを取得する
	def getCredential(self):
		"""Todo:設定ファイルからパスを取得"""
		cred_path = PROJECT_PATH + '/credentials/'
		cmd_ch = 'pwd'
		ret = commands.getstatusoutput(cmd_ch)

		if ret[0] != 0:
			self.logger.error('os command error.response=%s' % ret[0])
			raise Exception('os command error.')

		#return ret[1]+'/'+self.credentials_dir+'/'+'euca2-'+self.user.id+'@'+self.user.account_id+'-x509.zip'
		return cred_path + 'euca2-'+self.user.id+'@'+self.user.account_id+'-x509.zip'

	#クレデンシャルファイルのファイル名を取得する
	def getCredentialName(self):
		filename = 'euca2-'+self.user.id+'@'+self.user.account_id+'-x509.zip'
		return filename

#OSイメージを登録するクラス
class RegisterOSImage(object):
	"""Todo:設定ファイルからパスを取得"""
	tmp_file = PROJECT_PATH + '/tmp/command.result'
	manifest_dir = 'manifest'
	#カスタムログ
	logger = logging.getLogger('koalalog')

	#コンストラクタ
	def __init__(self,request):
		self.request = request

	#カーネルイメージの登録
	def registerKernel(self):
		self.logger.info('カーネルイメージの登録')
		cmd_ch = 'euca-bundle-image --image '+self.request.session['ss_img_imagepath']+' --kernel true > '+self.tmp_file
		self.logger.debug('bundle-image kernel: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)

		if ret[0] != 0:
			self.logger.error('bundle-image kernel command error.response=%s' % ret[0])
			raise Exception('bundle-image kernel command error.')

		cmd_ch = "grep 'Generating manifest' "+self.tmp_file+'| cut -d " " -f 3'

		self.logger.debug('grep manifest: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('grep manifest command error.response=%s' % ret[0])
			raise Exception('grep manifest command error.')

		manifest_path = ret[1]
		cmd_ch = 'euca-upload-bundle --bucket '+self.request.session['ss_img_bucketname']+' -m '+ manifest_path + ' > ' +self.tmp_file
		self.logger.debug('upload-bundle kernel: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('upload-bundle kernel command error.response=%s' % ret[0])
			raise Exception('upload-bundle kernel command error.')

		cmd_ch = "grep 'Uploaded image as' "+self.tmp_file+'| cut -d " " -f 4'
		self.logger.debug('grep Uploaded image: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('grep Uploaded image command error.response=%s' % ret[0])
			raise Exception('grep Uploaded image command error.')
		bucket_name = ret[1]

		cmd_ch = 'euca-register '+bucket_name + ' > ' +self.tmp_file
		self.logger.debug('euca-register kernel: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('euca-register kernel command error.response=%s' % ret[0])
			raise Exception('euca-register kernel command error.')

		cmd_ch = "grep 'IMAGE' " + self.tmp_file +" | sed 's/^IMAGE *//'"

		self.logger.debug('grep image kernel: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('grep Image command error.response=%s' % ret[0])
			raise Exception('grep Image command error.')

		return ret[1].strip()

	#ラムディスクイメージの登録
	def registerRamdisk(self):
		self.logger.info('ラムディスクイメージの登録')
		cmd_ch = 'euca-bundle-image --image '+self.request.session['ss_img_imagepath']+' --ramdisk true > '+self.tmp_file
		self.logger.debug('bundle-image ramdisk: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)

		if ret[0] != 0:
			self.logger.error('bundle-image ramdisk command error.response=%s' % ret[0])
			raise Exception('bundle-image ramdisk command error.')

		cmd_ch = "grep 'Generating manifest' "+self.tmp_file+'| cut -d " " -f 3'

		self.logger.debug('grep manifest: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('grep manifest command error.response=%s' % ret[0])
			raise Exception('grep manifest command error.')

		manifest_path = ret[1]
		cmd_ch = 'euca-upload-bundle --bucket '+self.request.session['ss_img_bucketname']+' -m '+ manifest_path + ' > ' +self.tmp_file
		self.logger.debug('upload-bundle ramdisk: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('upload-bundle ramdisk command error.response=%s' % ret[0])
			raise Exception('upload-bundle ramdisk command error.')

		cmd_ch = "grep 'Uploaded image as' "+self.tmp_file+'| cut -d " " -f 4'
		self.logger.debug('grep Uploaded image: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('grep Uploaded image command error.response=%s' % ret[0])
			raise Exception('grep Uploaded image command error.')
		bucket_name = ret[1]

		cmd_ch = 'euca-register '+bucket_name + ' > ' +self.tmp_file

		self.logger.debug('euca-register ramdisk: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('euca-register ramdisk command error.response=%s' % ret[0])
			raise Exception('euca-register ramdisk command error.')

		cmd_ch = "grep 'IMAGE' " + self.tmp_file +" | sed 's/^IMAGE *//'"

		self.logger.debug('grep image ramdisk: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('grep Image command error.response=%s' % ret[0])
			raise Exception('grep Image command error.')

		return ret[1].strip()

	#OSイメージの登録
	def registerOSImage(self):
		self.logger.info('OSイメージの登録')
		cmd_ch = 'euca-bundle-image --image '+self.request.session['ss_img_imagepath']+' --ramdisk '+self.request.session['ss_img_ramdisk']+' --kernel '+self.request.session['ss_img_kernel']+' > '+self.tmp_file
		self.logger.debug('bundle-image osimage: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)

		if ret[0] != 0:
			self.logger.error('bundle-image osimage command error.response=%s' % ret[0])
			raise Exception('bundle-image osimage command error.')

		cmd_ch = "grep 'Generating manifest' "+self.tmp_file+' | cut -d " " -f 3'

		self.logger.debug('grep manifest: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('grep manifest command error.response=%s' % ret[0])
			raise Exception('grep manifest command error.')

		manifest_path = ret[1]
		cmd_ch = 'euca-upload-bundle --bucket '+self.request.session['ss_img_bucketname']+' -m '+ manifest_path + ' > ' +self.tmp_file
		self.logger.debug('upload-bundle osimage: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('upload-bundle osimage command error.response=%s' % ret[0])
			raise Exception('upload-bundle osimage command error.')

		cmd_ch = "grep 'Uploaded image as' "+self.tmp_file+' | cut -d " " -f 4'
		self.logger.debug('grep Uploaded image: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('grep Uploaded image command error.response=%s' % ret[0])
			raise Exception('grep Uploaded image command error.')

		bucket_name = ret[1]

		cmd_ch = 'euca-register '+bucket_name + ' > ' +self.tmp_file

		self.logger.debug('euca-register osimage: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('euca-register osimage command error.response=%s' % ret[0])
			raise Exception('euca-register osimage command error.')

		cmd_ch = "grep 'IMAGE' " + self.tmp_file +" | sed 's/^IMAGE *//'"

		self.logger.debug('grep image osimage: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] != 0:
			self.logger.error('grep Image command error.response=%s' % ret[0])
			raise Exception('grep Image command error.')

		return ret[1].strip()

#OSイメージを削除するクラス
class DeregisterOSImage(object):

	manifest_dir = 'manifest'
	#カスタムログ
	logger = logging.getLogger('koalalog')

	#コンストラクタ
	def __init__(self,image_model):
		self.image = image_model
		cmd_ch = 'pwd'
		ret = commands.getstatusoutput(cmd_ch)

		if ret[0] != 0:
			self.logger.error('os command error.response=%s' % ret[0])
			raise Exception('os command error.')
		self.current = ret[1]

	def deregisterImage(self):
		cmd_ch = 'euca-deregister '+self.image.id
		self.logger.debug('euca-deregister: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)

		if ret[0] != 0:
			self.logger.error('deregister command error.response=%s' % ret[0])
			raise Exception('deregister command error.')

		bucket_path = self.image.location.encode('utf-8')

		image_str=bucket_path.split('/')

		bucket_name = image_str[0]
		manifest_name = image_str[1]

		userDir = self.makeUserDir(self.image.owner)

		cmd_ch = 'euca-download-bundle -b '+ bucket_name + ' -d ' + userDir
		self.logger.debug('euca-download-bundle: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)

		if ret[0] != 0:
			self.logger.error('euca-download-bundle command error.response=%s' % ret[0])
			raise Exception('euca-download-bundle command error.')

		cmd_ch = 'euca-delete-bundle -b '+ bucket_name + ' -m ' + userDir+manifest_name
		self.logger.debug('euca-delete-bundle: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)

		if ret[0] != 0:
			self.logger.error('euca-delete-bundle command error.response=%s' % ret[0])
			raise Exception('euca-delete-bundle command error.')

		cmd_ch = 'rm -f ' + userDir+'*'

		self.logger.debug('rm -f: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)

		if ret[0] != 0:
			self.logger.error('rm -f command error.response=%s' % ret[0])
			raise Exception('rm -f command error.')

	def makeUserDir(self,user_id=""):
		cmd_ch = 'mkdir -p '+self.current+'/'+self.manifest_dir +'/'+ user_id+'/'
		self.logger.debug('mkdir -p: %s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)
		if ret[0] == 0:
			return self.current+'/'+self.manifest_dir +'/'+ user_id+'/'
		if ret[0] == 256:
			"""ディレクトリがすでに存在する場合"""
			return self.current+'/'+self.manifest_dir +'/'+ user_id+'/'

		self.logger.error('mkdir command error. response=%s' % ret[0])
		raise Exception('mkdir command error.')
