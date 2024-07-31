from key_creator import KeyCreator


class ClaimKeyCreator(KeyCreator):
    """
    ClaimKeyCreator extends KeyCreator to handle specific key configurations and variants.

    Methods:
        _validate_variant(key): Validate the key variant length.
        _load_key_configuration(): Get key configuration from the database.
        get_variants(): Get all valid key variants.

    """

    compiled_replace_pattern = None
    compiled_regex_patterns = None

    def __init__(self, key_id: str, doctype: str, name: str):
        key_fields = {
            "doctype": "Claim Key",
            "claim_key": "",
            "claim_variant": "",
            "claim_id": key_id,
            "reference_doctype": doctype,
            "reference_name": name,
        }
        super().__init__(
            key_id=key_id, doctype=doctype, name=name, key_fields=key_fields
        )
        if (
            ClaimKeyCreator.compiled_replace_pattern is None
            or ClaimKeyCreator.compiled_regex_patterns is None
        ):
            (
                ClaimKeyCreator.compiled_replace_pattern,
                ClaimKeyCreator.compiled_regex_patterns,
            ) = self._load_key_configuration()

    @staticmethod
    def _load_key_configuration() -> tuple:
        """
        Fetch key configuration from the database.
        Return : Tuple of compiled_patterns
        """
        regex_conf = KeyCreator.get_key_configuration("ClaimKey")
        replace_pattern = regex_conf.get("replace_pattern", "")
        regex_patterns = regex_conf.get("regex_patterns", "")
        compiled_replace_pattern = KeyCreator.get_compiled_pattern(
            replace_pattern, "Replace Pattern"
        )
        compiled_regex_patterns = KeyCreator.compile_regex_patterns(regex_patterns)
        return compiled_replace_pattern, compiled_regex_patterns

    @staticmethod
    def _validate_variant(key) -> bool:
        """
        Validate the length of key greater than 4.
        Return: 
            bool: True or False 
        """
        return len(key) > 4

    def get_variants(self) -> set:
        """
        Generate and validate key variants.

        Returns:
            set: A set of valid key variants.
        """
        key_variants = set()
        normalized_key_id = self.normalize_key_id()

        if not self._validate_variant(normalized_key_id):
            return key_variants

        key_variants.add(normalized_key_id)
        formatted_key_id = self.compiled_replace_pattern.sub("", normalized_key_id)
        if self._validate_variant(formatted_key_id):
            key_variants.add(formatted_key_id)

        self.apply_regex_patterns(formatted_key_id, self.compiled_regex_patterns)
        return key_variants