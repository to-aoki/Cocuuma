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

from koala.eucalyptus.models import User,Keypair,Volume
from koala.eucalyptus import euca_common
from koala.eucalyptus.user_model import User_Model
from koala.eucalyptus.db_access import EucalyptusDB
from koala.eucalyptus.euca_access import GetEucalyptusInfo
import os ,logging, commands, re, csv

class BatchCommon(object):

	#カスタムログ
	logger = logging.getLogger('koalasetuplog')

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo()

	#Koala内部DBにユーザを登録するメソッド ##### 現在使用していません
	def registUser(self):

		#管理者ユーザ、アカウントの定義
		admin_user = 'admin'
		admin_account = 'eucalyptus'

		csvUserfile = '../koala/management/commands/user.csv'
		readerUser = csv.reader(file(csvUserfile, 'r'))
		csvUsers = self.createCSVUser(readerUser)

		new_user_list=[]

		self.logger.info('-----ユーザーの登録開始-----')
		# Eucalyptus内部DBからユーザ情報を取得
		db = EucalyptusDB()
		user_list = db.getEucalyptusUser()

		for user in user_list:

			try:
				tmp = User.objects.get(user_id=user.user_id, account_id=user.account_id)
				self.logger.info('ユーザー[ %s@%s ]の登録スキップ'  % (tmp.user_id.encode('UTF-8'), tmp.account_id.encode('UTF-8')))

			except User.DoesNotExist:

				self.logger.info('ユーザー[ %s@%s ]の登録開始', user.user_id , user.account_id)

				if user.accesskey == None:
					self.logger.warn('ユーザー[ %s@%s ]のアクセスキーが未登録です。' % (user.user_id , user.account_id))
					self.logger.debug('ユーザー[ %s@%s ]の登録スキップ', user.user_id , user.account_id)
					break
				elif user.secretkey == None:
					self.logger.warn('ユーザー[ %s@%s ]のシークレットキーが未登録です。' % (user.user_id , user.account_id))
					self.logger.debug('ユーザー[ %s@%s ]の登録スキップ', user.user_id , user.account_id)
					break

				#ユーザの画面表示名
				user.name = u"%s@%s" % (user.user_id, user.account_id)

				# admin@eucalyptusの場合、管理者権限をTrueに設定
				if re.match(admin_user, user.user_id) and re.match(admin_account, user.account_id):
					user.admin = True
				else:
					user.admin = False

				#クレデンシャルファイルのダウンロード
				cred_path = './credentials/euca2-' + user.name + '-x509.zip'

				if os.path.isfile(cred_path) == False:
					cmd_ch = 'euca_conf --cred-account ' + user.account_id + ' --cred-user ' + user.user_id + ' --get-credentials ' + cred_path
					self.logger.debug('download credentials=%s' % cmd_ch)
					ret = commands.getstatusoutput(cmd_ch)

					if ret[0] != 0:
						self.logger.error('euca_conf --cred-account command error.response=%s' % ret[0])
						raise Exception('euca_conf --cred-account command error.')

				csvUser = self.getCSVUser(user.user_id, user.account_id, csvUsers)

				addip=0
				addVolNum=0
				addVolSize=0

				if csvUser != None:
					user.name=csvUser.name
					user.maxvm=csvUser.maxvm
					user.maxvol=csvUser.maxvol
					user.maxip=csvUser.maxip
					addip=csvUser.addip
					addVolNum=csvUser.addVolNum
					addVolSize=csvUser.addVolSize

					if csvUser.permission == 1:
						user.permission="11111111"
					else:
						user.permission="10010000"

				user.save()

				self.logger.info('ユーザー[%s@%s]の登録完了', user.user_id , user.account_id)
				self.logger.info('ユーザー[%s@%s]の追加情報の登録開始', user.user_id , user.account_id)

				auth_flag = False

				# mykey取得とセキュリティグループへのルール追加
				# （eucalyptusアカウントの任意ユーザ or 任意アカウントの管理者の場合）
				if user.account_id == admin_account or user.user_id == admin_user:
					auth_flag = True

				#mykeyの取得
				if auth_flag:
					self.createKeyPair(user)
				else:
					self.logger.info('mykeyの登録スキップ')

				#Elastic_IPの確保
				#self.getElasticIP(user,addip)
				#EBSボリュームの追加
				#self.createEBSVolume(user, addVolNum, addVolSize)

				#セキュリティグループへのルール追加
				if auth_flag:
					self.setSecurityGroup(user)
				else:
					self.logger.info('接続許可ルール追加スキップ')

				self.logger.info('ユーザー[%s@%s]の追加情報の登録完了', user.user_id , user.account_id)

			except Exception, ex:
				self.logger.warn('ユーザー[%s@%s]の登録失敗', user.user_id , user.account_id)
				self.logger.error(ex)

			#new_user_listに追加
			new_user_list.append(user)

		self.logger.info('-----ユーザーの登録完了-----')
		return new_user_list


	def setSecurityGroup(self, user_db=None):

		#カスタムログ
		self.logger = logging.getLogger('koalasetuplog')
		user = User_Model(user_db)

		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(user)

		try:
			self.logger.info('セキュリティグループへTCP接続許可ルール追加開始')
			#return_code = get_euca_info.authorize_securitygroup(group_name='default',
			#					 ip_protocol='tcp', from_port=0,
			#					 to_port=65535, cidr_ip='0.0.0.0/0')
			return_code = get_euca_info.authorize_securitygroup(group_name='default',
								 ip_protocol='tcp', from_port=22,
								 to_port=22, cidr_ip='0.0.0.0/0')

			if not return_code:
				self.logger.warn("TCP接続許可ルール追加に失敗しました。")
			else:
				#self.logger.info('セキュリティグループへTCP接続許可ルール追加成功')
				self.logger.info('セキュリティグループへssh接続許可ルール追加成功')

			#self.logger.info('セキュリティグループへUDP接続許可ルール追加開始')
			#return_code = get_euca_info.authorize_securitygroup(group_name='default',
			#					 ip_protocol='udp', from_port=0,
			#					 to_port=65535, cidr_ip='0.0.0.0/0')

			#if not return_code:
			#	self.logger.warn("UDP接続許可ルール追加に失敗しました。")
			#else:
			#	self.logger.info('セキュリティグループへUDP接続許可ルール追加成功')

			self.logger.info('セキュリティグループへICMP接続許可ルール追加開始')

			return_code = get_euca_info.authorize_securitygroup(group_name='default',
								 ip_protocol='icmp', from_port=-1,
								 to_port=-1, cidr_ip='0.0.0.0/0')

			if not return_code:
				self.logger.warn("ICMP接続許可ルール追加に失敗しました。")
			else:
				self.logger.info('セキュリティグループへICMP接続許可ルール追加成功')

		except Exception, ex:

			# Eucalyptusエラー
			self.logger.warn("接続許可ルール追加に失敗しました。")
			errors = [euca_common.get_euca_error_msg('%s' % ex)]
			self.logger.error(errors)

