import logging
import re

# 민감 정보 키워드
SENSITIVE_KEYWORDS = {
    "password",
    "access_token",
    "refresh_token",
}


class SensitiveFilter(logging.Filter):
    """로깅시 민감 정보 마스킹 필터"""

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
