function goto(plugin_type,plugin_btype,plugin_name,plugin_bname) {
    $.get("/plugin/"+plugin_type+"/"+plugin_name, function(result){
        $("#target-windows").html(result);
        //$(".butobj").setAttribute("class","butobj");
        $("#now_position").text(plugin_btype+"/"+plugin_bname);
  });
}
