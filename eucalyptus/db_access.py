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

import pgdb
import logging
from koala.eucalyptus.models import User
from koala.eucalyptus.models import Group
from group_model import Group_Model
from xml.etree.ElementTree import parse
from koala.settings import EUCA_DB_HOST
from koala.settings import EUCA_DB_PORT
from koala.settings import PROJECT_PATH
from report_models import Report_Account_Model, Report_User_Model

# Eucalyptus 内部DB(PostgreSQL)クラス
#--------------------------------------------------------
class EucalyptusDB(object):

	#カスタムログ
	logger = logging.getLogger('koalalog')

	# Eucalyptus内部DB 接続情報
	db_address = 'localhost'
	db_port = '8777'
	db_user = 'eucalyptus'
	db_name = 'eucalyptus_auth'
	jdbc_conf_path = PROJECT_PATH +'/data/ha_jdbc_auth.xml'
	db_passwd = None

	# コンストラクタ
	def __init__(self):

		# settings.py からEucalyptus内部DBへの接続情報を取得
		self.db_address = EUCA_DB_HOST
		self.db_port = EUCA_DB_PORT

		try:
			#ha_jdbc_auth.xmlをパース
			tree = parse(self.jdbc_conf_path)
			#ルート要素を取得(Element型)
			elm = tree.getroot()
			#条件にマッチする要素のテキストを返す
			self.db_passwd = elm.find('.//password').text

		except Exception, ex:
			self.logger.error("dataディレクトリの設定ファイル（ha_jdbc_auth.xml）が正しいか確認してください")
			raise ex

	# Get all user's info from Eucalyptus DB
	def getEucalyptusUser(self, user=None, account=None):

		user_list = []

		sql =("SELECT u.auth_user_is_enabled, u.auth_user_name, a.auth_account_name, a.auth_account_number, "
		+ "ak.auth_access_key_active, ak.auth_access_key_query_id, ak.auth_access_key_key, "
		+ "u.auth_user_path, u.auth_user_id_external  "
		+ "FROM (auth_user u LEFT OUTER JOIN auth_access_key ak ON ak.auth_access_key_owning_user = u.id "
		+ "JOIN auth_group_has_users gu ON u.id=gu.auth_user_id "
		+ "JOIN auth_group g ON gu.auth_group_id=g.id "
		+ "JOIN auth_account a ON g.auth_group_owning_account=a.id)")

		if user != None and account != None:
			sql = sql + " WHERE u.auth_user_name = '" + user + "' AND a.auth_account_name = '" + account + "'"
		elif user == None and account != None:
			sql = sql + " WHERE a.auth_account_name = '" + account + "'"


		euca_users = self.executeQuery(sql)

		for u in euca_users:
			# if auth_user is enabled
			if u[0]:
				user = User()
				user.user_id = u[1]			# user name
				user.account_id = u[2]		# account name
				user.account_number = u[3]	# account number(internal)

				# if access key is active
				if u[4]:
					user.accesskey = u[5]	# access key
					user.secretkey = u[6]	# secret key
				else:
					user.accesskey = None
					user.secretkey = None
				user.enabled_stat = u[0]
				user.user_path = u[7]
				user.user_number = u[8]

				user_list.append(user)

		return user_list

	def getAccountList(self):

		account_list = []

		sql =("SELECT auth_account_name, auth_account_number FROM auth_account")

		euca_accounts = self.executeQuery(sql)

		for ac in euca_accounts:
			account = Report_Account_Model()
			account.name = ac[0]
			account.id_number = ac[1]
			account_list.append(account)

		return account_list


	def getAccountId(self,account_name):

		sql =("SELECT auth_account_number FROM auth_account")
		sql = sql + "WHERE auth_account_name = '"  + account_name + "'"

		euca_account_id = self.executeQuery(sql)

		return euca_account_id


	def getUserListInAccount(self, account_number):

		sql =("SELECT u.auth_user_is_enabled, u.auth_user_name, u.auth_user_id_external, a.auth_account_name, a.auth_account_number, "
		+ "u.auth_user_path, u.auth_user_reg_stat "
		+ "FROM (auth_user u JOIN auth_group_has_users gu ON u.id=gu.auth_user_id "
		+ "JOIN auth_group g ON gu.auth_group_id=g.id "
		+ "JOIN auth_account a ON g.auth_group_owning_account=a.id)")
		sql = sql + " WHERE a.auth_account_number = '" + account_number + "'"
		sql = sql + ("GROUP BY u.auth_user_is_enabled, u.auth_user_name, u.auth_user_id_external, a.auth_account_name, a.auth_account_number, "
		+ "u.auth_user_path, u.auth_user_reg_stat ")

		users = self.executeQuery(sql)
		user_list = []

		for u in users:
			if u[0]:
				user = Report_User_Model()
				user.user_id = u[1]
				user.user_internal_id = u[2]
				user.account_id = u[3]		# account name
				user.account_number = u[4]	# account number(internal)
				user.enabled_stat = u[0]
				user.user_path = u[5]
				user.user_reg_stat = u[6]

				userintid = u[2]

				group_names = []
				groups = self.getGroupListInUser(userintid)

				group_namess = ""
				for gr in groups:
					group_names.append(gr.group_name)
					if group_namess == "":
						group_namess = str(gr.group_name)
					else:
						group_namess = group_namess + "," + str(gr.group_name)

				if len(group_names) > 0:
					user.user_group = group_namess
				else:
					user.user_group = ""
				#if group_name[0] != None:
				#	user.user_group = ""
				#else:
				#	user.user_group = ""

				user_list.append(user)

		return user_list


	def getGroupUserList(self, group_number):

		sql =("select u.auth_user_name, u.auth_user_path, u.auth_user_is_enabled, u.auth_user_id_external, g.auth_group_name,"
		+ "a.auth_account_name from auth_group g, auth_user u, auth_group_has_users gu, auth_account a "
		+ "where auth_group_user_group is not true and u.id = gu.auth_user_id and g.id = gu.auth_group_id "
		+ "and g.auth_group_owning_account = a.id ")

		sql = sql + "and  g.auth_group_id_external = '" + group_number + "'"

		group_users = self.executeQuery(sql)
		group_user_list = []

		for u in group_users:
			user = User()
			user.user_id = u[0]
			user.user_internal_id = u[3]
			user.account_id = u[5]		# account name
			user.enabled_stat = u[2]
			user.user_path = u[1]

			group_user_list.append(user)

		return group_user_list



	def getGroupListInUser(self, user_number):

		sql =("select g.auth_group_name,g.auth_group_id_external,g.auth_group_path "
		+ "from auth_group g, auth_user u, auth_group_has_users gu "
		+ "where auth_group_user_group is not true and u.id = gu.auth_user_id and g.id = gu.auth_group_id ")

		sql = sql + "and  u.auth_user_id_external = '" + user_number + "'"

		groups = self.executeQuery(sql)
		group_list = []

		for gr in groups:
			group = Group()
			group.group_id = gr[1]
			group.group_name = gr[0]
			group.group_path = gr[2]
			#group.account_name = gr[3]
			#group.account_id = gr[4]
			#group.group_desc = ""
			#group.group_pol = ""
			group_list.append(group)

		return group_list


	def getGroupList(self, group_id=None, account_number=None):

		logger = logging.getLogger('koalalog')
		logger.info('グループ一覧取得処理')

		sql =("select g.auth_group_name,g.auth_group_id_external,g.auth_group_path,a.auth_account_name,a.auth_account_number "
		+ "from auth_group g, auth_account a "
		+ "where auth_group_user_group is not true and g.auth_group_owning_account = a.id ")

		if account_number != None:
			sql = sql + " and a.auth_account_number = '" + account_number + "'"


		if group_id != None:
			sql = sql + " and g.auth_group_id_external = '" + group_id + "'"

		groups = self.executeQuery(sql)
		#group_list = []

		for gr in groups:

			db_group = Group.objects.filter(group_id=gr[1])

			if not db_group:

				group = Group()
				group.group_id = gr[1]
				group.group_name = gr[0]
				group.group_path = gr[2]
				group.account_name = gr[3]
				group.account_id = gr[4]
				group.group_desc = ""
				group.group_pol = ""

				group.save()
				logger.info('cooala内部DBに未登録の %s グループを内部DBに登録しました' % str(group.group_name))

		#削除済みチェック
		db_group_acall = Group.objects.filter(account_id=account_number)

		for dbgr in db_group_acall:
			dbgr_ent = []
			dbgr_gr_id = dbgr.group_id
			sql ="select auth_group_name from auth_group where auth_group_id_external = '" + dbgr_gr_id + "'"
			dbgr_ent = self.executeQuery(sql)
			logger.debug('グループリスト更新処理  %s' % str(dbgr.group_name))
			if 0 == len(dbgr_ent):
				dbgr.delete()
				logger.info('cooala内部DBから %s グループのエントリを削除しました' % str(dbgr.group_name))
		logger.info('グループリスト更新６')

		db_group_ac = Group.objects.filter(account_id=account_number)


			#group_list.append(group)
		#return group_list

		return db_group_ac


	def group_list2(self, group_id=None, account=None):

		group_list = self.getGroupList(group_id,account)

		return group_list



	def getUserInternalId(self, account_number, user_id):

		internalId = "none"
		user_list = self.getUserListInAccount(account_number)

		for u in user_list:
			if u.user_id == user_id:
				internalId = u.user_internal_id
		return internalId

	def deleteVolume(self, volumeid):
		self.db_name = "eucalyptus_storage"
		sql = "delete from iscsivolumeinfo where volume_name='" + volumeid + "'"
		ret = self.executeQuery(sql,True)
		sql = "delete from volumes where volume_name='" + volumeid + "'"
		ret = self.executeQuery(sql,True)
		self.db_name = "eucalyptus_cloud"
		sql = "delete from metadata_volumes where metadata_display_name='" + volumeid + "'"
		ret = self.executeQuery(sql,True)

	# execute sql to the eucalyptus database
	def executeQuery(self, sql, commit=False):

		db_host = "%s:%s" % (self.db_address, self.db_port)

		try:
			db = pgdb.connect(host=db_host, user=self.db_user, database=self.db_name, password=self.db_passwd)
			cursor = db.cursor()
			cursor.execute(sql)
			result = None
			if not commit:
				result = cursor.fetchall()
			cursor.close()
			if commit:
				db.commit()
			db.close()

		except Exception, ex:
			raise ex

		return result
