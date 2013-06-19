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

from django.template import RequestContext
from django.shortcuts import render_to_response
from models import Image
from models import VMType
from models import Template
from template_model import Template_Model
from euca_access import GetEucalyptusInfo
from models import User
from user_model import User_Model
from template_form import TemplateModForm


import time
import euca_common
import logging

#テンプレート画面表示時に実行される処理
def top(request,template_id):

	#カスタムログ
	logger = logging.getLogger('koalalog')
	logger.info('テンプレート表示')

	#メニューを「テンプレート」に設定
	request.session['ss_sys_menu'] = "template"
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#テンプレートのデータモデルのリストを作成する
	template_model_List = createTemplateModelList(login_user)

	selectTemplateNumber = 0;

	logger.debug("select template_id=%s"  % template_id)

	if 'ss_tpl_selectNumber' in request.session:
		logger.debug("session=%s"  % request.session['ss_tpl_selectNumber'])

	if template_id != 'top':
		count = 0;
		for t in template_model_List:

			if template_id == t.id:
				selectTemplateNumber = count
				break

			count = count + 1

		#セッションに選択中のテンプレートナンバーの情報を保持する
		request.session['ss_tpl_selectNumber'] = selectTemplateNumber
		#セッションに選択中のテンプレートのID情報を保持する
		request.session['ss_tpl_selectID'] = template_id

		logger.debug('selectTemplateNumber=%s' % request.session['ss_tpl_selectNumber'])
		logger.debug('selectTemplateid=%s'  % request.session['ss_tpl_selectID'])
	elif 'ss_tpl_selectNumber' in request.session:
			del request.session['ss_tpl_selectNumber']
	elif 'ss_tpl_selectID' in request.session:
			del request.session['ss_tpl_selectID']

	#template_model_Listをセッションに渡すとエラー起こる・・・

	logger.info('テンプレート表示完了')

	return render_to_response('template_list.html',{'template_model_List':template_model_List},context_instance=RequestContext(request))

#テンプレート修正画面表示時に実行される処理
def mod(request):

	#カスタムログ
	logger = logging.getLogger('koalalog')
	logger.info('テンプレート修正')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	if not 'ss_tpl_selectNumber' in request.session:
		template_model_List = []
		return render_to_response('template_list.html',{'template_model_List':template_model_List},context_instance=RequestContext(request))

	#選択中のテンプレートの位置を取得する
	selectTemplateNumber = request.session['ss_tpl_selectNumber']

	logger.debug("template_id=%s "  % selectTemplateNumber)

	#テンプレートのデータモデルのリストを作成する
	template_model_List = createTemplateModelList(login_user)

	if len(template_model_List) <= 0:
		return render_to_response('template_list.html',{'template_model_List':template_model_List},context_instance=RequestContext(request))

	selectedTemplate = template_model_List[selectTemplateNumber]

	form = TemplateModForm({'name':selectedTemplate.name,'description':selectedTemplate.description,'count':selectedTemplate.count,'image':selectedTemplate.image.id,'vmtype':selectedTemplate.vmtype.vmtype})

	#ToDo Eucalyptusへの短時間接続エラー無理やり回避策
	time.sleep(1)

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#リスト型をタプル型に変換して値を渡す
	form.fields['image'].choices = getSelectListImage(get_euca_info)
	form.fields['vmtype'].choices = getSelectListVMType(get_euca_info)

	#エラーメッセージなし
	message = ""

	return render_to_response('modify_template.html',{'template_model_List':template_model_List,'form':form, 'message':message },context_instance=RequestContext(request))

