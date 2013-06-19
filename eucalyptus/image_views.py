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
from euca_access import GetEucalyptusInfo
from euca_access import RegisterOSImage
from euca_access import DeregisterOSImage
#from image_form import *
from image_form import ImageModForm
from image_form import ImagePublicRangeForm
from image_form import ImageCreateStep1Form
from image_form import ImageCreateStep2Form
from image_form import euca_common
from models import Image
from models import User
from user_model import User_Model
from db_access_metadata import EucalyptusMetadataDB

import logging
import time

#カスタムログ
logger = logging.getLogger('koalalog')

def top(request,image_id):
	"""仮想マシンイメージメニューの初期表示"""

	logger.info('仮想OSイメージ表示')

	#メニューを「仮想マシンイメージ」に設定
	request.session['ss_sys_menu'] = "image"
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#ログインユーザのイメージの一覧を取得
	images = get_euca_info.get_image()

	#イメージモデルのリストを取得
	image_model_List = createImageModelList(images)

	selectImageNumber = 0;

	logger.debug("image_id=%s"  % image_id)

	if 'ss_img_selectNumber' in request.session:
		logger.debug("session=%s"  % request.session['ss_img_selectNumber'])


	if image_id != 'top':
		count = 0;
		for i in image_model_List:

			if image_id == i.id:
				selectImageNumber = count
				break

			count = count + 1

		#セッションに選択中のイメージナンバーの情報を保持する
		request.session['ss_img_selectNumber'] = selectImageNumber
		#セッションに選択中のイメージのＩＤの情報を保持する
		request.session['ss_img_selectID'] = image_id

		logger.debug('selectImageNumber=%s'  % request.session['ss_img_selectNumber'])
		logger.debug('selectImageid=%s'  % request.session['ss_img_selectID'])
	elif 'ss_img_selectNumber' in request.session:
		del request.session['ss_img_selectNumber']
	elif 'ss_img_selectID' in request.session:
		del request.session['ss_img_selectID']

	#エラーメッセージ
	message = ""

	if request.method == 'POST':
		logger.info('保存ボタン押下')
		form = ImageModForm(request.POST)

		#保存ボタンを押下した時の処理
		if form.is_valid():
			selected_image_model = image_model_List[selectImageNumber]

			selected_image_model.name = form.cleaned_data['image_name']
			selected_image_model.description = form.cleaned_data['image_description']

			logger.info('仮想OSイメージ 設定保存完了')
			return render_to_response('image_list.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))

		else:
			#エラーメッセージ
			message = []
			tmp_errors = form.errors.values()
			for error in tmp_errors:
				message.extend(error)
				logger.warn(error)

			return render_to_response('image_list.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))

	else:

		form = None

		if len(image_model_List) > 0:
			form = ImageModForm({'image_name':image_model_List[selectImageNumber].name,'image_description':image_model_List[selectImageNumber].description})
		else:
			form = ImageModForm()

		logger.info('仮想OSイメージ表示完了')
		return render_to_response('image_list.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))

#公開範囲を変更する画面が表示された時の処理
def modpublicrange(request):

	logger.info('公開範囲を変更')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#ログインユーザのイメージの一覧を取得
	images = get_euca_info.get_image()

	#イメージモデルのリストを取得
	image_model_List = createImageModelList(images)

	#セッションに選択中のイメージナンバーの情報を取得する
	selectImageNumber = request.session['ss_img_selectNumber']

	form = ImagePublicRangeForm({'publicrange': image_model_List[selectImageNumber].is_public})

	publicrange_tuple = [('public','全体に公開 (システムOSイメージとして登録されます)'),('private','自分自身のみ (マイOSイメージとして登録されます)')]

	form.fields['publicrange'].choices = publicrange_tuple

	request.session['ss_img_publicrange'] = publicrange_tuple

	return render_to_response('modify_image_range.html',{'image_model_List':image_model_List,'form':form},context_instance=RequestContext(request))

#公開範囲を変更した時の処理
def domodpublicrange(request):

	logger.info('公開範囲の変更実施')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#ToDo Eucalyptusへの短時間接続エラー無理やり回避策
	time.sleep(1)

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#ログインユーザのイメージの一覧を取得
	images = get_euca_info.get_image()

	#セッションに選択中のイメージナンバーの情報を取得する
	selectImageNumber = request.session['ss_img_selectNumber']

	message=""

	#イメージモデルのリストを取得
	image_model_List = createImageModelList(images)


	if request.method == 'POST':

		logger.info('設定ボタンを押下')

		rangeform = ImagePublicRangeForm(request.POST)

		rangeform.fields['publicrange'].choices = request.session['ss_img_publicrange']

		#設定ボタンを押下した時の処理
		if rangeform.is_valid():

			selected_publicrange = rangeform.cleaned_data['publicrange']

			if selected_publicrange == 'public':
				result = get_euca_info.modify_image_attribute_groups(image_model_List[selectImageNumber].id,'add',groups=['all'])
				logger.debug('result = %s' % result)

			else:
				result = get_euca_info.modify_image_attribute_groups(image_model_List[selectImageNumber].id,'remove',groups=['all'])
				logger.debug('result = %s' % result)

			#ログインユーザのイメージの一覧を再び取得
			modimages = get_euca_info.get_image()
			#イメージモデルのリストを再び取得
			image_model_Mod_List = createImageModelList(modimages)
			form = ImageModForm({'image_name':image_model_Mod_List[selectImageNumber].name,'image_description':image_model_Mod_List[selectImageNumber].description})

			logger.info('公開範囲の変更完了 range=%s' % selected_publicrange.encode('utf-8'))

			return render_to_response('image_list.html',{'image_model_List':image_model_Mod_List,'form':form, 'message':message},context_instance=RequestContext(request))

		else:
			#エラーメッセージ
			message = []
			tmp_errors = form.errors.values()
			for error in tmp_errors:
				message.extend(error)
				logger.warn(error)

			form = ImageModForm({'image_name':image_model_List[selectImageNumber].name,'image_description':image_model_List[selectImageNumber].description})

			return render_to_response('image_list.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))
	else:

		form = ImageModForm({'image_name':image_model_List[selectImageNumber].name,'image_description':image_model_List[selectImageNumber].description})

		return render_to_response('image_list.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))

#OSイメージ作成のステップ1
def createstep1(request):

	logger.info('OSイメージ作成のステップ1')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#ログインユーザのイメージの一覧を取得
	images = get_euca_info.get_image()

	#イメージモデルのリストを取得
	image_model_List = createImageModelList(images)

	form = ImageCreateStep1Form({'imagetype':'machine'})

	imagetype_tuple = [('machine','仮想OSイメージ'),('ramdisk','ラムディスクイメージ'),('kernel','カーネルイメージ')]

	form.fields['imagetype'].choices = imagetype_tuple

	request.session['ss_img_imagetype'] = imagetype_tuple

	message=""

	return render_to_response('create_image_1.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))

#OSイメージ作成のステップ1終了時の処理
def createstep1end(request):

	logger.info('OSイメージ作成のステップ1 次へボタンを押下')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#ログインユーザのイメージの一覧を取得
	images = get_euca_info.get_image()

	message=""
	#イメージモデルのリストを取得
	image_model_List = createImageModelList(images)

	if request.method == 'POST':
		form = ImageCreateStep1Form(request.POST)

		form.fields['imagetype'].choices = request.session['ss_img_imagetype']

		#次へボタンを押下した時の処理
		if form.is_valid():
			logger.info('OSイメージ作成のステップ2')
			request.session['ss_img_name'] = form.cleaned_data['image_name']
			request.session['ss_img_description'] = form.cleaned_data['image_description']
			request.session['ss_img_bucketname'] = form.cleaned_data['bucket_name']
			request.session['ss_img_selectimagetype'] = form.cleaned_data['imagetype']

			imagetype_tuple = request.session['ss_img_imagetype']
			imagetype_list = list(imagetype_tuple)

			""" ToDoもっときれいな方法があるはず・・・"""
			for l in imagetype_list:
				if l[0] == form.cleaned_data['imagetype']:
					request.session['ss_img_selectimagetype_value'] = l[1]
					break

			step2form = ImageCreateStep2Form()
			step2form.fields['image_path'].update()
			step2form.fields['kernel'].choices = getSelectListKernelImage(image_model_List)
			step2form.fields['ramdisk'].choices = getSelectListRamdiskImage(image_model_List)

			return render_to_response('create_image_2.html',{'image_model_List':image_model_List,'form':step2form, 'message':message},context_instance=RequestContext(request))
		else:
			message = []
			tmp_errors = form.errors.values()
			for error in tmp_errors:
				message.extend(error)
				logger.warn(error)

			return render_to_response('create_image_1.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))

	else:
		message = 'リクエストはGETにしてください'
		logger.warn(message)
		return render_to_response('create_image_1.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))

#OSイメージ作成ステップ1に戻る時の処理
def createstep1back(request):

	logger.info('OSイメージ作成のステップ2からステップ1へ戻る')
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#ログインユーザのイメージの一覧を取得
	images = get_euca_info.get_image()

	#イメージモデルのリストを取得
	image_model_List = createImageModelList(images)

	form = ImageCreateStep1Form({'image_name':request.session['ss_img_name'],'image_description':request.session['ss_img_description'],'bucket_name':request.session['ss_img_bucketname'],'imagetype':request.session['ss_img_selectimagetype']})

	imagetype_tuple = [('machine','仮想OSイメージ'),('ramdisk','ラムディスクイメージ'),('kernel','カーネルイメージ')]

	form.fields['imagetype'].choices = imagetype_tuple

	message = ''

	return render_to_response('create_image_1.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))

#OSイメージ作成のステップ2の処理
def createstep2(request):

	logger.info('OSイメージ作成のステップ2 次へボタンを押下')
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#ログインユーザのイメージの一覧を取得
	images = get_euca_info.get_image()

	message=""
	#イメージモデルのリストを取得
	image_model_List = createImageModelList(images)

	if request.method == 'POST':

		form = ImageCreateStep2Form(request.POST)

		form.fields['kernel'].choices = getSelectListKernelImage(image_model_List)
		form.fields['ramdisk'].choices = getSelectListRamdiskImage(image_model_List)

		if request.session['ss_img_selectimagetype'] != 'machine':
			form.fields['kernel'].required=False
			form.fields['ramdisk'].required=False
		else:
			form.fields['kernel'].required=True
			form.fields['ramdisk'].required=True

		#次へボタンを押下した時の処理
		if form.is_valid():
			logger.info('OSイメージ作成のステップ3')
			if request.session['ss_img_selectimagetype'] == 'machine':
				request.session['ss_img_kernel'] = form.cleaned_data['kernel']

				kernel_list = list(getSelectListKernelImage(image_model_List))

				""" ToDoもっときれいな方法があるはず・・・"""
				for k in kernel_list:
					if k[0] == form.cleaned_data['kernel']:
						request.session['ss_img_kernel_value'] = k[1]
						break

				request.session['ss_img_ramdisk'] = form.cleaned_data['ramdisk']

				ramdisk_list = list(getSelectListRamdiskImage(image_model_List))

				""" ToDoもっときれいな方法があるはず・・・"""
				for r in ramdisk_list:
					if r[0] == form.cleaned_data['ramdisk']:
						request.session['ss_img_ramdisk_value'] = r[1]
						break

			request.session['ss_img_imagepath'] = form.cleaned_data['image_path']

			return render_to_response('create_image_3.html',{'image_model_List':image_model_List},context_instance=RequestContext(request))
		else:
			message = []
			tmp_errors = form.errors.values()
			for error in tmp_errors:
				message.extend(error)
				logger.warn(error)

			return render_to_response('create_image_2.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))

	else:
		message = 'リクエストはGETにしてください'
		logger.warn(message)
		return render_to_response('create_image_2.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))

#OSイメージ作成ステップ2に戻る時の処理
def createstep2back(request):

	logger.info('OSイメージ作成のステップ3からステップ2へ戻る')
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#ログインユーザのイメージの一覧を取得
	images = get_euca_info.get_image()

	message=""
	#イメージモデルのリストを取得
	image_model_List = createImageModelList(images)

	form = ImageCreateStep2Form({'kernel':request.session['ss_img_kernel'],'ramdisk':request.session['ss_img_ramdisk'],'image_path':request.session['ss_img_imagepath']})
	form.fields['image_path'].update()
	form.fields['kernel'].choices = getSelectListKernelImage(image_model_List)
	form.fields['ramdisk'].choices = getSelectListRamdiskImage(image_model_List)

	return render_to_response('create_image_2.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))

#OSイメージの登録処理
def createstep3(request):

	logger.info('OSイメージ作成 Step3のOSイメージの登録処理')

	register = RegisterOSImage(request)
	image_id=""

	if request.session['ss_img_selectimagetype'] == 'machine':
		image_id = register.registerOSImage()
	elif request.session['ss_img_selectimagetype'] == 'kernel':
		image_id = register.registerKernel()
	elif request.session['ss_img_selectimagetype'] == 'ramdisk':
		image_id = register.registerRamdisk()
	else:
		logger.error('selectImageType error .')
		raise Exception('selectImageType error .')

	new_db_image = Image()
	new_db_image.image_id = image_id
	new_db_image.name = request.session['ss_img_name']
	new_db_image.description = request.session['ss_img_description']

	new_db_image.save()

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#ログインユーザのイメージの一覧を取得
	images = get_euca_info.get_image()

	#イメージモデルのリストを取得
	image_model_List = createImageModelList(images)

	selectImageNumber = 0;

	count = 0;
	for i in image_model_List:

		if image_id == i.id:
			selectImageNumber = count
			break

		count = count + 1

	#セッションに選択中のイメージナンバーの情報を保持する
	request.session['ss_img_selectNumber'] = selectImageNumber

	#セッションに選択中のイメージのＩＤの情報を保持する
	request.session['ss_img_selectID'] = image_id

	message = ""

	form = ImageModForm({'image_name':image_model_List[selectImageNumber].name,'image_description':image_model_List[selectImageNumber].description})

	logger.info('OSイメージ作成 完了 image_id=%s' % image_id)

	return render_to_response('image_list.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))

#イメージを削除する処理
def delete(request):

	logger.info('イメージの削除')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#ログインユーザのイメージの一覧を取得
	images = get_euca_info.get_image()

	message=""
	form = ImageModForm()

	if not 'ss_img_selectNumber' in request.session:
		#イメージモデルのリストを取得
		image_model_List = createImageModelList(images)
		return render_to_response('image_list.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))


	#イメージモデルのリストを取得
	image_model_List = createImageModelList(images)

	selected_image_model = None

	for image_model in image_model_List:
		if image_model.id == request.session['ss_img_selectID']:
				selected_image_model = image_model
				break

	deregister = DeregisterOSImage(selected_image_model)

	deregister.deregisterImage()

	selected_image_model.delete()

	#選択中のイメージをリストから削除する
	del image_model_List[request.session['ss_img_selectNumber']]

	if 'ss_img_selectNumber' in request.session:
		del request.session['ss_img_selectNumber']
	if 'ss_img_selectID' in request.session:
		del request.session['ss_img_selectID']

	logger.info('イメージの削除完了')

	return render_to_response('image_list.html',{'image_model_List':image_model_List,'form':form, 'message':message},context_instance=RequestContext(request))


#OSイメージモデルのリストを生成する
def createImageModelList(images=[]):
	image_model_List = []

	euca_metadata = EucalyptusMetadataDB()
	image_snapshot_list = euca_metadata.getImageSnapshotList()

	for image in images:
		if not Image.objects.filter(image_id=image.id):
			new_image = Image()
			new_image.image_id = image.id
			new_image.name = "新しいOSイメージ"
			new_image.description = ""
			new_image.save()
			logger.debug('新しいOSイメージを登録しました: %s' % image.id.encode('utf8'))

	for image in images:
		if image.type == "machine":
			#(account_id, owner) = getUserFromImage(image)
			#logger.debug("account_id:%s owner:%s" % (account_id, owner))
			image_model = euca_common.createImageModel(images, image.id)
			if image_model != None:
				if image_model.root_device_type == "ebs":
					for snap in image_snapshot_list:
						if snap.image_id == image_model.id:
							image_model.image_snapshot = snap.snapshot_id
							break
				image_model_List.append(image_model)

	return image_model_List

def getUserFromImage(image=None):
	if image == None:
		return

	# Eucalyptus3.0 ではOSイメージのonwerIdにアカウント番号が格納される
	# アカウントまでしか特定できないため、"admin"ユーザー固定で処理する
	""" TODO: 引数にユーザー情報追加、アカウント番号が一致する場合は自分のユーザー情報を使用する
	"""
	try:
		#アカウント番号 No.1のイメージは暫定的に管理者の所有物とする
		if image.ownerId == '000000000001':
			db_user_set = User.objects.filter(account_id='eucalyptus', user_id='admin')
		else:
			db_user_set = User.objects.filter(account_number=image.ownerId, user_id='admin')

		#指定したアカウントの管理者がUserテーブルに存在するか
		if len(db_user_set) != 0:
			#クエリセットから要素を抽出
				db_user = db_user_set[0]
				return image.owner_id, db_user.account_id
		else:
			return image.ownerId, None

	except User.DoesNotExist:
		return image.ownerId, None


#カーネル選択用のタプル値を取得する
def getSelectListKernelImage(images=[]):

	kernel_List =[]

	for image in images:
		if image.type != 'kernel':
			continue

		sub_kernel=[]
		sub_kernel.append(image.id)
		kernel_name = image.name + ' (' + image.id + ')'
		sub_kernel.append(kernel_name)
		kernel_List.append(sub_kernel)

	return tuple(kernel_List)

#ラムディスク選択用のタプル値を取得する
def getSelectListRamdiskImage(images=[]):

	ramdisk_List =[]

	for image in images:
		if image.type != 'ramdisk':
			continue

		sub_ramdisk=[]
		sub_ramdisk.append(image.id)
		ramdisk_name = image.name + ' (' + image.id + ')'
		sub_ramdisk.append(ramdisk_name)

		ramdisk_List.append(sub_ramdisk)

	return tuple(ramdisk_List)
