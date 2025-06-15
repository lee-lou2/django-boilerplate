import logging
import re

# Sensitive information keywords
SENSITIVE_KEYWORDS = {
    "password",
    "access_token",
    "refresh_token",
}


class SensitiveFilter(logging.Filter):
    """Filter for masking sensitive information during logging"""

    def filter(self, record):
        for keyword in SENSITIVE_KEYWORDS:
            record.msg = str(record.msg)
            if keyword in record.msg:
                record.msg = self.sanitize_dict(record.msg, keyword)
        return True

    @staticmethod
    def sanitize_dict(msg, keyword):
        regex_mapper = {
            f'"{keyword}":[ ]*"[^"]*"': f'"{keyword}": "****"',
            f"'{keyword}':[ ]*'[^']*'": f"'{keyword}': '****'",
            f"{keyword}=[^&]+&?": f"{keyword}=****&",
        }
        for regex, replace in regex_mapper.items():
            msg = re.sub(regex, replace, msg)
        return msg
