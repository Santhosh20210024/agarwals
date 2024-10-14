import frappe
import re
import ast
import hashlib 
import unicodedata
from agarwals.utils.error_handler import log_error


class KeyCreator:
    """
    A class to create and manage key variants for different document types.

    The KeyCreator class provides functionality to generate, normalize, and validate keys. It also includes methods to
    fetch key configurations from the configuration doctype and apply regex patterns to generate key variants.
    """

    def __init__(self, key_id: str, key_type: str, reference_name: str, reference_doc: str):
        self.key_id = key_id
        self.key_type = key_type
        self.reference_name = reference_name
        self.reference_doc = reference_doc

    def get_variants(self) -> set: 
        """
        To be overridden in subclasses.
        """
        return set()

    def get_key(self) -> str: 
        """
        Generate a SHA-1 hash of the key_id.
        Returns:
            str: The SHA-1 hash of the key_id.
        """
        return hashlib.sha1(self.key_id.encode("utf-8")).hexdigest()

    def normalize_key_id(self) -> str: 
        """
        Normalize the key_id by converting it to lowercase and stripping whitespace.
        Returns:
            str: The normalized key_id.
        """
        return unicodedata.normalize("NFKD", self.key_id).strip()

    @staticmethod
    def get_key_configuration(doctype: str): 
        """
        Fetch key configuration from the database based on doctype.
        Returns:
            dict: The key configuration.
        """
        try:
            result = frappe.get_all(
                "Key Creator Configuration",
                filters={"doctype_name": doctype},
                fields=["regex_conf"],
            )

            if not result:
                raise ValueError("No key configuration found for this doctype.")
            regex_conf = result[0]["regex_conf"]
            return ast.literal_eval(regex_conf)
        except IndexError:
            raise ValueError("No key configuration found in the database.")
        except Exception as e:
            log_error(f"Exception: {e}", doc = doctype)
            
    @staticmethod
    def get_compiled_pattern(_pattern: str, _type: str): 
        """
        Compile a regex pattern.
        Returns:
            Pattern: The compiled regex pattern.
        """
        if not _pattern:
            raise ValueError(f"{_type} is missing or empty.")
            
        try:
            return re.compile(rf'{_pattern}',flags=re.I)
        except re.error as e:
            log_error(f"Invalid regex pattern configuration: {e}")
            raise ValueError(f"Invalid regex pattern configuration: {e}")
        except Exception as e:
            log_error(f"Exception: {e}")
            raise ValueError(f"Exception: {e}")

    @staticmethod
    def compile_regex_patterns(regex_patterns: str) -> list: 
        """
        Compile a list of regex patterns with replacements.
        Returns:
            list: A list of tuples containing compiled patterns and replacements.
        """
        compiled_patterns = []
        if regex_patterns:
            for item in regex_patterns.split(","):
                if "|" not in item:
                    raise ValueError(f"Invalid regex pattern format: {item}")
                pattern, replacement = item.split("|", 1)
                compiled_regex_pattern = KeyCreator.get_compiled_pattern(
                    pattern, "Regex Pattern"
                )
                compiled_patterns.append((compiled_regex_pattern, replacement))
        return compiled_patterns
    
    def apply_regex_patterns(self, key_id: str, compiled_regex_patterns: list) -> set:
        """
        Apply regex patterns to generate key variants.
        Returns:
            set: A set of generated key variants.
        """
        key_variants = set()
        for regex, replacement in compiled_regex_patterns:
            if regex.search(key_id):
                variant = regex.sub(rf'{replacement}', key_id)
                if not self._validate_variant(variant):
                    key_variants.add(variant)

        return key_variants

    def is_regex_present(self, regex, text):
        return re.search(rf'{regex}', text)

    def process(self, variants):
        """
        Set the key field in the key_fields dictionary based on the doctype.
        """
        key = self.get_key()
        if not variants:
            return ["IGNORED"]

        for variant in variants:
            try:
                if self.key_type == "Claim Key":
                    doc = frappe.new_doc("Claim Key")
                    doc.claim_key = key
                    doc.claim_variant = variant
                    doc.claim_id = self.key_id
                    doc.reference_doctype = self.reference_doc
                    doc.reference_name = self.reference_name
                elif self.key_type == "UTR Key":
                    doc = frappe.new_doc("UTR Key")
                    doc.utr_key = key
                    doc.utr_variant = variant
                    doc.utr_number = self.key_id
                    doc.reference_doctype = self.reference_doc
                    doc.reference_name = self.reference_name
                doc.insert(ignore_permissions=True)
            except Exception as e:
                log_error(f"While Key Insertion Error {e}", doc = self.key_type)
                raise ValueError("Not Able To Create Key")
        try:
            frappe.db.commit()
            return [key]
        except Exception as e:
            log_error(f"Database Commit Error {e}", doc = self.key_type)
            raise ValueError("Database Commit Error")
