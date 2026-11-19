def validate_post(title: str, content: str) -> str:
    if not 1 <= len(title.strip()) <= 50:
        return "제목은 1~50자로 입력하세요."
    if not 1 <= len(content.strip()) <= 5000:
        return "본문은 1~5000자로 입력하세요."
    return ""
