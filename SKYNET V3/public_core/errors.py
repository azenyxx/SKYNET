"""Typed errors. INVALID -> exit 2 (no evidence); UNSUPPORTED -> ABSTAINED_UNSUPPORTED evidence."""


class SkyError(Exception):
    INVALID = "INVALID"
    UNSUPPORTED = "UNSUPPORTED"

    def __init__(self, category: str, code: str, path: str, message: str):
        super().__init__(f"{category}:{code} at {path}: {message}")
        self.category = category
        self.code = code
        self.path = path
        self.message = message

    def to_dict(self) -> dict:
        return {"category": self.category, "code": self.code, "path": self.path, "message": self.message}


def invalid(code: str, path: str, message: str) -> SkyError:
    return SkyError(SkyError.INVALID, code, path, message)


def unsupported(code: str, path: str, message: str) -> SkyError:
    return SkyError(SkyError.UNSUPPORTED, code, path, message)
