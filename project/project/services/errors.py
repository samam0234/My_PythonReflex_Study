class AccessDenied(Exception):
    """인증·인가 실패. 외부에 상세 자격증명을 노출하지 않는다."""


class LimitExceeded(Exception):
    """서버가 허용한 요청량·동시성 상한 초과."""


class Conflict(Exception):
    """읽은 뒤 다른 요청이 변경한 행을 덮어쓰려는 경우."""
