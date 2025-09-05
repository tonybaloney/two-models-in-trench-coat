"""
API routes and endpoints for the FastAPI application.
"""

import os
import json
from typing import Any, List
from fastapi import APIRouter, Request, HTTPException
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionToolParam
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice, ChoiceDelta
from fastapi.responses import StreamingResponse
from opentelemetry import trace
from opentelemetry.semconv_ai import (
    LLMRequestTypeValues,
    SpanAttributes,
)
from opentelemetry.trace import SpanKind
import logging
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

mini_deployment = os.environ['MINI_DEPLOYMENT']
full_deployment = os.environ['FULL_DEPLOYMENT']

NEEDS_CLARIFICATION = '<needs_clarification>true</needs_clarification>'

def get_openai_client(request: Request) -> AsyncOpenAI:
    """
    Get the OpenAI client from the FastAPI app state.
    
    Args:
        request (Request): FastAPI request object
        
    Returns:
        OpenAI: The OpenAI client instance
        
    Raises:
        HTTPException: If the client is not available
    """
    client = getattr(request.app.state, 'openai_client', None)
    if client is None:
        raise HTTPException(
            status_code=500, 
            detail="OpenAI client not initialized"
        )
    return client


def get_last_user_request(text):
    matches = re.findall(r"<userRequest>(.*?)</userRequest>", text, re.DOTALL)
    if matches:
        return matches[-1]
    return None

