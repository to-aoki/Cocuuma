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

from euca_access import GetEucalyptusInfo
from models import Image, VMType
from image_model import Image_Model
from xml.dom import minidom
from django import forms

import re
import os
import commands
import traceback
import logging


#カスタムログ
logger = logging.getLogger('koalalog')


def countActiveMachine(login_user=None):
	"""起動中／起動処理中マシンの数を取得
		input: login_user:models.User
		return: int
	"""
	count = 0

	if login_user == None:
		return 0

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)
	#ログインユーザのインスタンスの一覧を取得
	reservations = get_euca_info.get_instancelist()

	if not reservations:
		return 0

	for reservation in reservations:
		for instance in reservation.instances:
			if instance.state == u"pending" or instance.state == u"running":
				# Eucalyptus3.0では管理者(admin@eucalyptus)でも自アカウントのインスタンスのみ取得(verboseオプション無しの場合)
				count += 1
#				logger.debug("countActiveMachine:reservation.owner_id=%s" % reservation.owner_id)
#				if login_user.admin:
#					# 管理者の場合は他ユーザーのインスタンスも取得されるのでユーザーIDチェック
#					if reservation.owner_id == login_user.id:
#						count += 1
#				else:
#					count += 1

	return count


def countActiveVolume(login_user=None):
	"""EBSボリューム利用量を取得
		input: login_user:models.User
		return: int
	"""

	if login_user == None:
		return 0

	db_volumes = ""

	# Eucalyptus3.0では管理者(admin@eucalyptus)でも自アカウントのEBSのみ取得(verboseオプション無しの場合)
#	if login_user.admin:
#		#ユーザが管理者属性の場合はDBに登録されているボリュームのみを取得
#		db_volumes = Volume.objects.filter(user_id=login_user.id).values_list('volume_id', flat=True)
#		if not db_volumes:
#			return 0

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)
	#ログインユーザのボリュームの一覧を取得
	volumes = get_euca_info.get_volumelist(db_volumes)

	#利用容量を集計
	total = 0
	for volume in volumes:
		total += volume.size			#サイズ

	return total


def countAllocatedAddress(login_user=None):
	"""取得済みIPアドレスの数を取得
		input: login_user:models.User
		return: int
	"""
	count = 0

	if login_user == None:
		return 0

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)
	#ログインユーザのIPアドレス一覧を取得
	addresslist = get_euca_info.get_addresslist()

	# IPアドレス数集計

	if login_user.account_id == "eucalyptus":
	#if login_user.admin:
		# 管理者の場合は全IPアドレスが表示されるのでフィルタ

#		# Eucalyptus2.0時のパターン
#		# インスタンスIDパターン(管理者の場合、取得済み、未使用)
#		INSTANCE_ID_PTN_MINE=re.compile(r"^available\s*\(%s\)$" % login_user.id)
#		# インスタンスIDパターン(管理者の場合、インスタンスへ取り付け済み)
#		INSTANCE_ID_PTN_MINE_USED=re.compile(r"^i-\w{8}\s*\(%s\)$" % login_user.id)

		# インスタンスIDパターン(管理者の場合、取得済み、未使用)
		INSTANCE_ID_PTN_MINE=re.compile(r"^available\s*\(arn:aws:euare::%s:user/%s\)$" % (login_user.account_number, login_user.id) )
		# インスタンスIDパターン(管理者の場合、インスタンスへ取り付け済み)
		INSTANCE_ID_PTN_MINE_USED=re.compile(r"^i-\w{8}\s*\(arn:aws:euare::%s:user/%s\)$" % (login_user.account_number, login_user.id) )

		for address in addresslist:
			if INSTANCE_ID_PTN_MINE.match(address.instance_id):
				#取得済み、未使用(管理者の場合)
				count += 1
			elif INSTANCE_ID_PTN_MINE_USED.match(address.instance_id):
				#取得済み、インスタンスへ取り付け済み(管理者の場合)
				count += 1

	else:
		# 非管理者の場合は取得件数そのまま
		count = len(addresslist)

	return count


