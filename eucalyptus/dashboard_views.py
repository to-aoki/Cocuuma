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

from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from euca_access import GetCredential
from koala.settings import EUCA_HOST
import euca_common
from models import Keypair
from machine_views import getMachineGroupList

import logging
import commands

#ダッシュボードのトップ画面が表示された時の処理
def top(request):

	#カスタムログ
	logger = logging.getLogger('koalalog')
	logger.info('ダッシュボード画面表示')

	#メニューを「ダッシュボード」に設定
	request.session['ss_sys_menu'] = "dashboard"

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	isNewuser = request.session['newuser']
	request.session['newuser'] = 'no'

	#エラー情報
	errors = []

	#仮想マシン利用状況
	try:
		login_user.usevm = euca_common.countActiveMachine(login_user)
		#仮想サーバ一覧表示用
		machineGroupList = getMachineGroupList(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("仮想マシン情報の参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		login_user.usevm = login_user.db_user.maxvm

	request.session['ss_mch_list'] = machineGroupList

	if login_user.usevm == 0:
		login_user.ratiovm = 1
	elif login_user.usevm >= login_user.db_user.maxvm:
		login_user.ratiovm = 100
	else:
		login_user.ratiovm = login_user.usevm * 100 / login_user.db_user.maxvm

	#ボリューム利用状況
	try:
		login_user.usevol = euca_common.countActiveVolume(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("ボリューム情報の参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		login_user.usevol = login_user.db_user.maxvol

	if login_user.usevol == 0:
		login_user.ratiovol = 1
	elif login_user.usevol >= login_user.db_user.maxvol:
		login_user.ratiovol = 100
	else:
		login_user.ratiovol = login_user.usevol * 100 / login_user.db_user.maxvol

	#IPアドレス利用状況
	try:
		login_user.useip = euca_common.countAllocatedAddress(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("IPアドレス情報の参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		login_user.useip = login_user.db_user.maxip

	try:
		login_user.assip = euca_common.countAssociatedAddress(login_user)
	except Exception, ex:
		# Eucalyptusエラー
		errors.append("IPアドレス情報の参照に失敗しました。")
		errors.append(euca_common.get_euca_error_msg('%s' % ex))
		login_user.assip = login_user.db_user.maxip

	if login_user.assip == 0:
		login_user.ratioip = 1
	elif login_user.assip >= login_user.useip:
		login_user.ratioip = 100
	else:
		login_user.ratioip = login_user.assip * 100 / login_user.useip

	db_keypairlist = Keypair.objects.filter(user_id=login_user.id,account_id=login_user.account_id)
	
	# セッション情報のオブジェクト内部が変更されていることを通知
	request.session.modified = True

	logger.info('ダッシュボード画面表示 完了')

	return render_to_response('dashboard.html',{'errors':errors,'newuser_alert':isNewuser,'default_keypair':db_keypairlist[0].name},context_instance=RequestContext(request))

def keypair(request):

	#カスタムログ
	logger = logging.getLogger('koalalog')
	logger.info('接続鍵ファイル[mykey]ダウンロード開始')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	#DB情報を参照
	db_keypairlist = Keypair.objects.filter(user_id=login_user.id,account_id=login_user.account_id)

	if not db_keypairlist:
		# 存在しないキーペアが指定された場合
		logger.warn("接続鍵ファイル[mykey]は保管されていません。")
		return render_to_response('dashboard.html',{'dashboard':'MyKeyError'},context_instance=RequestContext(request))
	else:
		response = HttpResponse(db_keypairlist[0].data, mimetype="application/octet-stream; charset=UTF-8")
		response['Content-Disposition'] = "attachment; filename=%s.pem" % db_keypairlist[0].name
		logger.info("接続鍵ファイル[mykey]ダウンロード完了")
		return response

#ダッシュボードの証明書ボタンが押下された時の処理
def credentials(request):

	#カスタムログ
	logger = logging.getLogger('koalalog')
	logger.info('証明書ボタン押下')

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	try:
		get_credential = GetCredential(login_user)
		credential_url = get_credential.getCredential()
		response = HttpResponse(open( credential_url,"rb").read(), mimetype="application/zip")
		response["Content-Disposition"] = "attachment; filename="+get_credential.getCredentialName()
		logger.info('証明書 取得完了')
		return response

	except:
		logger.warn('証明書取得に失敗 ')
		logger.info('証明書再取得開始')

		cmd_ch ='wget --no-check-certificate "https://'+EUCA_HOST+':8443/getX509?user='+login_user.id+'&code='+login_user.accesskey+'" -O ./credentials/euca2-'+login_user.id+'-x509.zip'
		logger.debug('download credentials=%s' % cmd_ch)
		ret = commands.getstatusoutput(cmd_ch)

		if ret[0] != 0:
			logger.warn('wget --no-check-certificate command error.response=%s' % ret[0])
			logger.warn('証明書再取得に失敗 ')

			return render_to_response('dashboard.html',{'dashboard':'CredentialsError'},context_instance=RequestContext(request))

		try:
			get_credential = GetCredential(login_user)
			credential_url = get_credential.getCredential()
			response = HttpResponse(open( credential_url,"rb").read(), mimetype="application/zip")
			response["Content-Disposition"] = "attachment; filename="+get_credential.getCredentialName()
			logger.info('証明書 再取得完了')
			return response

		except:
			logger.warn('証明書再取得に失敗 ')
			return render_to_response('dashboard.html',{'dashboard':'CredentialsError'},context_instance=RequestContext(request))
