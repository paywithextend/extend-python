"""Organization resources visible to the authenticated user."""

from ..validations import pagination, resource_id
from .resource import Resource


class Organizations(Resource):
    @property
    def _base_url(self):
        return "/organizations"

    async def get_organizations(self) -> dict:
        """Return the organizations envelope for the current user."""
        return await self._request("get")

    async def get_organization_members(
        self,
        organization_id: str,
        page=0,
        count=50,
        search=None,
        organization_role=None,
        organization_roles=None,
        show_deactivated_users=True,
        render_metrics=False,
    ) -> dict:
        """Return users and zero-based pagination; metrics are opt-in."""
        pagination(page, count)
        if organization_role is not None and organization_roles is not None:
            raise ValueError("Choose either organization_role or organization_roles")
        return await self._request(
            "get",
            path=f"/{resource_id(organization_id)}/members",
            params={
                "page": page,
                "count": count,
                "search": search,
                "organizationRole": organization_role,
                "organizationRoles": organization_roles,
                "showDeactivatedUsers": show_deactivated_users,
                "renderMetrics": render_metrics,
            },
        )

    async def get_expense_policy(self, organization_id: str) -> dict:
        """Return file/compile metadata; no policy URL is automatically fetched."""
        return await self._request("get", path=f"/{resource_id(organization_id)}/expensepolicy")
