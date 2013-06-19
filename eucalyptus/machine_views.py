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

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.db.models import Q
from django.db import transaction
from django.forms.formsets import formset_factory
from django.utils import simplejson, datastructures
from models import Template, VMType, MachineGroup, Machine, Volume
from euca_access import GetEucalyptusInfo
from euca_access import GetEucalyptusInfoBy2ool
import machine_model
from machine_model import MachineGroup_append, Machine_append, NonGroupMachine
from machine_form import GroupIdForm, MachineGroupForm, MachineForm, BaseMachineFormSet1, MachineEditForm, MachineDetailForm
import models
import volume_model
import volume_form
from volume_views import createNewVolume, updateVolume
import re
import time
import traceback
import euca_common
import threading
import logging
import copy
from models import Keypair

from zab_monitor_access import ZabbixAccess
from monitor_models import Monitorings

#カスタムログ
logger = logging.getLogger('koalalog')

# 初期表示
def top(request):
	"""仮想マシンメニューの初期表示"""

	logger.info('仮想マシン 一覧表示')

	#メニューを「仮想マシン」に設定
	request.session['ss_sys_menu'] = "machine"

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#エラー情報
	errors = []

	nonGroupMachines = []
	try:
		#マシングループのリストを取得
		machineGroupList = getMachineGroupList(login_user, nonGroupMachines)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("仮想マシン情報の参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		machineGroupList = []

	request.session['ss_mch_list'] = machineGroupList
	request.session['ss_mch_nongroupmachines'] = nonGroupMachines
	request.session.modified = True

	logger.info('仮想マシン 一覧表示 終了')

	#画面表示
	return render_to_response('machine_list.html',{'errors':errors}, context_instance=RequestContext(request))


def choice(request, group_id):
	"""仮想マシングループ選択時"""

	logger.info('仮想マシン グループ選択')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	request.session['ss_sys_menu'] = "machine"
	request.session.modified = True

	#マシングループのリストを取得
	nonGroupMachines = []
	machineGroupList = getMachineGroupList(login_user, nonGroupMachines)
	request.session['ss_mch_nongroupmachines'] = nonGroupMachines

	gid = int(group_id)
	activeIndex = 0
	# 選択値の確認、リスト内をグループIDで検索
	for i, machineGroup in enumerate(machineGroupList):
		if gid == machineGroup.db.id:
			activeIndex = i
			break

	#選択されたマシングループをアクティブ状態に設定
	activeObj = machineGroupList[activeIndex]
	gid_form = GroupIdForm({'group_id':machineGroupList[activeIndex].db.id})

	logger.info('仮想マシン グループ選択 終了')

	#画面表示
	return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj}, context_instance=RequestContext(request))


def grouprun(request):
	"""仮想マシングループ起動ボタン"""

	logger.info('仮想マシン グループ起動')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)

	# エラーメッセージ
	errors = []

	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
	else:
		"""TODO:エラー処理"""
		return HttpResponseRedirect('/machine/')

	#マシングループのリストを取得
	#machineGroupList = getMachineGroupList(login_user)
	machineGroupList = request.session['ss_mch_list']

	isActive=False
	activeIndex = 0
	# 選択値の確認、リスト内をグループIDで検索
	for i, machineGroup in enumerate(machineGroupList):
		if gid == machineGroup.db.id:
			activeIndex = i
			isActive=True
			break
	else:
		# 一致するIDが存在しない場合はエラーメッセージ表示
		""" TODO: エラーメッセージ表示
		"""
		return HttpResponseRedirect('/machine/')

	#選択されたマシングループをアクティブ状態に設定
	activeObj = machineGroupList[activeIndex]
	gid_form = GroupIdForm({'group_id':machineGroupList[activeIndex].db.id})

	if isActive:
		# 仮想マシン起動
		try:
			result = runMachineGroup(login_user, machineGroupList[activeIndex])
		except Exception, ex:
			# Eucalyptusエラー
			errors = [euca_common.get_euca_error_msg('%s' % ex)]
			return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

		request.session.modified = True

		# 起動結果がNone(正常)ではない場合
		if result:
			errors.append(result)

	logger.info('仮想マシン グループ起動 終了')

	#画面表示
	return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))


def groupterminate(request):
	"""仮想マシングループ停止ボタン"""

	logger.info('仮想マシン グループ停止')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)

	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
	else:
		"""TODO:エラー処理"""
		return HttpResponseRedirect('/machine/')

	#マシングループのリストを取得
	machineGroupList = getMachineGroupList(login_user)
	request.session['ss_mch_list'] = machineGroupList

	isActive=False
	activeIndex = 0
	# 選択値の確認、リスト内をグループIDで検索
	for i, machineGroup in enumerate(machineGroupList):
		if gid == machineGroup.db.id:
			activeIndex = i
			isActive=True
			break
	else:
		# 一致するIDが存在しない場合はエラーメッセージ表示
		""" TODO: エラーメッセージ表示
		"""
		return HttpResponseRedirect('/machine/')

	#選択されたマシングループをアクティブ状態に設定
	activeObj = machineGroupList[activeIndex]
	gid_form = GroupIdForm({'group_id':machineGroupList[activeIndex].db.id})

	if isActive:
		# 仮想マシン停止
		try:
			terminateMachineGroup(login_user, machineGroupList[activeIndex])
			request.session.modified = True
		except Exception, ex:
			# Eucalyptusエラー
			errors = [euca_common.get_euca_error_msg('%s' % ex)]
			return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

	logger.info('仮想マシン グループ停止 終了')

	#画面表示
	return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj}, context_instance=RequestContext(request))


