import json
import time
import logging
from uuid import uuid4

from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.responses import StreamingResponse, JSONResponse

from xaibo import Xaibo, ConfigOverrides, ExchangeConfig
from xaibo.primitives.modules.conversation.conversation import SimpleConversation

from asyncio import wait_for, Queue, create_task, TimeoutError

logger = logging.getLogger(__name__)


class OpenAiApiAdapter:
    def __init__(self, xaibo: Xaibo, streaming_timeout=10):
        self.xaibo = xaibo
        self.streaming_timeout = streaming_timeout
        self.router = APIRouter()

        # Register routes
        self.router.add_api_route("/models", self.get_models, methods=["GET"])
        self.router.add_api_route("/chat/completions", self.completion_request, methods=["POST"])

    def adapt(self, app: FastAPI):
        app.include_router(self.router, prefix="/openai")

    async def get_models(self):
        ids = []
        for agent in self.xaibo.list_agents():
            config = self.xaibo.get_agent_config(agent)
            for exchange in config.exchange:
                if exchange.module == '__entry__':
                    if isinstance(exchange.provider, list):
                        for module_id in exchange.provider:
                            ids.append(f"{agent}/{module_id}")
                    else:
                        ids.append(f"{agent}")
        return {
            "object": "list",
            "data": [
                dict(
                    id=agent,
                    object="model",
                    created=0,
                    owned_by="organization-owner"
                ) for agent in ids
            ]
        }

    async def completion_request(self, request: Request):
        try:
            data = await request.json()
            messages = data.get("messages", [])
            last_user_message = next((m['content'] for m in reversed(messages) if m['role'] == 'user'), None)
            
            # Create conversation history from messages
            conversation = SimpleConversation.from_openai_messages(messages)

            is_stream = data.get('stream', False)
            conversation_id = uuid4().hex
            
            if is_stream:
                return await self.handle_streaming_request(data, last_user_message, conversation_id, conversation)
            else:
                return await self.handle_non_streaming_request(data, last_user_message, conversation_id, conversation)
        except Exception as e:
            logger.exception(f"Unexpected error in completion_request: {str(e)}")
            raise

    async def handle_streaming_request(self, data, last_user_message, conversation_id, conversation):
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

                async def get_response(self):
                    return None

            agent_id = data['model']
            if '/' in agent_id:
                (id, entry_point) = agent_id.split('/')
            else:
                (id, entry_point) = (agent_id, '__entry__')

            try:
                # Get agent with streaming response handler and conversation history
                agent = self.xaibo.get_agent_with(id, ConfigOverrides(
                    instances={
                        '__conversation_history__': conversation,
                        '__response__': StreamingResponse()
                    },
                    exchange=[ExchangeConfig(
                        protocol='ConversationHistoryProtocol',
                        provider='__conversation_history__'
                    )]
                ))
            except KeyError:
                raise HTTPException(status_code=400, detail="model not found")
            except Exception as e:
                logger.exception(f"Error getting agent for streaming request: {str(e)}")
                raise

            # Start agent in background task
            agent_task = create_task(agent.handle_text(last_user_message, entry_point=entry_point))
            
            # Send initial empty chunk to flush headers
            yield f"data: {json.dumps(create_chunk_response({'content': ''}))}\n\n"

            while True:
                try:
                    # Check if agent is done
                    if agent_task.done():
                        # Check if there was an exception in the agent task
                        if agent_task.exception():
                            logger.exception(f"Agent task failed with exception: {agent_task.exception()}")
                            raise agent_task.exception()
                        
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
                except Exception as e:
                    logger.exception(f"Unexpected error in streaming response: {str(e)}")
                    raise

        try:
            return StreamingResponse(generate_stream(), media_type='text/event-stream')
        except Exception as e:
            logger.exception(f"Error setting up streaming response: {str(e)}")
            raise
    
    async def handle_non_streaming_request(self, data, last_user_message, conversation_id, conversation):
        agent_id = data['model']
        if '/' in agent_id:
            (id, entry_point) = agent_id.split('/')
        else:
            (id, entry_point) = (agent_id, '__entry__')
        try:
            # Regular non-streaming response with conversation history
            agent = self.xaibo.get_agent_with(id, ConfigOverrides(
                instances={
                    '__conversation_history__': conversation
                },
                exchange=[ExchangeConfig(
                    protocol='ConversationHistoryProtocol',
                    provider='__conversation_history__'
                )]
            ))
        except KeyError:
            raise HTTPException(status_code=400, detail="model not found")
        except Exception as e:
            logger.exception(f"Error getting agent for non-streaming request: {str(e)}")
            raise
            
        try:
            response = await agent.handle_text(last_user_message, entry_point=entry_point)
            
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
        except Exception as e:
            logger.exception(f"Error handling non-streaming text request: {str(e)}")
            raise