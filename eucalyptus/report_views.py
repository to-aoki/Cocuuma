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
from db_access import EucalyptusDB
from db_access_reporting import EucalyptusReportingDB
from models import Charge
from report_models import Charge_Model, Charge_Volume_Model, Charge_Walrus_Model
#from django.db.models import Q
#import euca_common
#import re
import logging
import datetime

#カスタムログ
logger = logging.getLogger('koalalog')

def top(request):
	"""レポートメニューの初期表示"""

	logger.info('レポート表示')

	#メニューを「IPアドレス」に設定
	request.session['ss_sys_menu'] = "dashboard"

	auth_db = EucalyptusDB()

	#ポイントの表示／非表示
	if not 'pointdisplay' in request.POST:
		request.session['pointdisplay'] = "no"
		logger.debug("pointdisplay undefined")
	else:
		request.session['pointdisplay'] = request.POST['pointdisplay']
		logger.debug("pointdisplay : %s" % request.POST['pointdisplay'])

	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	if not 'account_selected' in request.POST:
		account = login_user.account_number
		user = auth_db.getUserInternalId(account, login_user.id)
	else:
		account = request.POST['account_selected']
		if not 'user_selected' in request.POST:
			user = "all"
		else:
			user = request.POST['user_selected']

	request.session['account_selected'] = account
	logger.debug("selected account : %s" % account)

	request.session['user_selected'] = user
	logger.debug("selected user : %s" % user)

	#レポート参照権限の設定(TODO: policy参照の必要)
	request.session['account_admin'] = "no"
	request.session['user_admin'] = "no"
	if login_user.id == "admin":
		request.session['user_admin'] = "yes"
		if login_user.account_id == "eucalyptus":
			request.session['account_admin'] = "yes"

	db = EucalyptusReportingDB()

	if not 'month_selected' in request.POST:
		month = datetime.datetime.now().strftime(u"%Y-%m")
	else:
		month = request.POST['month_selected']
	request.session['month_selected'] = month
	logger.debug("selected month : %s" % month)

	(request.session['ss_repo_instancelist'], request.session['ss_sum_instance']) = db.getInstanceList(user, account, month)

	# volume report:
	volume_report = []
	account_list = auth_db.getAccountList()
	if account == "all":
		for a in account_list:
			user_list = auth_db.getUserListInAccount(a.id_number)
			for u in user_list:
				volume_report.append(db.getVolumeHistory(u.user_internal_id, u.user_id, a.name, month))
	else:
		if user == "all":
			user_list = auth_db.getUserListInAccount(account)
			for u in user_list:
				volume_report.append(db.getVolumeHistory(u.user_internal_id, u.user_id, "none", month))
		else:
			volume_report.append(db.getVolumeHistory(user, "none", "none", month))
	request.session['ss_repo_volumehistory'] = volume_report
	volume_sum = Charge_Volume_Model()
	for r in volume_report:
		volume_sum.ebs_gigabytes_by_hours += r.ebs_gigabytes_by_hours
		volume_sum.snapshot_gigabytes_by_hours += r.snapshot_gigabytes_by_hours

	# walrus report:
	walrus_report = []
	account_list = auth_db.getAccountList()
	if account == "all":
		for a in account_list:
			user_list = auth_db.getUserListInAccount(a.id_number)
			for u in user_list:
				walrus_report.append(db.getWalrusHistory(u.user_internal_id, u.user_id, a.name, month))
	else:
		if user == "all":
			user_list = auth_db.getUserListInAccount(account)
			for u in user_list:
				walrus_report.append(db.getWalrusHistory(u.user_internal_id, u.user_id, "none", month))
		else:
			walrus_report.append(db.getWalrusHistory(user, "none", "none", month))
	request.session['ss_repo_walrushistory'] = walrus_report
	walrus_sum = Charge_Walrus_Model()
	for r in walrus_report:
		walrus_sum.walrus_gigabytes_by_hours += r.walrus_gigabytes_by_hours

	at = Charge.objects.get(charge="デフォルト時間課金")
	charge = Charge_Model()
	charge.bootups = at.boot * request.session['ss_sum_instance'].bootups
	charge.cores = at.cpu * request.session['ss_sum_instance'].cores_by_hours
	charge.mem = at.mem * request.session['ss_sum_instance'].memgigabytes_by_hours
	charge.disk_io = at.disk * request.session['ss_sum_instance'].disk_io_gigabytes
	charge.net_io = at.net * request.session['ss_sum_instance'].network_io_gigabytes
	charge.ebs = at.ebs * volume_sum.ebs_gigabytes_by_hours
	charge.snapshot = at.snapshot * volume_sum.snapshot_gigabytes_by_hours
	charge.walrus = at.walrus * walrus_sum.walrus_gigabytes_by_hours

	request.session['ss_sum_volume'] = volume_sum
	request.session['ss_sum_walrus'] = walrus_sum
	request.session['ss_charge_at'] = at
	request.session['ss_charge'] = charge

	request.session['ss_month_list'] = db.getMonthList()

	request.session['ss_account_list'] = account_list
	if account != "all":
		request.session['ss_user_list'] = auth_db.getUserListInAccount(account)
		logger.info('ユーザリスト：%s' % len(request.session['ss_user_list']))

	#Eucalyptus基盤へのアクセサを生成する
	#get_euca_info=GetEucalyptusInfo(login_user)

	logger.info('レポート表示 完了')

	return render_to_response('report.html',{},context_instance=RequestContext(request))

