from conf.celery import app


@app.task
def task_send_re_agreement_notification(
    previous_version: "Agreement", latest_version: "Agreement"
):
    """
    약관 재동의 요청:
    필수 약관 변경 시 재동의 필요
    이메일이나 푸시 등을 통해 재동의 요청하는 태스크
    """
    # TODO: 이메일 발송 예약
    # TODO: 푸시 발송 예약
    pass