##### 現在使用していません
	def createEBSVolume(self, user_db=None, num=0,size=0):

		#カスタムログ
		self.logger = logging.getLogger('koalasetuplog')
		user = User_Model(user_db)

		usevol = 0

		self.logger.info('ユーザのボリュームリソースチェック開始')

		#リソース上限チェック
		try:
			usevol = euca_common.countActiveVolume(user)
		except Exception, ex:
			# Eucalyptusエラー
			errors = [euca_common.get_euca_error_msg('%s' % ex)]
			self.logger.error(errors)
			return

		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(user)

		i = 0

		while i < num:

			self.logger.info('ボリュームの追加開始 [%sGB]' % size)

			i += 1
			if (usevol + (size * i)) > user.db_user.maxvol:
				self.logger.warn('利用可能なボリュームの上限を超えています。')
				return

			#EBSボリューム作成(Eucalyptus操作)
			try:
				zones = get_euca_info.get_availabilityzones()
				zone = None
				if len(zones) > 0:
					zone = zones[0]
				else:
					self.logger.warn('クラスタが見つかりません。')
					continue
				#サイズ指定の場合
				volume = get_euca_info.create_volume(size, zone=zone, snapshot=None)

			except Exception, ex:
				# Eucalyptusエラー
				self.logger.warn("ボリューム作成に失敗しました。")
				errors = [euca_common.get_euca_error_msg('%s' % ex)]
				self.logger.error(errors)
				continue

			# DB登録
			db_volume = Volume()
			db_volume.volume_id = volume.id
			db_volume.user_id = user.id
			db_volume.account_id = user.account_id
			db_volume.name = 'ボリューム'+str(i)
			db_volume.description = 'ボリューム'+str(i)+'です。'
			db_volume.save()

			self.logger.info('ボリューム[%s]の追加完了' % volume.id.encode('utf_8'))

