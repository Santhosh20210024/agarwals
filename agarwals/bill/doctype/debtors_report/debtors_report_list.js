frappe.listview_settings['Debtors Report'] = {
    onload(listview) {
        console.log('List view loaded:', listview);
        listview.page.add_inner_button('View Unverified Bills', () => {
            console.log('Button clicked');
            frappe.set_route('List', 'Debtors Report','List',{ 'verified': 1 });
        });
    }
};
