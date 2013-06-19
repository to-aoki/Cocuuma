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

class Securitygroup_Model(object):

	def __init__(self,name=None,owner_id=None,description=None):
		self.name = name;				#セキュリティグループ名
		self.owner_id = owner_id		#オーナーID
		self.description = description 	#説明
		self.rules = []					#接続許可ルール


class Rule_Model(object):

	def __init__(self,ip_protocol=None,from_port=None,to_port=None):
		self.ip_protocol = ip_protocol;		#プロトコル
		self.from_port = from_port;			#解放ポート開始範囲
		self.to_port = to_port;				#解放ポート終了範囲
		self.from_user = None				#接続許可セキュリティグループオーナー
		self.from_group = None				#接続許可セキュリティグループ
		self.cidr = None					#接続許可アドレス範囲

	#接続許可セキュリティグループ
	@property
	def groupname(self):
		if self.from_user or self.from_group:
			if self.from_user:
				grant_string = "%s:" % self.from_user
			else:
				grant_string = ""
			if self.from_group:
				grant_string += self.from_group
		else:
			grant_string = None

		return grant_string