@router.post("/v1/chat/completions")
async def create_chat_completion(
    request: Request, 
    chat_request: dict[Any, Any]
) -> StreamingResponse:
    """
    Create a chat completion using OpenAI API.
    """
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("enhance_forward_request") as span:

        try:
            # Get the OpenAI client from app state
            openai_client = get_openai_client(request)
            assert chat_request.get('stream', False) is True, "Only streaming responses are supported currently"

            chat_request['model'] = full_deployment
            
            prompt = chat_request['messages'][-1]['content']
            user_request = get_last_user_request(prompt)
            
            # Do cleanup pass with tool calls for clarification
            cleanup_tools: List[ChatCompletionToolParam] = [
                {
                    "type": "function",
                    "function": {
                        "name": "request_clarification",
                        "description": "Request clarification when vague or contradictory instructions cannot be resolved",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "clarification_question": {
                                    "type": "string",
                                    "description": "The question asking for clarification about the instructions"
                                },
                                "contradictions_found": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of the vague or contradictory instructions that were found"
                                }
                            },
                            "required": ["clarification_question", "contradictions_found"]
                        }
                    }
                }
            ]

            cleanup_prompt = """Given the user's prompt, improve it following these guidelines:
    - Translate any text which is not English into English, whilst retaining the original meaning and keeping technical terms like "Python" or anything in backticks as-is.
    - Fix any spelling or grammatical errors.
    - If there are contradictory instructions, resolve them in a sensible way and explain your reasoning in the response.
    - If you cannot resolve contradictions, use the request_clarification tool to ask for clarification.
    - Respond with the improved prompt if improvements were made, or the original prompt if no improvements are needed.
    - Do not make any other changes.
    - Do no other actions like generate code or answer questions. Only improve the prompt text.
    """

            # Few-shot examples to demonstrate both tool usage and regular improvements
            few_shot_messages = [
                {"role": "system", "content": cleanup_prompt},
                
                # Example 1: Regular prompt improvement (no tool needed)
                {"role": "user", "content": "write a pyhton function that calcuates the sqaure of a numbr"},
                {"role": "assistant", "content": "Write a Python function that calculates the square of a number."},
                
                # Example 2: Contradictory instructions requiring tool call
                {"role": "user", "content": "Create a simple function but make it very complex with advanced features. Use Python 3.6 syntax but also use walrus operators and match statements."},
                {"role": "assistant", "content": "", "tool_calls": [
                    {
                        "id": "call_example",
                        "type": "function", 
                        "function": {
                            "name": "request_clarification",
                            "arguments": json.dumps({
                                "clarification_question": "I found contradictory requirements in your request. Would you like a simple function or one with complex advanced features? Also, which Python version should I target?",
                                "contradictions_found": [
                                    "Request asks for both 'simple function' and 'very complex with advanced features'",
                                    "Python 3.6 syntax requested but walrus operators require Python 3.8+",
                                    "Match statements are only available in Python 3.10+"
                                ]
                            })
                        }
                    }
                ]},
                {"role": "tool", "tool_call_id": "call_example", "content": "Clarification requested due to contradictory requirements."},
                
                # The actual user prompt to process
                {"role": "user", "content": user_request}
            ]

            cleanup_result = await openai_client.chat.completions.create(
                model=mini_deployment,
                messages=few_shot_messages,
                tools=cleanup_tools,
                tool_choice="auto",
                temperature=0.3,
                stream=False,
            )

            # Check if the model used the clarification tool
            choice = cleanup_result.choices[0]
            if choice.message.tool_calls:
                # Model called a tool - check if it's our clarification tool
                for tool_call in choice.message.tool_calls:
                    # Handle different tool call types safely
                    tool_name = getattr(getattr(tool_call, 'function', None), 'name', None)
                    if tool_name == "request_clarification":
                        try:
                            tool_args_str = getattr(getattr(tool_call, 'function', None), 'arguments', '{}')
                            tool_args = json.loads(tool_args_str)
                            clarification_question = tool_args.get("clarification_question", "Please clarify your request.")
                            contradictions = tool_args.get("contradictions_found", [])
                            
                            logger.info(f"❓ Needs clarification: {clarification_question}")
                            logger.info(f"📝 Contradictions found: {contradictions}")

                            # Format a nice clarification response
                            clarification_response = f"{clarification_question}\n\nContradictions found:\n"
                            for i, contradiction in enumerate(contradictions, 1):
                                clarification_response += f"{i}. {contradiction}\n"
                            
                            async def clarification_generator():
                                chunk = ChatCompletionChunk(
                                    id=cleanup_result.id,
                                    created=cleanup_result.created,
                                    choices=[ChunkChoice(
                                        index=0, 
                                        delta=ChoiceDelta(content=clarification_response),
                                        finish_reason='stop'
                                    )],
                                    usage=cleanup_result.usage,
                                    object='chat.completion.chunk',
                                    model=mini_deployment
                                )
                                yield f"data: {chunk.model_dump_json()}\n\n"
                            
                            return StreamingResponse(
                                content=clarification_generator(),
                                media_type="text/event-stream"
                            )
                        except (json.JSONDecodeError, AttributeError) as e:
                            logger.warning(f"⚠️ Failed to parse clarification tool: {e}")
                            break
            
            # If no tool call or regular response, use the cleaned content
            cleaned_content = choice.message.content or prompt
            span.set_attribute("cleaned_content", cleaned_content)
            span.add_event("cleaned_prompt", {"cleaned_content": cleaned_content})

            logger.info(f"🧹 Cleaned up prompt: {cleaned_content}")
            span.set_attribute("original_prompt", prompt)

            chat_request['messages'][-1]['content'] = chat_request['messages'][-1]['content'].replace(user_request, cleaned_content)

            with tracer.start_span(
                "openai.chat",
                kind=SpanKind.CLIENT,
                attributes={SpanAttributes.LLM_REQUEST_TYPE: LLMRequestTypeValues.CHAT.value},
            ) as span:
                span.set_attribute(SpanAttributes.LLM_REQUEST_MODEL, chat_request['model'])
                span.set_attribute(SpanAttributes.LLM_REQUEST_MAX_TOKENS, chat_request.get('max_tokens', 0))
                span.set_attribute(SpanAttributes.LLM_REQUEST_TEMPERATURE, chat_request.get('temperature', 1.0))

                # TODO: this is a hack to retain all the original context, 
                # it breaks some of the tracing
                result = await openai_client.chat.completions._post(
                    "/chat/completions",
                    body=chat_request,
                    cast_to=ChatCompletion,
                    stream=True,
                    stream_cls=AsyncStream[ChatCompletionChunk],
                )

                async def event_generator():
                    async for chunk in result:
                        yield f"data: {chunk.model_dump_json()}\n\n"
                return StreamingResponse(event_generator(), media_type="text/event-stream")

            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error creating chat completion: {str(e)}"
            )
