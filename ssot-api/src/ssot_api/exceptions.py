from fastapi import HTTPException, status


class NotFound(HTTPException):
    def __init__(self, what: str, ident: str) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, f"{what} '{ident}' not found")


class InvalidRelation(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)
