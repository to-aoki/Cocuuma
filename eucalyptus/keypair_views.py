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
from django.http import HttpResponse
from euca_access import GetEucalyptusInfo
import euca_common
import models
import keypair_form
import logging

#カスタムログ
logger = logging.getLogger('koalalog')

def top(request):
	"""接続鍵メニューの初期表示"""

	logger.info('接続鍵 一覧表示')

	#メニューを「接続鍵」に設定
	request.session['ss_sys_menu'] = "keypair"

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#エラー情報
	errors = []

	#入力フォーム
	form = keypair_form.KeypairForm()

	#キーペア一覧を取得
	try:
		keypairlist = getKeypairList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]

	#セッション情報
	request.session['ss_key_keypairlist'] = keypairlist

	logger.info('接続鍵 一覧表示 完了')

	return render_to_response('keypair_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))


def create(request):
	"""接続鍵を作成ボタン"""

	logger.info('接続鍵 作成')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#エラー情報
	errors = []

	#入力フォーム
	form = keypair_form.KeypairForm(request.POST)

	# 入力チェック
	if not form.is_valid():
		tmp_errors = form.errors.values()
		for error in tmp_errors:
			errors.extend(error)
		return render_to_response('keypair_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))

	try:
		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)
		# キーペアを作成
		keypair = get_euca_info.create_keypair(form.cleaned_data['name'])
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]

	#DBへキーペア情報を登録
	db_keypair = models.Keypair()
	db_keypair.user_id = login_user.id
	db_keypair.account_id = login_user.account_id
	db_keypair.name = form.cleaned_data['name']
	db_keypair.data = keypair.material
	db_keypair.save()

	#キーペア一覧を取得
	try:
		keypairlist = getKeypairList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]

	#セッション情報
	request.session['ss_key_keypairlist'] = keypairlist

	logger.info('接続鍵 作成 完了')

	return render_to_response('keypair_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))


def delete(request, keyname):
	"""削除ボタン"""

	logger.info('接続鍵 削除')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#エラー情報
	errors = []

	#入力フォーム
	form = keypair_form.KeypairForm(request.POST)

	#Eucalyptus操作
	try:
		#Eucalyptus基盤へのアクセサを生成する
		get_euca_info=GetEucalyptusInfo(login_user)
		# キーペアを削除
		#keypair = get_euca_info.delete_keypair(keyname)
		get_euca_info.delete_keypair(keyname)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]

	#DBへキーペア情報を削除
	models.Keypair.objects.filter(user_id=login_user.id,account_id=login_user.account_id,name=keyname).delete()

	#キーペア一覧を取得
	try:
		keypairlist = getKeypairList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors = [euca_common.get_euca_error_msg('%s' % ex)]

	#セッション情報
	request.session['ss_key_keypairlist'] = keypairlist

	logger.info('接続鍵 削除 完了')

	return render_to_response('keypair_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))


def download(request, keyname):
	"""ダウンロードボタン"""

	logger.info('接続鍵 ダウンロード')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#エラー情報
	errors = []

	#入力フォーム
	form = keypair_form.KeypairForm(request.POST)

	#DB情報を参照
	db_keypairlist = models.Keypair.objects.filter(user_id=login_user.id,account_id=login_user.account_id,name=keyname)

	if not db_keypairlist:
		# 存在しないキーペアが指定された場合
		errors.append("接続鍵ファイルは保管されていません。")
		return render_to_response('keypair_list.html',{'form':form,'errors':errors},context_instance=RequestContext(request))
	else:
		response = HttpResponse(db_keypairlist[0].data, mimetype="application/octet-stream; charset=UTF-8")
		response['Content-Disposition'] = "attachment; filename=%s.pem" % db_keypairlist[0].name
		logger.info('接続鍵 ダウンロード 完了')
		return response


def getKeypairList(login_user=None):
	"""キーペアのリストを取得
		input: login_user:models.User
		return: [["キーペア名", "フィンガープリント", ダウンロード可否]]
	"""
	if login_user == None:
		return []

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo(login_user)
	# キーペア一覧を取得
	keypairs = get_euca_info.get_keypairs()
	# キーペア一覧を選択リストへ設定
	keypairlist = []
	for keypair in keypairs:
		sub_keypair = []
		sub_keypair.append(keypair.name)			# 鍵名
		sub_keypair.append(keypair.fingerprint)		#フィンガープリント
#		if keypair.name in db_keypairlist:			#ダウンロード可否
		if models.Keypair.objects.filter(user_id=login_user.id, account_id=login_user.account_id, name=keypair.name):
			sub_keypair.append(True)
		else:
			sub_keypair.append(False)
		keypairlist.append(sub_keypair)

	return keypairlist