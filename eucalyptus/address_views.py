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
#

from django.shortcuts import render_to_response
from django.template import RequestContext
from euca_access import GetEucalyptusInfo
from address_model import Address_Model
from django.db.models import Q
from models import Machine
import euca_common
import re
import logging

#カスタムログ
logger = logging.getLogger('koalalog')

def top(request):
	"""IPアドレスメニューの初期表示"""

	logger.info('IPアドレス 一覧表示')

	#メニューを「IPアドレス」に設定
	request.session['ss_sys_menu'] = "address"

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)
	# IPアドレス一覧を取得
	request.session['ss_adr_addresslist'] = getAddressList(get_euca_info, login_user)

	logger.info('IPアドレス 一覧表示 完了')

	return render_to_response('address_list.html',{},context_instance=RequestContext(request))


def allocate(request):
	"""IPアドレスを取得ボタン"""

	logger.info('IPアドレス 取得')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	"""
	IPアドレスを取得
	"""
	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)
	# リソース制限チェック
	nowip = euca_common.countAllocatedAddress(login_user)
	if nowip >= login_user.db_user.maxip :
		# リソース制限エラー
		errors = ["IPアドレスはこれ以上取得できません。"]
		return render_to_response('address_list.html',{'errors':errors},context_instance=RequestContext(request))

	# IPアドレスを取得
	#newaddress = get_euca_info.allocate_address()
	try:
		get_euca_info.allocate_address()
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		return render_to_response('address_list.html',{'errors':errors}, context_instance=RequestContext(request))


	# IPアドレス一覧を取得
	request.session['ss_adr_addresslist'] = getAddressList(get_euca_info, login_user)

	logger.info('IPアドレス 取得 完了')

	return render_to_response('address_list.html',{},context_instance=RequestContext(request))


def disassociate(request, ip):
	"""関連付け解除ボタン"""

	logger.info('IPアドレス 関連付け解除')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	addresslist = request.session['ss_adr_addresslist']

	target = None
	for address in addresslist:
		if ip == address.ip:
			target = address
			break
	else:
		return render_to_response('address_list.html',{},context_instance=RequestContext(request))

	if target.machine_id:
		# 仮想マシンへ関連付けしている場合、DB情報更新
		machinelist = Machine.objects.filter(ip=ip)
		for machine in machinelist:
			machine.ip = None
			machine.save()

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	if target.instance_id:
		# 関連付け仮想マシンが起動している場合、Eucalyptus操作
		# IPアドレスを関連付け解除
		#result = get_euca_info.disassociate_address(ip)
		try:
			get_euca_info.disassociate_address(ip)
		except Exception, ex:
			# Eucalyptusエラー
			errors = [euca_common.get_euca_error_msg('%s' % ex)]
			return render_to_response('address_list.html',{'errors':errors}, context_instance=RequestContext(request))

	# IPアドレス一覧を取得
	request.session['ss_adr_addresslist'] = getAddressList(get_euca_info, login_user)

	logger.info('IPアドレス 関連付け解除 完了')

	return render_to_response('address_list.html',{},context_instance=RequestContext(request))


def release(request, ip):
	"""IPアドレス返却ボタン"""

	logger.info('IPアドレス 返却')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	addresslist = request.session['ss_adr_addresslist']

	target = None
	for address in addresslist:
		if ip == address.ip:
			target = address
			break
	else:
		return render_to_response('address_list.html',{},context_instance=RequestContext(request))

	if target.machine_id:
		# 仮想マシンへ関連付けしている場合、DB情報更新
		machinelist = Machine.objects.filter(ip=ip)
		for machine in machinelist:
			machine.ip = None
			machine.save()

	"""
	IPアドレスを返却
	"""
	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)
	# IPアドレスを返却
	#result = get_euca_info.release_address(ip)
	try:
		get_euca_info.release_address(ip)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		return render_to_response('address_list.html',{'errors':errors}, context_instance=RequestContext(request))

	# IPアドレス一覧を取得
	request.session['ss_adr_addresslist'] = getAddressList(get_euca_info, login_user)

	logger.info('IPアドレス 返却 完了')

	return render_to_response('address_list.html',{},context_instance=RequestContext(request))


