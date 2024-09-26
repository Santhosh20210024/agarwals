function build_report(report_name){
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Report Configuration",
            name: report_name
        },
        async : false,
        callback: function(response) {
            if (response.message) {
                frappe.query_reports[report_name] = {
                    onload: function (report) {
                        report.page.add_inner_button("Apply Filter", function () {
                            if(response.message.apply_filter_parameter && response.message.apply_filter_parameter != '' && response.message.apply_filter_parameter != null){
                                let apply_filters_parameters = JSON.parse(response.message.apply_filter_parameter)
                                for (let key in apply_filters_parameters){
                                    report.set_filter_value(key, apply_filters_parameters[key])
                            }}
                        });
                        report.page.add_inner_button("Remove Filter", function () {
                            if(response.message.remove_filter_parameter && response.message.remove_filter_parameter != '' && response.message.remove_filter_parameter != null){
                            let remove_filters_parameters = JSON.parse(response.message.remove_filter_parameter)
                            console.log(typeof remove_filters_parameters)
                            for (let key in remove_filters_parameters){
                                report.set_filter_value(key, remove_filters_parameters[key])
                            }
                            }
                        })
                    },
                    filters: eval(response.message.filters)
                }
            }
        }
    });
}