import frappe
import tldextract
from agarwals.utils.error_handler import log_error
from typing import List


def create_pattern(url:str) -> str:
    url_parts: object = tldextract.extract(url)
    pattern: str = url_parts.subdomain.lower() if url_parts.subdomain.lower() not in ['www'] else '' + url_parts.domain.lower() + url_parts.suffix.lower()
    return pattern

def is_pattern_exists(pattern:str) -> bool:
    if frappe.db.exists('SA Downloader Configuration',{'portal_pattern':pattern}):
        return True
    return False

@frappe.whitelist()
def get_patterns(url:str = None) -> str:
    try:
        if url:
            return create_pattern(url)

        status: str = 'Success'
        sa_configuration_docs: List[dict] = frappe.get_all("SA Downloader Configuration",{},"name,website_url")
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


