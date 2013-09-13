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

from datetime import datetime, timedelta
from django.utils import dateformat
import traceback


class MachineGroup_append(object):
	"""仮想マシングループ"""

	def __init__(self):
		#DBデータ
		self.db_object = None
		#仮想マシンのリスト
		self.machine_list = []

	@property
	def db(self):
		return self._db_object

	@db.setter
	def db(self, db_object):
		self._db_object = db_object

	#マシングループの状態
	@property
	def status(self):
		if not self.machine_list:
			return "terminated"

		# グループ状態表示用にマシン状態集計
		group_stat = "unknown"
		for i, machine in enumerate(self.machine_list):
			if i == 0:
				group_stat = machine.status
			elif machine.status != group_stat:
				if ( machine.status == "shutting-down" or machine.status == "terminated" ) and ( group_stat == "shutting-down" or group_stat == "terminated" ):
					group_stat = "shutting-down"
				elif ( machine.status == "pending" or machine.status == "running" ) and ( group_stat == "pending" or group_stat == "running" ):
					group_stat = "pending"
				else:
					group_stat = "unknown"
					break
		"""
		group_stat = "running"
		for machine in self.machine_list:
			# 表示優先順位："terminated"＞"shutting-down"＞"pending"＞"running"
			if machine.status == "terminated":
				group_stat = "terminated"
			elif machine.status == "shutting-down" and group_stat != "terminated":
				group_stat = "shutting-down"
			elif machine.status == "pending" and group_stat == "running":
				group_stat = "pending"
		"""

		return group_stat


class Machine_append(object):
	"""仮想マシン"""

	def __init__(self):
		#DBデータ
		self.db_object = None
		#ボリュームのリスト
		self.volume_list = []
		#状態
		self.status = ""
		#起動時刻
		self.starttime = ""
		#プライベートIP
		self.privateip = ""
		#パブリックIP(自動設定時)
		self.auto_ip = ""
		#AvaulabilityZone(自動設定時)
		self.auto_zone = ""
		#起動タイプ(VMtype)表示名
		self.displayVMType = None
		#デバイスタイプ
		self.device_type=""
		#使用テンプレート
		self.template_name="設定されていません"
		self.monitoring = None
		self.creating_image_name = ""

	@property
	def db(self):
		return self._db_object

	@db.setter
	def db(self, db_object):
		self._db_object = db_object

	@property
	def displayStatus(self):
		"""マシン状態を表示用に変換する"""

		dic = { u"pending":u"起動処理中", u"running":u"起動状態", u"shutting-down":u"終了処理中", u"terminated":u"初期状態", u"stopping":u"停止処理中", u"stopped":u"停止状態"}

		try:
			return dic[self.status]
		except:
			print traceback.format_exc()
			return u"不正な状態(%s)" % self.status

	@property
	def displayAddress(self):
		"""IPアドレス表示"""

		if self.db.ip:
			return self.db.ip
		elif self.auto_ip:
			return u"%s (自動設定)" % self.auto_ip
		else:
			return u"指定しない"

	@property
	def displayStartTime(self):
		"""起動時刻表示"""

		if self.starttime:
			utc_time = datetime.strptime(self.starttime[0:19], "%Y-%m-%dT%H:%M:%S")
			locale_time = utc_time + timedelta(hours=9)
			dateStr = dateformat.format(locale_time, 'Y年m月d日 H:i:s')
			return dateStr
		else:
			return self.starttime

	@property
	def displayZone(self):
		"""AvaulabilityZone表示"""

		if self.db.avaulability_zone:
			return self.db.avaulability_zone
		elif self.auto_zone:
			return u"自動設定(%s)" % self.auto_zone
		else:
			return u"指定しない"

	@property
	def displayVolume(self):
		"""ボリューム表示"""

		if self.volume_list:
			dispList = [x[1] for x in self.volume_list]
			return "\n".join(dispList)
		else:
			return u"使用しない"

	def displayStopButton(self):
		"""サーバを停止ボタン表示"""

		if self.device_type == "ebs":
			return True
		else:
			return False


class NonGroupMachine(object):
	"""グループ外仮想マシン"""

	def __init__(self):
		self.instance_id = ""			#インスタンスID
		self.image_id = ""				#イメージID
		self.vmtype = ""				#VMType
		self.ip = ""					#Pアドレス
		self.keypair = ""				#キーペア名
		self.security_group = ""		#セキュリティグループ名
		self.avaulability_zone = ""		#AvaulabilityZone
		self.status = ""				#状態
		self.starttime = ""				#起動時刻
		self.privateip = ""				#プライベートIP
		self.displayVMType = None		#起動タイプ(VMtype)表示名

	@property
	def displayStatus(self):
		"""マシン状態を表示用に変換する"""

		dic = { u"pending":u"起動処理中", u"running":u"起動状態", u"shutting-down":u"停止処理中", u"terminated":u"停止状態", u"stopping":u"中断処理中", u"stopped":u"中断状態"}

		try:
			return dic[self.status]
		except:
			print traceback.format_exc()
			return u"不正な状態(%s)" % self.status

	@property
	def displayStartTime(self):
		"""起動時刻表示"""

		if self.starttime:
			utc_time = datetime.strptime(self.starttime[0:19], "%Y-%m-%dT%H:%M:%S")
			locale_time = utc_time + timedelta(hours=9)
			dateStr = dateformat.format(locale_time, 'Y年m月d日 H:i:s')
			return dateStr
		else:
			return self.starttime


def createEditGroupData():
	data = EditGroupData()
	data.group_id = None			#マシングループID
	data.name = ""					#マシングループ名
	data.description = ""			#マシングループ説明
	data.template_list = []		#選択済みテンプレートリスト
	data.machine_list = []		#仮想マシンリスト
	return data

class EditGroupData():
	""""「1.テンプレート選択」の入力フォーム保存オブジェクト"""
#	def __init__(self):
#		self.group_id = None			#マシングループID
#		self.name = ""					#マシングループ名
#		self.description = ""			#マシングループ説明
#		self.template_list = None		#選択済みテンプレートリスト
#		self.machine_list = None		#仮想マシンリスト

	template_base = {
				'template_id':None,			#テンプレートID
				'template_name':None,		#テンプレート名
				'count':None				#仮想マシン個数
				}

	# マシン情報用辞書
	machine_base = {
				'group':None,				#マシングループID
				'name':None,				#マシン名
				'instance_id':None,			#インスタンスID
				'image_id':None,			#イメージID
				'vmtype':None,				#VMType
				'vmtype_disp':None,			#VMType表示名
				'volume':None,				#ボリュームID
				'volume_disp':None,			#ボリューム表示名
				'ip':None,					#IPアドレス
				'keypair':"yourkey",				#キーペア名
				'security_group':"default",		#セキュリティグループ名
				'avaulability_zone':None,	#AvaulabilityZone
				'user_data':"",			#ユーザーデータ
				'template_id':None,			#テンプレートID
				'order':None				#表示順
				}

