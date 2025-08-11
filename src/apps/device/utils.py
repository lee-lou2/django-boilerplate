from firebase_admin import messaging

from apps.device.models import PushToken


def send_test_push_to_all(message: dict, data: dict = None):
    """전체 사용자 테스트 푸시 발송"""

    token_qs = (
        PushToken.objects.filter(is_valid=True)
        .values_list("token", flat=True)
        .iterator()
    )

    # 전체 결과 집계를 위한 변수
    total_success_count = 0
    total_failure_count = 0
    total_invalid_tokens = []

    # 500개씩 담을 배치 리스트
    batch_tokens = []

    for token in token_qs:
        batch_tokens.append(token)
        # 배치가 500개가 되면 발송
        if len(batch_tokens) == 500:
            success, failure, invalid = send_test_push(batch_tokens, message, data)

            # 결과 집계
            total_success_count += success
            total_failure_count += failure
            total_invalid_tokens.extend(invalid)

            # 배치 리스트 초기화
            batch_tokens = []
    else:
        # 남아있는 토큰들 발송
        if batch_tokens:
            success, failure, invalid = send_test_push(batch_tokens, message, data)

            # 결과 집계
            total_success_count += success
            total_failure_count += failure
            total_invalid_tokens.extend(invalid)

    return total_success_count, total_failure_count, total_invalid_tokens


def send_test_push(tokens: list, message: dict, data: dict = None):
    """테스트 푸시 발송"""

    messages = []
    for token in tokens:
        message_data = {"token": token}
        if message:
            message_data["notification"] = messaging.Notification(**message)
        if data:
            message_data["data"] = data
        messages.append(messaging.Message(**message_data))

    # 푸시 발송
    response = messaging.send_each(messages)

    # 결과 수집
    success_count = 0
    failure_count = 0
    invalid_tokens = []
    for i, resp in enumerate(response.responses):
        if resp.success:
            success_count += 1
        else:
            if resp.exception.code == "messaging/invalid-registration-token":
                invalid_tokens.append(tokens[i])
            failure_count += 1

    return success_count, failure_count, invalid_tokens
