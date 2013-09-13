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

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import dateformat
from datetime import datetime, timedelta
from django.db import transaction
from euca_access import GetEucalyptusInfo
import models
from volume_model import VolumeData, SnapshotData
import euca_common
import volume_form
import logging
from db_access_metadata import EucalyptusMetadataDB

#import pickle


#カスタムログ
logger = logging.getLogger('koalalog')

def top(request):
	"""データボリュームメニューの初期表示"""

	logger.info('データボリュームメニューの初期表示開始')

	#メニューを「データボリューム」に設定
	request.session['ss_sys_menu'] = "volume"

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	# ボリューム一覧を取得
	try:
		volumes = getVolumeList(login_user)
		rootDevices = getVolumeList(login_user,True)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		logger.warn(errors)
		volumes = []

	#スナップショット一覧を取得
	try:
		snapshots = getSnapshotList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		logger.warn(errors)
		snapshots = []

	#セッション情報
	request.session['ss_vol_volumes'] = volumes
	request.session['ss_vol_root_devices'] = rootDevices
	request.session['ss_vol_volumes_selected'] = None
	request.session['ss_vol_snapshots'] = snapshots
	request.session['ss_vol_snapshots_selected'] = None

	logger.info('データボリュームメニューの初期表示成功')

	return render_to_response('volume_list.html',{'errors':errors},context_instance=RequestContext(request))


def choice(request, index):
	"""ボリューム選択"""

	logger.info('データボリュームメニュー ボリューム選択開始')

	#セッションからログインユーザ情報を取得する
	#login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	# 選択されたボリューム
	activeIndex = int(index)

	#セッション情報
	volumes = request.session['ss_vol_volumes']
	if activeIndex < len(volumes):

		logger.debug('volume_id=%s' % volumes[activeIndex].db.volume_id)

		request.session['ss_vol_volumes_selected'] = volumes[activeIndex]
		form = volume_form.VolumeForm({'volume_id':volumes[activeIndex].db.volume_id, 'name':volumes[activeIndex].db.name, 'description':volumes[activeIndex].db.description})
		request.session['ss_vol_snapshots_selected'] = None
	else:
		errors.append("不正なボリュームが選択されました。")
		logger.warn(errors)

	logger.info('データボリュームメニュー ボリューム選択成功')

	return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))


def choice_root(request, index):
	"""ボリューム選択"""

	logger.info('データボリュームメニュー ルートデバイス選択開始')

	#セッションからログインユーザ情報を取得する
	#login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	# 選択されたボリューム
	activeIndex = int(index)

	#セッション情報
	root_devices = request.session['ss_vol_root_devices']
	if activeIndex < len(root_devices):

		logger.debug('volume_id=%s' % root_devices[activeIndex].db.volume_id)

		request.session['ss_vol_volumes_selected'] = root_devices[activeIndex]
		form = volume_form.VolumeForm({'volume_id':root_devices[activeIndex].db.volume_id, 'name':root_devices[activeIndex].db.name, 'description':root_devices[activeIndex].db.description})
		request.session['ss_vol_snapshots_selected'] = None
	else:
		errors.append("不正なボリュームが選択されました。")
		logger.warn(errors)

	logger.info('データボリュームメニュー ルートデバイス選択成功')

	return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))


def refresh(request):
	"""表示更新(ボリューム)"""

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('データボリュームメニュー 表示更新(ボリューム)開始')

	# ボリューム一覧を取得
	try:
		volumes = getVolumeList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		logger.warn(errors)
		volumes = []

	#セッション情報
	request.session['ss_vol_volumes'] = volumes
	selected = request.session['ss_vol_volumes_selected']

	if selected:
		for volume in volumes:
			if volume.db.volume_id == selected.db.volume_id:
				request.session['ss_vol_volumes_selected'] = volume
				form = volume_form.VolumeForm({'volume_id':volume.db.volume_id, 'name':volume.db.name, 'description':volume.db.description})
				logger.info('データボリュームメニュー 表示更新(ボリューム)成功')
				return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))
			else:
				request.session['ss_vol_volumes_selected'] = None

	logger.info('データボリュームメニュー 表示更新(ボリューム)成功')

	return render_to_response('volume_list.html',{'errors':errors},context_instance=RequestContext(request))