def groupdelete(request):
	"""グループを削除ボタン"""

	logger.info('仮想マシン グループ削除')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)

	# エラーメッセージ
	errors = []

	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
		gid_form = GroupIdForm({'group_id':gid})
	else:
		"""TODO:エラー処理"""
		return HttpResponseRedirect('/machine/')

	#マシングループのリストを取得
	machineGroupList = getMachineGroupList(login_user)
	request.session['ss_mch_list'] = machineGroupList

	isActive=False
	activeIndex = 0
	# 選択値の確認、リスト内をグループIDで検索
	for i, machineGroup in enumerate(machineGroupList):
		if gid == machineGroup.db.id:
			activeIndex = i
			activeObj = machineGroup
			isActive=True
			break
	else:
		# 一致するIDが存在しない場合はエラーメッセージ表示
		""" TODO: エラーメッセージ表示
		"""

	isTerminated = True
	for machine in machineGroupList[activeIndex].machine_list:
		if machine.status != "terminated":
			isTerminated = False
			break

	if not isTerminated:
		errors.append("グループ内の仮想マシンを全て停止してから削除してください。")
		#画面表示
		return render_to_response('machine_list.html',{'machineGroupList':machineGroupList, 'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

	if isActive:

		# マシングループに関連付けられたボリューム削除
		get_euca_info=GetEucalyptusInfo(login_user)

		for mch in machineGroupList[activeIndex].machine_list:

			for vol in mch.volume_list:
				volumes = Volume.objects.filter(volume_id=vol[0])
				for volume in volumes:
					try:
						logger.debug("関連付け済みボリューム %s の削除" % str(volume.volume_id))
						get_euca_info.delete_volume(volume.volume_id)

					except Exception, ex:
						# Eucalyptusエラー
						errors.append("関連付け済みのボリューム削除に失敗しました。")
						errors.append(euca_common.get_euca_error_msg('%s' % ex))

		# マシングループ削除(FKで関連している仮想マシンも削除される)
		machineGroupList[activeIndex].db.delete()

	logger.info('仮想マシン グループ削除 終了')

	#画面表示
	return HttpResponseRedirect('/machine/')


def autorefresh(request):
	"""javascriptタイマーによる状態表示の自動更新"""

	logger.info('仮想マシン 状態表示自動更新')

	if request.is_ajax():
		#AJAXリクエストの場合のみ処理する

		#セッションからログインユーザ情報を取得する
		login_user = request.session['ss_usr_user']

		try:
			#マシングループのリストを取得
			machineGroupList = getMachineGroupList(login_user)
			request.session['ss_mch_list'] = machineGroupList
		except Exception, ex:
			# Eucalyptusエラー
			logger.warn(euca_common.get_euca_error_msg('%s' % ex))

		gid = None
		if request.POST['group_id'] and request.POST['group_id'].isdigit():
			logger.debug( "group_id=%s" % request.POST['group_id'] )
			gid = int(request.POST['group_id'])

		resp = {}
		try:
			for machineGroup in machineGroupList:
				# サブメニュー部分更新情報
				gkey = "gid%d" % machineGroup.db.id
				resp[gkey] = machineGroup.status
				for machine in machineGroup.machine_list:
					mkey = "mid%d" % machine.db.id
					resp[mkey] = machine.status
				if machineGroup.db.id == gid:
					# メイン部分更新情報
					active = {}
					active['status'] = machineGroup.status
					machineInfoList = []
					for machine in machineGroup.machine_list:
						machineInfo = {}
						machineInfo['id'] = machine.db.id
						machineInfo['status'] = machine.status
						machineInfo['displayStatus'] = machine.displayStatus
						machineInfo['displayAddress'] = machine.displayAddress
						machineInfo['displayStartTime'] = machine.displayStartTime
						machineInfoList.append(machineInfo)
					active['machine'] = machineInfoList
					resp['active'] = active
		except:
			print traceback.format_exc()
		#logger.debug( resp )

		logger.info('仮想マシン 状態表示自動更新 終了')

		# JSON形式レスポンスを返却
		#machineGroupListJSON = serializers.serialize("json", machineGroupList)
		#return HttpResponse(simplejson.dumps(dict(is_success=False), ensure_ascii=False), content_type=u'application/json')
		#logger.debug( simplejson.dumps(resp, ensure_ascii=False) )
		return HttpResponse(simplejson.dumps(resp, ensure_ascii=False), content_type=u'application/json')


def refresh(request):
	"""表示更新ボタン"""

	logger.info('仮想マシン 表示更新')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)

	#エラー情報
	errors = []

	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
	else:
		"""TODO:エラー処理"""
		return HttpResponseRedirect('/machine/')

	nonGroupMachines = []
	try:
		#マシングループのリストを取得
		machineGroupList = getMachineGroupList(login_user, nonGroupMachines)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("仮想マシン情報の参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		machineGroupList = []

	request.session['ss_mch_list'] = machineGroupList
	request.session['ss_mch_nongroupmachines'] = nonGroupMachines

	setIndex = 0
	# 選択値の確認、リスト内をグループIDで検索
	for i, machineGroup in enumerate(machineGroupList):
		if gid == machineGroup.db.id:
			setIndex = i
			break

	#選択されたマシングループをアクティブ状態に設定
	activeIndex = setIndex
	if len(machineGroupList) > 0:
		activeObj = machineGroupList[activeIndex]
		gid_form = GroupIdForm({'group_id':machineGroupList[activeIndex].db.id})
	else:
		activeObj=None
		gid_form = GroupIdForm()

	logger.info('仮想マシン 表示更新 終了')

	#画面表示
	return render_to_response('machine_list.html',{'machineGroupList':machineGroupList, 'gid_form':gid_form, 'activeObj':activeObj}, context_instance=RequestContext(request))


def groupcreate(request):
	"""グループを作成ボタン"""

	logger.info('仮想マシン グループ作成')

	#メニューからサーバグループを選択した場合
	if request.session['ss_sys_menu'] != "machine":
		#メニューを「仮想マシン」に設定
		request.session['ss_sys_menu'] = "machine"

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# マシングループフォーム
	group_form = MachineGroupForm()

	#テンプレートのリストを取得
	templateList = getTemplateList(login_user)
	request.session['ss_mch_templateList'] = templateList

	#templateListJSON = serializers.serialize("json", templateList)
	# 追加済みテンプレート数
	request.session['ss_mch_addTemplateLength'] = 0
	# 仮想マシン数
	request.session['ss_mch_machineLength'] = 0

	# 不正な遷移で編集データがセッションに残っていたら削除
	if 'ss_mch_editData' in request.session:
		del request.session['ss_mch_editData']

	#フォームのグループIDをリセット
	gid_form = GroupIdForm()

	logger.info('仮想マシン グループ作成 終了')

	#画面表示
	return render_to_response('machine_group_create_1.html',{'gid_form':gid_form, 'group_form':group_form}, context_instance=RequestContext(request))


def groupupdate(request):
	"""変更ボタン"""

	logger.info('仮想マシン グループ編集')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)

	# エラーメッセージ
	errors = []

	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
		gid_form = GroupIdForm({'group_id':gid})
	else:
		"""TODO:エラー処理"""
		return HttpResponseRedirect('/machine/')

	#マシングループのリストを取得
	machineGroupList = getMachineGroupList(login_user)
	request.session['ss_mch_list'] = machineGroupList

	activeIndex = 0
	# 選択値の確認、リスト内をグループIDで検索
	for i, machineGroup in enumerate(machineGroupList):
		if gid == machineGroup.db.id:
			activeIndex = i
			activeObj = machineGroup
			break
	else:
		# 一致するIDが存在しない場合はエラーメッセージ表示
		""" TODO: エラーメッセージ表示
		"""
		return HttpResponseRedirect('/machine/')

	isTerminated = True
	for machine in machineGroupList[activeIndex].machine_list:
		if machine.status != "terminated":
			isTerminated = False
			break

	if not isTerminated:
		errors.append("グループ内の仮想マシンを全て停止してから編集してください。")
		#画面表示
		return render_to_response('machine_list.html',{'machineGroupList':machineGroupList, 'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

	# マシングループフォーム
	#group_form = MachineGroupForm(instance=machineGroupList[activeIndex].db)

	#テンプレートのリストを取得
	templateList = getTemplateList(login_user)
	request.session['ss_mch_templateList'] = templateList

	"""
	セッションデータ復元
	"""
	# 編集データ
	editGroupData = machine_model.createEditGroupData()

	# マシングループ
	editGroupData.group_id = machineGroupList[activeIndex].db.id
	editGroupData.name = machineGroupList[activeIndex].db.name
	editGroupData.description = machineGroupList[activeIndex].db.description
	# 追加済みテンプレート,マシン
	addTemplateCount = 0
	for machine in machineGroupList[activeIndex].machine_list:
		if not addTemplateCount:
			# テンプレート
			for template in templateList:
				if template.id == machine.db.template_id:
					templatedData = editGroupData.template_base.copy()
					templatedData['template_id'] = template.id
					templatedData['template_name'] = template.name
					templatedData['count'] = template.count
					editGroupData.template_list.append(templatedData)
					addTemplateCount = template.count
					break

		# マシン
		machineData = editGroupData.machine_base.copy()
		machineData['name'] = machine.db.name					#マシン名
		machineData['image_id'] = machine.db.image_id			#イメージID
		machineData['vmtype'] = machine.db.vmtype				#VMType
		if machine.volume_list:
			machineData['volume'] = machine.volume_list[0][0]		#ボリューム
		machineData['ip'] = machine.db.ip						#IPアドレス
		machineData['template_id'] = machine.db.template_id		#テンプレートID
		machineData['order'] = machine.db.order					#表示順
		machineData['keypair'] = machine.db.keypair						#キーペア名
		machineData['security_group'] = machine.db.security_group		#セキュリティグループ名
		machineData['avaulability_zone'] = machine.db.avaulability_zone	#AvaulabilityZone
		machineData['user_data'] = machine.db.user_data					#ユーザーデータ
		editGroupData.machine_list.append(machineData)

		addTemplateCount -= 1

	request.session['ss_mch_editData'] = editGroupData

	# 追加済みテンプレート数
	request.session['ss_mch_addTemplateLength'] = len(editGroupData.template_list)
	# 仮想マシン数
	request.session['ss_mch_machineLength'] = len(editGroupData.machine_list)

	"""
	マシングループ、選択済みテンプレート、マシン名フォーム復元
	"""
	# マシングループフォーム
	group_form = MachineGroupForm({'name':editGroupData.name, 'description':editGroupData.description})

	# 追加済みテンプレート
	formsetList = []
	MachineFormSet1 = formset_factory(MachineForm, formset=BaseMachineFormSet1, extra=0)
	machineIndex = 0
	for cnt, templatedData in enumerate(editGroupData.template_list):
		initial = []
		count = int(templatedData['count'])
		for i in xrange(0, count):
			if machineIndex < len(editGroupData.machine_list):
				machineData = editGroupData.machine_list[machineIndex]
				initdic = machineData.copy()
				initdic['template_name'] = templatedData['template_name']
				initial.append(initdic)
				machineIndex += 1

		prefix = "form%d" % cnt
		old_formset = MachineFormSet1(initial=initial, prefix=prefix)
		formsetList.append(old_formset)

	logger.info('仮想マシン グループ編集 終了')

	#画面表示
	return render_to_response('machine_group_create_1.html',{'gid_form':gid_form, 'group_form':group_form, 'formsetList':formsetList}, context_instance=RequestContext(request))



def addTemplate(request):
	"""「1.テンプレート選択」のテンプレート追加ボタン"""

	logger.info('仮想マシン 1.テンプレート選択 テンプレート追加')

	#セッションからログインユーザ情報を取得する
	#login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)

	# マシングループフォーム
	group_form = MachineGroupForm(request.POST)

	#セッションからテンプレートのリストを取得
	templateList = request.session['ss_mch_templateList']

	#選択されたテンプレート
	selectedTemplate = request.POST['template_select']
	if not selectedTemplate:
		"""TODO:エラー処理"""
		return render_to_response('machine_group_create_1.html',{'gid_form':gid_form, 'group_form':group_form}, context_instance=RequestContext(request))

	targetTemplate=None
	pk = int(selectedTemplate)
	for template in templateList:
		if pk == template.pk:
			targetTemplate = template
			break
	else:
		"""TODO:エラー処理"""
		return render_to_response('machine_group_create_1.html',{'gid_form':gid_form, 'group_form':group_form}, context_instance=RequestContext(request))

	formsetList = []
	# 追加済みテンプレート
	MachineFormSet1 = formset_factory(MachineForm, formset=BaseMachineFormSet1, extra=0)
	addTemplateLength = int(request.session['ss_mch_addTemplateLength'])
	for cnt in xrange(0, addTemplateLength):
		prefix = "form%d" % cnt
		old_formset = MachineFormSet1(request.POST, prefix=prefix)
		formsetList.append(old_formset)

	#表示順
	machineLength = int(request.session['ss_mch_machineLength'])

	#追加されたテンプレート
	newMachineList = []
	for cnt in xrange(0, targetTemplate.count):
		data = {
			'template_name': targetTemplate.name,
			'image_id': targetTemplate.image_id,
			'vmtype': targetTemplate.vmtype,
			'template_id': targetTemplate.id,
			'order': machineLength + cnt }
		newMachineList.append(data)

	prefix = "form%d" % addTemplateLength
	formset = MachineFormSet1(initial=newMachineList, prefix=prefix)
	formsetList.append(formset)

	# 追加済みテンプレート数
	request.session['ss_mch_addTemplateLength'] = addTemplateLength + 1
	# 仮想マシン数
	request.session['ss_mch_machineLength'] = machineLength + targetTemplate.count

	logger.info('仮想マシン 1.テンプレート選択 テンプレート追加 終了')

	#画面表示
	return render_to_response('machine_group_create_1.html',{'gid_form':gid_form, 'group_form':group_form, 'formsetList':formsetList}, context_instance=RequestContext(request))


def step1end(request):
	"""「1.テンプレート選択」の次へボタン"""

	logger.info('仮想マシン 1.テンプレート選択 次へ')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)
	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
		gid_form = GroupIdForm({'group_id':gid})

	"""
	入力情報
	"""
	# マシングループフォーム
	group_form = MachineGroupForm(request.POST)

	formsetList = []
	# 追加済みテンプレート,マシン名
	MachineFormSet1 = formset_factory(MachineForm, formset=BaseMachineFormSet1, extra=0)
	addTemplateLength = int(request.session['ss_mch_addTemplateLength'])
	for cnt in xrange(0, addTemplateLength):
		prefix = "form%d" % cnt
		old_formset = MachineFormSet1(request.POST, prefix=prefix)
		formsetList.append(old_formset)

	#表示順
	#machineLength = int(request.session['ss_mch_machineLength'])

	"""
	入力情報のバリデーション
	"""
	errors = []
	if not group_form.is_valid():
		tmp_errors = group_form.errors.values()
		for error in tmp_errors:
			errors.extend(error)
		#errors.extend(group_form.non_field_errors.values())

	if not addTemplateLength:
		#テンプレートが1個も追加されていない
		""" TODO: メッセージプロパティ"""
		errors.append(u"テンプレートを1個以上追加してください。")

	for formset in formsetList:
		if not formset.is_valid():
			tmp_errorList = formset.errors
			for tmp_errorDic in tmp_errorList:
				tmp_errors = tmp_errorDic.values()
				for error in tmp_errors:
					errors.extend(error)

	if errors:
		return render_to_response('machine_group_create_1.html',{'gid_form':gid_form, 'group_form':group_form, 'formsetList':formsetList, 'errors':errors}, context_instance=RequestContext(request))

	"""
	入力情報をセッションへ保存
	"""
	newFlag = False
	if not 'ss_mch_editData' in request.session or not request.session['ss_mch_editData']:

		newFlag = True
		#新規作成の場合
		editGroupData = machine_model.createEditGroupData()
		# マシングループフォーム
		editGroupData.name = group_form.cleaned_data['name']
		editGroupData.description = group_form.cleaned_data['description']
		# 追加済みテンプレート,マシン
		for formset in formsetList:
			# テンプレート
			templatedData = editGroupData.template_base.copy()
			templatedData['template_id'] = formset.forms[0].cleaned_data['template_id']
			templatedData['template_name'] = formset.forms[0].cleaned_data['template_name']
			templatedData['count'] = formset.total_form_count()
			editGroupData.template_list.append(templatedData)
			for form in formset:
				# マシン
				machineData = editGroupData.machine_base.copy()
				machineData['name'] = form.cleaned_data['name']					#マシン名
				machineData['image_id'] = form.cleaned_data['image_id']			#イメージID
				machineData['vmtype'] = form.cleaned_data['vmtype']				#VMType
				machineData['template_id'] = form.cleaned_data['template_id']	#テンプレートID
				machineData['order'] = form.cleaned_data['order']				#表示順
				editGroupData.machine_list.append(machineData)

		request.session['ss_mch_editData'] = editGroupData

	else:
		# 更新や戻るボタン遷移の場合
		editGroupData = request.session['ss_mch_editData']
		# マシングループフォーム
		editGroupData.name = group_form.cleaned_data['name']
		editGroupData.description = group_form.cleaned_data['description']
		machineLen = 0
		# 追加済みテンプレート,マシン
		for i, formset in enumerate(formsetList):
			# テンプレート
			if i < len(editGroupData.template_list):
				oldTemplatedData = editGroupData.template_list[i]
				if oldTemplatedData['template_id'] == formset.forms[0].cleaned_data['template_id']:
					# マシン名変更の場合
					for form in formset:
						# マシン
						machineData = editGroupData.machine_list[machineLen]
						machineData['name'] = form.cleaned_data['name']					#マシン名
						machineLen += 1
				else:
					# テンプレートが削除されている場合
					""" TODO: テンプレート削除時の処理 """
			else:
				# テンプレートが追加されている場合
				templatedData = editGroupData.template_base.copy()
				templatedData['template_id'] = formset.forms[0].cleaned_data['template_id']
				templatedData['template_name'] = formset.forms[0].cleaned_data['template_name']
				templatedData['count'] = formset.total_form_count()
				editGroupData.template_list.append(templatedData)
				for form in formset:
					# マシン
					machineData = editGroupData.machine_base.copy()
					machineData['name'] = form.cleaned_data['name']					#マシン名
					machineData['image_id'] = form.cleaned_data['image_id']			#イメージID
					machineData['vmtype'] = form.cleaned_data['vmtype']				#VMType
					machineData['template_id'] = form.cleaned_data['template_id']	#テンプレートID
					machineData['order'] = form.cleaned_data['order']				#表示順
					editGroupData.machine_list.append(machineData)
					machineLen += 1

		request.session.modified = True


	"""
	次画面用情報の設定
	"""
	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)
	try:
		# IPアドレスの一覧を取得
		addresslist = getAddressList(get_euca_info, login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("IPアドレス情報の参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		addresslist = []

	""" TODO:他のマシンでの利用状況をマージ
	"""
	request.session['ss_mch_addresslist'] = addresslist

	# VMType
	vmtypelist = getSelectListVMType()
	request.session['ss_mch_vmtypelist'] = vmtypelist

	vmdict = dict((vmtype[0], vmtype[1]) for vmtype in vmtypelist)
	for machineData in editGroupData.machine_list:
		machineData['vmtype_disp'] = vmdict[machineData['vmtype']]			#VMType表示名

	try:
		# ボリュームの一覧を取得
		volumelist = getVolumeList(get_euca_info, login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("ボリューム情報の参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		volumelist = []

	""" TODO:他のマシンでの利用状況をマージ
	"""
	request.session['ss_mch_volumelist'] = volumelist

	# 編集対象のマシン
	machineIndex = 0
	request.session['ss_mch_machineIndex'] = machineIndex
	
	#try:
	#	# キーペア一覧を取得
	#	keypairs = get_euca_info.get_keypairs()
	#	# キーペア一覧を選択リストへ設定
	#	keypairs_value = []
	#	for keypair in keypairs:
	#		if Keypair.objects.filter(user_id=login_user.id,account_id=login_user.account_id,name=keypair.name):
	#			sub_keypair = []
	#			sub_keypair.append(keypair.name)
	#			sub_keypair.append(keypair.name)
	#			keypairs_value.append(sub_keypair)
	#	keypairlist = tuple(sorted(keypairs_value))
	#except Exception, ex:
	#	# Eucalyptusエラー
	#	errors.append("仮想マシン接続鍵情報の参照に失敗しました。")
	#	errors.append(euca_common.get_euca_error_msg('%s' % ex))

	#keypairlist = Keypair.objects.filter(user_id=login_user.id,account_id=login_user.account_id)

	#入力フォーム
	form = MachineEditForm(data=editGroupData.machine_list[machineIndex])
	form.fields['ip'].choices = addresslist
	form.fields['vmtype'].choices = vmtypelist
	form.fields['volume'].choices = volumelist
	#form.set_keypair(keypairlist[0].name)
	
	#form.fields['keypair'].choices = keypairlist
	#request.session['ss_mch_keypairlist'] = keypairlist

	#Availablity Zone取得
	try:
		zones = get_euca_info.get_availabilityzones()
		# Availability Zone一覧を選択リストへ設定
		zones_value = []
		for zone in zones:
			sub_zone = []
			sub_zone.append(zone.name)
			sub_zone.append(zone.name)
			zones_value.append(sub_zone)
		avaulabilityzonelist = tuple(zones_value)
		form.fields['avaulability_zone'].choices = avaulabilityzonelist
		request.session['ss_mch_avaulabilityzonelist'] = avaulabilityzonelist
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("Availability Zone情報の参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))

	request.session['ss_mch_volumezonelist'] = avaulabilityzonelist
	form.fields['volume_zone'].choices = avaulabilityzonelist

	machineData = editGroupData.machine_list[machineIndex]
	if newFlag or machineData['volume'] != 'new':
		form.fields['volume_size'].widget.attrs['disabled']=True
		form.fields['volume_zone'].widget.attrs['disabled']=True

	#logger.debug( editGroupData.machine_list[machineIndex] )
	#logger.debug( form.fields.get('ip').initial )
	#print form

	#詳細設定
	detail_form = MachineDetailForm()

	logger.info('仮想マシン 1.テンプレート選択 次へ 終了')

	#画面表示
	return render_to_response('machine_group_create_2.html',{'gid_form':gid_form, 'form':form, 'detail_form':detail_form, 'errors':errors}, context_instance=RequestContext(request))


def step2select(request, order):
	"""「2.仮想マシン設定」のマシン選択ボタン"""

	logger.info('仮想マシン 2.仮想マシン設定 マシン選択')

	#セッションからログインユーザ情報を取得する
	#login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)
	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
		gid_form = GroupIdForm({'group_id':gid})

	#入力情報を取得
	form = MachineEditForm(request.POST)
	form.fields['ip'].choices = request.session['ss_mch_addresslist']
	form.fields['vmtype'].choices = request.session['ss_mch_vmtypelist']
	form.fields['volume'].choices = request.session['ss_mch_volumelist']
	form.fields['volume_zone'].choices = request.session['ss_mch_volumezonelist']

	if 'ss_mch_keypairlist' in request.session:
		form.fields['keypair'].choices = request.session['ss_mch_keypairlist']
	if 'ss_mch_securitygrouplist' in request.session:
		form.fields['security_group'].choices = request.session['ss_mch_securitygrouplist']
	if 'ss_mch_avaulabilityzonelist' in request.session:
		form.fields['avaulability_zone'].choices = request.session['ss_mch_avaulabilityzonelist']

	detail_form = MachineDetailForm(request.POST)

	"""
	入力情報のバリデーション
	"""
	errors = []
	if not form.is_valid():
		tmp_errors = form.errors.values()
		for error in tmp_errors:
			errors.extend(error)
		return render_to_response('machine_group_create_2.html',{'gid_form':gid_form, 'form':form, 'errors':errors, 'detail_form':detail_form}, context_instance=RequestContext(request))

	if form.cleaned_data['volume'] == 'new':
		if not form.cleaned_data['volume_size']:
			errors.append(u"データボリューム：作成サイズを入力してください。")
			logger.warn("データボリューム：作成サイズを入力してください。")
			return render_to_response('machine_group_create_2.html',{'gid_form':gid_form, 'form':form, 'errors':errors, 'detail_form':detail_form}, context_instance=RequestContext(request))


	vmtypelist = request.session['ss_mch_vmtypelist']
	vmdict = dict((vmtype[0], vmtype[1]) for vmtype in vmtypelist)
	volumelist = request.session['ss_mch_volumelist']
	voldict = dict((volume[0], volume[1]) for volume in volumelist)

	"""
	入力情報をセッションへ保存
	"""
	editGroupData = request.session['ss_mch_editData']
	oldOrder = int(form.cleaned_data['order'])
	machineData = editGroupData.machine_list[oldOrder]
	machineData['ip'] = form.cleaned_data['ip']										#IPアドレス
	machineData['vmtype'] = form.cleaned_data['vmtype']								#VMType
	machineData['vmtype_disp'] = vmdict[machineData['vmtype']]						#VMType表示名
	machineData['volume'] = form.cleaned_data['volume']								#データボリューム
	machineData['volume_disp'] = voldict[machineData['volume']]						#データボリューム表示名

	# EBSボリューム新規作成情報
	if machineData['volume'] == 'new':
		machineData['volume_size'] = form.cleaned_data['volume_size']
		machineData['volume_zone'] = form.cleaned_data['volume_zone']
		machineData['volume_disp'] = unicode(machineData['volume_disp']) + u'　（サイズ：' + unicode(machineData['volume_size']) + u'[GB] Availavility Zone：' + unicode(machineData['volume_zone']) + u'）'


	# 詳細表示項目
	if form.cleaned_data['keypair']:
		machineData['keypair'] = form.cleaned_data['keypair']						#キーペア名
	else:
		login_user = request.session['ss_usr_user']
		keypairlist = Keypair.objects.filter(user_id=login_user.id,account_id=login_user.account_id)
		machineData['keypair'] = keypairlist[0].name
	if form.cleaned_data['security_group']:
		machineData['security_group'] = form.cleaned_data['security_group']			#セキュリティグループ名
	if form.cleaned_data['avaulability_zone']:
		machineData['avaulability_zone'] = form.cleaned_data['avaulability_zone']	#AvaulabilityZone
	if form.cleaned_data['user_data']:
		machineData['user_data'] = form.cleaned_data['user_data']					#ユーザーデータ
	request.session.modified = True

	"""
	次画面用情報の設定
	"""
	newOder = int(order)
	if newOder >= len(editGroupData.machine_list):
		"""TODO:エラー処理"""
		errors.extend(u"不正な仮想マシンが選択されました。")
		return render_to_response('machine_group_create_2.html',{'gid_form':gid_form, 'form':form, 'errors':errors, 'detail_form':detail_form}, context_instance=RequestContext(request))

	# 編集対象のマシン
	machineIndex = newOder
	request.session['ss_mch_machineIndex'] = machineIndex

	#入力フォーム
	form = MachineEditForm(data=editGroupData.machine_list[machineIndex])
	form.fields['ip'].choices = request.session['ss_mch_addresslist']
	form.fields['vmtype'].choices = request.session['ss_mch_vmtypelist']
	form.fields['volume'].choices = request.session['ss_mch_volumelist']
	form.fields['volume_zone'].choices = request.session['ss_mch_volumezonelist']

	machineData = editGroupData.machine_list[machineIndex]
	if machineData['volume'] != 'new':
		form.fields['volume_size'].widget.attrs['disabled']=True
		form.fields['volume_zone'].widget.attrs['disabled']=True

	#詳細設定
	detail_form = MachineDetailForm()

	logger.info('仮想マシン 2.仮想マシン設定 マシン選択 終了')

	#画面表示
	return render_to_response('machine_group_create_2.html',{'gid_form':gid_form, 'form':form, 'detail_form':detail_form}, context_instance=RequestContext(request))


def step1back(request):
	"""「2.仮想マシン設定」の戻るボタン"""

	logger.info('仮想マシン 2.仮想マシン設定 戻る')

	#セッションからログインユーザ情報を取得する
	#login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)
	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
		gid_form = GroupIdForm({'group_id':gid})

	editGroupData = request.session['ss_mch_editData']

	"""
	マシングループ、選択済みテンプレート、マシン名復元
	"""
	# マシングループフォーム
	group_form = MachineGroupForm({'name':editGroupData.name, 'description':editGroupData.description})

	# 追加済みテンプレート
	formsetList = []
	MachineFormSet1 = formset_factory(MachineForm, formset=BaseMachineFormSet1, extra=0)
	machineIndex = 0
	for cnt, templatedData in enumerate(editGroupData.template_list):
		initial = []
		count = int(templatedData['count'])
		for i in xrange(0, count):
			if machineIndex < len(editGroupData.machine_list):
				machineData = editGroupData.machine_list[machineIndex]
				initdic = machineData.copy()
				if initdic['template_id'] == templatedData['template_id']:
					initdic['template_name'] = templatedData['template_name']
					initial.append(initdic)
					machineIndex += 1
				else:
					break
			else:
				break

		prefix = "form%d" % cnt
		old_formset = MachineFormSet1(initial=initial, prefix=prefix)
		formsetList.append(old_formset)

	logger.info('仮想マシン 2.仮想マシン設定 戻る 終了')

	#画面表示
	return render_to_response('machine_group_create_1.html',{'gid_form':gid_form, 'group_form':group_form, 'formsetList':formsetList}, context_instance=RequestContext(request))


def getip(request):
	"""「2.仮想マシン設定」のIPアドレスを取得ボタン"""

	logger.info('仮想マシン 2.仮想マシン設定 IPアドレスを取得')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)
	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
		gid_form = GroupIdForm({'group_id':gid})

	#エラー情報
	errors = []

	#現在の入力情報を保存
	form = MachineEditForm(request.POST)
	form.fields['ip'].choices = request.session['ss_mch_addresslist']
	form.fields['vmtype'].choices = request.session['ss_mch_vmtypelist']
	form.fields['volume'].choices = request.session['ss_mch_volumelist']
	form.fields['volume_zone'].choices = request.session['ss_mch_volumezonelist']

	if 'ss_mch_keypairlist' in request.session:
		form.fields['keypair'].choices = request.session['ss_mch_keypairlist']
	if 'ss_mch_securitygrouplist' in request.session:
		form.fields['security_group'].choices = request.session['ss_mch_securitygrouplist']
	if 'ss_mch_avaulabilityzonelist' in request.session:
		form.fields['avaulability_zone'].choices = request.session['ss_mch_avaulabilityzonelist']

	detail_form = MachineDetailForm(request.POST)

	"""
	IPアドレスを取得
	"""
	try:
		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)
		# リソース制限チェック
		nowip = euca_common.countAllocatedAddress(login_user)
		if nowip >= login_user.db_user.maxip :
			# リソース制限エラー
			errors = ["IPアドレスはこれ以上取得できません。"]
			return render_to_response('machine_group_create_2.html',{'gid_form':gid_form, 'form':form, 'detail_form':detail_form, 'errors':errors}, context_instance=RequestContext(request))


		# IPアドレスを取得
		newaddress = get_euca_info.allocate_address()
		adrs_val = (newaddress.public_ip, newaddress.public_ip)

		#IPアドレス一覧へ追加
		addresstuple = request.session['ss_mch_addresslist']
		addresslist = list(addresstuple)
		addresslist.append(adrs_val)
		newlist = tuple(addresslist)

		request.session['ss_mch_addresslist'] = newlist
		form.fields['ip'].choices = newlist

	except Exception, ex:
	# Eucalyptusエラー
		errors.append(euca_common.get_euca_error_msg('%s' % ex))

	logger.info('仮想マシン 2.仮想マシン設定 IPアドレスを取得 終了')

	#画面表示
	return render_to_response('machine_group_create_2.html',{'gid_form':gid_form, 'form':form, 'detail_form':detail_form, 'errors':errors}, context_instance=RequestContext(request))


def step2detail(request):
	"""「2.仮想マシン設定」の詳細設定ボタン"""

	logger.info('仮想マシン 2.仮想マシン設定 詳細設定')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)
	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
		gid_form = GroupIdForm({'group_id':gid})

	#エラー情報
	errors = []

	#
	# 現在の入力情報と詳細設定項目の初期値をマージしてフォームに保存
	#
	# マージ辞書を作成
	editGroupData = request.session['ss_mch_editData']
	order = int(request.POST['order'])
	machineData = editGroupData.machine_list[order]
	#tmp_data = copy.deepcopy(machineData)
	tmp_data = datastructures.MultiValueDict()
	tmp_data.update(machineData)
	tmp_data.update(request.POST)
	#logger.debug(tmp_data)
	# フォームに保存
	form = MachineEditForm(tmp_data)
	#form = MachineEditForm(request.POST)
	# セレクトメニューのリスト
	form.fields['ip'].choices = request.session['ss_mch_addresslist']
	form.fields['vmtype'].choices = request.session['ss_mch_vmtypelist']
	form.fields['volume'].choices = request.session['ss_mch_volumelist']
	form.fields['volume_zone'].choices = request.session['ss_mch_volumezonelist']

	detail_form = MachineDetailForm(request.POST)
	if detail_form.is_valid():
		detail_form = MachineDetailForm()

	else:

		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)

		try:
			# キーペア一覧を取得
			keypairs = get_euca_info.get_keypairs()
			# キーペア一覧を選択リストへ設定
			keypairs_value = []
			for keypair in keypairs:
				if Keypair.objects.filter(user_id=login_user.id,account_id=login_user.account_id,name=keypair.name):
					sub_keypair = []
					sub_keypair.append(keypair.name)
					sub_keypair.append(keypair.name)
					keypairs_value.append(sub_keypair)
			keypairlist = tuple(sorted(keypairs_value))
			form.fields['keypair'].choices = keypairlist
			request.session['ss_mch_keypairlist'] = keypairlist
		except Exception, ex:
			# Eucalyptusエラー
			errors.append("仮想マシン接続鍵情報の参照に失敗しました。")
			errors.append(euca_common.get_euca_error_msg('%s' % ex))

		try:
			# ファイアウォール（セキュリティグループ）一覧を取得
			securitygroups = get_euca_info.get_securitygroups()
			# ファイアウォール（セキュリティグループ）一覧を選択リストへ設定
			securitygroups_value = []
			for securitygroup in securitygroups:
				if login_user.account_number == securitygroup.owner_id:
					sub_securitygroup = []
					sub_securitygroup.append(securitygroup.name)
					sub_securitygroup.append(securitygroup.name)
					securitygroups_value.append(sub_securitygroup)
			securitygrouplist = tuple(sorted(securitygroups_value))
			form.fields['security_group'].choices = securitygrouplist
			request.session['ss_mch_securitygrouplist'] = securitygrouplist
		except Exception, ex:
			# Eucalyptusエラー
			errors.append("ファイアウォール情報の参照に失敗しました。")
			errors.append(euca_common.get_euca_error_msg('%s' % ex))

		try:
			# Availability Zone一覧を取得
			zones = get_euca_info.get_availabilityzones()
			# Availability Zone一覧を選択リストへ設定
			zones_value = [["", u"指定しない"]]
			for zone in zones:
				sub_zone = []
				sub_zone.append(zone.name)
				sub_zone.append(zone.name)
				zones_value.append(sub_zone)
			avaulabilityzonelist = tuple(zones_value)
			form.fields['avaulability_zone'].choices = avaulabilityzonelist
			request.session['ss_mch_avaulabilityzonelist'] = avaulabilityzonelist
		except Exception, ex:
			# Eucalyptusエラー
			errors.append("Availability Zone情報の参照に失敗しました。")
			errors.append(euca_common.get_euca_error_msg('%s' % ex))

		detail_form = MachineDetailForm({'detail':True})

	#logger.debug( dir(form.fields.get('keypair')) )

	logger.info('仮想マシン 2.仮想マシン設定 詳細設定 終了')

	#画面表示
	return render_to_response('machine_group_create_2.html',{'gid_form':gid_form, 'form':form, 'detail_form':detail_form, 'errors':errors}, context_instance=RequestContext(request))


def step2end(request):
	"""「2.仮想マシン設定」の次へボタン"""

	logger.info('仮想マシン 2.仮想マシン設定 次へ')

	#エラー情報
	errors = []

	#セッションからログインユーザ情報を取得する
	#login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)
	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
		gid_form = GroupIdForm({'group_id':gid})

	#入力情報を取得
	form = MachineEditForm(request.POST)
	form.fields['ip'].choices = request.session['ss_mch_addresslist']
	form.fields['vmtype'].choices = request.session['ss_mch_vmtypelist']
	form.fields['volume'].choices = request.session['ss_mch_volumelist']
	form.fields['volume_zone'].choices = request.session['ss_mch_volumezonelist']

	if 'ss_mch_keypairlist' in request.session:
		form.fields['keypair'].choices = request.session['ss_mch_keypairlist']
	if 'ss_mch_securitygrouplist' in request.session:
		form.fields['security_group'].choices = request.session['ss_mch_securitygrouplist']
	if 'ss_mch_avaulabilityzonelist' in request.session:
		form.fields['avaulability_zone'].choices = request.session['ss_mch_avaulabilityzonelist']

	detail_form = MachineDetailForm(request.POST)

	vmtypelist = request.session['ss_mch_vmtypelist']
	vmdict = dict((vmtype[0], vmtype[1]) for vmtype in vmtypelist)
	volumelist = request.session['ss_mch_volumelist']
	voldict = dict((volume[0], volume[1]) for volume in volumelist)

	"""
	入力情報のバリデーション
	"""
	if not form.is_valid():
		tmp_errors = form.errors.values()
		for error in tmp_errors:
			errors.extend(error)
		return render_to_response('machine_group_create_2.html',{'gid_form':gid_form, 'form':form, 'errors':errors, 'detail_form':detail_form}, context_instance=RequestContext(request))

	if form.cleaned_data['volume'] == 'new':
		if not form.cleaned_data['volume_size']:
			errors.append(u"データボリューム：作成サイズを入力してください。")
			logger.warn("データボリューム：作成サイズを入力してください。")
			return render_to_response('machine_group_create_2.html',{'gid_form':gid_form, 'form':form, 'errors':errors, 'detail_form':detail_form}, context_instance=RequestContext(request))

	"""
	入力情報をセッションへ保存
	"""
	editGroupData = request.session['ss_mch_editData']
	order = int(form.cleaned_data['order'])
	machineData = editGroupData.machine_list[order]
	machineData['ip'] = form.cleaned_data['ip']										#IPアドレス
	machineData['vmtype'] = form.cleaned_data['vmtype']								#VMType
	machineData['vmtype_disp'] = vmdict[machineData['vmtype']]						#VMType表示名
	machineData['volume'] = form.cleaned_data['volume']								#データボリューム
	machineData['volume_disp'] = voldict[machineData['volume']]						#データボリューム表示名

	# EBSボリューム新規作成情報
	if machineData['volume'] == 'new':
		machineData['volume_size'] = int(form.cleaned_data['volume_size'])			#ボリュームサイズ
		machineData['volume_zone'] = form.cleaned_data['volume_zone']				#ボリュームサイズ
		machineData['volume_disp'] = unicode(machineData['volume_disp']) + u'　（サイズ：' + unicode(machineData['volume_size']) + u'[GB] Availavility Zone：' + unicode(machineData['volume_zone']) + u'）'

	for i in range(len(editGroupData.machine_list)-1):

		mch_0 = editGroupData.machine_list[i]
		mch_1 = editGroupData.machine_list[i+1]

		if (mch_0['volume'] == mch_1['volume']) and (mch_0['volume'] != '') and (mch_0['volume'] != 'new'):
			errors.append(u"データボリューム："+ mch_0['volume']+ u" を複数のサーバに関連付けることはできません。" )
			logger.warn("データボリューム関連付けエラー" )
			return render_to_response('machine_group_create_2.html',{'gid_form':gid_form, 'form':form, 'errors':errors, 'detail_form':detail_form}, context_instance=RequestContext(request))

	# 詳細表示項目
	if form.cleaned_data['keypair']:
		machineData['keypair'] = form.cleaned_data['keypair']						#キーペア名
	else:
		login_user = request.session['ss_usr_user']
		keypairlist = Keypair.objects.filter(user_id=login_user.id,account_id=login_user.account_id)
		machineData['keypair'] = keypairlist[0].name
	if form.cleaned_data['security_group']:
		machineData['security_group'] = form.cleaned_data['security_group']			#セキュリティグループ名
	if form.cleaned_data['avaulability_zone']:
		machineData['avaulability_zone'] = form.cleaned_data['avaulability_zone']	#AvaulabilityZone
	if form.cleaned_data['user_data']:
		machineData['user_data'] = form.cleaned_data['user_data']					#ユーザーデータ
	request.session.modified = True


	"""
	次画面用情報の設定
	"""

	logger.info('仮想マシン 2.仮想マシン設定 次へ 終了')

	#画面表示
	return render_to_response('machine_group_create_3.html',{'gid_form':gid_form}, context_instance=RequestContext(request))


def step2back(request):
	"""「3.構成確認」の戻るボタン"""

	logger.info('仮想マシン 3.構成確認 戻る')

	#セッションからログインユーザ情報を取得する
	#login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)
	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
		gid_form = GroupIdForm({'group_id':gid})

	# 編集データ
	editGroupData = request.session['ss_mch_editData']

	"""
	次画面用情報の設定
	"""
	# 編集対象のマシン
	machineIndex = request.session['ss_mch_machineIndex']

	#入力フォーム
	form = MachineEditForm(data=editGroupData.machine_list[machineIndex])
	form.fields['ip'].choices = request.session['ss_mch_addresslist']
	form.fields['vmtype'].choices = request.session['ss_mch_vmtypelist']
	form.fields['volume'].choices = request.session['ss_mch_volumelist']
	form.fields['volume_zone'].choices = request.session['ss_mch_volumezonelist']

	machineData = editGroupData.machine_list[machineIndex]
	if machineData['volume'] != 'new':
		form.fields['volume_size'].widget.attrs['disabled']=True
		form.fields['volume_zone'].widget.attrs['disabled']=True

	detail_form = MachineDetailForm()

	logger.info('仮想マシン 3.構成確認 戻る 終了')

	#画面表示
	return render_to_response('machine_group_create_2.html',{'gid_form':gid_form, 'form':form, 'detail_form':detail_form}, context_instance=RequestContext(request))


def step3run(request):
	"""「3.構成確認」の保存して起動ボタン"""

	logger.info('仮想マシン 3.構成確認 保存して起動')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#エラー情報
	errors = []

	# 編集データ
	editGroupData = request.session['ss_mch_editData']

	# DB更新
	try:
		group_id = saveMachineGroup(login_user, editGroupData, errors)
	except Exception, ex:
		errors.append("仮想マシングループの起動に失敗しました。")
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		return render_to_response('machine_group_create_3.html',{'errors':errors}, context_instance=RequestContext(request))

	"""
	次画面用情報の設定
	"""
	#マシングループのリストを取得
	nonGroupMachines = []
	try:
		#マシングループのリストを取得
		machineGroupList = getMachineGroupList(login_user, nonGroupMachines)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("仮想マシン情報の参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		machineGroupList = []

	request.session['ss_mch_list'] = machineGroupList
	request.session['ss_mch_nongroupmachines'] = nonGroupMachines

	activeIndex = 0
	# リスト内をグループIDで検索
	for i, machineGroup in enumerate(machineGroupList):
		if group_id == machineGroup.db.id:
			activeIndex = i
			break

	#作成/更新したマシングループをアクティブ状態に設定
	activeObj = machineGroupList[activeIndex]
	gid_form = GroupIdForm({'group_id':machineGroupList[activeIndex].db.id})

	#リソース上限チェック
	try:
		usevm = euca_common.countActiveMachine(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

	if (usevm + len(machineGroupList[activeIndex].machine_list)) >= login_user.db_user.maxvm:
		errors.append("利用可能な仮想マシンの上限を超えています。")
		return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

	# 仮想マシン起動
	try:
		result = runMachineGroup(login_user, machineGroupList[activeIndex])
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("仮想マシングループの起動に失敗しました。")
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

	# 起動結果がNone(正常)ではない場合
	errors = []
	if result:
		errors.append("仮想マシングループの起動に失敗しました。")
		errors.append(result)
		return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

	# 不要なセッションデータ削除
	if 'ss_mch_editData' in request.session:
		del request.session['ss_mch_editData']

	logger.info('仮想マシン 3.構成確認 保存して起動 終了')

	#画面表示
	return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj}, context_instance=RequestContext(request))


def step3save(request):
	"""「3.構成確認」の保存のみボタン"""

	logger.info('仮想マシン 3.構成確認 保存のみ')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#エラー情報
	errors = []

	# 編集データ
	editGroupData = request.session['ss_mch_editData']

	# DB更新
	try:
		group_id = saveMachineGroup(login_user, editGroupData, errors)
	except Exception, ex:
		errors.append("仮想マシングループの作成に失敗しました。")
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		return render_to_response('machine_group_create_3.html',{'errors':errors}, context_instance=RequestContext(request))

	"""
	次画面用情報の設定
	"""
	nonGroupMachines = []
	try:
		#マシングループのリストを取得
		machineGroupList = getMachineGroupList(login_user, nonGroupMachines)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("仮想マシン情報の参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		machineGroupList = []

	request.session['ss_mch_list'] = machineGroupList
	request.session['ss_mch_nongroupmachines'] = nonGroupMachines

	activeIndex = 0
	# リスト内をグループIDで検索
	for i, machineGroup in enumerate(machineGroupList):
		if group_id == machineGroup.db.id:
			activeIndex = i
			break

	#作成/更新したマシングループをアクティブ状態に設定
	activeObj = machineGroupList[activeIndex]
	gid_form = GroupIdForm({'group_id':machineGroupList[activeIndex].db.id})

	# 不要なセッションデータ削除
	if 'ss_mch_editData' in request.session:
		del request.session['ss_mch_editData']

	logger.info('仮想マシン 3.構成確認 保存のみ 終了')

	#画面表示
	return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj}, context_instance=RequestContext(request))


def cancel(request):
	"""グループ作成キャンセルボタン"""

	logger.info('仮想マシン キャンセル')

	#セッションからグループ作成の途中情報を削除する

	#テンプレートのリスト
	if 'ss_mch_templateList' in request.session:
		del request.session['ss_mch_templateList']
	#編集中のデータ
	if 'ss_mch_editData' in request.session:
		del request.session['ss_mch_editData']

	"""TODO:セッションクリーン処理"""

	logger.info('仮想マシン キャンセル 終了')

	return HttpResponseRedirect('/machine/')


def machinerun(request, machine_id):
	"""仮想マシン起動ボタン"""

	logger.info('仮想マシン マシン起動')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)

	# エラーメッセージ
	errors = []

	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
	else:
		"""TODO:エラー処理"""
		return HttpResponseRedirect('/machine/')

	#マシングループのリストを取得
	#machineGroupList = getMachineGroupList(login_user)
	machineGroupList = request.session['ss_mch_list']

	isActive=False
	activeIndex = 0
	# 選択値の確認、リスト内をグループIDで検索
	for i, machineGroup in enumerate(machineGroupList):
		if gid == machineGroup.db.id:
			activeIndex = i
			isActive=True
			break
	else:
		# 一致するIDが存在しない場合はエラーメッセージ表示
		""" TODO: エラーメッセージ表示
		"""
		return HttpResponseRedirect('/machine/')

	#選択されたマシングループをアクティブ状態に設定
	activeObj = machineGroupList[activeIndex]
	gid_form = GroupIdForm({'group_id':machineGroupList[activeIndex].db.id})

	if isActive:
		# 仮想マシン起動
		try:
			result = runMachine(login_user, machineGroupList[activeIndex], machine_id)
		except Exception, ex:
			# Eucalyptusエラー
			errors = [euca_common.get_euca_error_msg('%s' % ex)]
			return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

		# セッション内容が変更されたことを通知
		request.session.modified = True

		# 起動結果がNone(正常)ではない場合
		if result:
			errors.append(result)

	logger.info('仮想マシン マシン起動 終了')

	#画面表示
	return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))


