from xaibo.core.protocols import TextMessageHandlerProtocol, ResponseProtocol

class Echo(TextMessageHandlerProtocol):
    """A simple echo module that repeats back the received text message with a prefix."""

    @classmethod
    def provides(cls):
        # This method isn't absolutely necessary as the class is already inheriting from the
        # handler protocol, and the system can therefore know that it provides that protocol
        # But if the module provides multiple protocols, this makes it easier for the user
        # to know.
        return [TextMessageHandlerProtocol]

    def __init__(self, response: ResponseProtocol, config: dict = None):
        """Initialize the Echo module.
        
        Args:
            response: Response handler for sending messages (required)
            config: Configuration dictionary that may contain a 'prefix' key
        """
        self.config: dict = config or {}
        self.prefix: str = self.config.get("prefix", "")
        self.response: ResponseProtocol = response
    
    async def handle_text(self, text: str) -> None:
        """Handle an incoming text message by echoing it back with a prefix.
        
        Args:
            text: The text message to handle
        """
        await self.response.respond_text(f"{self.prefix}{text}")