def update(request):
	"""保存ボタン(ボリューム)"""

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('データボリュームメニュー プロパティ変更 保存開始')

	if request.method == 'POST':
		logger.info("request.method == Post")

	#入力フォーム
	form = volume_form.VolumeForm(request.POST)

	# 入力チェック
	if not form.is_valid():
		tmp_errors = form.errors.values()
		for error in tmp_errors:
			errors.extend(error)
			logger.warn(errors)
		return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	#セッション情報との一致チェック
	selected = request.session['ss_vol_volumes_selected']
	if selected.db.volume_id != form.cleaned_data['volume_id']:
		errors.append("不正な画面遷移です。表示更新を行ってから再操作してください。")
		logger.warn(errors)
		return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	# DB更新
	selected.db.name = form.cleaned_data['name']
	selected.db.description = form.cleaned_data['description']
	updateVolume(selected.db)

	# ボリューム一覧を取得
	try:
		volumes = getVolumeList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		logger.warn(errors)
		volumes = []

	#セッション情報
	request.session['ss_vol_volumes'] = volumes
	selected = request.session['ss_vol_volumes_selected']

	for volume in volumes:
		if volume.db.volume_id == selected.db.volume_id:
			request.session['ss_vol_volumes_selected'] = volume
			form = volume_form.VolumeForm({'volume_id':volume.db.volume_id, 'name':volume.db.name, 'description':volume.db.description})
			break
	else:
		request.session['ss_vol_volumes_selected'] = None

	logger.info('データボリュームメニュー プロパティ変更 保存成功')

	return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))


def delete(request):
	"""削除ボタン(ボリューム)"""

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('データボリュームメニュー 削除(ボリューム)開始')

	#入力フォーム
	form = volume_form.VolumeForm(request.POST)
	form.is_valid()

	#セッション情報との一致チェック
	selected = request.session['ss_vol_volumes_selected']
	if selected.db.volume_id != form.cleaned_data['volume_id']:
		errors.append("不正な画面遷移です。表示更新を行ってから再操作してください。")
		logger.warn(errors)
		return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	#Eucalyptus操作
	try:
		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)
		# EBSボリューム削除
		get_euca_info.delete_volume(selected.db.volume_id)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		logger.warn(errors)
		return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	# DB更新
	deleteVolume(selected.db)

	# ボリューム一覧を取得
	try:
		volumes = getVolumeList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		logger.warn(errors)
		volumes = []

	#セッション情報
	request.session['ss_vol_volumes'] = volumes
	request.session['ss_vol_volumes_selected'] = None

	logger.info('データボリュームメニュー 削除(ボリューム)成功')

	return render_to_response('volume_list.html',{'errors':errors},context_instance=RequestContext(request))


