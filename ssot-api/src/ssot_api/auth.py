"""Caller dependency for ssot-api. See yani_shared.auth for the token contract."""

from typing import Annotated

from fastapi import Depends

from ssot_api.config import auth_settings
from yani_shared.auth import Auth, Caller

auth = Auth(auth_settings)
CallerDep = Annotated[Caller, Depends(auth)]