#テンプレート修正処理時に呼び出されるメソッド
def domod(request):

	#カスタムログ
	logger = logging.getLogger('koalalog')
	logger.info('テンプレート修正 保存ボタン押下')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#選択中のテンプレートの位置を取得する
	selectTemplateNumber = request.session['ss_tpl_selectNumber']

	logger.debug("template_id=%s "  % selectTemplateNumber)

	#テンプレートのデータモデルのリストを作成する
	template_model_List = createTemplateModelList(login_user)

	selectedTemplate = template_model_List[selectTemplateNumber]

	form = TemplateModForm(request.POST)

	#ToDo Eucalyptusへの短時間接続エラー無理やり回避策
	time.sleep(1)

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#リスト型をタプル型に変換して値を渡す
	form.fields['image'].choices = getSelectListImage(get_euca_info)
	form.fields['vmtype'].choices = getSelectListVMType(get_euca_info)

	#保存ボタンを押下した時の処理
	if form.is_valid():
		logger.info('テンプレート修正 保存')
		selectedTemplate.name = form.cleaned_data['name']
		selectedTemplate.description = form.cleaned_data['description']
		selectedTemplate.count = form.cleaned_data['count']


		#ToDo Eucalyptusへの短時間接続エラー無理やり回避策
		time.sleep(1)

		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)

		#ログインユーザのイメージの一覧を取得
		images = get_euca_info.get_image()

		selectImage = form.cleaned_data['image']
		selectVMType = form.cleaned_data['vmtype']

		logger.debug('selectImage = %s ' % selectImage)
		logger.debug('selectVMType = %s' % selectVMType)

		if euca_common.createImageModel(images, selectImage) != None:
			selectedTemplate.image = euca_common.createImageModel(images, selectImage)

		# Apache対応（VMTypesオブジェクトを取得できるよう、DBからユーザ情報を取得）
		#db_user = User.objects.get(account_id=login_user.account_id, user_id=login_user.id)
		#vmtypes = get_euca_info.get_vmtypes(db_user)

		if euca_common.createVMTypeModel(selectVMType) != None:
			selectedTemplate.vmtype = euca_common.createVMTypeModel(selectVMType)

		logger.info('テンプレート修正 完了')

		return render_to_response('template_list.html',{'template_model_List':template_model_List},context_instance=RequestContext(request))

	else:
		#エラーメッセージ
		message = []
		tmp_errors = form.errors.values()
		for error in tmp_errors:
			message.extend(error)
			logger.warn(error)

		return render_to_response('modify_template.html',{'template_model_List':template_model_List,'form':form, 'message':message },context_instance=RequestContext(request))


#テンプレートを新規作成する処理
def create(request):

	#カスタムログ
	logger = logging.getLogger('koalalog')
	logger.info('テンプレート新規作成')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#テンプレートのデータモデルのリストを作成する
	template_model_List = createTemplateModelList(login_user)

	form = TemplateModForm()

	#ToDo Eucalyptusへの短時間接続エラー無理やり回避策
	time.sleep(1)

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#リスト型をタプル型に変換して値を渡す
	form.fields['image'].choices = getSelectListImage(get_euca_info)
	form.fields['vmtype'].choices = getSelectListVMType(get_euca_info)

	#エラーメッセージなし
	message = ""

	return render_to_response('create_template.html',{'template_model_List':template_model_List,'form':form ,'message':message},context_instance=RequestContext(request))


#テンプレートを新規作成する処理
def docreate(request):

	#カスタムログ
	logger = logging.getLogger('koalalog')
	logger.info('テンプレート新規作成 作成ボタン押下')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#テンプレートのデータモデルのリストを作成する
	template_model_List = createTemplateModelList(login_user)

	form = TemplateModForm(request.POST)

	#ToDo Eucalyptusへの短時間接続エラー無理やり回避策
	time.sleep(1)

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#リスト型をタプル型に変換して値を渡す
	form.fields['image'].choices = getSelectListImage(get_euca_info)
	form.fields['vmtype'].choices = getSelectListVMType(get_euca_info)

	#保存ボタンを押下した時の処理
	if form.is_valid():
		logger.info('テンプレート新規作成 作成実施')
		#ToDo Eucalyptusへの短時間接続エラー無理やり回避策
		time.sleep(1)

		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)

		#ログインユーザのイメージの一覧を取得
		images = get_euca_info.get_image()

		selectImage = form.cleaned_data['image']
		selectVMType = form.cleaned_data['vmtype']

		new_image_model = euca_common.createImageModel(images, selectImage)

		# Apache対応（VMTypesオブジェクトを取得できるよう、DBからユーザ情報を取得）
		#db_user = User.objects.get(account_id = login_user.account_id, user_id = login_user.id)
		#vmtypes = get_euca_info.get_vmtypes(db_user)

		new_vmtype_model = euca_common.createVMTypeModel(selectVMType)

		new_db_template = Template()

		new_db_template.name = form.cleaned_data['name']
		new_db_template.description = form.cleaned_data['description']
		new_db_template.count = form.cleaned_data['count']
		new_db_template.account_id = login_user.account_id
		new_db_template.user_id = login_user.id
		new_db_template.image_id = selectImage
		new_db_template.vmtype = selectVMType

		if login_user.admin == True:
			new_db_template.kind = 1
		else:
			new_db_template.kind = 0

		#DBに登録
		new_db_template.save()

		#新規登録したテンプレートのモデルを生成する
		new_template_model = Template_Model(new_db_template, login_user, new_image_model, new_vmtype_model )

		template_model_List.append(new_template_model)

		#新規作成したテンプレートを選択状態にする

		#セッションに選択中のテンプレートナンバーの情報を保持する
		request.session['ss_tpl_selectNumber'] = len(template_model_List) - 1

		#セッションに選択中のテンプレートナンバーの情報を保持する
		request.session['ss_tpl_selectID'] = new_db_template.id

		logger.info('テンプレート新規作成 完了')

		return render_to_response('template_list.html',{'template_model_List':template_model_List},context_instance=RequestContext(request))

	else:
		message = []
		tmp_errors = form.errors.values()
		for error in tmp_errors:
			message.extend(error)
			logger.warn(error)

		return render_to_response('create_template.html',{'template_model_List':template_model_List,'form':form ,'message':message},context_instance=RequestContext(request))