def machineterminate(request, machine_id):
	"""仮想マシン停止ボタン"""

	logger.info('仮想マシン マシン停止')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)

	# エラーメッセージ
	errors = []

	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
	else:
		"""TODO:エラー処理"""
		return HttpResponseRedirect('/machine/')

	#マシングループのリストを取得
	#machineGroupList = getMachineGroupList(login_user)
	machineGroupList = request.session['ss_mch_list']

	isActive=False
	activeIndex = 0
	# 選択値の確認、リスト内をグループIDで検索
	for i, machineGroup in enumerate(machineGroupList):
		if gid == machineGroup.db.id:
			activeIndex = i
			isActive=True
			break
	else:
		# 一致するIDが存在しない場合はエラーメッセージ表示
		""" TODO: エラーメッセージ表示
		"""
		return HttpResponseRedirect('/machine/')

	#選択されたマシングループをアクティブ状態に設定
	activeObj = machineGroupList[activeIndex]
	gid_form = GroupIdForm({'group_id':machineGroupList[activeIndex].db.id})

	if isActive:
		# 仮想マシン停止
		try:
			result = terminateMachine(login_user, machineGroupList[activeIndex], machine_id)
		except Exception, ex:
			# Eucalyptusエラー
			errors = [euca_common.get_euca_error_msg('%s' % ex)]
			return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

		# セッション内容が変更されたことを通知
		request.session.modified = True

		# 起動結果がNone(正常)ではない場合
		if result:
			errors.append(result)

	logger.info('仮想マシン マシン停止 終了')

	#画面表示
	return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

