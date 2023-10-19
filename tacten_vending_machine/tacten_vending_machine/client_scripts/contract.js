frappe.ui.form.on('Cup Definition', {
    cup_name:function(frm,cdt,cdn){
        let row = locals[cdt][cdn]
        if(row.cup_name){
            frappe.db.get_list(
				"Product Bundle Item" , {filters:{"parent":row.cup_name}, fields:['item_code','uom']}
			).then((res) => {
                let item_list = []
                for(let item of frm.doc.custom_cup_constituents){
                    item_list.push(item.constituent)
                }
                for(var i = 0;i < res.length ; i++){
                    if(!in_list(item_list,res[i]["item_code"])){
                        let ct = frm.add_child("custom_cup_constituents")
                        ct.constituent = res[i]["item_code"]
                        ct.uom = res[i]["uom"]
                        frm.refresh_fields("custom_cup_constituents")
                    }
                }
            })
        }
    }
});