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

class VolumeData(object):

	def __init__(self,db_object=None):
		self.db_object = db_object		#DBデータ
		self.size = None				#サイズ
		self.snapshot_id = ""			#スナップショットID
		self.snapshot_name = ""			#スナップショット名
		self.zone = None				#availabilityZone
		self.status = None				#ステータス
		self.createTime = None			#作成日時
		self.machine_name = ""			#仮想マシン名
		self.attached = False			#アタッチフラグ
		self.instance_id = ""			#アタッチ時：インスタンスID
		self.device = ""				#アタッチ時：デバイス
		self.attach_status = ""			#アタッチ時：アタッチ状況
		self.attach_time = ""			#アタッチ時：アタッチ日時
		self.root_device = False		#ルートデバイス

	@property
	def db(self):
		return self.db_object

	@db.setter
	def db(self, db_object):
		self.db_object = db_object


class SnapshotData(object):

	def __init__(self,db_object=None):
		#self.db_object = db_object		#DBデータ
		self.id = None					#スナップショットID
		self.volume_id = None			#ボリュームID
		self.start_time = None			#作成日時
		self.status = None				#ステータス
		self.progress = None			#進行状況
		self.owner_id = None			#オーナーID
		self.volume_size = None			#作成元ボリュームサイズ(Eucalyptus3.0から有効)
		self.image = None