def machinestop(request, machine_id):
	"""仮想マシン中断ボタン"""

	logger.info('仮想マシン マシン中断')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)

	# エラーメッセージ
	errors = []

	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
	else:
		"""TODO:エラー処理"""
		return HttpResponseRedirect('/machine/')

	#マシングループのリストを取得
	#machineGroupList = getMachineGroupList(login_user)
	machineGroupList = request.session['ss_mch_list']

	isActive=False
	activeIndex = 0
	# 選択値の確認、リスト内をグループIDで検索
	for i, machineGroup in enumerate(machineGroupList):
		if gid == machineGroup.db.id:
			activeIndex = i
			isActive=True
			break
	else:
		# 一致するIDが存在しない場合はエラーメッセージ表示
		""" TODO: エラーメッセージ表示
		"""
		return HttpResponseRedirect('/machine/')

	#選択されたマシングループをアクティブ状態に設定
	activeObj = machineGroupList[activeIndex]
	gid_form = GroupIdForm({'group_id':machineGroupList[activeIndex].db.id})

	if isActive:
		# 仮想マシン中断
		try:
			result = stopMachine(login_user, machineGroupList[activeIndex], machine_id)
		except Exception, ex:
			# Eucalyptusエラー
			errors = [euca_common.get_euca_error_msg('%s' % ex)]
			return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

		# セッション内容が変更されたことを通知
		request.session.modified = True

		# 起動結果がNone(正常)ではない場合
		if result:
			errors.append(result)

	logger.info('仮想マシン マシン中断 終了')

	#画面表示
	return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))


