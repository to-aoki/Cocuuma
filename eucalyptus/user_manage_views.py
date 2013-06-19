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

# Create your views here.
#from django.utils.dateparse import parse_datetime
from django.template import RequestContext
from django.utils import dateformat
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from datetime import datetime, timedelta
from django.db import transaction
#from resource_models import Instance_information
from euca_access import GetEucalyptusInfo, GetEucalyptusInfoBy2ool
from euare_access import Euarecmd
from db_access import EucalyptusDB
from db_access_metadata import EucalyptusMetadataDB
from resource_models import *
from monitor_models import Monitorings
from zab_monitor_access import ZabbixAccess
import models
import re
import euca_common
import group_form
import logging
from db_access_metadata import EucalyptusMetadataDB
from server_access import ServerAccess
from models import Policyset
from models import Group


#
logger = logging.getLogger('koalalog')

def filter_ins(raw_list,status,account,node):
	if status != "all":
		filtered_list = []
		for ins in raw_list:
			if ins.status == status:
				filtered_list.append(ins)
		raw_list = filtered_list
	if account != "all":
		filtered_list = []
		for ins in raw_list:
			if ins.account == account:
				filtered_list.append(ins)
		raw_list = filtered_list
	if node != "all":
		filtered_list = []
		for ins in raw_list:
			if ins.node == node and ins.using_resources():
				filtered_list.append(ins)
		raw_list = filtered_list
	return raw_list



#

def sort_user(raw_list,sortname,sortpath,sortgroup,sortacc):
	if sortname=='1':
		return sorted(raw_list,key=lambda x:x['user_id'])
	elif sortname=='2':
		return sorted(raw_list,key=lambda x:x['user_id'], reverse=True)
	if sortpath=='1':
		return sorted(raw_list,key=lambda x:x['user_path'])
	elif sortpath=='2':
		return sorted(raw_list,key=lambda x:x['user_path'], reverse=True)
	if sortgroup=='1':
		return sorted(raw_list,key=lambda x:x['user_group'])
	elif sortgroup=='2':
		return sorted(raw_list,key=lambda x:x['user_group'], reverse=True)
	if sortacc=='1':
		return sorted(raw_list,key=lambda x:x['account_id'])
	elif sortacc=='2':
		return sorted(raw_list,key=lambda x:x['account_id'], reverse=True)
	return raw_list




def user_params(request):
	if 'sortnamehide' in request.POST:
		sortname=request.POST['sortnamehide']
	else:
		sortname = '0'
	if 'sortpathhide' in request.POST:
		sortpath=request.POST['sortpathhide']
	else:
		sortpath = '0'
	if 'sortgrouphide' in request.POST:
		sortgroup=request.POST['sortgrouphide']
	else:
		sortgroup = '0'
	if 'sortacchide' in request.POST:
		sortacc=request.POST['sortacchide']
	else:
		sortacc = '0'
	return sortname, sortpath, sortgroup, sortacc

#


def creategroupform(request):
	"""グループ作成画面へ"""

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('グループ 新規作成フォーム表示開始')

	request.session['account_name'] = login_user.account_id
	account_name = login_user.account_id

	# 入力フォーム
	form = group_form.GroupCreateForm()


	polset_list = []
	#入力フォーム用権限セット一覧取得
	pol_list = Policyset.objects.all()

	logger.info('グループ フォーム デバッグ1')

	for pol in pol_list:
		pols = []
		pols.append(pol.psetname)
		pols.append(pol.psetname)
		polset_list.append(pols)

	logger.info('グループ フォーム デバッグ2')


	form.fields['group_polset'].choices = polset_list
	request.session['ss_vol_polsetlist'] = polset_list

	#form.fields['account_name'] = login_user.account_id

	logger.info('グループ作成フォーム表示')

	return render_to_response('create_group.html',{'account_name':account_name,'form':form,'errors':errors},context_instance=RequestContext(request))




