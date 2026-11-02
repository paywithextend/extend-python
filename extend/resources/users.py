from ..validations import resource_id
from .resource import Resource


class Users(Resource):
    @property
    def _base_url(self):
        return "/users"

    async def get_user_details(self, user_id: str) -> dict:
        """Return a flat user view, subject to server-side access controls."""
        return await self._request("get", path=f"/{resource_id(user_id)}")