def machinestart(request, machine_id):
	"""仮想マシン再開ボタン"""

	logger.info('仮想マシン マシン再開')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#フォームからグループIDを取得
	gid_form = GroupIdForm(request.POST)

	# エラーメッセージ
	errors = []

	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
	else:
		"""TODO:エラー処理"""
		return HttpResponseRedirect('/machine/')

	#マシングループのリストを取得
	#machineGroupList = getMachineGroupList(login_user)
	machineGroupList = request.session['ss_mch_list']

	isActive=False
	activeIndex = 0
	# 選択値の確認、リスト内をグループIDで検索
	for i, machineGroup in enumerate(machineGroupList):
		if gid == machineGroup.db.id:
			activeIndex = i
			isActive=True
			break
	else:
		# 一致するIDが存在しない場合はエラーメッセージ表示
		""" TODO: エラーメッセージ表示
		"""
		return HttpResponseRedirect('/machine/')

	#選択されたマシングループをアクティブ状態に設定
	activeObj = machineGroupList[activeIndex]
	gid_form = GroupIdForm({'group_id':machineGroupList[activeIndex].db.id})

	if isActive:
		# 仮想マシン中断
		try:
			result = startMachine(login_user, machineGroupList[activeIndex], machine_id)
		except Exception, ex:
			# Eucalyptusエラー
			errors = [euca_common.get_euca_error_msg('%s' % ex)]
			return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

		# セッション内容が変更されたことを通知
		request.session.modified = True

		# 起動結果がNone(正常)ではない場合
		if result:
			errors.append(result)

	logger.info('仮想マシン マシン再開 終了')

	#画面表示
	return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))


