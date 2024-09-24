import frappe 

@frappe.whitelist()
def construct_file_url(*args):
    """Construct a file URL from the given path components, handling None values."""
    args = [str(arg) for arg in args if arg is not None]
    formatted_url = "/".join(args)
    return formatted_url