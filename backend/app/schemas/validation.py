from typing import Annotated

from pydantic import AfterValidator


def nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("Must not be blank")
    return value


NonBlank = Annotated[str, AfterValidator(nonblank)]
