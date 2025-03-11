from typing import BinaryIO

from xaibo.core.protocols import ResponseProtocol
from xaibo.core.models import FileAttachment, FileType, Response


class ResponseHandler(ResponseProtocol):
    def __init__(self, config: dict = None):
        self._response = Response()

    async def get_response(self) -> Response:
        return self._response

    async def respond_text(self, response: str) -> None:
        if self._response.text is None:
            self._response.text = response
        else:
            self._response.text += response

    async def respond_image(self, iolike: BinaryIO) -> None:
        self._response.attachments.append(FileAttachment(content=iolike, type=FileType.IMAGE))

    async def respond_audio(self, iolike: BinaryIO) -> None:
        self._response.attachments.append(FileAttachment(content=iolike, type=FileType.AUDIO))

    async def respond_file(self, iolike: BinaryIO) -> None:
        self._response.attachments.append(FileAttachment(content=iolike, type=FileType.FILE))

    async def respond(self, response: Response) -> None:
        if response.text is not None:
            if self._response.text is None:
                self._response.text = response.text
            else:
                self._response.text += response.text
        self._response.attachments.extend(response.attachments)