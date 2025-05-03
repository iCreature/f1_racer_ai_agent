# src/utils/decorators.py

import functools
from fastapi import HTTPException
from pydantic import ValidationError
from .logger import Logger

def validate_payload(model_class):
    """
    Validates incoming JSON payload against a Pydantic model.
    If validation fails, raises HTTPException(422).
    Ensures all endpoints enforce schema checks in a DRY way.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            raw_payload = kwargs.get("payload") or (args[0] if args else {})
            try:
                validated = model_class(**raw_payload)
            except ValidationError as ve:
                Logger.error(f"Payload validation error: {ve}")
                raise HTTPException(status_code=422, detail=ve.errors())
            # replace raw with validated object
            kwargs["payload"] = validated
            return await func(*args, **kwargs)
        return wrapper
    return decorator
