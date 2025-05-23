import json
import time
import logging
import sqlite3
import os
from uuid import uuid4
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, APIRouter, Query
from fastapi.responses import StreamingResponse, JSONResponse

from xaibo import Xaibo, ConfigOverrides, ExchangeConfig
from xaibo.primitives.modules.conversation.conversation import SimpleConversation
from xaibo.core.models.llm import LLMMessage

from asyncio import wait_for, Queue, create_task, TimeoutError

logger = logging.getLogger(__name__)


class OpenAiResponsesApiAdapter:
    def __init__(self, xaibo: Xaibo, streaming_timeout=10, responses_dir="./responses"):
        self.xaibo = xaibo
        self.streaming_timeout = streaming_timeout
        self.responses_dir = responses_dir
        self.router = APIRouter()
        
        # Ensure responses directory exists
        os.makedirs(self.responses_dir, exist_ok=True)
        
        # Initialize database
        self._init_database()

        # Register routes
        self.router.add_api_route("/responses", self.create_response, methods=["POST"])
        self.router.add_api_route("/responses/{response_id}", self.get_response, methods=["GET"])
        self.router.add_api_route("/responses/{response_id}", self.delete_response, methods=["DELETE"])
        self.router.add_api_route("/responses/{response_id}/cancel", self.cancel_response, methods=["POST"])
        self.router.add_api_route("/responses/{response_id}/input_items", self.get_input_items, methods=["GET"])

    def adapt(self, app: FastAPI):
        app.include_router(self.router, prefix="/openai")

    def _init_database(self):
        """Initialize SQLite database for storing responses"""
        db_path = os.path.join(self.responses_dir, "responses.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create responses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id TEXT PRIMARY KEY,
                object TEXT DEFAULT 'response',
                created_at INTEGER,
                status TEXT,
                error TEXT,
                incomplete_details TEXT,
                instructions TEXT,
                max_output_tokens INTEGER,
                model TEXT,
                output TEXT,
                parallel_tool_calls BOOLEAN,
                previous_response_id TEXT,
                reasoning TEXT,
                store BOOLEAN,
                temperature REAL,
                text TEXT,
                tool_choice TEXT,
                tools TEXT,
                top_p REAL,
                truncation TEXT,
                usage TEXT,
                user_id TEXT,
                metadata TEXT,
                background BOOLEAN
            )
        """)
        
        # Create input_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS input_items (
                id TEXT PRIMARY KEY,
                response_id TEXT,
                type TEXT,
                role TEXT,
                content TEXT,
                created_at INTEGER,
                FOREIGN KEY (response_id) REFERENCES responses (id)
            )
        """)
        
        # Create conversation_history table for stateful conversations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id TEXT PRIMARY KEY,
                response_id TEXT,
                previous_response_id TEXT,
                conversation_data TEXT,
                created_at INTEGER,
                FOREIGN KEY (response_id) REFERENCES responses (id)
            )
        """)
        
        conn.commit()
        conn.close()

    def _get_db_connection(self):
        """Get database connection"""
        db_path = os.path.join(self.responses_dir, "responses.db")
        return sqlite3.connect(db_path)

    def _store_response(self, response_data: Dict[str, Any]):
        """Store response in database"""
        if not response_data.get('store', True):
            return
            
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO responses (
                id, object, created_at, status, error, incomplete_details,
                instructions, max_output_tokens, model, output, parallel_tool_calls,
                previous_response_id, reasoning, store, temperature, text,
                tool_choice, tools, top_p, truncation, usage, user_id, metadata, background
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            response_data['id'],
            response_data.get('object', 'response'),
            response_data['created_at'],
            response_data['status'],
            json.dumps(response_data.get('error')) if response_data.get('error') else None,
            json.dumps(response_data.get('incomplete_details')) if response_data.get('incomplete_details') else None,
            response_data.get('instructions'),
            response_data.get('max_output_tokens'),
            response_data['model'],
            json.dumps(response_data.get('output', [])),
            response_data.get('parallel_tool_calls', True),
            response_data.get('previous_response_id'),
            json.dumps(response_data.get('reasoning')) if response_data.get('reasoning') else None,
            response_data.get('store', True),
            response_data.get('temperature'),
            json.dumps(response_data.get('text')) if response_data.get('text') else None,
            json.dumps(response_data.get('tool_choice')) if response_data.get('tool_choice') else None,
            json.dumps(response_data.get('tools', [])),
            response_data.get('top_p'),
            response_data.get('truncation'),
            json.dumps(response_data.get('usage')) if response_data.get('usage') else None,
            response_data.get('user'),
            json.dumps(response_data.get('metadata', {})),
            response_data.get('background', False)
        ))
        
        conn.commit()
        conn.close()

    def _store_input_items(self, response_id: str, input_data: Any):
        """Store input items for a response"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # Convert input to standardized format
        if isinstance(input_data, str):
            # Simple text input
            item_id = f"msg_{uuid4().hex}"
            cursor.execute("""
                INSERT INTO input_items (id, response_id, type, role, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                response_id,
                "message",
                "user",
                json.dumps([{"type": "input_text", "text": input_data}]),
                int(time.time())
            ))
        elif isinstance(input_data, list):
            # Array of input items
            for item in input_data:
                item_id = f"msg_{uuid4().hex}"
                cursor.execute("""
                    INSERT INTO input_items (id, response_id, type, role, content, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    item_id,
                    response_id,
                    item.get('type', 'message'),
                    item.get('role', 'user'),
                    json.dumps(item.get('content', [])),
                    int(time.time())
                ))
        
        conn.commit()
        conn.close()

    def _get_stored_response(self, response_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored response from database"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM responses WHERE id = ?", (response_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        # Convert row to dict
        columns = [desc[0] for desc in cursor.description]
        response_data = dict(zip(columns, row))
        
        # Parse JSON fields
        json_fields = ['error', 'incomplete_details', 'output', 'reasoning', 'text', 'tool_choice', 'tools', 'usage', 'metadata']
        for field in json_fields:
            if response_data.get(field):
                try:
                    response_data[field] = json.loads(response_data[field])
                except json.JSONDecodeError:
                    pass
                    
        return response_data

    def _get_conversation_history(self, previous_response_id: str) -> Optional[SimpleConversation]:
        """Get conversation history from previous response"""
        if not previous_response_id:
            return None
            
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT conversation_data FROM conversation_history 
            WHERE response_id = ? ORDER BY created_at DESC LIMIT 1
        """, (previous_response_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            try:
                conversation_data = json.loads(row[0])
                # Reconstruct conversation from stored data using OpenAI format
                openai_messages = conversation_data.get('messages', [])
                return SimpleConversation.from_openai_messages(openai_messages)
            except json.JSONDecodeError:
                pass
                
        return None

    async def _store_conversation_history(self, response_id: str, previous_response_id: str, conversation: SimpleConversation):
        """Store conversation history"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # Get conversation history and convert to storable format
        messages = await conversation.get_history()
        conversation_data = {
            'messages': [
                {
                    'role': msg.role.value,
                    'content': msg.content[0].text if msg.content and msg.content[0].text else ''
                }
                for msg in messages
            ]
        }
        
        cursor.execute("""
            INSERT INTO conversation_history (id, response_id, previous_response_id, conversation_data, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            uuid4().hex,
            response_id,
            previous_response_id,
            json.dumps(conversation_data),
            int(time.time())
        ))
        
        conn.commit()
        conn.close()

    async def create_response(self, request: Request):
        """Create a model response"""
        try:
            data = await request.json()
            
            # Extract required fields
            input_data = data.get("input")
            model = data.get("model")
            
            if not input_data or not model:
                raise HTTPException(status_code=400, detail="input and model are required")
            
            # Generate response ID
            response_id = f"resp_{uuid4().hex}"
            created_at = int(time.time())
            
            # Get conversation history if previous_response_id is provided
            previous_response_id = data.get("previous_response_id")
            conversation = self._get_conversation_history(previous_response_id)
            
            # Convert input to conversation format
            if isinstance(input_data, str):
                if conversation is None:
                    conversation = SimpleConversation()
                await conversation.add_message(LLMMessage.user(input_data))
                last_user_message = input_data
            else:
                # Handle array input format - for now, take the last user message
                if conversation is None:
                    conversation = SimpleConversation()
                last_user_message = "Hello"  # Default fallback
                
                if isinstance(input_data, list):
                    for item in input_data:
                        if item.get('type') == 'message' and item.get('role') == 'user':
                            content = item.get('content', [])
                            if content and isinstance(content, list):
                                for content_item in content:
                                    if content_item.get('type') == 'input_text':
                                        text = content_item.get('text', '')
                                        await conversation.add_message(LLMMessage.user(text))
                                        last_user_message = text

            # Create initial response object
            response_data = {
                "id": response_id,
                "object": "response",
                "created_at": created_at,
                "status": "in_progress",
                "error": None,
                "incomplete_details": None,
                "instructions": data.get("instructions"),
                "max_output_tokens": data.get("max_output_tokens"),
                "model": model,
                "output": [],
                "parallel_tool_calls": data.get("parallel_tool_calls", True),
                "previous_response_id": previous_response_id,
                "reasoning": data.get("reasoning"),
                "store": data.get("store", True),
                "temperature": data.get("temperature", 1.0),
                "text": data.get("text"),
                "tool_choice": data.get("tool_choice", "auto"),
                "tools": data.get("tools", []),
                "top_p": data.get("top_p", 1.0),
                "truncation": data.get("truncation", "disabled"),
                "usage": None,
                "user": data.get("user"),
                "metadata": data.get("metadata", {}),
                "background": data.get("background", False)
            }
            
            # Store input items
            self._store_input_items(response_id, input_data)
            
            is_stream = data.get('stream', False)
            
            if is_stream:
                return await self._handle_streaming_response(response_data, last_user_message, conversation)
            else:
                return await self._handle_non_streaming_response(response_data, last_user_message, conversation)
                
        except Exception as e:
            logger.exception(f"Unexpected error in create_response: {str(e)}")
            raise

    async def _handle_streaming_response(self, response_data: Dict[str, Any], last_user_message: str, conversation: SimpleConversation):
        """Handle streaming response"""
        sequence_number = 1
        
        async def generate_stream():
            nonlocal sequence_number
            
            # Send response.created event
            event_data = {
                'type': 'response.created',
                'response': response_data,
                'sequence_number': sequence_number
            }
            yield f"data: {json.dumps(event_data)}\n\n"
            sequence_number += 1
            
            # Send response.in_progress event
            event_data = {
                'type': 'response.in_progress',
                'response': response_data,
                'sequence_number': sequence_number
            }
            yield f"data: {json.dumps(event_data)}\n\n"
            sequence_number += 1
            
            queue = Queue()
            
            class StreamingResponseHandler:
                def __init__(self):
                    self.message_id = f"msg_{uuid4().hex}"
                    self.output_index = 0
                    self.content_index = 0
                    self.accumulated_text = ""
                    
                async def respond_text(self, text: str) -> None:
                    # Send output_text.delta event
                    event_data = {
                        'type': 'response.output_text.delta',
                        'item_id': self.message_id,
                        'output_index': self.output_index,
                        'content_index': self.content_index,
                        'delta': text,
                        'sequence_number': sequence_number
                    }
                    await queue.put(f"data: {json.dumps(event_data)}\n\n")
                    self.accumulated_text += text

                async def get_response(self):
                    return None

            # Get agent
            agent_id = response_data['model']
            if '/' in agent_id:
                (id, entry_point) = agent_id.split('/')
            else:
                (id, entry_point) = (agent_id, '__entry__')

            try:
                streaming_handler = StreamingResponseHandler()
                
                # Send output_item.added event
                event_data = {
                    'type': 'response.output_item.added',
                    'output_index': 0,
                    'item': {
                        'id': streaming_handler.message_id,
                        'status': 'in_progress',
                        'type': 'message',
                        'role': 'assistant',
                        'content': []
                    },
                    'sequence_number': sequence_number
                }
                yield f"data: {json.dumps(event_data)}\n\n"
                sequence_number += 1
                
                # Send content_part.added event
                event_data = {
                    'type': 'response.content_part.added',
                    'item_id': streaming_handler.message_id,
                    'output_index': 0,
                    'content_index': 0,
                    'part': {
                        'type': 'output_text',
                        'text': '',
                        'annotations': []
                    },
                    'sequence_number': sequence_number
                }
                yield f"data: {json.dumps(event_data)}\n\n"
                sequence_number += 1
                
                agent = self.xaibo.get_agent_with(id, ConfigOverrides(
                    instances={
                        '__conversation_history__': conversation,
                        '__response__': streaming_handler
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

            while True:
                try:
                    # Check if agent is done
                    if agent_task.done():
                        # Check if there was an exception in the agent task
                        if agent_task.exception():
                            logger.exception(f"Agent task failed with exception: {agent_task.exception()}")
                            # Send error response
                            response_data['status'] = 'failed'
                            response_data['error'] = {
                                'code': 'server_error',
                                'message': str(agent_task.exception())
                            }
                            event_data = {
                                'type': 'response.failed',
                                'response': response_data,
                                'sequence_number': sequence_number
                            }
                            yield f"data: {json.dumps(event_data)}\n\n"
                            break
                        
                        # Send final events
                        # content_part.done
                        event_data = {
                            'type': 'response.content_part.done',
                            'item_id': streaming_handler.message_id,
                            'output_index': 0,
                            'content_index': 0,
                            'part': {
                                'type': 'output_text',
                                'text': streaming_handler.accumulated_text,
                                'annotations': []
                            },
                            'sequence_number': sequence_number
                        }
                        yield f"data: {json.dumps(event_data)}\n\n"
                        sequence_number += 1
                        
                        # output_text.done
                        event_data = {
                            'type': 'response.output_text.done',
                            'item_id': streaming_handler.message_id,
                            'output_index': 0,
                            'content_index': 0,
                            'text': streaming_handler.accumulated_text,
                            'sequence_number': sequence_number
                        }
                        yield f"data: {json.dumps(event_data)}\n\n"
                        sequence_number += 1
                        
                        # output_item.done
                        event_data = {
                            'type': 'response.output_item.done',
                            'output_index': 0,
                            'item': {
                                'id': streaming_handler.message_id,
                                'status': 'completed',
                                'type': 'message',
                                'role': 'assistant',
                                'content': [{
                                    'type': 'output_text',
                                    'text': streaming_handler.accumulated_text,
                                    'annotations': []
                                }]
                            },
                            'sequence_number': sequence_number
                        }
                        yield f"data: {json.dumps(event_data)}\n\n"
                        sequence_number += 1
                        
                        # Update response data for final event
                        response_data['status'] = 'completed'
                        response_data['output'] = [{
                            'type': 'message',
                            'id': streaming_handler.message_id,
                            'status': 'completed',
                            'role': 'assistant',
                            'content': [{
                                'type': 'output_text',
                                'text': streaming_handler.accumulated_text,
                                'annotations': []
                            }]
                        }]
                        response_data['usage'] = {
                            'input_tokens': 0,
                            'input_tokens_details': {'cached_tokens': 0},
                            'output_tokens': 0,
                            'output_tokens_details': {'reasoning_tokens': 0},
                            'total_tokens': 0
                        }
                        
                        # response.completed
                        event_data = {
                            'type': 'response.completed',
                            'response': response_data,
                            'sequence_number': sequence_number
                        }
                        yield f"data: {json.dumps(event_data)}\n\n"
                        
                        # Store final response
                        self._store_response(response_data)
                        
                        # Store conversation history
                        await conversation.add_message(LLMMessage.assistant(streaming_handler.accumulated_text))
                        await self._store_conversation_history(
                            response_data['id'],
                            response_data.get('previous_response_id'),
                            conversation
                        )
                        
                        yield "data: [DONE]\n\n"
                        break

                    # Get next chunk from queue with timeout
                    chunk = await wait_for(queue.get(), timeout=self.streaming_timeout)
                    yield chunk
                    sequence_number += 1
                    
                except TimeoutError:
                    # Continue waiting
                    continue
                except Exception as e:
                    logger.exception(f"Unexpected error in streaming response: {str(e)}")
                    raise

        try:
            return StreamingResponse(generate_stream(), media_type='text/event-stream')
        except Exception as e:
            logger.exception(f"Error setting up streaming response: {str(e)}")
            raise

    async def _handle_non_streaming_response(self, response_data: Dict[str, Any], last_user_message: str, conversation: SimpleConversation):
        """Handle non-streaming response"""
        agent_id = response_data['model']
        if '/' in agent_id:
            (id, entry_point) = agent_id.split('/')
        else:
            (id, entry_point) = (agent_id, '__entry__')
            
        try:
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
            agent_response = await agent.handle_text(last_user_message, entry_point=entry_point)
            
            # Create message output
            message_id = f"msg_{uuid4().hex}"
            response_data['status'] = 'completed'
            response_data['output'] = [{
                'type': 'message',
                'id': message_id,
                'status': 'completed',
                'role': 'assistant',
                'content': [{
                    'type': 'output_text',
                    'text': agent_response.text,
                    'annotations': []
                }]
            }]
            response_data['usage'] = {
                'input_tokens': 0,
                'input_tokens_details': {'cached_tokens': 0},
                'output_tokens': 0,
                'output_tokens_details': {'reasoning_tokens': 0},
                'total_tokens': 0
            }
            
            # Store response
            self._store_response(response_data)
            
            # Store conversation history
            await conversation.add_message(LLMMessage.assistant(agent_response.text))
            await self._store_conversation_history(
                response_data['id'],
                response_data.get('previous_response_id'),
                conversation
            )
            
            return response_data
            
        except Exception as e:
            logger.exception(f"Error handling non-streaming text request: {str(e)}")
            raise

    async def get_response(self, response_id: str, include: List[str] = Query(default=[])):
        """Retrieve a model response"""
        response_data = self._get_stored_response(response_id)
        if not response_data:
            raise HTTPException(status_code=404, detail="Response not found")
        
        # Apply include filters if needed
        # For now, return the full response
        return response_data

    async def delete_response(self, response_id: str):
        """Delete a model response"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # Check if response exists
        cursor.execute("SELECT id FROM responses WHERE id = ?", (response_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Response not found")
        
        # Delete response and related data
        cursor.execute("DELETE FROM input_items WHERE response_id = ?", (response_id,))
        cursor.execute("DELETE FROM conversation_history WHERE response_id = ?", (response_id,))
        cursor.execute("DELETE FROM responses WHERE id = ?", (response_id,))
        
        conn.commit()
        conn.close()
        
        return {
            "id": response_id,
            "object": "response",
            "deleted": True
        }

    async def cancel_response(self, response_id: str):
        """Cancel a model response"""
        response_data = self._get_stored_response(response_id)
        if not response_data:
            raise HTTPException(status_code=404, detail="Response not found")
        
        # Only background responses can be cancelled
        if not response_data.get('background', False):
            raise HTTPException(status_code=400, detail="Only background responses can be cancelled")
        
        # Update status to cancelled
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE responses SET status = ? WHERE id = ?", ("cancelled", response_id))
        conn.commit()
        conn.close()
        
        # Return updated response
        response_data['status'] = 'cancelled'
        return response_data

    async def get_input_items(
        self, 
        response_id: str,
        after: Optional[str] = Query(default=None),
        before: Optional[str] = Query(default=None),
        include: List[str] = Query(default=[]),
        limit: int = Query(default=20, ge=1, le=100),
        order: str = Query(default="desc")
    ):
        """List input items for a response"""
        # Check if response exists
        response_data = self._get_stored_response(response_id)
        if not response_data:
            raise HTTPException(status_code=404, detail="Response not found")
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # Build query with pagination
        query = "SELECT * FROM input_items WHERE response_id = ?"
        params = [response_id]
        
        if after:
            query += " AND id > ?"
            params.append(after)
        if before:
            query += " AND id < ?"
            params.append(before)
            
        query += f" ORDER BY created_at {'ASC' if order == 'asc' else 'DESC'} LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to response format
        items = []
        for row in rows:
            item = {
                "id": row[0],
                "type": row[2],
                "role": row[3],
                "content": json.loads(row[4]) if row[4] else []
            }
            items.append(item)
        
        return {
            "object": "list",
            "data": items,
            "first_id": items[0]["id"] if items else None,
            "last_id": items[-1]["id"] if items else None,
            "has_more": len(items) == limit
        }