import frappe
import tldextract
from agarwals.utils.error_handler import log_error
from typing import List


def convert_to_lower(url_part:str):
    return url_part.lower() if url_part else ''

def create_pattern(url:str) -> str:
    """
     Generate a pattern from a given URL by extracting its components.
     Args:
        url (str): The URL from which to extract the pattern.
     Returns:
        str: The constructed pattern
    """
    url_parts: object = tldextract.extract(url)
    subdomain_exclusion: List = ['www']
    subdomain: str =  convert_to_lower(url_parts.subdomain)
    domain: str =  convert_to_lower(url_parts.domain)
    suffix: str = convert_to_lower(url_parts.suffix)
    pattern: str = subdomain + domain + suffix if subdomain not in subdomain_exclusion else '' + domain + suffix
    return pattern

def is_pattern_exists(pattern:str) -> bool:
    if frappe.db.exists('SA Downloader Configuration',{'portal_pattern':pattern}):
        return True
    return False

@frappe.whitelist()
def update_downloader_patterns() -> str:
    """
    Update unique patterns for all SA Downloader Configuration documents.
    Returns:
        str: A status message indicating the result of the operation:
             - 'Success' if all patterns were updated without issues,
             - 'Error' if any exceptions occurred during processing,
             - 'Doc Not Found' if no configuration documents were found.
    """
    try:
        status: str = 'Success'
        sa_configuration_docs: List[dict] = frappe.get_all(doctype="SA Downloader Configuration",filters = {},fields="name,website_url")
        if sa_configuration_docs:
            for sa_configuration_doc in sa_configuration_docs:
                try:
                    doc: object = frappe.get_doc("SA Downloader Configuration",sa_configuration_doc.name)
                    doc.portal_pattern: str = create_pattern(sa_configuration_doc.website_url)
                    if is_pattern_exists(doc.portal_pattern):
                        raise ValueError(f"Pattern {doc.portal_pattern} already exists in SA Downloader Configuration - {doc.name}")
                    doc.save()
                    frappe.db.commit()
                except Exception as e:
                    status = 'Error'
                    log_error(error=f"Error occurred while processing URL pattern generation: {e}", doc='SA Downloader Configuration')
        else:
            status = 'Doc Not Found'
    except Exception as e:
        status = 'Error'
        log_error(error=f"Error occurred while processing URL pattern generation: {e}",doc='SA Downloader Configuration')

    return status


