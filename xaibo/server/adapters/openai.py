import json
import time
from uuid import uuid4

from quart import Quart, request, abort

from xaibo import Xaibo

from asyncio import wait_for, Queue, create_task, TimeoutError


class OpenAiApiAdapter:
    def __init__(self, xaibo: Xaibo, streaming_timeout=10):
        self.xaibo = xaibo
        self.streaming_timeout = streaming_timeout

    def adapt(self, app: Quart):
        @app.get("/openai/models")
        async def get_models():
            return {
                "object": "list",
                "data": [
                    dict(
                        id=agent,
                        object="model",
                        created=0,
                        owned_by="organization-owner"
                    ) for agent in self.xaibo.list_agents()
                ]
            }

        @app.post("/openai/chat/completions")
        async def completion_request():
            async with app.app_context():
                data = await request.get_json()
                messages = data.get("messages", [])
                last_user_message = next((m['content'] for m in reversed(messages) if m['role'] == 'user'), None)
                history = [m for m in messages if m['content'] is not last_user_message]

                is_stream = data.get('stream', False)
                conversation_id = uuid4().hex
                
                if is_stream:
                    return await self.handle_streaming_request(app, data, last_user_message, conversation_id)
                else:
                    return await self.handle_non_streaming_request(app, data, last_user_message, conversation_id)

    async def handle_streaming_request(self, app, data, last_user_message, conversation_id):
        # Create response helper
        def create_chunk_response(delta={}, finish_reason=None):
            return {
                "id": f"chatcmpl-{conversation_id}",
                "created": int(time.time()),
                "model": data['model'],
                "object": "chat.completion.chunk",
                "choices": [{
                    "delta": delta,
                    "finish_reason": finish_reason,
                    "index": 0
                }]
            }
            
        async def generate_stream():
            queue = Queue()
            
            class StreamingResponse:
                async def respond_text(self, text: str) -> None:
                    response = create_chunk_response({"content": text})
                    await queue.put(f"data: {json.dumps(response)}\n\n")

            try:
                # Get agent with streaming response handler
                agent = self.xaibo.get_agent_with(data['model'], {
                    'ResponseProtocol': StreamingResponse()
                })
            except KeyError:
                abort(400, "model not found")

            # Start agent in background task
            agent_task = create_task(agent.handle_text(last_user_message))
            
            # Send initial empty chunk to flush headers
            yield f"data: {json.dumps(create_chunk_response({'content': ''}))}\n\n"

            while True:
                try:
                    # Check if agent is done
                    if agent_task.done():
                        # Send final chunks and exit
                        yield f"data: {json.dumps(create_chunk_response({}, 'stop'))}\n\n"
                        yield "data: [DONE]\n\n"
                        break

                    # Get next chunk from queue with timeout
                    chunk = await wait_for(queue.get(), timeout=self.streaming_timeout)
                    yield chunk                    
                except TimeoutError:
                    # Send empty chunk on timeout
                    yield f"data: {json.dumps(create_chunk_response({'content': ''}))}\n\n"
                    continue

        return generate_stream(), 200, {'Content-Type': 'text/event-stream'}
    
    async def handle_non_streaming_request(self, app, data, last_user_message, conversation_id):
        try:
            # Regular non-streaming response
            agent = self.xaibo.get_agent(data['model'])
        except KeyError:
            abort(400, "model not found")
            
        response = await agent.handle_text(last_user_message)
        return {
            'id': f"chatcmpl-{conversation_id}",
            "object": "chat.completion", 
            "created": int(time.time()),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response.text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }