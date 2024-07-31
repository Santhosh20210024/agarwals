from . import re
from key_creator import KeyCreator
 
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

    def __init__(self, key_id: str, doctype: str, name: str):
        key_fields = {
                      "doctype":"UTR Key",
                      "utr_key": "",
                      "utr_variant": "",
                      "utr_number": key_id,
                      "reference_doctype": doctype,
                      "reference_name": name
                    }
        super().__init__(key_id = key_id, doctype = doctype, name = name, key_fields = key_fields)
        if (
            UTRKeyCreator.compiled_ignore_pattern is None
            or UTRKeyCreator.compiled_utr_format_pattern is None
            or UTRKeyCreator.compiled_citin_pattern is None
            or UTRKeyCreator.compiled_regex_patterns is None
        ):

           (UTRKeyCreator.compiled_ignore_pattern,
            UTRKeyCreator.compiled_utr_format_pattern,
            UTRKeyCreator.compiled_citin_pattern,
            UTRKeyCreator.compiled_regex_patterns) = self._load_key_configuration()

    @staticmethod
    def _load_key_configuration() -> tuple:
        regex_conf = KeyCreator.get_key_configuration("UTR Key")
        ignore_pattern = regex_conf.get("ignore_pattern", "")
        utr_format_pattern = regex_conf.get("utr_format_pattern", "")
        citin_pattern = regex_conf.get("citin_pattern", "")
        regex_patterns = regex_conf.get("regex_patterns", "")

        compiled_ignore_pattern = KeyCreator.get_compiled_pattern(
            ignore_pattern, "Ignore Pattern"
        )
        compiled_utr_format_pattern = KeyCreator.get_compiled_pattern(
            utr_format_pattern, "UTR Format Pattern"
        )
        compiled_citin_pattern = KeyCreator.get_compiled_pattern(
            citin_pattern, "CITIN Pattern"
        )
        compiled_regex_patterns = KeyCreator.compile_regex_patterns(regex_patterns)
        return (
            compiled_ignore_pattern,
            compiled_utr_format_pattern,
            compiled_citin_pattern,
            compiled_regex_patterns,
        )

    @staticmethod
    def _validate_variant(key) -> bool:
        """
        Validate the key variant.
        A valid key variant is either purely alphabetic or has a length less than 4 characters.

        Returns: 
            bool: True if the key variant is valid, False otherwise.
        """
        return key.isalpha() or len(key) < 4

    def format_utr(self, utr) -> set:
        """
        Format the UTR (Unique Transaction Reference) and generate key variants.
        
        Returns:
            set: A set of valid key variants generated from the input UTR.
        """
        utr = re.sub(self.ignore_pattern, "", utr)
        variants = set()

        if self._validate_variant(utr):
            return variants

        variants.add(utr)
        variants.update(self.apply_regex_patterns(utr, self.compiled_regex_patterns))

        if self.compiled_citin_pattern.match(utr):
            variants.add("citin" + utr)

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
        normalized_key_id = self.normalize_key_id()
        if not self._validate_variant(normalized_key_id):
            return key_variants

        key_variants.update(self.format_utr(normalized_key_id))

        if "/" in normalized_key_id and len(normalized_key_id.split("/")) == 2:
            extracted_utr = normalized_key_id.split("/")[1]
            if "-" in extracted_utr:
                key_variants.update(self.format_utr(extracted_utr.split("-")[-1]))
            else:
                key_variants.update(self.format_utr(extracted_utr))

        if "-" in normalized_key_id:
            key_variants.update(self.format_utr(normalized_key_id.split("-")[-1]))

        match = self.compiled_utr_format_pattern.match(normalized_key_id)
        if match:
            _, utr_number, _ = match.groups()
            key_variants.update(self.format_utr(utr_number))

        return key_variants