##### 現在使用していません
	def getElasticIP(self, user_db=None, num=0):
		#カスタムログ
		self.logger = logging.getLogger('koalasetuplog')

		user = User_Model(user_db)

		self.logger.info('ElasticIPの確保開始')

		#リソース上限チェック
		try:
			useip = euca_common.countAllocatedAddress(user)
		except Exception, ex:
			# Eucalyptusエラー
			errors = [euca_common.get_euca_error_msg('%s' % ex)]
			self.logger.error(errors)
			return

		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(user)

		i = 0

		while i < num:
			i += 1

			if (useip + i) > user.db_user.maxip:
				self.logger.warn('取得可能な固定IPの上限を超えています。')
				return

			try:
				self.logger.info('ElasticIPの確保開始')
				get_euca_info.allocate_address()
				self.logger.info('ElasticIPの確保成功')
			except Exception, ex:
				errors = [euca_common.get_euca_error_msg('%s' % ex)]
				self.logger.error('ElasticIPの確保失敗')
				self.logger.error(errors)
				continue


	def createKeyPair(self, user_db=None):

		#カスタムログ
		self.logger = logging.getLogger('koalasetuplog')
		if user_db==None:
			return False

		user = User_Model(user_db)
		keyname = user.id + '_mykey'

		self.logger.info('mykeyの登録開始')

		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(user)

		try:
			Keypair.objects.get(user_id=user.id,account_id=user.account_id,name=keyname)
			self.logger.info('既存のmykeyのDB削除開始')
			Keypair.objects.filter(user_id=user.id,account_id=user.account_id,name=keyname).delete()
			self.logger.info('既存のmykeyのDB削除成功')

		except Keypair.DoesNotExist:
			self.logger.info('既存のmykeyのDB削除スキップ')

		try:
			self.logger.info('mykeyの削除開始')
			get_euca_info.delete_keypair(keyname)
			self.logger.info('mykeyの削除成功')

		except Exception, ex:
			# Eucalyptusエラー
			errors = [euca_common.get_euca_error_msg('%s' % ex)]
			self.logger.warn('mykeyの削除失敗')
			self.logger.warn(errors)
			return False

		try:
			self.logger.info('mykeyの新規登録')
			# キーペアを作成
			keypair = get_euca_info.create_keypair(keyname)

		except Exception, ex:
			# Eucalyptusエラー
			errors = [euca_common.get_euca_error_msg('%s' % ex)]
			self.logger.error('mykeyの登録失敗')
			self.logger.error(errors)
			return False

		#DBへキーペア情報を登録
		db_keypair = Keypair()
		db_keypair.user_id = user.id
		db_keypair.account_id = user.account_id
		db_keypair.name = keyname
		db_keypair.data = keypair.material
		db_keypair.save()

		self.logger.info('mykeyの登録成功')
		return True

##### 現在使用していません
	def createCSVUser(self, reader=None):
		UserCSV = []

		if reader == None:
			return []

		for row in reader:

			user = CSVUser()

			if row[0][0] == '#':
				continue

			user.account_id=row[0].decode('utf_8')
			user.id=row[1].decode('utf_8')
			user.name=row[2].decode('utf_8')
			user.maxvm=int(row[3].decode('utf_8'))
			user.maxvol=int(row[4].decode('utf_8'))
			user.maxip=int(row[5].decode('utf_8'))
			user.addip=int(row[6].decode('utf_8'))
			user.addVolSize=int(row[7].decode('utf_8'))
			user.addVolNum=int(row[8].decode('utf_8'))

			try:
				user.permission=int(row[9].decode('utf_8'))
			except:
				user.permission=0

			UserCSV.append(user)

		return UserCSV


##### 現在使用していません
	def getCSVUser(self, user_id="", account_id="", csvUser=[]):

		for csv in csvUser:
			if user_id == csv.id:
				if account_id==csv.account_id:
					return csv

		return None

##### 現在使用していません
class CSVUser(object):

	def __init__(self):
		self.account_id=""
		self.account_number=0
		self.id=""
		self.name=""
		self.maxvm=10
		self.maxvol=50
		self.maxip=5
		self.addip=0
		self.addVolSize=3
		self.addVolNum=2
		self.permission=0
