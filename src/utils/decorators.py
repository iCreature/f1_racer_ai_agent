import functools
import inspect
from typing import Any, Callable, Type, TypeVar, Optional
from pydantic import BaseModel, ValidationError
from fastapi import HTTPException
from .logger import F1Logger

ModelT = TypeVar('ModelT', bound=BaseModel)
logger = F1Logger()

def validate_payload(
    model_class: Type[ModelT],
    *,
    param_name: str = "payload",
    enable_async: bool = True
) -> Callable:
    """
    Generic payload validation decorator with async/sync support and proper DI.
    
    Args:
        model_class: Pydantic model to validate against
        param_name: Name of the parameter to validate (default: "payload")
        enable_async: Support async functions (default: True)
    """
    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        payload_param = sig.parameters.get(param_name)
        
        if not payload_param:
            raise ValueError(f"No parameter named '{param_name}' in {func.__name__}")

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return await _validate_and_execute(func, args, kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return _validate_and_execute(func, args, kwargs)

        def _validate_and_execute(fn: Callable, args: tuple, kwargs: dict) -> Any:
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            raw = bound_args.arguments.get(param_name)

            try:
                validated = model_class(**raw) if isinstance(raw, dict) else raw
                bound_args.arguments[param_name] = validated
            except ValidationError as exc:
                logger.error(
                    action="payload_validation",
                    response=f"Invalid {param_name} in {fn.__name__}",
                    exc=exc
                )
                raise HTTPException(
                    status_code=422,
                    detail=exc.errors()
                ) from exc

            return fn(*bound_args.args, **bound_args.kwargs)

        return async_wrapper if enable_async and inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator