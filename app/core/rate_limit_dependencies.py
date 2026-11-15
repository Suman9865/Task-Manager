
from fastapi import Depends, Request

from app.models.user import User
from app.core.dependencies import get_current_user
from app.core.rate_limiter import check_rate_limit, check_ip_rate_limit


def rate_limit_dependency(
    current_user: User = Depends(get_current_user)
) -> dict[str, int]:

    return check_rate_limit(current_user.id)


def ip_rate_limit_dependency(request: Request):

    client_ip = request.client.host

    return check_ip_rate_limit(client_ip)