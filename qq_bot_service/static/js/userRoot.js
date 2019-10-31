function randomPassword(){
	password = ""
	seed = "0123456789asdfghjklqwertyuiopzxcvbnmASDFGHJKLQWERTYUIOPZXCVBNM________".split("")
	for (i=0;i<10;i++){
		j = Math.floor(Math.random()*seed.length)
		password += seed[j]
	}
	return password
}

function toCopyboard(inputId){
	var Url2=document.getElementById(inputId);
	Url2.select(); // 选择对象
	document.execCommand("Copy");
	alert("复制成功");
}

function try_submit(){
	OTPpassword =$("#password").val();
	Newpassword = randomPassword();
	console.log(Newpassword);
	$.post("/plugin/main/API/v1/reset_by_admin.json",{
		s_id:$("#s_id").val(),
		newpassword:Newpassword,
		otppassword:OTPpassword
	},
	function(data,status){
		if (status == "success"){
			if (data == "success"){
				$("#newpassword").val(Newpassword);
				$("#resetModal").modal("show");
			}else{
				alert("动态密码错误或过期");
			}
		}else{
			alert("server error");
		}
	})
}