def getMachineGroupList(login_user=None, nonGroupMachines=None):
	"""マシングループのリストを取得
		input: login_user:models.User
		return: [machine_model.MachineGroup_append]
	"""
	machineGroupList = []
	if login_user == None:
		return []

	# 起動タイプ(VMType)の表示名
	vmtype_dict = getVMTypeDict()

	#マシングループテーブルとマシンテーブルのオブジェクトを取得する
	if login_user.admin:
		db_MachineGroupList = MachineGroup.objects.select_related().filter(account_id=login_user.account_id).order_by('id')
	else:
		db_MachineGroupList = MachineGroup.objects.select_related().filter(account_id=login_user.account_id, user_id=login_user.id).order_by('id')

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)
	#ログインユーザのインスタンスの一覧を取得
	reservations = get_euca_info.get_instancelist()

	#イメージ一覧を取得
	images = get_euca_info.get_image()

	zabb = ZabbixAccess()
	if zabb.isValid():
		cpus = zabb.getItem('system.cpu.util[,idle]')
		mems = zabb.getItem('vm.memory.size[available]')
		totalmems = zabb.getItem('vm.memory.size[total]')
		disk = zabb.getItem('vfs.fs.size[/,free]')
		totaldisk = zabb.getItem('vfs.fs.size[/,total]')

	#DB情報とEucalyptusAPI情報を合成する
	for db_machineGroup in db_MachineGroupList:
		#マシングループ
		machineGroup = MachineGroup_append()
		machineGroup.db = db_machineGroup
		for db_machine in db_machineGroup.machine_set.all():
			#仮想マシン
			machine = Machine_append()
			machine.db = db_machine

			#ルートデバイスタイプを取得
			for img in images:
				if img.id == machine.db.image_id:
					machine.device_type = img.root_device_type

			machine.displayVMType = vmtype_dict[machine.db.vmtype]
			for db_volume in db_machine.volume_set.all():
				# ボリューム
				machine.volume_list.append([db_volume.volume_id, u"%s(%s)" % (db_volume.name, db_volume.volume_id)])
			matched = False
			for reservation in reservations:
				for instance in reservation.instances:
					if instance.id == machine.db.instance_id:
						if instance.state != "shutting-down"  and instance.state != "terminated":
							machine.status = instance.state
							machine.starttime = instance.launch_time
							machine.privateip = instance.private_dns_name
							machine.auto_ip = instance.dns_name
							machine.auto_zone = instance.placement
						else:
							# 停止済みの場合はステータスのみ反映
							machine.status = instance.state
						matched = True
						break
				if matched:
					break
			else:
				# インスタンス一覧に存在しない場合は状態を"terminated"に設定
				machine.status = "terminated"
			if Template.objects.filter(id=machine.db.template_id):
				template = Template.objects.get(id=machine.db.template_id)
				machine.template_name = template.name

			if zabb.isValid():
				mon = Monitorings()
				if zabb.hostname2id(machine.db.instance_id):
					mon.isAvailable = True
					mon.cpu_used = round(100 - float(zabb.itemByHostname(cpus, machine.db.instance_id)), 2)
					total = zabb.itemByHostname(totalmems, machine.db.instance_id)
					if total and total != "0":
						mon.mem_total = round(float(total)/1024/1024, 1)
						mon.mem_used = mon.mem_total - round(float(zabb.itemByHostname(mems, machine.db.instance_id))/1024/1024, 1)
						#zabb.updateItemDelay('vm.memory.size[total]', machine.db.instance_id, 3600)
					#else:
						#zabb.updateItemDelay('vm.memory.size[total]', machine.db.instance_id, 60)
					total = zabb.itemByHostname(totaldisk, machine.db.instance_id)
					if total and total != "0":
						mon.disk_var_total = round(float(total)/1024/1024, 1)
						mon.disk_var_used = mon.disk_var_total - round(float(zabb.itemByHostname(disk, machine.db.instance_id))/1024/1024, 1)
						#zabb.updateItemDelay('vfs.fs.discovery', machine.db.instance_id, 3600, "discovery")
						#zabb.updateItemDelay('vfs.fs.size[/,total]', machine.db.instance_id, 3600)
					#else:
						#zabb.updateItemDelay('vfs.fs.discovery', machine.db.instance_id, 60, "discovery")
						#zabb.updateItemDelay('vfs.fs.size[/,total]', machine.db.instance_id, 60)
				machine.monitoring = mon

			machineGroup.machine_list.append(machine)

		machineGroupList.append(machineGroup)

	# グループ外仮想マシン(GUI以外から起動した仮想マシン)
	if nonGroupMachines != None:
		db_instanceIdList = Machine.objects.filter(group__account_id=login_user.account_id).values_list('instance_id', flat=True)
		for reservation in reservations:
			#if reservation.owner_id == login_user.id:
				for instance in reservation.instances:
					if instance.state != "shutting-down"  and instance.state != "terminated":
						if not instance.id in db_instanceIdList:
							machine = NonGroupMachine()
							machine.instance_id = instance.id				#インスタンスID
							machine.image_id = instance.image_id			#イメージID
							machine.vmtype = instance.instance_type			#VMType
							machine.ip = instance.dns_name					#Pアドレス
							machine.keypair = instance.key_name				#キーペア名
							groups = [group.id for group in reservation.groups]
							machine.security_group = ", ".join(groups)		#セキュリティグループ名
							machine.avaulability_zone = instance.placement	#AvaulabilityZone
							machine.status = instance.state					#状態
							machine.starttime = instance.launch_time		#起動時刻
							machine.privateip = instance.private_dns_name	#プライベートIP
							nonGroupMachines.append(machine)

	return machineGroupList


def runMachineGroup(login_user=None, machineGroup=None):
	"""マシングループを起動
		input: login_user:models.User
				machineGroup:machine_model.MachineGroup_append
		return: None, エラー時は(u'エラーメッセージ')
	"""
	if login_user == None or machineGroup == None:
		return u"ユーザー情報またはマシングループ情報が不正です。"

	"""
	リソース制限チェック
	"""
	# 現在起動中の仮想マシン数
	activeCount = euca_common.countActiveMachine(login_user)
	# マシングループの仮想マシン数
	nowCount = len(machineGroup.machine_list)

	if login_user.db_user.maxvm < (activeCount + nowCount):
		return u"利用可能な仮想マシンリソースの上限値を超えています。"

	# 起動後処理対象リスト
	afterList = []

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	for machine in machineGroup.machine_list:
		if machine.status == "running" or machine.status == "pending" or machine.status == "shutting-down" :
			#既に起動済みの場合はスキップ、停止処理中のものもスキップ
			continue

		#インスタンスを起動
		reservation = get_euca_info.run_instances(machine.db)
		# 起動時の戻り値をセッション情報へ更新
		for instance in reservation.instances:
			machine.db.instance_id = instance.id
			machine.status = instance.state
			machine.starttime = instance.launch_time
			machine.privateip = instance.private_dns_name
			machine.auto_ip = instance.dns_name
			machine.auto_zone = instance.placement
			break

		# DB更新（インスタンスID）
		saveMachine(machine.db)

		if machine.db.ip or machine.volume_list:
			afterList.append(machine)

	if afterList:
		# 起動後処理（IPアドレス、ボリューム）が必要なマシンが存在する場合
		# 非同期処理で仮想マシンの起動を待って処理
		t = threading.Thread(target=afterRunMachine, args=(get_euca_info, afterList))
		t.setDaemon(True)
		t.start()

	return


