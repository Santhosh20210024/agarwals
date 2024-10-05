from enum import Enum
import string

class TagType(Enum):
    INCLUSION = "inclusion_tag"
    SKIPPED_INCLUSION = "skipped_inclusion_tag"
    EXCLUSION = "exclusion_tag"
    ADVICE = "advice_tag"
    CLAIM = "claim_tag"
    EXCLUDE_CHECK = "exclude_tag"

def get_tagger_query(tag_type: TagType) -> str:
    """Get the Insurance tagger queries based on the given tag type"""
    query_list = {
        TagType.INCLUSION: (
            "UPDATE `tabBank Transaction Staging` "
            "SET tag = %(tag)s, based_on = 'Insurance Pattern', staging_status = 'Open' "
            "WHERE search REGEXP %(patterns)s "
            "AND tag IS NULL AND staging_status in ('Skipped', 'Open')"
        ),
        TagType.EXCLUSION: (
            "UPDATE `tabBank Transaction Staging` "
            "SET tag = NULL, based_on = NULL, staging_status = 'Skipped' "
            "WHERE tag = %(tag)s "
            "AND search REGEXP %(patterns)s "
            "AND based_on = 'Insurance Pattern'"
        ),
        TagType.ADVICE: (
            "UPDATE `tabBank Transaction Staging` tbts, `tabSettlement Advice` tuk "
            "SET tbts.tag = %(tag)s, tbts.based_on = 'Settlement Advice' "
            "WHERE tbts.reference_number = tuk.final_utr_number "
            "AND tbts.tag IS NULL "
            "AND tbts.reference_number != '0'"
        ),
        TagType.CLAIM: (
            "UPDATE `tabBank Transaction Staging` tbts, `tabClaimBook` tuk "
            "SET tbts.tag = %(tag)s, tbts.based_on = 'ClaimBook' "
            "WHERE tbts.reference_number = tuk.utr_number "
            "AND tbts.tag IS NULL "
            "AND tbts.reference_number != '0'"
        ),
        TagType.EXCLUDE_CHECK: (
            "SELECT tbt.name as bank_name, tbts.name as staging_name FROM `tabBank Transaction` tbt "
            "INNER JOIN `tabBank Transaction Staging` tbts "
            "ON tbts.reference_number = tbt.reference_number "
            "where tag IS NULL and staging_status = 'Skipped' "
        )
    }

    query = query_list.get(tag_type, None)
    if query is None:
        raise ValueError(f"Invalid tag_type: {tag_type}. Valid options are: {', '.join(query_list.keys())}.")
    
    return query

def normalize_text(text):
    """Normalize text by removing whitespace and converting to lowercase"""
    return text.translate({ ord(_text): None for _text in string.whitespace }).lower()

def compile_patterns(patterns):
    """To get the compiled patterns from the input pattern"""
    return '(?:%s)' % '|'.join(normalize_text(pattern) for pattern in patterns if pattern)