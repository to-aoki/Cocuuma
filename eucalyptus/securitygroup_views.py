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

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from euca_access import GetEucalyptusInfo
from securitygroup_model import Securitygroup_Model, Rule_Model
from securitygroup_form import CreateForm, ModifyForm
from models import User
from user_model import User_Model
import euca_common
import logging
import copy

#カスタムログ
logger = logging.getLogger('koalalog')

def top(request):
	"""ファイアウォールメニューの初期表示"""

	logger.info('ファイアウォール 一覧表示')

	#メニューを「ファイアウォール」に設定
	request.session['ss_sys_menu'] = "securitygroup"

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	# セキュリティグループ一覧を取得
	try:
		securitygrouplist = getSecurityGroupList(login_user)
		request.session['ss_scr_securitygrouplist'] = securitygrouplist
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("ファイアウォール一覧取得に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		request.session['ss_scr_securitygrouplist'] = None

	logger.info('ファイアウォール 一覧表示 完了')

	return render_to_response('securitygroup_list.html',{'errors':errors},context_instance=RequestContext(request))


def createform(request):
	"""ファイアウォールを作成ボタン"""

	logger.info('ファイアウォール 作成画面表示')

	#セッションからログインユーザ情報を取得する
	#login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	# 入力フォーム
	form = CreateForm()

	logger.info('ファイアウォール 作成画面表示 完了')

	return render_to_response('securitygroup_create.html',{'form':form,'errors':errors},context_instance=RequestContext(request))


def create(request):
	"""ファイアウォール作成"""

	logger.info('ファイアウォール 作成')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	# 入力フォーム
	form = CreateForm(request.POST)

	# 入力チェック
	if not form.is_valid():
		tmp_errors = form.errors.values()
		for error in tmp_errors:
			errors.extend(error)
		return render_to_response('securitygroup_create.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	#セキュリティグループ作成(Eucalyptus操作)
	try:
		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)

		#セキュリティグループ作成
		security_group = get_euca_info.create_securitygroup(name=form.cleaned_data['name'], description=form.cleaned_data['description'])

		if form.cleaned_data['defaultrule']:
			# 初期ルール設定
			# icmp
			return_code = get_euca_info.authorize_securitygroup(group_name=form.cleaned_data['name'],
								 ip_protocol='icmp', from_port=-1, to_port=-1,
								 cidr_ip='0.0.0.0/0')

			if not return_code:
				errors.append("初期ルールの登録に失敗しました。")

			# ssh
			return_code = get_euca_info.authorize_securitygroup(group_name=form.cleaned_data['name'],
								 ip_protocol='tcp', from_port=22, to_port=22,
								 cidr_ip='0.0.0.0/0')

			if not return_code:
				errors.append("初期ルールの登録に失敗しました。")

	except Exception, ex:
		# Eucalyptusエラー
		errors.append("ファイアウォール作成に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		return render_to_response('securitygroup_create.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	"""
	次画面処理
	"""
	# セキュリティグループ一覧を取得
	try:
		securitygrouplist = getSecurityGroupList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("ファイアウォール一覧取得に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))

	request.session['ss_scr_securitygrouplist'] = securitygrouplist

	logger.info('ファイアウォール 作成 完了')

	return render_to_response('securitygroup_list.html',{'errors':errors},context_instance=RequestContext(request))


def delete(request, groupname):
	"""ファイアウォール削除"""

	logger.info('ファイアウォール 削除')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	#セキュリティグループ削除(Eucalyptus操作)
	try:
		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)

		#セキュリティグループ削除
		security_group = get_euca_info.delete_securitygroup(name=groupname)

	except Exception, ex:
		# Eucalyptusエラー
		errors.append("ファイアウォール削除に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		return render_to_response('securitygroup_list.html',{'errors':errors},context_instance=RequestContext(request))

	"""
	次画面処理
	"""
	# セキュリティグループ一覧を取得
	try:
		securitygrouplist = getSecurityGroupList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("ファイアウォール一覧取得に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))

	request.session['ss_scr_securitygrouplist'] = securitygrouplist

	logger.info('ファイアウォール 削除 完了')

	return render_to_response('securitygroup_list.html',{'errors':errors},context_instance=RequestContext(request))


def modify(request, groupname):
	"""変更ボタン押下"""

	logger.info('ファイアウォール 変更画面表示')

	#セッションからログインユーザ情報を取得する
	#login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	# セッション情報
	securitygrouplist = request.session['ss_scr_securitygrouplist']

	# 変更対象
	target = None
	for group in securitygrouplist:
		if group.name == groupname:
			target = group
			break

	if not target:
		errors.append("選択されたファイアウォールは存在しません。")
		return render_to_response('securitygroup_list.html',{'errors':errors},context_instance=RequestContext(request))

	"""
	次画面処理
	"""

	# セッション情報
	request.session['ss_scr_modify'] = target

	# 入力フォーム
	form = ModifyForm({'addType':'address'})
	#logger.debug(form['addType'].data)

	logger.info('ファイアウォール 変更画面表示 完了')

	return render_to_response('securitygroup_mod.html',{'form':form, 'errors':errors},context_instance=RequestContext(request))


def ruledel(request, rule_num):
	"""接続ルール削除"""

	logger.info('ファイアウォール 接続ルール削除')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	# 入力フォーム
	form = ModifyForm(request.POST)

	# セッション情報
	target = request.session['ss_scr_modify']

	index = int(rule_num)
	if index < len(target.rules):
		del_rule = target.rules[index]
	else:
		errors.append("不正な接続ルールが選択されました。")
		return render_to_response('securitygroup_mod.html',{'form':form, 'errors':errors},context_instance=RequestContext(request))

	#ルール削除(Eucalyptus操作)
	try:
		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)

		#ルール削除
		return_code = get_euca_info.revoke_securitygroup(group_name=target.name, src_security_group_name=del_rule.from_group,
								 src_security_group_owner_id=del_rule.from_user,
								 ip_protocol=del_rule.ip_protocol, from_port=del_rule.from_port, to_port=del_rule.to_port,
								 cidr_ip=del_rule.cidr)

		if not return_code:
			errors.append("接続許可ルール削除に失敗しました。")
			return render_to_response('securitygroup_mod.html',{'form':form, 'errors':errors},context_instance=RequestContext(request))

	except Exception, ex:
		# Eucalyptusエラー
		errors.append("接続許可ルール削除に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		return render_to_response('securitygroup_mod.html',{'form':form, 'errors':errors},context_instance=RequestContext(request))

	"""
	画面再表示用処理
	"""
	groupnames = [ target.name ]

	# セキュリティグループを取得
	try:
		securitygrouplist = getSecurityGroupList(login_user, groupnames)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("ファイアウォール参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))

	target = securitygrouplist[0]
	request.session['ss_scr_modify'] = target

	ss_securitygrouplist = request.session['ss_scr_securitygrouplist']
	for i, group in enumerate(ss_securitygrouplist):
		if group.name == target.name:
			ss_securitygrouplist[i] = target
			request.session.modified = True
			break

	logger.info('ファイアウォール 接続ルール削除 完了')

	return render_to_response('securitygroup_mod.html',{'form':form, 'errors':errors},context_instance=RequestContext(request))


def ruleadd(request):
	"""接続ルール追加"""

	logger.info('ファイアウォール 接続ルール追加')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	# 入力フォーム
	form = ModifyForm(request.POST)

	# セッション情報
	target = request.session['ss_scr_modify']

	# 入力チェック
	if not form.is_valid():
		tmp_errors = form.errors.values()
		for error in tmp_errors:
			errors.extend(error)
		return render_to_response('securitygroup_mod.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	if form.cleaned_data['addType'] == "address":
		# 外部接続
		if not form.cleaned_data['protocol']:
			errors.append("プロトコルを入力してください。")
		if not form.cleaned_data['portMin'] or not form.cleaned_data['portMax']:
			errors.append("解放ポート範囲を入力してください。")
		elif form.cleaned_data['portMin'] > form.cleaned_data['portMax']:
			errors.append("解放ポート範囲が不正です。")
		if not form.cleaned_data['cidr']:
			errors.append("接続許可アドレス範囲を入力してください。")

	elif form.cleaned_data['addType'] == "group":
		# グループ間接続
		if not form.cleaned_data['fromUser']:
			errors.append("接続許可ユーザーを入力してください。")
		if not form.cleaned_data['fromGroup']:
			errors.append("接続許可ファイアウォールを入力してください。")

	if errors:
		return render_to_response('securitygroup_mod.html',{'form':form,'errors':errors},context_instance=RequestContext(request))


	#ルール追加(Eucalyptus操作)
	try:
		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)

		#ルール削除
		return_code = get_euca_info.authorize_securitygroup(group_name=target.name, src_security_group_name=form.cleaned_data['fromGroup'],
								 src_security_group_owner_id=form.cleaned_data['fromUser'],
								 ip_protocol=form.cleaned_data['protocol'], from_port=form.cleaned_data['portMin'],
								 to_port=form.cleaned_data['portMax'], cidr_ip=form.cleaned_data['cidr'])

		if not return_code:
			errors.append("接続許可ルール追加に失敗しました。")
			return render_to_response('securitygroup_mod.html',{'form':form, 'errors':errors},context_instance=RequestContext(request))

	except Exception, ex:
		# Eucalyptusエラー
		errors.append("接続許可ルール追加に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		return render_to_response('securitygroup_mod.html',{'form':form, 'errors':errors},context_instance=RequestContext(request))

	"""
	画面再表示用処理
	"""
	groupnames = [ target.name ]

	# セキュリティグループを取得
	try:
		securitygrouplist = getSecurityGroupList(login_user, groupnames)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("ファイアウォール参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))

	target = securitygrouplist[0]
	request.session['ss_scr_modify'] = target

	ss_securitygrouplist = request.session['ss_scr_securitygrouplist']
	for i, group in enumerate(ss_securitygrouplist):
		if group.name == target.name:
			ss_securitygrouplist[i] = target
			request.session.modified = True
			break

	logger.info('ファイアウォール 接続ルール追加 完了')

	return render_to_response('securitygroup_mod.html',{'form':form, 'errors':errors},context_instance=RequestContext(request))


def getSecurityGroupList(login_user=None, groupnames=None):
	"""ファイアウォール(セキュリティグループ)のリストを取得
		input: login_user:models.User
		return: [securitygroup_model.Securitygroup_Model]
	"""
	if login_user == None:
		return []

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)
	# ファイヤウォール（セキュリティグループ）一覧を取得
	securitygroups = get_euca_info.get_securitygroups(groupnames=groupnames)
	# ファイヤウォール（セキュリティグループ）一覧を選択リストへ設定
	securitygrouplist = []
	for group in securitygroups:
# Eucalyptus3.0では管理者も自アカウントのセキュリティグループのみ取得するので、ID一致によるフィルタ不要
#		if login_user.id == group.owner_id:
			#groupData = Securitygroup_Model(name=group.name, owner_id=group.owner_id, description=group.description)

			owner = getUserFromSecurityGroup(group)
			groupData = Securitygroup_Model(name=group.name, owner_id=owner.name, description=group.description)
			for rule in group.rules:
				ruleBase = Rule_Model(ip_protocol=rule.ip_protocol, from_port=rule.from_port, to_port=rule.to_port)
				for grant in rule.grants:
					ruleData = copy.deepcopy(ruleBase)
					if grant.owner_id or grant.name:
						if grant.owner_id:
							ruleData.from_user = grant.owner_id
						if grant.name:
							ruleData.from_group = grant.name
					else:
						ruleData.cidr = grant.cidr_ip

					groupData.rules.append(ruleData)

			securitygrouplist.append(groupData)

	return securitygrouplist

def getUserFromSecurityGroup(group=None):
	if group == None:
		return None

	try:
		# Eucalyptus3.0 ではGROUPのownerIdにアカウント番号が格納される
		# アカウントまでしか特定できないため、"admin"ユーザー固定で処理する
		db_user_set = User.objects.filter(account_number=group.owner_id, user_id='admin')

		#指定したアカウントの管理者がUserテーブルに存在するか
		if len(db_user_set) != 0:
			#クエリセットから要素を抽出
				db_user = db_user_set[0]
				return User_Model(db_user)
		else:
			return None

	except User.DoesNotExist:
		return None