def afterRunMachine(get_euca_info, machines):
	"""仮想マシン起動後処理
		1)IPアドレス関連付け
		2)データボリューム取り付け
		input: get_euca_info:euca_access.GetEucalyptusInfo
				machines:[machine_model.Machine_append]
		return:-
	"""
	if not machines:
		return

	ipSets = {}
	volSets = {}
	for machine in machines:
		if machine.db.ip:
			ipSets[machine.db.instance_id] = machine.db.ip
		if machine.volume_list:
			volSets[machine.db.instance_id] = machine

	if ipSets:
		# 固定IPアドレスの設定が存在する場合
		timeout = 180
		while timeout >= 0:
			logger.debug("associate address loop")
			time.sleep(5)
			#インスタンスの一覧を取得
			reservations = get_euca_info.get_instancelist( ipSets.keys() )

			for reservation in reservations:
				for instance in reservation.instances:
					if instance.id in ipSets and instance.private_dns_name != "0.0.0.0":
						# IPアドレス設定
						logger.debug("trying to associate address %s to %s" % (ipSets[instance.id], instance.id))
						result = get_euca_info.associate_address(instance.id, ipSets[instance.id])
						if result:
							del ipSets[instance.id]
						else:
							logger.debug("associate address failed")
							"""TODO:IPアドレス関連付けエラー"""

			if not ipSets.keys():
				break

		else:
			"""TODO:タイムアウトエラー処理"""

	if volSets:
		# データボリュームの設定が存在する場合
		timeout = 1200
		while timeout >= 0:
			time.sleep(20)
			#インスタンスの一覧を取得
			reservations = get_euca_info.get_instancelist( volSets.keys() )

			for reservation in reservations:
				for instance in reservation.instances:
					if instance.id in volSets and instance.state == "running":
						# データボリューム取り付け
						machine = volSets[instance.id]
						for i, volInfo in enumerate(machine.volume_list):
							#EBSブート対応
							device = "/dev/vdz"
							logger.debug(device)
							result = get_euca_info.attach_volume(volInfo[0], instance.id, device)
						if result:
							del volSets[instance.id]
						else:
							"""TODO:ボリューム取り付けエラー"""

			if not volSets.keys():
				break

		else:
			"""TODO:タイムアウトエラー処理"""

	return


def terminateMachineGroup(login_user=None, machineGroup=None):
	"""マシングループを停止
		input: login_user:models.User
				machineGroup:machine_model.MachineGroup_append
		return: -
	"""
	instanceIdList = []
	if login_user == None or machineGroup == None:
		return machineGroup

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	for machine in machineGroup.machine_list:
		if machine.status == "shutting-down" or machine.status == "terminated" :
			#既に停止済みの場合はスキップ
			continue
		else:
			instanceIdList.append(machine.db.instance_id)
			machine.status = "shutting-down"

	#インスタンスを停止
	#instances = get_euca_info.terminate_instances(instanceIdList)
	get_euca_info.terminate_instances(instanceIdList)

	# DB更新
	#machine.db.save()

	return


def getTemplateList(login_user=None):
	"""テンプレート一覧を取得する
		input: login_user:models.User
		return: [models.Template]
	"""
	if login_user == None:
		return []

	#テンプレートテーブルのオブジェクトを取得する
	templateList = Template.objects.filter(Q(kind=1) | Q(user_id=login_user.id,account_id=login_user.account_id)).order_by('-kind', 'name')

	logger.debug("getTemplateList!")

	return templateList


# インスタンスIDパターン
INSTANCE_ID_PTN=re.compile(r"^i-\w{8}$")
# インスタンスIDパターン(Eucalyptusによる自動付与)
INSTANCE_ID_PTN_AUTO=re.compile(r"^i-\w{8}\s*\(arn:aws:euare::000000000000:user/eucalyptus\)$")

def getAddressList(get_euca_info=None, login_user=None):
	"""IPアドレス一覧を取得する
		input: get_euca_info:euca_access.GetEucalyptusInfo
		input: login_user:ユーザ情報
		return: (('IPアドレス',u'画面表示情報'))
	"""
	if get_euca_info == None or login_user == None :
		return []

	# インスタンスIDパターン(管理者の場合、取得済み、未使用)
	INSTANCE_ID_PTN_MINE=re.compile(r"^available\s*\(arn:aws:euare::%s:user/%s\)$" % (login_user.account_number, login_user.id) )
	# インスタンスIDパターン(管理者の場合、インスタンスへ取り付け済み)
	INSTANCE_ID_PTN_MINE_USED=re.compile(r"^i-\w{8}\s*\(arn:aws:euare::%s:user/%s\)$" % (login_user.account_number, login_user.id) )

	addressSet = []
	#デフォルト値(アドレス設定なし)追加
	adrs_val = [ "", u"指定しない(自動付与、起動毎にIPアドレス変動)" ]
	addressSet.append(adrs_val)

	#IPアドレス一覧を取得
	addresslist = get_euca_info.get_addresslist()

	for address in addresslist:
		displayStr = None
		if not address.instance_id:
			#取得済み、未使用
			displayStr = address.public_ip
			if Machine.objects.filter(ip=address.public_ip).count():
				displayStr = u"%s (関連付け済)" % address.public_ip
		elif INSTANCE_ID_PTN.match(address.instance_id):
			#取得済み、インスタンスへ取り付け済み
			displayStr = u"%s (利用中)" % address.public_ip
		elif address.instance_id == "nobody":
			#誰にも取得されていない(管理者の場合)
			continue
		elif INSTANCE_ID_PTN_AUTO.match(address.instance_id):
			#Eucalyptusが仮想マシンへ自動付与(管理者の場合)
			continue
		elif INSTANCE_ID_PTN_MINE.match(address.instance_id):
			#取得済み、未使用(管理者の場合)
			displayStr = address.public_ip
			if Machine.objects.filter(ip=address.public_ip).count():
				displayStr = u"%s (関連付け済)" % address.public_ip
		elif INSTANCE_ID_PTN_MINE_USED.match(address.instance_id):
			#取得済み、インスタンスへ取り付け済み(管理者の場合)
			displayStr = u"%s (利用中)" % address.public_ip
		else:
			# その他：他ユーザが利用中(管理者の場合)
			# 「available (ユーザID)」、「インスタンスID (ユーザID)」
			continue

		adrs_val = (address.public_ip, displayStr)
		addressSet.append(adrs_val)

	return tuple(addressSet)


def getVolumeList(get_euca_info=None, login_user=None):
	"""ボリューム一覧を取得する
		input: get_euca_info:euca_access.GetEucalyptusInfo
		input: login_user:ユーザ情報
		return: (('volumeID',u'画面表示情報'))
	"""
	if get_euca_info == None:
		return []

	#ボリューム一覧を取得
	#db_volumeList = Volume.objects.select_related(depth=1).filter(user_id=login_user.id)
	db_volumeList = Volume.objects.filter(user_id=login_user.id, account_id=login_user.account_id)

	volumeSet = []

	#デフォルト値(使用しない)追加
	vol_val = [ "", u"使用しない" ]
	volumeSet.append(vol_val)

	#EBSボリューム新規作成
	vol_val = [ "new", u"新規作成" ]
	volumeSet.append(vol_val)

	for db_volume in db_volumeList:

		volumesize=""

		volumes = get_euca_info.get_volumelist()

		for volume in volumes:

			if volume.id == db_volume.volume_id:
				volumesize = str(volume.size) +'[GB]'
				break

		"""displayStr = u"%s(%s)"  % (db_volume.name, db_volume.volume_id)"""

		displayStr = u"%s(サイズ:%s ボリュームID:%s)"  % (db_volume.name, volumesize, db_volume.volume_id)

		if db_volume.machine:
			#使用中
			displayStr += u", (関連付け済)"

		vol_val = (db_volume.volume_id, displayStr)
		volumeSet.append(vol_val)

	return tuple(volumeSet)


def getSelectListVMType():
	"""VMType選択用のタプル値を取得する"""

	vmtype_value = []
	db_vmtypes = VMType.objects.all()
	for vmtype in db_vmtypes:
		sub_vmtype = []
		sub_vmtype.append(vmtype.vmtype)
		sub_vmtype.append(vmtype.full_name)
		vmtype_value.append(sub_vmtype)

	return tuple(vmtype_value)


def getVMTypeDict():
	"""VMType表示用の辞書を取得する"""

	vmtype_dict = {}
	db_vmtypes = VMType.objects.all()
	for vmtype in db_vmtypes:
		vmtype_dict[vmtype.vmtype] = vmtype.full_name

	return vmtype_dict


@transaction.commit_on_success
def saveMachine(machine=None):
	machine.save()
	return


@transaction.commit_on_success
def saveMachineGroup(login_user=None, editGroupData=None, errors=None):

	"""マシングループを保存
		input: login_user:models.User
				editGroupData:machine_model.EditGroupData
		return: マシングループID
	"""
	if login_user == None or editGroupData == None:
		return editGroupData


	#仮想マシン情報削除の前に、ボリューム情報を退避
	db_volume_list = []
	for m in editGroupData.machine_list:
		if m['volume'] != '' and m['volume'] != 'new':
			db_volume_list.append(Volume.objects.get(volume_id=m['volume']))
		else:
			db_volume_list.append(None)

	if editGroupData.group_id:
		#更新の場合、マシングループ内の仮想マシン情報を一旦削除
		old_machine_list = Machine.objects.all().filter(group=editGroupData.group_id)

		old_volume_list = []
		for old_mch in old_machine_list:
			tmp_vol = Volume.objects.filter(machine=old_mch.id)
			for tmp in tmp_vol:
				old_volume_list.append(tmp)

		#Machine.objects.all().filter(group=editGroupData.group_id).delete()
		old_machine_list.delete()
		db_group = MachineGroup.objects.get(pk=editGroupData.group_id)
	else:
		# 新規作成の場合
		db_group = MachineGroup()

	db_group.name = editGroupData.name
	db_group.description = editGroupData.description
	db_group.account_id = login_user.account_id
	db_group.user_id = login_user.id

	# DB更新(新規作成の場合はここでグループIDが発行される)
	db_group.save()

	i = 0
	for machine in editGroupData.machine_list:
		db_machine = Machine()
		db_machine.group = db_group
		db_machine.name = machine['name']
		db_machine.image_id = machine['image_id']
		db_machine.vmtype = machine['vmtype']
		db_machine.ip = machine['ip']
		db_machine.keypair =  machine['keypair']
		db_machine.security_group =  machine['security_group']
		db_machine.avaulability_zone = machine['avaulability_zone']
		db_machine.user_data = machine['user_data']
		db_machine.template_id = machine['template_id']
		db_machine.order = machine['order']

		# DB更新
		db_machine.save()
		# ボリューム情報更新
		if machine['volume']:
			if machine['volume'] == 'new':
				#ボリューム新規作成
				initialData = {}
				vol_form =  volume_form.VolumeCreateForm(initial=initialData)
				vol_form.fields['name'] = machine['name'] + u'用ボリューム'
				vol_form.fields['description'] = vol_form.fields['name'] + u'です。'
				vol_form.fields['size'] = machine['volume_size']
				vol_form.fields['zone'] = machine['volume_zone']

				# EBSボリュームの新規作成
				logger.debug('EBSボリューム 新規作成')

				try:
					volume = createNewVolume(login_user, vol_form)
				except Exception, ex:
					raise ex

				# DB登録
				db_volume = models.Volume()
				db_volume.volume_id = volume.id
				db_volume.user_id = login_user.id
				db_volume.account_id = login_user.account_id
				db_volume.name = vol_form.fields['name']
				db_volume.description = vol_form.fields['description']
				db_volume.machine = db_machine
				db_volume.save()

			else:

				#マシン情報を上書き
				db_volume = db_volume_list[i]
				db_volume.machine = db_machine
				db_volume.name = db_machine.name +  u'用ボリューム'
				db_volume.description = db_volume.name + u'です。'
				updateVolume(db_volume)

		i = i + 1

	if editGroupData.group_id:
		#サーバ登録後処理(DBから消されたボリュームを削除する)
		db_vols = Volume.objects.filter(user_id=login_user.id, account_id=login_user.account_id)

		for vol in old_volume_list:

			deleteFlag = True

			for new_vol in db_vols:

				if vol.volume_id == new_vol.volume_id:
					deleteFlag = False

			if deleteFlag:
				try:
					get_euca_info=GetEucalyptusInfo(login_user)
					get_euca_info.delete_volume(vol.volume_id)

				except Exception, ex:
					# Eucalyptusエラー
					errors.append(euca_common.get_euca_error_msg('%s' % ex))
					logger.warn(errors)

	#トランザクション制御は'@transaction.commit_on_success'デコレータで関数正常終了時にcommit
	return db_group.id


