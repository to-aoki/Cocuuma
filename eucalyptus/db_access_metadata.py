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
from image_model import Image_Snapshot
from resource_models import Volume_owner

# Eucalyptus 内部DB(PostgreSQL)クラス
#--------------------------------------------------------
class EucalyptusMetadataDB(object):

	#カスタムログ
	logger = logging.getLogger('koalalog')

	# Eucalyptus内部DB 接続情報
	db_address = 'localhost'
	db_port = '8777'
	db_user = 'eucalyptus'
	db_name = 'eucalyptus_cloud'
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

	def getImageSnapshotList(self):
		result_list = []
		sql = "SELECT metadata_display_name, metadata_image_snapshot_id"
		sql = sql + " FROM metadata_images WHERE NOT metadata_image_snapshot_id='None'"
		snapshotList = self.executeQuery(sql)
		for snap in snapshotList:
			image_snapshot = Image_Snapshot()
			image_snapshot.image_id = snap[0]
			image_snapshot.snapshot_id = snap[1]
			result_list.append(image_snapshot)
		return result_list

	def getVolumeOwnerList(self):
		result_list = []
		sql = "SELECT metadata_display_name, metadata_account_id, metadata_user_name"
		sql = sql + " FROM metadata_volumes"
		volumeOwnerList = self.executeQuery(sql)
		for vol in volumeOwnerList:
			vol_own = Volume_owner()
			vol_own.volumeid = vol[0]
			vol_own.account_number = vol[1]
			vol_own.user_name = vol[2]
			result_list.append(vol_own)
		return result_list

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

