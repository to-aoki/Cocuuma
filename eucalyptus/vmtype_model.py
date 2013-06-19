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

class VMType(object):

	def __init__(self,db_vmtype_object):
		self.db_vmtype = db_vmtype_object

	@property
	def vmtype(self):
		return self.db_vmtype.vmtype

	@vmtype.getter
	def vmtype(self):
		return self.db_vmtype.vmtype

	@property
	def name(self):
		return self.db_vmtype.name

	@name.setter
	def name(self,value):
		self.db_vmtype.name = value
		self.save()

	@name.getter
	def name(self):
		return self.db_vmtype.name

	@property
	def cpu(self):
		return self.cpu

	@cpu.setter
	def cpu(self,value):
		self.cpu = value

	@cpu.getter
	def cpu(self):
		return self.cpu

	@property
	def mem(self):
		return self.mem

	@mem.setter
	def mem(self,value):
		self.mem = value

	@mem.getter
	def mem(self):
		return self.mem

	@property
	def disk(self):
		return self.disk

	@disk.setter
	def disk(self,value):
		self.disk = value

	@disk.getter
	def disk(self):
		return self.disk

	def save(self):
		self.db_vmtype.save()

class Euca_VMType(object):

	def __init__(self):
		self.vmtype = ""
		self.cpu = 0
		self.mem = 0
		self.disk = 0
		self.max = 0