def countAssociatedAddress(login_user=None):
	"""関連付け済みIPアドレスの数を取得
		input: login_user:models.User
		return: int
	"""
	count = 0
	if login_user == None:
		return 0

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)
	#ログインユーザのIPアドレス一覧を取得
	addresslist = get_euca_info.get_addresslist()

	# IPアドレス数集計
	if login_user.account_id == "eucalyptus":
	#if login_user.admin:
		# 管理者の場合は全IPアドレスが表示されるのでフィルタ
		# インスタンスIDパターン(管理者の場合、インスタンスへ取り付け済み)
		INSTANCE_ID_PTN_MINE_USED=re.compile(r"^i-\w{8}\s*\(arn:aws:euare::%s:user/%s\)$" % (login_user.account_number, login_user.id) )

		for address in addresslist:
			if INSTANCE_ID_PTN_MINE_USED.match(address.instance_id):
				#取得済み、インスタンスへ取り付け済み(管理者の場合)
				count += 1

	else:
		# 非管理者の場合は取得件数そのまま
		for address in addresslist:
			if address.instance_id:
				count += 1

	return count


#イメージのデータモデルを生成する
def createImageModel(images=[],image_id=""):
	#if user==None:
	#	return None

	for image in images:
		if image.id == image_id:
			try:
				db_image = Image.objects.get(image_id=image.id)
			except:
				return None
			imageModel = Image_Model(db_image, image)
			return imageModel
	return None

#VMTypeのデータモデルを生成する
def createVMTypeModel(vmtype=""):
	try:
		db_vmtype = VMType.objects.get(vmtype=vmtype)
		return db_vmtype
	except:
		return None


def createVMTypeModelNG(vmtypes=[], vmtype=""):

	for v in vmtypes:
		if v.vmtype != vmtype:
			continue

		try:
			db_vmtype = VMType.objects.get(vmtype=vmtype)
			vmtype_model = VMType(db_vmtype)
			vmtype_model.cpu = v.cpu
			vmtype_model.mem = v.mem
			vmtype_model.disk = v.disk

			return db_vmtype

		except:
			return None

	return None

#OSイメージの格納パスを取得する
def createImagePath():
	#imagePath = "image"
	cmd_ch = 'pwd'
	ret = commands.getstatusoutput(cmd_ch)

	if ret[0] != 0:
		raise Exception('os command error.')

	#return ret[1]+'/'+ imagePath
	return '/var/tmp/kikuchi/koala/image'


def displaymsg(func):
	def _(*args, **keywords):
		return u"Eucalyptus操作でエラーが発生しました。「%s」"  % func(*args, **keywords)
	return _

# euca2oolsの__init__.pyのdisplay_error_and_exitの劣化コピー
@displaymsg
def get_euca_error_msg(msg):
	"""
	botoAPIのエラーレスポンスからエラーメッセージを取得する
	"""
	logger.debug(msg)
	code = None
	message = None
	index = msg.find('<')
	if index < 0:
		return msg
	msg = msg[index - 1:]
	msg = msg.replace('\n', '')
	dom = minidom.parseString(msg)
	try:
		error_elem = dom.getElementsByTagName('Error')[0]
		code_elem = error_elem.getElementsByTagName('Code')[0]
		nodes = code_elem.childNodes
		for node in nodes:
			if node.nodeType == node.TEXT_NODE:
				code = node.data

		msg_elem = error_elem.getElementsByTagName('Message')[0]
		nodes = msg_elem.childNodes
		for node in nodes:
			if node.nodeType == node.TEXT_NODE:
				message = node.data

		return u'原因コード:%s, 詳細メッセージ:%s' % (code, message)
	except Exception:
		print traceback.format_exc()
		return msg

class CustomFilePathField(forms.FilePathField):
	""" form.FilePathFieldに更新メソッドを追加"""
	def update(self):
		self.choices = []
		if self.recursive:
			for root, files in sorted(os.walk(self.path)):
				for f in files:
					if self.match is None or self.match_re.search(f):
						f = os.path.join(root, f)
						self.choices.append((f, f.replace(self.path, "", 1)))
		else:
			try:
				for f in sorted(os.listdir(self.path)):
					full_file = os.path.join(self.path, f)
					if os.path.isfile(full_file) and (self.match is None or self.match_re.search(f)):
						self.choices.append((full_file, f))
			except OSError:
				pass

		self.widget.choices = self.choices
