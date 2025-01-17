from agarwals.reconciliation.step.key_creator.key_creator import KeyCreator
from agarwals.utils.error_handler import log_error
import re

class ClaimKeyCreator(KeyCreator):
    """
    ClaimKeyCreator extends KeyCreator to handle specific key configurations and variants.

    Methods:
        _load_key_configuration(): Get key configuration from the configuration doctype.
        _validate_variant(key): Validate the key variant length.
        get_variants(): Get all valid key variants.
    """

    compiled_replace_patterns = None
    compiled_regex_patterns = None
    compiled_slash_patterns = None
    compiled_star_health_patterns = None

    def __init__(self, key_id: str, key_type: str, reference_name: str, reference_doc: str):
        super().__init__(key_id=key_id, key_type=key_type, reference_name=reference_name, reference_doc=reference_doc)
        if (ClaimKeyCreator.compiled_replace_patterns is None 
            or ClaimKeyCreator.compiled_regex_patterns is None 
            or ClaimKeyCreator.compiled_star_health_patterns is None
            or ClaimKeyCreator.compiled_slash_patterns is None):
            ClaimKeyCreator._load_key_configuration()

    @classmethod
    def _load_key_configuration(cls):
        """
        Fetch key configuration from the database.
        Return: Tuple of compiled_patterns
        """
        try:
            regex_conf = KeyCreator.get_key_configuration("Claim Key")
            replace_patterns = regex_conf.get("replace_patterns", "")
            regex_patterns = regex_conf.get("regex_patterns", "")
            slash_patterns = regex_conf.get("slash_patterns","")
            star_health_patterns = regex_conf.get("star_health_patterns", "")
            cls.compiled_replace_patterns = KeyCreator.get_compiled_pattern(replace_patterns, "Replace Pattern")
            cls.compiled_regex_patterns = KeyCreator.compile_regex_patterns(regex_patterns)
            cls.compiled_slash_patterns = KeyCreator.compile_regex_patterns(slash_patterns)
            cls.compiled_star_health_patterns = star_health_patterns
        except Exception as e:
            log_error(f"Error loading key configuration: {e}", doc="Claim Key")
    
    def strip_claim_key(self, key):
        return key.strip().lstrip("-").lstrip("0").rstrip("-")

    @staticmethod
    def _validate_variant(key) -> bool:
        """
        Validate the length of key greater than 4.
        Return:
            bool: True or False
        """
        return len(key.strip()) < 4

    def remove_slash_patterns(self, item):
        result = re.sub(r'^\d+/\d{1,2}$', lambda match: match.group(0).split('/')[0], item)
        return result

    def replace_item(self, item):
        item = self.strip_claim_key(ClaimKeyCreator.compiled_replace_patterns.sub("", item))
        return item

    def get_variants(self) -> set:
        """
        Generate and validate key variants.

        Returns:
            set: A set of valid key variants.
        """
        key_variants = set()
        n_key_id = self.normalize_key_id()

        if self._validate_variant(n_key_id):
            return key_variants

        key_variants.add(n_key_id)

        if ClaimKeyCreator.compiled_replace_patterns:
            f_key_id = self.replace_item(n_key_id)

            if self._validate_variant(f_key_id):
                return key_variants

            key_variants.add(f_key_id)

            if self.is_regex_present(ClaimKeyCreator.compiled_star_health_patterns, f_key_id):
                star_pattern = self.strip_claim_key(f_key_id.split('/')[-1])
                if not self._validate_variant(star_pattern) and star_pattern:
                    key_variants.add(star_pattern)

            f_key_id = self.remove_slash_patterns(f_key_id)
            key_variants.add(f_key_id)
            key_variants.update(self.apply_regex_patterns(f_key_id, ClaimKeyCreator.compiled_regex_patterns))
            
        else:
            log_error("Compiled replace pattern is not set.", doc="Claim Key")
        return key_variants
