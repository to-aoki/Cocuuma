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
		$("#sinstanceid").attr("src",getimg($("#sortinshide").val()));
		$("#saccountname").attr("src",getimg($("#sortacchide").val()));
		$("#snodeip").attr("src",getimg($("#sortnodhide").val()));
		$("#srootdevicetype").attr("src",getimg($("#sortroohide").val()));
    });
});

//ソート
	function sortInstance() {
		var f = document.getElementById("form1")
		sortVal = f.sortinshide.value;
		f.sortinshide.value = f.sortacchide.value = f.sortnodhide.value = f.sortroohide.value = 0;
		if (sortVal == 0)
			sortVal = 1
		else
			sortVal = 1 + sortVal%2;
		f.sortinshide.value = sortVal;
		f.action = "/resource/nodeinfo/";
		f.submit();
	}
	function sortAccount() {
		var f = document.getElementById("form1")
		sortVal = f.sortacchide.value;
		f.sortinshide.value = f.sortacchide.value = f.sortnodhide.value = f.sortroohide.value = 0;
		if (sortVal == 0)
			sortVal = 1
		else
			sortVal = 1 + sortVal%2;
		f.sortacchide.value = sortVal;
		f.action = "/resource/nodeinfo/";
		f.submit();
	}
	function sortNode() {
		var f = document.getElementById("form1")
		sortVal = f.sortnodhide.value;
		f.sortinshide.value = f.sortacchide.value = f.sortnodhide.value = f.sortroohide.value = 0;
		if (sortVal == 0)
			sortVal = 1
		else
			sortVal = 1 + sortVal%2;
		f.sortnodhide.value = sortVal;
		f.action = "/resource/nodeinfo/";
		f.submit();
	}
	function sortRootdev() {
		var f = document.getElementById("form1")
		sortVal = f.sortroohide.value;
		f.sortinshide.value = f.sortacchide.value = f.sortnodhide.value = f.sortroohide.value = 0;
		if (sortVal == 0)
			sortVal = 1
		else
			sortVal = 1 + sortVal%2;
		f.sortroohide.value = sortVal;
		f.action = "/resource/nodeinfo/";
		f.submit();
	}

// 展開
	function extract(num) {
		var f = document.getElementById("form1")
		f.extract.value = num
		//alert("extract" + num)
		f.action = "/resource/nodeinfo/";
		f.submit();
	}
// データ再読み込み
	function refresh() {
		var f = document.getElementById("form1")
		f.resource_refresh.value = 'yes'
		f.action = "/resource/nodeinfo/";
		f.submit();
	}
