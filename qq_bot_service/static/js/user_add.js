function toCopyboard(inputId){
	var Url2=document.getElementById(inputId);
	Url2.select(); // 选择对象
	document.execCommand("Copy");
	alert("复制成功");
}

function try_submit(){
	user_id =$("#user_id").val();
	password =$("#password").val();
	auth =$("#user_auth").val();
	console.log(auth);
	$.post("/plugin/main/API/v1/new_user.json",{
		s_id:user_id,
		otppassword:password,
        auth:auth
	},
	function(data,status){
		if (status == "success"){
			console.log(data);
			data = JSON.parse(data)
			if (data.state == "success"){
				$("#newpassword").val(data.password);
				$("#resetModal").modal("show");
			}else{
				alert(data.message);
			}
		}else{
			alert("server error");
		}
	})
}

function check(inputID,infoID){
	info = "内容错误或英文字母小写"
	user_id = $("#"+inputID).val();
	console.log(user_id);
	if(user_id.length != $("#len").val() || /[^0-9^A-Z]/.test(user_id)){
		$("#"+infoID).text(info);
		$("#"+infoID).attr("class","help-block alert-danger");
	}else{
		$("#"+infoID).text("ok");
		$("#"+infoID).attr("class","help-block alert-success");
	}
}