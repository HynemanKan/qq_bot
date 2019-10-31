function isValidPassword(str){
    if(str.length<6||str.length>20){
      return false
    }
    if(/[^a-zA-Z0-9_]/.test(str)){
      return false
    }
    if(/(^[a-z]+$|^[A-Z]+$|^\d+$|^_+$)/.test(str)){
      return false
    }
    return true
  }

function check(inputID){
	info = "长度6-20个字符，包括大写字母、小写字母、数字、下划线至少两种"
	password = $("#"+inputID).find("input").val();
	console.log(password)
	if (isValidPassword(password)){
		$("#"+inputID).children("p").text("ok");
		$("#"+inputID).children("p").attr("class","help-block alert-success");
		
	}else{
		$("#"+inputID).children("p").text(info);
		$("#"+inputID).children("p").attr("class","help-block alert-danger");
		
	}
}

function checksame(id1,id2){
	password1 = $("#"+id1).val();
	password2 = $("#"+id2).val();
	console.log(password1+"+"+password2)
	if ( password1 == password2){
		$("#samecheck").text("ok");
		$("#samecheck").attr("class","help-block alert-success");
	}else{
		$("#samecheck").text("不一致");
		$("#samecheck").attr("class","help-block alert-danger");
	}
}

function try_submit(){
	password1 = $("#passwordNew").val();
	password2 = $("#passwordNewR").val();
	console.log(password1+"+"+password2)
	if ( password1 == password2){
		$("#samecheck").text("ok");
		$("#samecheck").attr("class","help-block alert-success");
		oldpassword = $("#password").val()
		$.post("/plugin/main/API/v1/reset_by_self.json",{
				oldpassword:oldpassword,
				newpassword:password1,
			},
			function(data,status){
				if (status == "success"){
					console.log(data);
					data = JSON.parse(data)
					if (data.state == "success"){
						alert(data.message);
					}else{
						alert(data.message);
					}
				}else{
					alert("server error");
				}
			})
	}else{
		$("#samecheck").text("不一致");
		$("#samecheck").attr("class","help-block alert-danger");
	}
}

function showQr(){
	$('#QrModal').modal('show')
}