def associate(request, ip):
	"""仮想マシンへ関連付けボタン"""

	logger.info('IPアドレス 関連付け')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	addresslist = request.session['ss_adr_addresslist']

	target = None
	for address in addresslist:
		if ip == address.ip:
			target = address
			break
	else:
		return render_to_response('address_list.html',{},context_instance=RequestContext(request))

	"""
	TODO:IPアドレスを関連付けていない仮想マシンリストを表示して選択させる

	TODO: 仮想マシンへの関連付け
		DB情報更新
		仮想マシンが起動中の場合はEucalyptusコマンド
	"""

	logger.info('IPアドレス 関連付け 完了')

	return render_to_response('address_list.html',{},context_instance=RequestContext(request))



# インスタンスIDパターン
INSTANCE_ID_PTN=re.compile(r"^i-\w{8}$")
# インスタンスIDパターン(Eucalyptusによる自動付与)
INSTANCE_ID_PTN_AUTO=re.compile(r"^i-\w{8}\s*\(arn:aws:euare::000000000000:user/eucalyptus\)$")

def getAddressList(get_euca_info=None, login_user=None):
	"""IPアドレス一覧を取得する
		input: get_euca_info:euca_access.GetEucalyptusInfo
		input: login_user:ユーザー情報
		return: [address_model.Address_Model]
	"""
	if get_euca_info == None:
		return []

	# インスタンスIDパターン(管理者の場合、取得済み、未使用)
	INSTANCE_ID_PTN_MINE=re.compile(r"^available\s*\(arn:aws:euare::%s:user/%s\)$" % (login_user.account_number, login_user.id) )
	# インスタンスIDパターン(管理者の場合、インスタンスへ取り付け済み)
	INSTANCE_ID_PTN_MINE_USED=re.compile(r"^i-\w{8}\s*\(arn:aws:euare::%s:user/%s\)$" % (login_user.account_number, login_user.id) )

	ipDict = {}
	result = []

	#IPアドレス一覧を取得
	addresslist = get_euca_info.get_addresslist()

	for address in addresslist:
		instance_id = None
		if not address.instance_id:
			#取得済み、未使用
			pass
		elif INSTANCE_ID_PTN.match(address.instance_id):
			#取得済み、インスタンスへ取り付け済み
			instance_id = address.instance_id
		elif address.instance_id == "nobody":
			#誰にも取得されていない(管理者の場合)
			continue
		elif INSTANCE_ID_PTN_AUTO.match(address.instance_id):
			#Eucalyptusが仮想マシンへ自動付与(管理者の場合)
			continue
		elif INSTANCE_ID_PTN_MINE.match(address.instance_id):
			#取得済み、未使用(管理者の場合)
			pass
		elif INSTANCE_ID_PTN_MINE_USED.match(address.instance_id):
			#取得済み、インスタンスへ取り付け済み(管理者の場合)
			instance_id = address.instance_id[0:10]
		else:
			# その他：他ユーザが利用中(管理者の場合)
			# 「available (ユーザID)」、「インスタンスID (ユーザID)」
			continue

		addressData = Address_Model(address.public_ip)
		if instance_id:
			addressData.instance_id = instance_id
		result.append(addressData)
		ipDict[address.public_ip] = addressData

	#仮想マシンとの関連付け情報(DBとマッチング)
	if ipDict:
		machinelist = getMachineNameList(ipDict.keys())
		for ip in machinelist.keys():
			addressData = ipDict[ip]
			addressData.machine_id = machinelist[ip][0]
			addressData.machine_name = machinelist[ip][1]

	#表示用ステータス設定
	for addressData in result:
		if not addressData.machine_id:
			addressData.status = u"未使用"
		elif addressData.instance_id:
			addressData.status = u"使用中（%s）" % addressData.machine_name
		else:
			addressData.status = u"関連付け済仮想マシン停止（%s）" % addressData.machine_name
		#print "(%s, %s, %s,%s, %s)" % (addressData.ip, addressData.status, addressData.instance_id, addressData.machine_id, addressData.machine_name)

	return result


def getMachineNameList(ipList=None):
	"""IPアドレスに関連付けられた仮想マシン一覧を取得する
		input: [IPアドレス]
		return: {IPアドレス:['マシンID',u'マシン名']}
	"""
	if ipList == None:
		return {}

	# 検索クエリーを設定
	queries = [Q(ip=ip) for ip in ipList]
	query = queries.pop()
	for item in queries:
		query |= item

	result = {}
	machinelist = Machine.objects.filter(query)
	for machine in machinelist:
		result[machine.ip] = [machine.id, machine.name]

	return result


