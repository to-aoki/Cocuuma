/* COPYRIGHT FUJITSU SOCIAL SCIENCE LABORATORY LIMITED 2012
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

+ Redistributions of source code must retain the above copyright notice, this list of conditions
and the following disclaimer.
+ Redistributions in binary form must reproduce the above copyright notice, this list of conditions
and the following disclaimer in the documentation and/or other materials provided with the distribution.
+ Neither the name of the FUJITSU SOCIAL SCIENCE LABORATORY LIMITED nor the names of its contributors
may be used to endorse or promote products derived from this software without specific prior written
permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. */

function getimg(value){
		if (value=='0'){ return "/static/images/sort_default.png"; }
		else if(value=='1') { return "/static/images/sort_up.png"; }
		else { return "/static/images/sort_down.png"; }
	}

// ページロード時処理
$(function () {
     $(this).ready(function () {
		$("#saccountname").attr("src",getimg($("#sortnamehide").val()));
		$("#scpu").attr("src",getimg($("#sortcpuhide").val()));
		$("#smem").attr("src",getimg($("#sortmemhide").val()));
		$("#stotalvol").attr("src",getimg($("#sortvolhide").val()));
    });
});

//ソート
	function sortName() {
		var f = document.getElementById("form1")
		sortVal = f.sortnamehide.value;
		f.sortnamehide.value = f.sortcpuhide.value = f.sortmemhide.value = f.sortvolhide.value = 0;
		if (sortVal == 0)
			sortVal = 1
		else
			sortVal = 1 + sortVal%2;
		f.sortnamehide.value = sortVal;
		f.action = "/resource/accountlist/";
		f.submit();
	}
	function sortCpu() {
		var f = document.getElementById("form1")
		sortVal = f.sortcpuhide.value;
		f.sortnamehide.value = f.sortcpuhide.value = f.sortmemhide.value = f.sortvolhide.value = 0;
		if (sortVal == 0)
			sortVal = 1
		else
			sortVal = 1 + sortVal%2;
		f.sortcpuhide.value = sortVal;
		f.action = "/resource/accountlist/";
		f.submit();
	}
	function sortMem() {
		var f = document.getElementById("form1")
		sortVal = f.sortmemhide.value;
		f.sortnamehide.value = f.sortcpuhide.value = f.sortmemhide.value = f.sortvolhide.value = 0;
		if (sortVal == 0)
			sortVal = 1
		else
			sortVal = 1 + sortVal%2;
		f.sortmemhide.value = sortVal;
		f.action = "/resource/accountlist/";
		f.submit();
	}
	function sortVol() {
		var f = document.getElementById("form1")
		sortVal = f.sortvolhide.value;
		f.sortnamehide.value = f.sortcpuhide.value = f.sortmemhide.value = f.sortvolhide.value = 0;
		if (sortVal == 0)
			sortVal = 1
		else
			sortVal = 1 + sortVal%2;
		f.sortvolhide.value = sortVal;
		f.action = "/resource/accountlist/";
		f.submit();
	}

// アカウント情報へ
	function selectAccount(accountname) {
		var f = document.getElementById("form1")
		f.selected_account.value = accountname;
		f.action = "/resource/accountinfo/";
		f.submit();
	}

// データ再読み込み
	function refresh() {
		var f = document.getElementById("form1")
		f.resource_refresh.value = 'yes'
		f.action = "/resource/accountlist/";
		f.submit();
	}
