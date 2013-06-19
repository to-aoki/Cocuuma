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

import pgdb
import logging
#from koala.eucalyptus.models import User
from xml.etree.ElementTree import parse
from koala.settings import EUCA_DB_HOST
from koala.settings import EUCA_DB_PORT
from koala.settings import PROJECT_PATH
from report_models import *
from datetime import datetime
from time import strptime
from models import VMType
from decimal import *

# Eucalyptus 内部DB(PostgreSQL)クラス
#--------------------------------------------------------
class EucalyptusReportingDB(object):

	#カスタムログ
	logger = logging.getLogger('koalalog')

	# Eucalyptus内部DB 接続情報
	db_address = 'localhost'
	db_port = '8777'
	db_user = 'eucalyptus'
	db_name = 'eucalyptus_reporting'
	# 今のところ auth と同じ xml でアクセス可能
	jdbc_conf_path = PROJECT_PATH +'/data/ha_jdbc_auth.xml'
	db_passwd = None

	# コンストラクタ
	def __init__(self):

		# settings.py からEucalyptus内部DBへの接続情報を取得
		self.db_address = EUCA_DB_HOST
		self.db_port = EUCA_DB_PORT

		try:
			#ha_jdbc_auth.xmlをパース
			tree = parse(self.jdbc_conf_path)
			#ルート要素を取得(Element型)
			elm = tree.getroot()
			#条件にマッチする要素のテキストを返す
			self.db_passwd = elm.find('.//password').text

		except Exception, ex:
			self.logger.error("dataディレクトリの設定ファイル（ha_jdbc_reporting.xml）が正しいか確認してください")
			raise ex

	def getMonthList(self):
		result_list = []
		sql = "SELECT DISTINCT date_trunc('month', creation_timestamp)"
		sql = sql + " FROM instance_usage_snapshot ORDER by date_trunc('month', creation_timestamp) desc"
		month_list = self.executeQuery(sql)
		for month in month_list:
			month_str = month[0][0:7]
			result_list.append(month_str)
		return result_list

	# instance report info from Eucalyptus DB
	def getInstanceList(self, user=None, account=None, month=None):

		result_list = []
		result_sum = Charge_Instance_Model()
		sql =("SELECT instance_id, instance_type, creation_timestamp, uuid FROM reporting_instance")
		if account and account != 'all':
			sql = sql + " WHERE account_id = '" + account + "'"
			if user and user != 'all':
				sql = sql + " AND user_id = '" + user + "'"
		sql = sql + " ORDER by creation_timestamp desc"

		#self.logger.debug("query:%s" % sql)
		instance_list = self.executeQuery(sql)

		vmtypes = VMType.objects.all()

		if month and month != 'all':
			month = month + "-01 00:00:00"

		instance_id = ""
		for ins in instance_list:
			if instance_id == ins[0]:
				continue

			repo = Report_Instance_Model()
			sql = "SELECT min(creation_timestamp), max(creation_timestamp), count(creation_timestamp), sum(total_disk_io_megs), sum(total_network_io_megs)"
			sql = sql + " FROM instance_usage_snapshot"
			sql = sql + " WHERE uuid = '" + ins[3] + "'"
			if month and month != 'all':
				sql = sql + " AND date_trunc('month', creation_timestamp)='" + month + "'"
			instance_data = self.executeQuery(sql)

			if not instance_data[0][2]:
				continue
			# set instance data
			repo.instance_id = ins[0]
			repo.instance_type = ins[1]
			repo.start_time = ins[2][0:16]
			if instance_data[0][1]:
				repo.last_seen_time = instance_data[0][1][0:16]
				(repo.duration, repo.duration_hour) = duration(ins[2][0:16], instance_data[0][1][0:16])
			run_min = instance_data[0][2]*20
			repo.running_time = "%04d-%02d:%02d" % ( run_min//1440, (run_min//60)%24, run_min%60 )
			repo.running_hour = round(float(run_min)/60.0, 1)
			repo.disk_io = instance_data[0][3]
			repo.network_io = instance_data[0][4]
			vmtype = vmtypes.get(name=ins[1])
			repo.mem_gigabytes = round(float(vmtype.mem) / 1024.0, 1)
			repo.cores = vmtype.cpu
			if repo.running_hour > repo.duration_hour:
				repo.running_hour = repo.duration_hour
			result_list.append(repo)

			# add to sum
			if not month or month == 'all' or ins[2][0:7] == month[0:7]:
				result_sum.bootups += 1
			result_sum.cores_by_hours += vmtype.cpu * repo.running_hour
			result_sum.memgigabytes_by_hours += repo.mem_gigabytes * repo.running_hour
			if instance_data[0][3]:
				result_sum.disk_io_gigabytes += instance_data[0][3] / 8 / 1024
			if instance_data[0][4]:
				result_sum.network_io_gigabytes += instance_data[0][4] / 8 / 1024

			instance_id = ins[0]

		result_sum.disk_io_gigabytes = round(result_sum.disk_io_gigabytes,1)
		result_sum.network_io_gigabytes = round(result_sum.network_io_gigabytes,1)

		self.logger.info("instance report count %s" % len(result_list))

		return result_list, result_sum

	def getVolumeHistory(self, user, user_id, account_name, month=None):

		result_list = []
		result_sum = Report_Volume_History_Model()
		result_sum.user_id = user_id
		result_sum.account_name = account_name
		sql =("SELECT creation_timestamp, date_trunc('month', creation_timestamp), snapshot_megs, volumes_megs FROM storage_usage_snapshot")
		sql = sql + " WHERE owner_id = '" + user + "'"
		sql = sql + " ORDER by creation_timestamp"

		#self.logger.debug("query:%s" % sql)
		history = self.executeQuery(sql)

		last_h = None
		for h in history:
			if month and month != "all" and last_h:
				if h[1] != last_h[1]:
					if h[1][0:7] == month:
						last_h[0] = h[1]
					elif last_h[1][0:7] == month:
						h[0] = h[1]
					else:
						last_h = None
				elif h[1][0:7] != month:
					last_h = None

			if last_h:
				data = Report_Volume_Model()
				data.ebs_megabytes = float(last_h[3])
				data.snapshot_megabytes = float(last_h[2])
				data.start_time = last_h[0][0:16]
				data.end_time = h[0][0:16]
				(data.duration, data.duration_hour) = duration(data.start_time, data.end_time)
				result_list.append(data)
				result_sum.ebs_gigabytes_by_hours += data.ebs_megabytes / 1024 * data.duration_hour
				result_sum.snapshot_gigabytes_by_hours += data.snapshot_megabytes / 1024 * data.duration_hour

			last_h = h

		#result_sum.ebs_gigabytes_by_hours = result_sum.ebs_gigabytes_by_hours//1.0
		#result_sum.snapshot_gigabytes_by_hours = result_sum.snapshot_gigabytes_by_hours//1.0
		result_sum.history = result_list
		return result_sum

	def getWalrusHistory(self, user, user_id, account_name, month=None):

		result_list = []
		result_sum = Report_Walrus_History_Model()
		result_sum.user_id = user_id
		result_sum.account_name = account_name
		sql =("SELECT creation_timestamp, date_trunc('month', creation_timestamp), objects_megs, objects_num, date_trunc('hour', creation_timestamp) FROM s3_usage_snapshot")
		sql = sql + " WHERE owner_id = '" + user + "'"
		sql = sql + " ORDER by creation_timestamp"

		#self.logger.debug("query:%s" % sql)
		history = self.executeQuery(sql)

		last_h = None
		skip_h = None
		for h in history:
			if skip_h and skip_h[4] == h[4]:
				skip_h = h
				continue

			if month and month != "all" and last_h:
				if h[1] != last_h[1]:
					if h[1][0:7] == month:
						last_h[0] = h[1]
					elif last_h[1][0:7] == month:
						h[0] = h[1]
					else:
						last_h = None
				elif h[1][0:7] != month:
					last_h = None

			if last_h:
				data = Report_Walrus_Model()
				data.objects_megabytes = float(last_h[2])
				data.objects_num = last_h[3]
				data.start_time = last_h[0][0:16]
				data.end_time = h[0][0:16]
				(data.duration, data.duration_hour) = duration(data.start_time, data.end_time)
				result_list.append(data)
				result_sum.walrus_gigabytes_by_hours += data.objects_megabytes / 1024 * data.duration_hour

			last_h = h
			skip_h = h

		result_sum.walrus_gigabytes_by_hours = round(result_sum.walrus_gigabytes_by_hours, 1)
		result_sum.history = result_list
		return result_sum

	# execute sql to the eucalyptus database
	def executeQuery(self, sql):

		db_host = "%s:%s" % (self.db_address, self.db_port)

		try:
			db = pgdb.connect(host=db_host, user=self.db_user, database=self.db_name, password=self.db_passwd)
			cursor = db.cursor()
			cursor.execute(sql)
			result = cursor.fetchall()
			cursor.close()
			db.close()

		except Exception, ex:
			raise ex

		return result

def duration(start, end):

	end_time = datetime(*strptime(end, "%Y-%m-%d %H:%M")[0:6])
	start_time = datetime(*strptime(start, "%Y-%m-%d %H:%M")[0:6])
	dur = end_time - start_time
	result = "%04d-%02d:%02d" % (dur.days, dur.seconds//3600, (dur.seconds//60)%60)
	result_hour = float(dur.seconds)/3600.0 + dur.days * 24
	return result, round(result_hour, 1)

