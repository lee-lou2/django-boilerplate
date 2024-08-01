import json
import logging
import os

import boto3


class AWSManager:
    """AWS 서비스 관리자"""

    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str):
        self.region_name = "ap-northeast-2"
        self.session = (
            boto3.session.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=self.region_name,
            )
            if aws_access_key_id
            else boto3.session.Session(region_name=self.region_name)
        )

    def load_parameters(self, path: str):
        """AWS SSM 환경 변수 조회 후 설정"""
        # client 생성
        ssm = self.session.client(service_name="ssm", region_name=self.region_name)
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
            # .env 파일 생성 및 환경 변수 지정
            with open(".env", "w") as f:
                for key, value in values.items():
                    f.write(f"{key}={value}\n")
                    os.environ[key] = value
        except Exception as e:
            logging.info(f"파라미터 스토어 환경 변수 조회 실패, 오류 내용 : {e}")
