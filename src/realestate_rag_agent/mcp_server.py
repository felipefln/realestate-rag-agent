"""MCP server exposing the property search as tools over stdio.

Run it directly (``python -m realestate_rag_agent.mcp_server`` or the
``realestate-mcp`` script) and point an MCP client (e.g. Claude Desktop) at it.
"""

from mcp.server.mcpserver import MCPServer

from realestate_rag_agent.agent import tools as agent_tools
from realestate_rag_agent.agent.tools import SESSION_CONFIG_KEY
from realestate_rag_agent.core.db import SessionLocal

mcp = MCPServer("realestate-rag-agent")


def _run(lc_tool, **kwargs) -> str:
    with SessionLocal() as session:
        return lc_tool.invoke(kwargs, config={"configurable": {SESSION_CONFIG_KEY: session}})


@mcp.tool()
def search_properties(
    query: str,
    operation: str | None = None,
    property_type: str | None = None,
    neighborhood: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_bedrooms: int | None = None,
    min_area: float | None = None,
    amenities: list[str] | None = None,
    limit: int = 8,
) -> str:
    """Semantic search over real-estate listings, optionally narrowed by filters."""
    return _run(
        agent_tools.search_properties,
        query=query,
        operation=operation,
        property_type=property_type,
        neighborhood=neighborhood,
        min_price=min_price,
        max_price=max_price,
        min_bedrooms=min_bedrooms,
        min_area=min_area,
        amenities=amenities,
        limit=limit,
    )


@mcp.tool()
def filter_properties(
    operation: str | None = None,
    property_type: str | None = None,
    neighborhood: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_bedrooms: int | None = None,
    min_area: float | None = None,
    amenities: list[str] | None = None,
    limit: int = 8,
) -> str:
    """List properties by structured filters only (no semantic ranking)."""
    return _run(
        agent_tools.filter_properties,
        operation=operation,
        property_type=property_type,
        neighborhood=neighborhood,
        min_price=min_price,
        max_price=max_price,
        min_bedrooms=min_bedrooms,
        min_area=min_area,
        amenities=amenities,
        limit=limit,
    )


@mcp.tool()
def get_property_details(property_id: str) -> str:
    """Full details of a single property by its id."""
    return _run(agent_tools.get_property_details, property_id=property_id)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
