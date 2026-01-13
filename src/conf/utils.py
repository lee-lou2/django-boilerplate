import json
import logging
import os

import boto3

logger = logging.getLogger(__name__)


def load_aws_parameters(path: str, region_name: str):
    """AWS 파라미터 스토어에서 환경변수 로드"""
    ssm = boto3.client(service_name="ssm", region_name=region_name)
    if ssm is None:
        return

    try:
        resp = ssm.get_parameter(Name=path, WithDecryption=True)
        if (
            not resp
            or "ResponseMetadata" not in resp
            or "HTTPStatusCode" not in resp.get("ResponseMetadata", {})
            or "Parameter" not in resp
            or resp.get("ResponseMetadata").get("HTTPStatusCode") != 200
        ):
            return

        parameter_value = resp.get("Parameter").get("Value")
        values = json.loads(parameter_value)
        for key, value in values.items():
            os.environ[key] = value
    except Exception as e:
        logger.info("파라미터 스토어 환경 변수 조회 실패, 오류 내용 : %s", e)
