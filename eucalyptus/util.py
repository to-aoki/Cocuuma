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

#
# リスト形式のデータモデルに未対応

from django.utils import simplejson

class utils(object):

	#オブジェクトをjson形式で取得する
	def get_json(self,datamodel=None):
		if datamodel == None:
			return None
		dict_list = datamodel.__dict__.items()
		jsonstr = '{'
		for d in dict_list:
			try:
				judge = int(d[0])
				if type(d[0]) == bool:
					jsonstr = jsonstr + "'" + str(d[0]) +"'"
				else:
					jsonstr = jsonstr + str(d[0])
			except:
				jsonstr = jsonstr + "'" + str(d[0]) +"'"
			try:
				judge = int(d[1])
				if type(d[1]) == bool:
					jsonstr = jsonstr + ':' + "'" + str(d[1]) + "'"+ ','
				else:
					jsonstr = jsonstr + ':' + str(d[1])
			except:
				jsonstr = jsonstr + ':' + "'" + str(d[1]) + "'"+ ','

		jsonstr = jsonstr.strip(',')
		jsonstr = jsonstr + '}'
		return jsonstr

	#json形式で利用するキー値を取得する
	def get_key_value(self,datamodel=None,key=""):
		if datamodel == None:
			return None
		dict_list = datamodel.__dict__.items()
		for d in dict_list:
			if key == d[0]:
				keystr = ""
				try:
					judge = int(d[1])
					if type(d[1]) == bool:
                                		keystr = "'" + str(d[1]) + "'"
					else:
						keystr = str(d[1])
                        	except:
                                	keystr = "'" + str(d[1]) + "'"
				return keystr
		return None

	#オブジェクトのリストをjson形式で取得する
	def get_list_json(self,datalist=[],key=""):
		if len(datalist) == 0:
			return None
		jsonstr = '{'
		try:
			for data in datalist:
				str1 = self.get_json(data);
				keyvalue = self.get_key_value(data,key);
				if str1 == None:
					return None
				if keyvalue == None:
					return None
				jsonstr = jsonstr + keyvalue +':'+ str1 + ','
			jsonstr = jsonstr.strip(',')
			jsonstr = jsonstr + '}'
			print(jsonstr)
			jsonstr = simplejson.dumps(jsonstr ,ensure_ascii=False)
			jsonstr = jsonstr.strip('"')
			return jsonstr
		except:
			return None