def groupcreate(request):
	"""作成ボタン(ボリューム)"""

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('グループ作成処理 開始')

	# 入力フォーム
	form = group_form.GroupCreateForm(request.POST)
	form.fields['group_polset'].choices = request.session['ss_vol_polsetlist']
	account_name = request.session['account_name']

	logger.debug('グループ作成処理 入力チェック')

	if not form.is_valid():
		tmp_errors = form.errors.values()
		for error in tmp_errors:
			errors.extend(error)

		logger.warn(errors)

		return render_to_response('create_group.html',{'account_name':account_name,'form':form,'errors':errors},context_instance=RequestContext(request))

	logger.debug('グループ作成処理 入力チェック終了')

	#グループ作成(Eucalyptus操作)
	try:
		#Eucalyptus基盤へのアクセサを生成する
		euare_cmd=Euarecmd()

		new_group_id = euare_cmd.create_group(user=login_user, group_name=form.cleaned_data['group_name'], \
group_path=form.cleaned_data['group_path'] )

		logger.debug('グループ作成結果 グループID戻り値 %s' % new_group_id)

	except Exception, ex:
		# Eucalyptusエラー
		errors.append("グループ作成に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		logger.warn(errors)

	logger.debug('ポリシー情報取得')

	select_pol = form.cleaned_data['group_polset']
	logger.debug('ポリシー情報取得2')
	#select_pol = 'EC2操作権限'
	#logger.debug('グループ作成結果 グループID戻り値 %s' % str(select_pol[0]))
	pol = []
	pol = Policyset.objects.filter(psetname = select_pol)
	pol_name = pol[0].pname
	logger.debug('設定ポリシー情報 ポリシー名 %s' % str(pol_name))
	pol_cont = pol[0].pcontent
	logger.debug('設定ポリシー情報 ポリシー内容 %s' % str(pol_cont))


	#グループポリシー作成(euareコマンド操作)
	try:
		new_group_policy = euare_cmd.create_group_policy(user=login_user, group_name=form.cleaned_data['group_name'], \
pol_name=pol_name, pol_cont=pol_cont )

		logger.debug('グループポリシー作成結果 ポリシー名戻り値 %s' % new_group_policy)

	except Exception, ex:
		# Eucalyptusエラー
		errors.append("グループ作成に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		logger.warn(errors)




	logger.info('グループのcooalaDBへの登録')
	#DB登録
	db_group = models.Group()
	db_group.group_id = new_group_id
	db_group.group_name = form.cleaned_data['group_name']
	db_group.group_path = form.cleaned_data['group_path']
	db_group.account_name = login_user.account_id
	db_group.account_id = login_user.account_number
	db_group.group_pol = form.cleaned_data['group_polset']
	db_group.group_desc = form.cleaned_data['group_desc']
	db_group.save()
	logger.debug('グループのcooalaDBへの登録完了')



	#updateVolume(db_volume)

	"""
	グループリスト画面表示
	"""

	euca_db = EucalyptusDB()
	account = login_user.account_number
	#request.session['users'] = euca_db.getEucalyptusUser(account, login_user.id)
	request.session['groups'] = euca_db.group_list2(account)
	#request.session['groups'] = euca_db.getGroupList(account)
	# request.session['users'] = euca_db.getEucalyptusUser()

	group_manage_list = request.session['groups']

	logger.info('グループ管理画面表示')

	return render_to_response('group_manage_view.html',
		{'group_manage_list': group_manage_list},
		context_instance=RequestContext(request))




	#


def user_manage_view(request):

	#メニューを「テンプレート」に設定
	request.session['ss_sys_menu'] = "access_adm"
	request.session['ss_sys_useradm_menu'] = "user_list_view"
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	refresh = True
	if 'resource_refresh' in request.POST and request.POST['resource_refresh'] == 'no':
		refresh = False

	# get data
	if refresh or not 'users' in request.session:
		euca_db = EucalyptusDB()
		account = login_user.account_number
		#request.session['users'] = euca_db.getEucalyptusUser(account, login_user.id)
		request.session['users'] = euca_db.getUserListInAccount(account)
		# request.session['users'] = euca_db.getEucalyptusUser()

	user_manage_list = request.session['users']
	#user_manage_list = sort_user(request.session['users'],sortname,sortpath,sortgroup,sortacc)

	logger.info('ユーザー管理画面表示')

	return render_to_response('user_manage_view.html',
		{'user_manage_list': user_manage_list},
		context_instance=RequestContext(request))



def group_manage_view(request):

	#メニューを設定
	request.session['ss_sys_menu'] = "access_adm"
	request.session['ss_sys_useradm_menu'] = "group_list_view"
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	refresh = True
	if 'resource_refresh' in request.POST and request.POST['resource_refresh'] == 'no':
		refresh = False

	# get data
	if refresh or not 'groups' in request.session:
		euca_db = EucalyptusDB()
		account = login_user.account_number
		group_id = None
		#request.session['users'] = euca_db.getEucalyptusUser(account, login_user.id)
		request.session['groups'] = euca_db.group_list2(group_id,account)
		#request.session['groups'] = euca_db.getGroupList(account)
		# request.session['users'] = euca_db.getEucalyptusUser()

	group_manage_list = request.session['groups']

	logger.info('グループ管理画面表示')

	return render_to_response('group_manage_view.html',
		{'group_manage_list': group_manage_list},
		context_instance=RequestContext(request))



def group_info(request):

	#メニューを設定
	logger.info('グループ詳細画面表示')
	request.session['ss_sys_menu'] = "access_adm"
	request.session['ss_sys_useradm_menu'] = "group_list_view"
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	if 'selected_group' in request.POST:
		selected_group = request.POST['selected_group']
	else:
		selected_group = "all"
	logger.info('グループ詳細画面表示 %s' % str(selected_group))

	refresh = True
	if 'resource_refresh' in request.POST and request.POST['resource_refresh'] == 'no':
		refresh = False

	logger.info('グループ詳細情報取得')
	# get data
	#if refresh or not 'groups' in request.session:
	euca_db = EucalyptusDB()
	account = login_user.account_number
	group_id = selected_group
	request.session['group_user_list'] = euca_db.getGroupUserList(group_id)
	#request.session['selected_group_info'] = euca_db.group_list2(group_id,account)
	request.session['selected_group_info'] = Group.objects.filter(group_id=selected_group)


	logger.info('グループ詳細情報取得完了')

	group_infom = request.session['selected_group_info']
	group_user_list = request.session['group_user_list']

	logger.info('グループ情報画面表示')


	logger.info('グループ詳細画面表示 %s' % str(selected_group))
	logger.info('グループ詳細画面表示 %s' % group_infom[0])
	logger.info('グループ詳細画面表示 %s' % group_user_list)


	return render_to_response('group_info.html',
		{'selected_group':selected_group,
		'group_info': group_infom,
		'group_user_list':group_user_list},
		context_instance=RequestContext(request))



def policy_set_view(request):

	#メニューを設定
	request.session['ss_sys_menu'] = "access_adm"
	request.session['ss_sys_useradm_menu'] = "group_policy_set_view"
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	refresh = True
	if 'resource_refresh' in request.POST and request.POST['resource_refresh'] == 'no':
		refresh = False

	# get data
	if refresh or not 'groups' in request.session:
		request.session['policy_set_list'] = Policyset.objects.all()


	policy_set_list = request.session['policy_set_list']

	return render_to_response('policy_set_view.html',
		{'policy_set_list': policy_set_list},
		context_instance=RequestContext(request))


