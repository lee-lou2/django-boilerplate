import re

from django.contrib.auth.password_validation import (
    CommonPasswordValidator,
    NumericPasswordValidator,
    UserAttributeSimilarityValidator,
)
from django.core.exceptions import ValidationError


def get_username_validators():
    validators = [
        ASCIIUsernameValidator(),
        CustomLengthValidator(4, 16),
    ]
    return validators


def validate_username(username):
    validators = get_username_validators()
    errors = []
    for validator in validators:
        try:
            validator.validate(username)
        except ValidationError as error:
            errors.append(error)
    if errors:
        raise ValidationError(errors)


def get_password_validators():
    validators = [
        CustomLengthValidator(8, 16),
        UserAttributeSimilarityValidator(),
        CommonPasswordValidator(),
        NumericPasswordValidator(),
    ]
    return validators


def validate_password(password):
    validators = get_password_validators()
    errors = []
    for validator in validators:
        try:
            validator.validate(password)
        except ValidationError as error:
            errors.append(error)
    if errors:
        raise ValidationError(errors)


class ASCIIUsernameValidator:
    def __init__(self):
        regex = r"^[\w]+\Z"
        self.p = re.compile(regex, re.ASCII)

    def validate(self, username):
        if not self.p.match(username):
            msg = "영문, 숫자, 밑줄만 가능합니다."
            raise ValidationError(msg)


class CustomLengthValidator:
    def __init__(self, min_length, max_length):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, fields, user=None):
        if len(fields) < self.min_length:
            msg = f"최소 {self.min_length} 문자를 입력해주세요."
            raise ValidationError(msg)
        if len(fields) > self.max_length:
            msg = f"최대 {self.max_length} 문자를 입력해주세요."
            raise ValidationError(msg)