#テンプレートを削除する時の処理
def delete(request):
	#カスタムログ
	logger = logging.getLogger('koalalog')
	logger.info('テンプレート削除')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	if not 'ss_tpl_selectNumber' in request.session:
		template_model_List = createTemplateModelList(login_user)
		return render_to_response('template_list.html',{'template_model_List':template_model_List},context_instance=RequestContext(request))

	#選択中のテンプレートの位置を取得する
	selectTemplateNumber = request.session['ss_tpl_selectNumber']

	#テンプレートのデータモデルのリストを作成する
	template_model_List = createTemplateModelList(login_user)

	if len(template_model_List) <= 0:
		return render_to_response('template_list.html',{'template_model_List':template_model_List},context_instance=RequestContext(request))

	#選択中のテンプレートを取得する
	selectedTemplate = template_model_List[selectTemplateNumber]

	#選択中のテンプレートをDBから削除する
	selectedTemplate.delete()

	#選択中のテンプレートをリストから削除する
	del template_model_List[selectTemplateNumber]

	#セッションに選択中のテンプレートナンバーの情報を保持する
	request.session['ss_tpl_selectNumber'] = 0

	if 'ss_tpl_selectNumber' in request.session:
		del request.session['ss_tpl_selectNumber']

	if 'ss_tpl_selectID' in request.session:
		del request.session['ss_tpl_selectID']

	logger.info('テンプレート削除 完了')

	return render_to_response('template_list.html',{'template_model_List':template_model_List},context_instance=RequestContext(request))


#テンプレートのモデルのリストを生成する
def createTemplateModelList(login_user=None):
	template_model_List = []
	if login_user == None:
		return []

	#テンプレートdbのオブジェクトをすべて取得する
	db_templateList = Template.objects.all()

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)

	#ログインユーザのイメージの一覧を取得
	images = get_euca_info.get_image()
	#リソースの一覧を取得する

	# Apache対応（VMTypesオブジェクトを取得できるよう、DBからユーザ情報を取得）
	#db_user = User.objects.get(account_id=login_user.account_id, user_id=login_user.id)
	#vmtypes = get_euca_info.get_vmtypes(db_user)

	for db_template in db_templateList:

		vmtype_model = euca_common.createVMTypeModel(db_template.vmtype)

		if vmtype_model == None:
			continue

		db_user = User.objects.get(account_id=db_template.account_id, user_id=db_template.user_id)
		if db_user == None:
			continue

		templete_user = User_Model(db_user)

		image_model = euca_common.createImageModel(images, db_template.image_id)

		if image_model == None:
			continue

		template_model = Template_Model(db_template,templete_user,image_model,vmtype_model)
		template_model_List.append(template_model)

	return template_model_List



#Image選択用のタプル値を取得する
def getSelectListImage(get_euca_info=None):
	if get_euca_info == None:
		return ()

	#ログインユーザのイメージの一覧を取得
	images = get_euca_info.get_image()

	#イメージ用のリストを生成
	image_value = []

	for image in images:
		if image.type != 'machine':
			continue

		try:
				db_image = Image.objects.get(image_id=image.id)
		except:
				continue

		subimage=[]
		subimage.append(db_image.image_id)
		subimage.append(db_image.name)
		image_value.append(subimage)

	return tuple(image_value)

#VMType選択用のタプル値を取得する
def getSelectListVMType(get_euca_info=None):

	if get_euca_info == None:
		return ()

	#VMType用のリストを生成
	vmtype_value = []
	db_vmtypes = VMType.objects.all()
	for vmtype in db_vmtypes:
		sub_vmtype=[]
		sub_vmtype.append(vmtype.vmtype)
		sub_vmtype.append(vmtype.full_name)
		vmtype_value.append(sub_vmtype)

	return tuple(vmtype_value)

