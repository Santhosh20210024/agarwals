import re
from agarwals.reconciliation.step.key_creator.key_creator import KeyCreator
from agarwals.utils.error_handler import log_error


class UTRKeyCreator(KeyCreator):
    """
    UTRKeyCreator extends KeyCreator to handle specific key configurations and variants.

    Methods:
        _validate_variant(key): Validate the key variant length.
        _load_key_configuration(): Get key configuration from the database.
        get_variants(): Get all valid key variants.
        format_utr(): convert all the utrs into correct format.
    """

    compiled_ignore_pattern = None
    compiled_utr_format_pattern = None
    compiled_citin_pattern = None
    compiled_regex_patterns = None

    def __init__(self, key_id: str, key_type: str, reference_name: str, reference_doc: str):
        super().__init__(key_id, key_type, reference_name, reference_doc)
        
        # Initialize the class variables only if they are None
        if (UTRKeyCreator.compiled_ignore_pattern is None or
            UTRKeyCreator.compiled_utr_format_pattern is None or
            UTRKeyCreator.compiled_citin_pattern is None or
            UTRKeyCreator.compiled_regex_patterns is None 
            ):
            UTRKeyCreator._load_key_configuration()
        
    @classmethod
    def _load_key_configuration(cls):
        try:
            regex_conf = KeyCreator.get_key_configuration("UTR Key")
            ignore_pattern = regex_conf.get("ignore_pattern", "")
            utr_format_pattern = regex_conf.get("utr_format_pattern", "")
            citin_pattern = regex_conf.get("citin_pattern", "")
            regex_patterns = regex_conf.get("regex_patterns", "")

            cls.compiled_ignore_pattern = KeyCreator.get_compiled_pattern(ignore_pattern, "Ignore Pattern")
            cls.compiled_utr_format_pattern = KeyCreator.get_compiled_pattern(utr_format_pattern, "UTR Format Pattern")
            cls.compiled_citin_pattern = KeyCreator.get_compiled_pattern(citin_pattern, "CITIN Pattern")
            cls.compiled_regex_patterns = KeyCreator.compile_regex_patterns(regex_patterns)
        except Exception as e:
            log_error(f"Error loading key configuration: {e}", doc="UTR Key")

    @staticmethod
    def _validate_variant(key) -> bool:
        """
        Validate the key variant.
        A valid key variant is either purely alphabetic or has a length less than 4 characters.

        Returns:
            bool: True if the key variant is valid, False otherwise.
        """
        return key.isalpha() or len(key.strip()) < 4

    def format_utr(self, utr) -> set:
        """
        Format the UTR (Unique Transaction Reference) and generate key variants.

        Returns:
            set: A set of valid key variants generated from the input UTR.
        """
        utr = UTRKeyCreator.compiled_ignore_pattern.sub("", utr)
        variants = set()

        if self._validate_variant(utr):
            return variants

        variants.add(utr)
        variants.update(self.apply_regex_patterns(utr, UTRKeyCreator.compiled_regex_patterns))

        if UTRKeyCreator.compiled_citin_pattern.match(utr):
            variants.add("citin" + utr)
            
        if utr.startswith("s") and utr[1:].isdigit():
            variants.add(utr[1:])
            
        if len(utr) == 9:
            variants.add("aiscn0" + utr)

        if utr.startswith("s") and len(utr) == 13:
            variants.add(utr[1:])

        return variants

    def get_variants(self) -> set:
        """
        Generate and validate key variants.

        Returns:
            set: A set of valid key variants.
        """
        key_variants = set()
        n_key_id = self.normalize_key_id()

        if self._validate_variant(re.sub("[^a-zA-Z0-9]+", "", n_key_id)):
            return key_variants
        
        key_variants.add(n_key_id)
        key_variants.update(self.format_utr(n_key_id))

        if "/" in n_key_id and len(n_key_id.split("/")) == 2:
            e_key_id = n_key_id.split("/")[1]
            if "-" in e_key_id:
                key_variants.update(self.format_utr(e_key_id.split("-")[-1]))
            else:
                key_variants.update(self.format_utr(e_key_id))

        if "-" in n_key_id:
            key_variants.update(self.format_utr(n_key_id.split("-")[-1]))

        match = UTRKeyCreator.compiled_utr_format_pattern.match(n_key_id)
        if match:
            _, utr_number, _ = match.groups()
            key_variants.update(self.format_utr(utr_number))

        return key_variants
