from xaibo.primitives.modules.tools.python_tool_provider import tool

@tool
def sample_function(location: str, unit: str = "celsius"):
    """Get the current weather in a given location

    Args:
        location: The city and state, e.g. San Francisco, CA
        unit: The temperature unit to use (celsius or fahrenheit)

    Returns:
        Weather information for the location
    """
    return f"Weather in {location} is sunny and 25 degrees {unit}"


@tool
def another_function(query: str):
    """Search for information

    Args:
        query: The search query

    Returns:
        Search results
    """
    return f"Results for {query}"


def not_a_tool(x: int):
    """This is not marked as a tool"""
    return x * 2