def runMachine(login_user=None, machineGroup=None, machine_id=None):
	"""マシングループを起動
		input: login_user:models.User
				machineGroup:machine_model.Machine_append
				machine_id:unicode
		return: None, エラー時は(u'エラーメッセージ')
	"""
	if login_user == None or machineGroup == None or machine_id == None:
		return u"ユーザー情報またはマシン情報が不正です。"

	"""
	リソース制限チェック
	"""
	# 現在起動中の仮想マシン数
	activeCount = euca_common.countActiveMachine(login_user)

	if login_user.db_user.maxvm <= activeCount:
		return u"利用可能な仮想マシンリソースの上限値を超えています。"

	m_id = int(machine_id)

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	for machine in machineGroup.machine_list:
		if machine.db.id == m_id:

			if machine.status == "running" or machine.status == "pending" :
				#既に起動済みの場合は終了
				break

			#インスタンスを起動
			reservation = get_euca_info.run_instances(machine.db)
			# 起動時の戻り値をセッション情報へ更新
			for instance in reservation.instances:
				machine.db.instance_id = instance.id
				machine.status = instance.state
				machine.starttime = instance.launch_time
				machine.privateip = instance.private_dns_name
				machine.auto_ip = instance.dns_name
				machine.auto_zone = instance.placement
				break

			# DB更新（インスタンスID）
			saveMachine(machine.db)


			if machine.db.ip or machine.volume_list:
				# 起動後処理（IPアドレス、ボリューム）が必要なマシンが存在する場合
				# 非同期処理で仮想マシンの起動を待って処理
				afterList = [machine]
				t = threading.Thread(target=afterRunMachine, args=(get_euca_info, afterList))
				t.setDaemon(True)
				t.start()

			break

	return


def terminateMachine(login_user=None, machineGroup=None, machine_id=None):
	"""マシングループを停止
		input: login_user:models.User
				machineGroup:machine_model.Machine_append
				machine_id:unicode
		return: None, エラー時は(u'エラーメッセージ')
	"""
	instanceIdList = []
	if login_user == None or machineGroup == None or machine_id == None:
		return u"ユーザー情報またはマシン情報が不正です。"

	m_id = int(machine_id)

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	for machine in machineGroup.machine_list:
		if machine.db.id == m_id:
			if machine.status == "shutting-down" or machine.status == "terminated" :
				#既に停止済みの場合は終了
				break
			else:
				instanceIdList.append(machine.db.instance_id)
				machine.status = "shutting-down"
				#インスタンスを停止
				get_euca_info.terminate_instances(instanceIdList)
				break
	else:
		return u"マシン情報が不正です。"

	# DB更新
	#machine.db.save()

	return


def stopMachine(login_user=None, machineGroup=None, machine_id=None):
	"""マシンを中断
		input: login_user:models.User
				machineGroup:machine_model.Machine_append
				machine_id:unicode
		return: None, エラー時は(u'エラーメッセージ')
	"""
	instanceIdList = []
	if login_user == None or machineGroup == None or machine_id == None:
		return u"ユーザー情報またはマシン情報が不正です。"

	m_id = int(machine_id)

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	for machine in machineGroup.machine_list:
		if machine.db.id == m_id:
			if machine.status == "stopping" or machine.status == "stopped" :
				#既に中断済みの場合は終了
				break
			else:
				instanceIdList.append(machine.db.instance_id)
				machine.status = "stopping"
				#インスタンスを中断
				get_euca_info.stop_instances(instanceIdList)
				break
	else:
		return u"マシン情報が不正です。"

	# DB更新
	#machine.db.save()

	return



def startMachine(login_user=None, machineGroup=None, machine_id=None):
	"""マシンを再開
		input: login_user:models.User
				machineGroup:machine_model.Machine_append
				machine_id:unicode
		return: None, エラー時は(u'エラーメッセージ')
	"""
	instanceIdList = []
	if login_user == None or machineGroup == None or machine_id == None:
		return u"ユーザー情報またはマシン情報が不正です。"

	m_id = int(machine_id)

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	for machine in machineGroup.machine_list:
		if machine.db.id == m_id:
			machineFound = True
			if machine.status == "running" or machine.status == "pending" :
				#既に起動済みの場合は終了
				break
			else:
				instanceIdList.append(machine.db.instance_id)
				machine.status = "pending"
				#インスタンスを再開
				get_euca_info.start_instances(instanceIdList)

				if machine.db.ip or machine.volume_list:
				# 起動後処理（IPアドレス、ボリューム）が必要なマシンが存在する場合
				# 非同期処理で仮想マシンの起動を待って処理
					logger.debug("starting a afterRunMachine thread")
					afterList = [machine]
					t = threading.Thread(target=afterRunMachine, args=(get_euca_info, afterList))
					t.setDaemon(True)
					t.start()
				break

	else:
		return u"マシン情報が不正です。"

	return


#### 監視機能

def afterMonitorOn(zabb, instance_id):
	### 未使用

	if not zabb.isValid():
		return

	logger.debug("temporary changing monitor item delays for %s" % instance_id)
	zabb.updateItemDelay('vm.memory.size[total]', instance_id, 10)
	zabb.updateItemDelay('vfs.fs.discovery', instance_id, 10, "discovery")
	zabb.updateItemDelay('vfs.fs.size[/,total]', instance_id, 10)

	timeout = 120
	totalmem_available = False
	totaldisk_available = False
	disk_discovered = False

	while timeout >= 0:
		time.sleep(5)
		timeout -= 5
		logger.debug("timeout:%d" % timeout)

		if not totalmem_available:
			totalmem = zabb.getItem('vm.memory.size[total]', instance_id)
			if totalmem and totalmem[0]['lastvalue'] != "0":
				logger.debug("total memory available for %s" % instance_id)
				totalmem_available = True

		#if not disk_discovered:
		#	if zabb.hasItem('vfs.fs.size[/,total]',instance_id):
		#		logger.debug("disk discovered for %s, resuming discover delay" % instance_id)
		#		disk_discovered = True
		#		zabb.updateItemDelay('vfs.fs.discovery', instance_id, 3600, "discovery")
		#		zabb.updateItemDelay('vfs.fs.size[/,total]', instance_id, 10)

		if not totaldisk_available:
			totaldisk = zabb.getItem('vfs.fs.size[/,total]', instance_id)
			if totaldisk:
				if totaldisk[0]['lastvalue'] != "0":
					logger.debug("total disk available for %s" % instance_id)
					totaldisk_available = True
				else:
					logger.debug("disk discovered for %s" % instance_id)
					zabb.updateItemDelay('vfs.fs.size[/,total]', instance_id, 10)

		if totalmem_available and totaldisk_available:
			break

	else:
		logger.debug("total mem/disk monitoring for %s not available, resuming item delay" % instance_id)

	zabb.updateItemDelay('vm.memory.size[total]', instance_id, 3600)
	zabb.updateItemDelay('vfs.fs.discovery', instance_id, 3600, "discovery")
	zabb.updateItemDelay('vfs.fs.size[/,total]', instance_id, 3600)
	return

def vmmonitoron(request, machine_id):

	logger.info('仮想マシン 監視開始')
	gid_form = GroupIdForm(request.POST)

	errors = []

	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
	else:
		logger.debug("form not valid")
		#TODO:エラー処理
		return HttpResponseRedirect('/machine/')

	machineGroupList = request.session['ss_mch_list']

	isActive=False
	activeIndex = 0
	for i, machineGroup in enumerate(machineGroupList):
		if gid == machineGroup.db.id:
			activeIndex = i
			isActive=True
			break
		else:
			return HttpResponseRedirect('/machine/')

	#選択されたマシングループをアクティブ状態に設定
	activeObj = machineGroupList[activeIndex]
	gid_form = GroupIdForm({'group_id':machineGroupList[activeIndex].db.id})

	zabb = ZabbixAccess()
	if zabb.isValid():
		ip = None
		instance_id = None
		mac = None
		logger.debug('add monitor for vm:%s' % machine_id)
		for machine in activeObj.machine_list:
			if machine.db.id == int(machine_id):
				ip = machine.auto_ip
				instance_id = machine.db.instance_id
				mac = machine
				break
				#logger.debug('ip:%s id:%s' % (ip, instance_id))
		if mac:
			monitored_hostid = zabb.addHost(instance_id, 'Template OS Linux', ip, 'VMs')
			if monitored_hostid:
				#t = threading.Thread(target=afterMonitorOn, args=(zabb, instance_id))
				#t.setDaemon(True)
				#t.start()
				mac.monitoring.isAvailable = True
				request.session.modified = True

	return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

def vmmonitoroff(request, machine_id):

	logger.info('仮想マシン 監視終了')
	gid_form = GroupIdForm(request.POST)

	errors = []

	if gid_form.is_valid():
		gid = gid_form.cleaned_data["group_id"]
	else:
		logger.debug("form not valid")
		#TODO:エラー処理
		return HttpResponseRedirect('/machine/')

	machineGroupList = request.session['ss_mch_list']

	isActive=False
	activeIndex = 0
	for i, machineGroup in enumerate(machineGroupList):
		if gid == machineGroup.db.id:
			activeIndex = i
			isActive=True
			break
		else:
			return HttpResponseRedirect('/machine/')

	#選択されたマシングループをアクティブ状態に設定
	activeObj = machineGroupList[activeIndex]
	gid_form = GroupIdForm({'group_id':machineGroupList[activeIndex].db.id})

	zabb = ZabbixAccess()
	if zabb.isValid():
		instance_id = None
		mac = None
		logger.debug('remove monitor for vm:%s' % machine_id)
		for machine in activeObj.machine_list:
			if machine.db.id == int(machine_id):
				instance_id = machine.db.instance_id
				mac = machine
				break
		if instance_id:
			monitored_hostid = zabb.deleteHost(instance_id)
			if monitored_hostid:
				mac.monitoring.isAvailable = False
				request.session.modified = True

	return render_to_response('machine_list.html',{'gid_form':gid_form, 'activeObj':activeObj, 'errors':errors}, context_instance=RequestContext(request))

def get_console(request, instance_id):
	
	logger.info('コンソール出力開始')
	login_user = request.session['ss_usr_user']
	tool=GetEucalyptusInfoBy2ool()

	output = ""
	errors = []
	try:
		output = tool.getConsoleOutput(instance_id, login_user)
	except Exception, ex:
		errors.append("コンソール出力の取得に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))

	return render_to_response('console_output.html',{'output':output, 'errors':errors}, context_instance=RequestContext(request))
