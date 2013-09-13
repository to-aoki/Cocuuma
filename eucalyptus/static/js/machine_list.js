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

function switchDisplay($buttonInfo){
    //$buttonInfoはjQueryオブジェクトです。
    var isShown;
    isShown = $buttonInfo.parents("table").find(".detail").hasClass("shown");
    if(isShown){;
        $buttonInfo.parents("table").find(".detail").hide();
        $buttonInfo.parents("table").find(".detail").addClass("hidden");
        $buttonInfo.parents("table").find(".detail").removeClass("shown");
        $buttonInfo.text("↓詳細表示");
    }else{
        $buttonInfo.parents("table").find(".detail").show();
        $buttonInfo.parents("table").find(".detail").addClass("shown");
        $buttonInfo.parents("table").find(".detail").removeClass("hidden");
        $buttonInfo.text("↑標準表示");
    }
}

$(document).ready(function(){
    //table偶数行に"even"クラスを付加する。
    //色の指定はスタイルシートにて行う。
    $(".vmachine_info tr:even").addClass("even");

    //////////いまは、色変え＆"＞"の位置替えだけ///////////
    //////////色替えですが一時的にここでやります///
    $("#left_contents .nav li.left_contents_item").click(function(){
        $("#left_contents .nav li.left_contents_item").css("backgroundColor","#ECEFE7");
        $(".menu_selected_text").text("");

        $(this).css("backgroundColor","#ffdf3a");
    });
});

function console_output_window(instance_id){
    url = "/machine/getconsole/" + instance_id　+ "/";
	window.open(url,"window01","width=800,height=600,status=no,scrollbars=yes");
}

function create_image(machine_id, init_name){
    template_name = window.prompt("新しいテンプレート名を入力してください", init_name)
	if( template_name ) {
		var f = document.getElementById("form1");
		f.action = "/machine/createimage/" + machine_id　+ "/";
		f.elements['creating_template_name'].value = template_name;
		f.submit();
	}
}

function isIE()
{
	var userAgent = window.navigator.userAgent.toLowerCase();
	if (userAgent.indexOf('msie') != -1) {
		return true
	} else {
		return false
	}
}

function mySetCookie(myCookie,myValue,myDay){
   myExp = new Date();
   myExp.setTime(myExp.getTime()+(myDay*24*60*60*1000));
   myItem = "@" + myCookie + "=" + escape(myValue) + ";";
   myExpires = "expires="+myExp.toGMTString();
   myPath = "path=/;";
   document.cookie =  myItem + myPath + myExpires;
}

function myGetCookie(myCookie){
   myCookie = "@" + myCookie + "=";
   myValue = null;
   myStr = document.cookie + ";" ;
   myOfst = myStr.indexOf(myCookie);
   if (myOfst != -1){
      myStart = myOfst + myCookie.length;
      myEnd   = myStr.indexOf(";" , myStart);
      myValue = unescape(myStr.substring(myStart,myEnd));
   }
   return myValue;
}

function sshLogin(machine_id)
{
	if ( isIE() ) {
	    ip = document.getElementById("address_" + machine_id).innerHTML.split(" ")[0]
	    if ( !ip ) {
		    window.alert("IPアドレスが取得できませんでした")
		    return
		}
		keypath = myGetCookie("RSA_PUBLIC_KEY_PATH")
		exepath = myGetCookie("SSH_TERMINAL_PATH")
		options = myGetCookie("SSH_TERMINAL_OPTIONS")
		if ( !keypath || !exepath || !options || !window.confirm(ip + " にログイン\n前回の設定でログインします") ) {
			if ( exepath ) {
				exepath = window.prompt("login to " + ip + " : SSHターミナル・プログラムのパスを入力してください", exepath)
			} else {
				exepath = window.prompt("login to " + ip + " : SSHターミナル・プログラムのパスを入力してください", '\"C:\\Program Files\\teraterm\\ttermpro.exe\"')
			}
			if ( !exepath ) return
			if ( options ) {
				options = window.prompt("SSHターミナル・プログラムのオプションを入力してください", options)
			} else {
				options = window.prompt("SSHターミナル・プログラムのオプションを入力してください", "/user=root /auth=publickey /keyfile=")
			}
			if ( !options ) return
			if ( keypath ) {
				keypath = window.prompt("RSAプライベート・キーのパスを入力してください", keypath)
			} else {
				keypath = window.prompt("RSAプライベート・キーのパスを入力してください", "")
			}
			if ( !keypath ) return
		}
		if ( keypath && exepath && options) {
			mySetCookie("RSA_PUBLIC_KEY_PATH",keypath,365)
			mySetCookie("SSH_TERMINAL_PATH",exepath,365)
			mySetCookie("SSH_TERMINAL_OPTIONS",options,365)
			wshshell=new ActiveXObject("WScript.Shell")
			//wshshell.run("\"C:\\Program Files (x86)\\teraterm\\ttermpro.exe\" " + ip + " /user=root /auth=publickey /keyfile=" + keypath)
			wshshell.run(exepath + " " + ip + " " + options + keypath)
		}
	}
	else {
		window.alert("プログラムの呼び出しはIEからのみ有効です")
	}
}
