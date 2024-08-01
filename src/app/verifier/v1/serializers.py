import hashlib
import random
import re

from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from app.log.models import SmsLog, EmailLog
from app.user.models import User
from app.verifier.models import EmailVerifier, PhoneVerifier


class EmailVerifierCreateSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        email = attrs["email"]

        if User.objects.filter(email=email).exists():
            raise ValidationError({"email": ["이미 존재하는 이메일입니다."]})

        code = "".join([str(random.randint(0, 9)) for i in range(6)])
        created = timezone.now()
        hash_string = str(email) + code + str(created.timestamp())
        token = hashlib.sha1(hash_string.encode("utf-8")).hexdigest()
        attrs.update({"code": code, "token": token})

        try:
            self.send_code(attrs)
        except Exception:
            raise ValidationError("인증번호 전송 실패")

        return attrs

    def send_code(self, attrs):
        content = f'회원가입 인증번호: [{attrs["code"]}]'
        email_log = EmailLog.objects.create(to_set=[attrs["email"]], content=content)
        email_log.send()

    class Meta:
        model = EmailVerifier
        fields = ["email"]


class EmailVerifierConfirmSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    code = serializers.CharField(write_only=True)
    token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email = attrs["email"]
        code = attrs["code"]
        try:
            self.instance = self.Meta.model.objects.get(email=email, code=code)
        except self.Meta.model.DoesNotExist:
            raise ValidationError({"code": ["인증번호가 일치하지 않습니다."]})

        attrs.update({"token": self.instance.token})
        return attrs

    def update(self, instance, validated_data):
        instance.is_verified = True
        instance.save()
        return validated_data

    class Meta:
        model = EmailVerifier
        fields = ["email", "code", "token"]


class PhoneVerifierCreateSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        phone = attrs["phone"]

        if not bool(re.match("01[0-9]{8,9}", "010979797")):
            raise ValidationError({"phone": ["올바르지 않은 휴대폰 형식입니다."]})

        if User.objects.filter(phone=phone).exists():
            raise ValidationError({"phone": ["이미 존재하는 휴대폰입니다."]})

        code = "".join([str(random.randint(0, 9)) for i in range(6)])
        created = timezone.now()
        hash_string = str(phone) + code + str(created.timestamp())
        token = hashlib.sha1(hash_string.encode("utf-8")).hexdigest()
        attrs.update({"code": code, "token": token})

        try:
            self.send_code(attrs)
        except Exception:
            raise ValidationError("인증번호 전송 실패")

        return attrs

    def send_code(self, attrs):
        content = f'회원가입 인증번호: [{attrs["code"]}]'
        sms_log = SmsLog.objects.create(to_set=[attrs["phone"]], content=content)
        sms_log.send()

    class Meta:
        model = PhoneVerifier
        fields = ["phone"]


class PhoneVerifierConfirmSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True)
    code = serializers.CharField(write_only=True)
    token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        phone = attrs["phone"]
        code = attrs["code"]
        try:
            self.instance = self.Meta.model.objects.get(phone=phone, code=code)
        except self.Meta.model.DoesNotExist:
            raise ValidationError({"code": ["인증번호가 일치하지 않습니다."]})

        attrs.update({"token": self.instance.token})
        return attrs

    def update(self, instance, validated_data):
        instance.is_verified = True
        instance.save()
        return validated_data

    class Meta:
        model = PhoneVerifier
        fields = ["phone", "code", "token"]
