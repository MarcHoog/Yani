from fastapi import HTTPException, status


class NotFound(HTTPException):
    def __init__(self, what: str, ident: str) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, f"{what} '{ident}' not found")
