from typing import Callable, Any, Iterable
from .registry import TelemetryRegister
from functools import wraps
import httpx
import warnings
import asyncio

from .api import ApiHandler


def ipy_register_func(
    service: str,
    extra_fields: dict[str, Any] | None = None,
    pop_fields: Iterable[str] | None = None,
) -> Callable[..., Any]:
    """
    Decorator to register a function in the specified service and track usage
    using IPython events. This hides a lot of complexity which is more visible in
    the `register_func` decorator.

    Parameters
    ----------
    func : Callable
        The function to register.
    service : str
        The name of the telemetry register to use.
    extra_fields : Iterable[dict[str, Any]], optional
        Extra fields to add to the telemetry record. These can also be added after
        the fact using the `add_extra_field` method.
    pop_fields : Iterable[str], optional
        Fields to remove from the telemetry record. This can be useful for removing
        default fields that are not needed for a particular function

    Returns
    -------
    Callable
        The function with the telemetry decorator.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        api_handler = ApiHandler()

        api_handler.add_extra_fields(service, extra_fields or {})
        api_handler.remove_fields(service, pop_fields or [])
        TelemetryRegister(service).register(func.__name__)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def register_func(
    service: str,
    extra_fields: dict[str, Any] | None = None,
    pop_fields: Iterable[str] | None = None,
) -> Callable[..., Any]:
    """
    Decorator to register a function in the specified service and track usage
    with async requests.

    Parameters
    ----------
    func : Callable
        The function to register.
    service : str
        The name of the telemetry register to use.
    extra fields : Iterable[dict[str, Any]], optional
        Extra fields to add to the telemetry record. These can also be added after
        the fact using the `add_extra_field` method.
    pop_fields : Iterable[str], optional
        Fields to remove from the telemetry record. This can be useful for removing
        default fields that are not needed for a particular function.

    Returns
    -------
    Callable
        The function with the telemetry decorator.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        api_handler = ApiHandler()

        # Configure fields & register the function
        api_handler.add_extra_fields(service, extra_fields or {})
        api_handler.remove_fields(service, pop_fields or [])
        TelemetryRegister(service).register(func.__name__)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            telemetry_data = api_handler._create_telemetry_record(
                service, func.__name__, args, kwargs
            )

            endpoint = f"{api_handler.server_url}{api_handler.endpoints[service]}"

            print(f"Sending telemetry data to {endpoint}")

            async def send_telemetry(data: dict[str, Any]) -> None:

                print(f"Telemetry Data: {data}")
                print(f"Endpoint: {endpoint}")
                headers = {"Content-Type": "application/json"}
                print(f"Headers: {headers}")

                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.post(
                            endpoint, json=data, headers=headers
                        )
                        response.raise_for_status()
                    except httpx.RequestError as e:
                        warnings.warn(
                            f"Request failed: {e}",
                            category=RuntimeWarning,
                            stacklevel=2,
                        )
            # Check if there's an existing event loop, otherwise create a new one


            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                loop.create_task(send_telemetry(telemetry_data))
            else:
                # breakpoint()
                # loop.create_task(send_telemetry(telemetry_data))
                loop.run_until_complete(send_telemetry(telemetry_data))
                warnings.warn(
                    "Event loop not running, telemetry will block execution",
                    category=RuntimeWarning,
                )

            # Call the original function
            return func(*args, **kwargs)

        return wrapper

    return decorator