def createform(request):
	"""作成ボタン(ボリューム)"""

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('データボリュームメニュー 新規作成フォーム作成 開始')

	# 入力フォーム
	form = volume_form.VolumeCreateForm()


	#入力フォーム用Availability Zone一覧
	try:
		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)
		# Availability Zone一覧を取得
		zones = get_euca_info.get_availabilityzones()
		# Availability Zone一覧を選択リストへ設定
		zonelist = []
		for zone in zones:
			sub_zone = []
			sub_zone.append(zone.name)
			sub_zone.append(zone.name)
			zonelist.append(sub_zone)
		form.fields['zone'].choices = zonelist
		request.session['ss_vol_avalabilityzonelist'] = zonelist
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("Availability Zone情報の参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		logger.warn(errors)

	logger.info('データボリュームメニュー 新規作成フォーム作成 成功')

	#選択されたスナップショット情報を初期化しない(IT01)
	#request.session['ss_vol_snapshots_selected'] = None

	return render_to_response('create_volume.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

def createform_from_snapshot(request):
	"""作成ボタン(スナップショットボリューム)"""

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('データボリュームメニュー スナップショットからボリューム作成フォーム作成 開始')

	#入力フォーム用スナップショット一覧
	snapshots = request.session['ss_vol_snapshots']
	snapshotChoice = [ [snapshot.id, snapshot.id] for snapshot in snapshots ]

	# スナップショット画面からの遷移の場合、初期状態でスナップショットID選択
	initialData = {}
	selectedSnapshot = request.session['ss_vol_snapshots_selected']
	if selectedSnapshot:
		initialData['snapshot'] = selectedSnapshot.id

	# 入力フォーム
	form = volume_form.VolumeCreateForm(initial=initialData)
	form.fields['snapshot'].choices = snapshotChoice

	#入力フォーム用Availability Zone一覧
	try:
		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)
		# Availability Zone一覧を取得
		zones = get_euca_info.get_availabilityzones()
		# Availability Zone一覧を選択リストへ設定
		zonelist = []
		for zone in zones:
			sub_zone = []
			sub_zone.append(zone.name)
			sub_zone.append(zone.name)
			zonelist.append(sub_zone)
		form.fields['zone'].choices = zonelist
		request.session['ss_vol_avalabilityzonelist'] = zonelist
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("Availability Zone情報の参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		logger.warn(errors)

	logger.info('データボリュームメニュー スナップショットからボリューム作成フォーム作成 成功')

	return render_to_response('create_volume_from_snapshot.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

def create(request):
	"""作成ボタン(ボリューム)"""

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('データボリュームメニュー ボリューム作成 開始')

	fromsnapshot = False

	if request.session['ss_vol_snapshots_selected'] != None:
		fromsnapshot = True

	#入力フォーム用スナップショット一覧
	snapshots = request.session['ss_vol_snapshots']
	snapshotChoice = [ [snapshot.id, snapshot.id] for snapshot in snapshots ]

	# 入力フォーム
	form = volume_form.VolumeCreateForm(request.POST)
	form.fields['snapshot'].choices = snapshotChoice
	form.fields['zone'].choices = request.session['ss_vol_avalabilityzonelist']

	if not form.is_valid():
		tmp_errors = form.errors.values()
		for error in tmp_errors:
			errors.extend(error)

		logger.warn(errors)

		if fromsnapshot:
			return render_to_response('create_volume_from_snapshot.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

		return render_to_response('create_volume.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	if fromsnapshot:
		if not form.cleaned_data['snapshot']:
			errors.append(u"バックアップファイルを入力してください。")
			logger.warn(errors)
			return render_to_response('create_volume_from_snapshot.html',{'form':form,'errors':errors},context_instance=RequestContext(request))
	else:
		if not form.cleaned_data['size']:
			errors.append(u"作成サイズを入力してください。")
			logger.warn(errors)
			return render_to_response('create_volume.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	#リソース上限チェック
	try:
		usevol = euca_common.countActiveVolume(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append(euca_common.get_euca_error_msg('%s' % ex))

		logger.warn(errors)

		if fromsnapshot:
			return render_to_response('create_volume_from_snapshot.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

		return render_to_response('create_volume.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	if form.cleaned_data['size']:
		create_size = form.cleaned_data['size']
	else:
		create_size = 0
		snapshots = request.session['ss_vol_snapshots']
		for snapshot in snapshots:
			if snapshot.id == form.cleaned_data['snapshot']:
				create_size = snapshot.volume_size
				create_size = create_size if create_size >= 0 else 0

	if (usevol + create_size) > login_user.db_user.maxvol:
		errors.append("利用可能なボリュームの上限を超えています。")
		logger.warn(errors)

		if fromsnapshot:
			return render_to_response('create_volume_from_snapshot.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

		return render_to_response('create_volume.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	#EBSボリューム作成(Eucalyptus操作)
	try:
		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)

		if form.cleaned_data['size']:
			#サイズ指定の場合
			volume = get_euca_info.create_volume(size=form.cleaned_data['size'], zone=form.cleaned_data['zone'], snapshot=None)
		else:
			#スナップショット指定の場合
			volume = get_euca_info.create_volume(size=None, zone=form.cleaned_data['zone'], snapshot=form.cleaned_data['snapshot'])

	except Exception, ex:
		# Eucalyptusエラー
		errors.append("ボリューム作成に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		logger.warn(errors)

	# DB登録
	db_volume = models.Volume()
	db_volume.volume_id = volume.id
	db_volume.user_id = login_user.id
	db_volume.account_id = login_user.account_id
	db_volume.name = form.cleaned_data['name']
	db_volume.description = form.cleaned_data['description']
	updateVolume(db_volume)

	"""
	次画面情報
	"""
	# ボリューム一覧を取得
	try:
		volumes = getVolumeList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		logger.warn(errors)
		volumes = []

	#スナップショット一覧を取得
	try:
		snapshots = getSnapshotList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		logger.warn(errors)
		snapshots = []

	#セッション情報
	request.session['ss_vol_volumes'] = volumes
	request.session['ss_vol_snapshots'] = snapshots

	#作成したボリュームを選択状態に設定
	for volume in volumes:
		if volume.db.volume_id == db_volume.volume_id :
			request.session['ss_vol_volumes_selected'] = volume
			form = volume_form.VolumeForm({'volume_id':volume.db.volume_id, 'name':volume.db.name, 'description':volume.db.description})
			break
	else:
		request.session['ss_vol_volumes_selected'] = None

	logger.info('データボリュームメニュー ボリューム作成 成功')

	return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

def attachselect(request):
	"""仮想マシンへ取り付けボタン(ボリューム)"""

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('データボリュームメニュー 仮想マシンへ取り付けフォーム作成 開始')

	#入力フォーム
	form = volume_form.VolumeForm(request.POST)
	form.is_valid()

	#セッション情報との一致チェック
	selected = request.session['ss_vol_volumes_selected']
	if selected.db.volume_id != form.cleaned_data['volume_id']:
		errors.append("不正な画面遷移です。表示更新を行ってから再操作してください。")
		logger.warn(errors)
		return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	"""
	次画面設定
	"""
	# 入力フォーム
	form = volume_form.VolumeAttachForm()

	machines = models.Machine.objects.filter(group__user_id=login_user.id).values_list('id', 'name')
	form.fields['machine'].widget.choices = machines
	request.session['ss_vol_machines'] = machines
	if not machines:
		errors.append("選択可能な仮想マシンがありません。")
		logger.warn(errors)

	logger.info('データボリュームメニュー 仮想マシンへ取り付けフォーム作成 成功')

	return render_to_response('attach_volume.html',{'form':form,'errors':errors},context_instance=RequestContext(request))


def attach(request):
	"""取り付けボタン(ボリューム)"""

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#セッション情報
	selected = request.session['ss_vol_volumes_selected']

	# エラー情報
	errors = []

	logger.info('データボリュームメニュー 仮想マシンへ取り付け 開始')

	#入力フォーム
	form = volume_form.VolumeAttachForm(request.POST)
	form.fields['machine'].widget.choices = request.session['ss_vol_machines']
	if not form.is_valid():
		tmp_errors = form.errors.values()
		for error in tmp_errors:
			errors.extend(error)
		logger.warn(errors)
		return render_to_response('attach_volume.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	machine = models.Machine.objects.get(pk=form.cleaned_data['machine'])
	if not machine:
		errors.append("不正な仮想マシンが選択されました。")
		logger.warn(errors)
		return render_to_response('attach_volume.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	# 取り付け先仮想マシンが起動中の場合
	if machine.instance_id:
		""" TODO:デバイス名を自動設定する
		"""
		device = form.cleaned_data['device'].encode('utf-8')
		#Eucalyptus操作
		try:
			#Eucalyptus基盤へのアクセサを生成する
			get_euca_info=GetEucalyptusInfo(login_user)

			#仮想マシンの現在ステータスを確認
			reservations = get_euca_info.get_instancelist(instance_ids=[machine.instance_id])
			if reservations:
				if reservations[0].instances[0].state == "running":

					# EBSボリュームアタッチ
					return_code = get_euca_info.attach_volume(volume_id=selected.db.volume_id, instance_id=machine.instance_id, device=device)

					if not return_code:
						errors.append("起動中の仮想マシンへのボリューム取り付けに失敗しました。")
						logger.warn(errors)
						return render_to_response('attach_volume.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

					""" TODO:アタッチ状況が"attaching"->"attached"へ遷移するのを確認する"""

		except Exception, ex:
			# Eucalyptusエラー
			errors.append(euca_common.get_euca_error_msg('%s' % ex))
			logger.warn(errors)
			return render_to_response('attach_volume.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	# DB情報更新
	selected.db.machine = machine
	updateVolume(selected.db)

	# 不要なセッションを削除
	del request.session['ss_vol_machines']

	# ボリューム一覧を取得
	try:
		volumes = getVolumeList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		logger.warn(errors)
		volumes = []

	for vol in volumes:
		if vol.db.volume_id == selected.db.volume_id:
			selected = vol
			break

	#セッション情報
	request.session['ss_vol_volumes'] = volumes
	if volumes:
		request.session['ss_vol_volumes_selected'] = selected
		form = volume_form.VolumeForm({'volume_id':selected.db.volume_id, 'name':selected.db.name, 'description':selected.db.description})
	else:
		request.session['ss_vol_volumes_selected'] = None
		form = volume_form.VolumeForm()

	logger.info('データボリュームメニュー 仮想マシンへ取り付け 成功')

	return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))


def detach(request):
	"""取り外しボタン(ボリューム)"""

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('データボリュームメニュー 仮想マシンから取り外し 開始')

	#入力フォーム
	form = volume_form.VolumeForm(request.POST)
	form.is_valid()

	#セッション情報との一致チェック
	selected = request.session['ss_vol_volumes_selected']
	if selected.db.volume_id != form.cleaned_data['volume_id']:
		errors.append("不正な画面遷移です。表示更新を行ってから再操作してください。")
		logger.warn(errors)
		return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	print selected.instance_id

	# 取り付け先の仮想マシンが起動中の場合
	if selected.instance_id:
		#Eucalyptus操作
		try:
			#Eucalyptus基盤へのアクセサを生成する
			get_euca_info=GetEucalyptusInfo(login_user)
			# EBSボリューム取り外し
			return_code = get_euca_info.detach_volume(volume_id=selected.db.volume_id, instance_id=selected.instance_id,force=True)

			if not return_code:
				errors.append("起動中の仮想マシンからのボリューム取り外しに失敗しました。")
				logger.warn(errors)
				return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

			""" TODO:アタッチ状況が"detaching"->"detached"->""(ステータス"available")へ遷移するのを確認する"""

		except Exception, ex:
			# Eucalyptusエラー
			errors.append(euca_common.get_euca_error_msg('%s' % ex))
			logger.warn(errors)
			return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	# DB更新
	selected.db.machine = None
	updateVolume(selected.db)

	# ボリューム一覧を取得
	try:
		volumes = getVolumeList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		logger.warn(errors)
		volumes = []

	for vol in volumes:
		if vol.db.volume_id == selected.db.volume_id:
			selected = vol
			break

	#セッション情報
	request.session['ss_vol_volumes'] = volumes
	if volumes:
		request.session['ss_vol_volumes_selected'] = selected
		form = volume_form.VolumeForm({'volume_id':selected.db.volume_id, 'name':selected.db.name, 'description':selected.db.description})
	else:
		request.session['ss_vol_volumes_selected'] = None
		form = volume_form.VolumeForm()

	logger.info('データボリュームメニュー 仮想マシンから取り外し 成功')

	return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))


def createsnapshot(request):
	"""バックアップを作成ボタン(ボリューム)"""

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('データボリュームメニュー バックアップを作成 開始')

	#入力フォーム
	form = volume_form.VolumeForm(request.POST)
	form.is_valid()

	#セッション情報との一致チェック
	selected = request.session['ss_vol_volumes_selected']
	if selected.db.volume_id != form.cleaned_data['volume_id']:
		errors.append("不正な画面遷移です。表示更新を行ってから再操作してください。")
		logger.warn(errors)
		return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	#Eucalyptus操作
	try:
		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)
		# スナップショット作成
		created_snapshot = get_euca_info.create_snapshot(volume_id=selected.db.volume_id)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		logger.warn(errors)
		return render_to_response('volume_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))


	# スナップショット一覧を取得
	try:
		snapshots = getSnapshotList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		logger.warn(errors)
		snapshots = []

	#セッション情報
	request.session['ss_vol_snapshots'] = snapshots

	#作成したスナップショットを選択
	activeIndex = len(snapshots)
	if snapshots:
		for i, snapshot in enumerate(snapshots):
			if snapshot.id == created_snapshot.id:
				activeIndex = i
				break

	#セッション情報
	if activeIndex < len(snapshots):
		request.session['ss_vol_volumes_selected'] = None
		request.session['ss_vol_snapshots_selected'] = snapshots[activeIndex]
	else:
		errors.append("不正なバックアップが選択されました。")
		logger.warn(errors)

	logger.info('データボリュームメニュー バックアップを作成 完了')

	return render_to_response('snapshot_list.html',{'errors':errors},context_instance=RequestContext(request))


def snapshot(request, index):
	"""バックアップ(スナップショット)選択"""

	#セッションからログインユーザ情報を取得する
	#login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('データボリュームメニュー スナップショット選択 開始')

	# 選択されたスナップショット
	activeIndex = int(index)

	#セッション情報
	snapshots = request.session['ss_vol_snapshots']
	if activeIndex < len(snapshots):
		request.session['ss_vol_volumes_selected'] = None
		request.session['ss_vol_snapshots_selected'] = snapshots[activeIndex]
	else:
		errors.append("不正なバックアップが選択されました。")
		logger.warn(errors)

	logger.info('データボリュームメニュー スナップショット選択 成功')

	return render_to_response('snapshot_list.html',{'errors':errors},context_instance=RequestContext(request))


def snapshot_refresh(request):
	"""表示更新(バックアップ)"""

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('データボリュームメニュー スナップショット更新 開始')

	# スナップショット一覧を取得
	try:
		snapshots = getSnapshotList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		logger.warn(errors)
		snapshots = []

	#セッション情報
	request.session['ss_vol_snapshots'] = snapshots
	selected = request.session['ss_vol_snapshots_selected']

	for snapshot in snapshots:
		if snapshot.id == selected.id:
			request.session['ss_vol_snapshots_selected'] = snapshot
			break
	else:
		request.session['ss_vol_snapshots_selected'] = None

	logger.info('データボリュームメニュー スナップショット更新 成功')

	return render_to_response('snapshot_list.html',{'errors':errors},context_instance=RequestContext(request))


def snapshot_delete(request):
	"""バックアップ削除ボタン(スナップショット)"""

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('データボリュームメニュー バックアップ削除 開始')

	#セッション情報
	snapshot = request.session['ss_vol_snapshots_selected']

	#Eucalyptus操作
	try:
		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)
		# スナップショット削除
		get_euca_info.delete_snapshot(snapshot_id=snapshot.id)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		logger.warn(errors)
		return render_to_response('snapshot_list.html',{'errors':errors},context_instance=RequestContext(request))


	# スナップショット一覧を取得
	try:
		snapshots = getSnapshotList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]
		logger.warn(errors)
		snapshots = []

	#セッション情報
	request.session['ss_vol_snapshots'] = snapshots
	request.session['ss_vol_snapshots_selected'] = None

	logger.info('データボリュームメニュー バックアップ削除 成功')

	return render_to_response('volume_list.html',{'errors':errors},context_instance=RequestContext(request))


def cancel(request):
	"""キャンセルボタン"""

	#セッションからログインユーザ情報を取得する
	#login_user = request.session['ss_usr_user']

	# エラー情報
	errors = []

	logger.info('データボリュームメニュー キャンセル 開始')

	"""
	TODO:キャンセル元画面のセッション情報削除
	"""

	if request.session['ss_vol_snapshots_selected']:
		logger.info('データボリュームメニュー キャンセル 成功')
		return render_to_response('snapshot_list.html',{'errors':errors},context_instance=RequestContext(request))
	else:
		selected = request.session['ss_vol_volumes_selected']
		form = volume_form.VolumeForm({'volume_id':selected.db.volume_id, 'name':selected.db.name, 'description':selected.db.description})
		logger.info('データボリュームメニュー キャンセル 成功')
		return render_to_response('volume_list.html',{'form':form, 'errors':errors},context_instance=RequestContext(request))


def isRootDevice(volume, image_snapshot_list=[]):
	if volume.attach_data.device == "/dev/sda1":
		return True
	if volume.snapshot_id:
		for snap in image_snapshot_list:
			if volume.snapshot_id == snap.snapshot_id:
				return True
	return False

def getInstanceNameFromId(instance_id):
	m = models.Machine.objects.filter(instance_id=instance_id)
	if len(m):
		return models.Machine.objects.get(instance_id=instance_id).name
	else:
		return "管理外の仮想サーバ"

def getVolumeList(login_user=None, rootDevice=False):
	"""データボリューム(EBSボリューム)のリストを取得
		input: login_user:models.User
		return: [volume_model.VolumeData]
	"""
	volumeList = []
	if login_user == None:
		return []

	#ボリュームのオブジェクトを取得する
	db_volumeList = models.Volume.objects.select_related(depth=1).filter(user_id=login_user.id).order_by('name')

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)
	#ログインユーザのボリュームの一覧を取得
	volumes = get_euca_info.get_volumelist()

	euca_metadata = EucalyptusMetadataDB()
	image_snapshot_list = euca_metadata.getImageSnapshotList()

	#DB情報とEucalyptusAPI情報を合成する
	for volume in volumes:
		if rootDevice != isRootDevice(volume, image_snapshot_list):
			continue

		volumeData = VolumeData()
		volumeData.size = volume.size						#サイズ
		volumeData.root_device = rootDevice
		if volume.snapshot_id:
			volumeData.snapshot_id = volume.snapshot_id		#スナップショットID
		volumeData.zone = volume.zone						#availabilityZone
		volumeData.status = volume.status					#ステータス
		volumeData.createTime = getDisplayTime(volume.create_time)			#作成日時
		if volume.status == 'in-use':
			volumeData.attached = True						#アタッチフラグ
			volumeData.instance_id = volume.attach_data.instance_id		#アタッチ時：インスタンスID
			volumeData.machine_name = getInstanceNameFromId(volume.attach_data.instance_id)
			volumeData.device = volume.attach_data.device				#アタッチ時：デバイス
			volumeData.attach_status = volume.attach_data.status		#アタッチ時：アタッチ状況
			volumeData.attach_time = getDisplayTime(volume.attach_data.attach_time)		#アタッチ時：アタッチ日時
		for db_volume in db_volumeList:
			if volume.id == db_volume.volume_id:
				volumeData.db = db_volume
				if db_volume.machine:
					volumeData.machine_name = db_volume.machine.name	#仮想マシン名
				break
		else:
			# 内部DBに情報が存在しないEBSの場合
			db_volume = models.Volume()
			db_volume.volume_id = volume.id
			db_volume.name = volume.id
			db_volume.account_id = login_user.account_id
			db_volume.user_id = login_user.id
			volumeData.db = db_volume

		#print pickle.dumps(volumeData)
		volumeList.append(volumeData)

	return volumeList


def getSnapshotList(login_user=None):
	"""バックアップ(スナップショット)のリストを取得
		input: login_user:models.User
		return: [volume_model.SnapshotData]
	"""
	snapshotList = []
	if login_user == None:
		return []


	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)
	#ログインユーザのボリュームの一覧を取得
	snapshots = get_euca_info.get_snapshotlist()

	euca_metadata = EucalyptusMetadataDB()
	image_snapshot_list = euca_metadata.getImageSnapshotList()

	#DB情報とEucalyptusAPI情報を合成する
	for snapshot in snapshots:
# Eucalyptus3.0では管理者でも他ユーザーのリソースを取得しないので、ユーザIDによるフィルタ不要。
# 処理を残したい場合は「if login_user.account_number == snapshot.owner_id:」でアカウント番号との一致チェックにする
#		if login_user.id == snapshot.owner_id:
			snapshotData = SnapshotData()
			snapshotData.id = snapshot.id						#スナップショットID
			snapshotData.volume_id = snapshot.volume_id			#ボリュームID
			snapshotData.start_time = getDisplayTime(snapshot.start_time)		#作成日時
			snapshotData.status = snapshot.status				#ステータス
			snapshotData.progress = snapshot.progress			#進行状況
			snapshotData.owner_id = snapshot.owner_id			#オーナーID
			snapshotData.volume_size = snapshot.volume_size		#作成元ボリュームサイズ(Eucalyptus3.0から有効)

			for snap in image_snapshot_list:
				if snap.snapshot_id == snapshot.id:
					snapshotData.image = snap.image_id
					break

			#print pickle.dumps(snapshotData)
			snapshotList.append(snapshotData)

	return snapshotList


def getDisplayTime(dateStr=None):

	if not dateStr:
		return ""

	utc_time = datetime.strptime(dateStr[0:19], "%Y-%m-%dT%H:%M:%S")
	locale_time = utc_time + timedelta(hours=9)
	dateStr = dateformat.format(locale_time, 'Y年m月d日 H:i:s')
	return dateStr


@transaction.commit_on_success
def updateVolume(volume=None):
	"""ボリュームのDB情報を更新
		input: volume:models.Volume
		return: -
	"""
	if volume == None:
		return

	volume.save()

	return


@transaction.commit_on_success
def deleteVolume(volume=None):
	"""ボリュームのDB情報を削除
		input: login_user:models.User
		return: -
	"""
	if volume == None:
		return

	volume.delete()

	return

# 新規ボリューム作成
def createNewVolume(login_user, form):
	#リソース上限チェック
	try:
		usevol = euca_common.countActiveVolume(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		logger.warn("ボリューム利用状況の取得に失敗しました。")
		logger.warn(euca_common.get_euca_error_msg('%s' % ex))
		raise ex

	if form.fields['size']:
		create_size = form.fields['size']
	if (usevol + create_size) > login_user.db_user.maxvol:
		logger.warn("利用可能なボリュームの上限を超えています。")
		raise Exception('Couldn\'t create volume because the total size of volume is larger than the limit you are allowed.')

	#EBSボリューム作成(Eucalyptus操作)
	try:
		get_euca_info=GetEucalyptusInfo(login_user)
		volume = get_euca_info.create_volume(size=form.fields['size'], zone=form.fields['zone'], snapshot=None)
		return volume
	except Exception, ex:
		logger.error("ボリュームの新規作成に失敗しました。")
		raise ex