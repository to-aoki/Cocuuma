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
from django.template import RequestContext
from django.shortcuts import render_to_response
from login_form import LoginTextForm
from models import User
from user_model import User_Model
from django.utils import dateformat
from datetime import datetime
from http import EucalyptusHttpAuthenticator
from db_access import EucalyptusDB
from koala.management.commands.batch_common import BatchCommon

from version import CocuumaVersion

import logging


#カスタムログ
logger = logging.getLogger('koalalog')

#ログイン画面表示時の処理
def login(request):
	logger.info('ログイン画面')

	message='アカウントID、ユーザーIDとパスワードを入力後、ログインをクリックしてください。'
	form = LoginTextForm()
	return render_to_response('login.html',{'form':form,'message':message}, context_instance=RequestContext(request))

#ログイン処理
def dologin(request):
	logger.info('ログイン処理実行')

	message='アカウントID、ユーザーID、またはパスワードが違います。'
	form = LoginTextForm(request.POST)
	if form.is_valid():
		try:
			account_id=form.cleaned_data['account_id']
			user_id=form.cleaned_data['user_id']
			password=form.cleaned_data['user_password']

			logger.debug('account_id=%s, user_id=%s' % (account_id, user_id) )

			if not EucalyptusHttpAuthenticator.get_session_id_by_global_setting(account_id, user_id, password):
				logger.error('eucalyptus frontend auth error :%s' % user_id)
				raise StandardError('eucalyptus frontend auth error : ' + user_id)

			request.session['newuser']='no'
			if not User.objects.filter(user_id=user_id, account_id=account_id):
				logger.warn('user not imported to koala :%s' % user_id)
				db = EucalyptusDB()
				user_list = db.getEucalyptusUser()
				found = False
				for user in user_list:
					if user.user_id == user_id and user.account_id == account_id:
						if not user.accesskey:
							message = "このユーザにはアクセスキーが発行されていません。"
							raise StandardError('no accesskey error : ' + user_id)
						user.name = user_id + "@" + account_id
						if user_id == "admin":
							user.permission = "11111111"
							user.admin = True
						else:
							if not User.objects.filter(user_id="admin", account_id=account_id):
								message = "アカウント管理者(admin)の登録がありません。"
								raise StandardError('no account admin error : ' + account_id)								
						found = True
						logger.info('user added to koala :' + user.name)
						batch = BatchCommon()
						if not batch.createKeyPair(user):
							message = "キーペアを作成できません"
							raise StandardError('creating keypair error : ' + user.name)								
						if user_id == "admin":
							batch.setSecurityGroup(user)
							logger.info('mykey created (renewed) for account:' + user.account_id)
						user.save()
						request.session['newuser']='yes'
						break
				if not found:
					raise StandardError('cannot imported user to koala : ' + user_id)

			login_user = User_Model(User.objects.get(user_id=user_id, account_id=account_id))
			logger.debug('login_user=%s' % login_user.name)
			request.session['ss_usr_user']=login_user
			dateStr=dateformat.format(datetime.now(), 'Y年n月d日')
			request.session['ss_usr_lastlogin']=dateStr
			if login_user.resource_admin:
				logger.debug("リソース管理者としてログイン")
			else:
				logger.debug("ユーザとしてログイン")
			logger.info('ログイン 完了')
			ver = CocuumaVersion()
			logger.info('Cocuuma version %s / revision %s' % (ver.getVersion(), ver.getLocalRevision()))
			return HttpResponseRedirect('/dashboard/')

		except Exception, e:
			logger.debug('Login Exception: %s' % e)
			logger.warn('ログイン失敗')

	return render_to_response('login.html',{'form':form,'message':message}, context_instance=RequestContext(request))

#ログアウト処理
def logout(request):
	logger.info('ログアウト処理')

	message='アカウントID、ユーザーIDとパスワードを入力後、ログインをクリックしてください。'
	if 'ss_usr_user' in request.session:
		login_user = request.session['ss_usr_user']
		form = LoginTextForm({'account_id':login_user.account_id, 'user_id':login_user.id})
	else:
		form = LoginTextForm()

	# セッションをクリアする
	request.session.clear()

	logger.info('ログアウト 完了')
	return render_to_response('login.html',{'form':form,'message':message}, context_instance=RequestContext(request))

# Create your views here.
