"""
API routes and endpoints for the FastAPI application.
"""

import os
from typing import Any, Optional, List
from fastapi import APIRouter, Request, HTTPException
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice, ChoiceDelta
from fastapi.responses import StreamingResponse
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


@router.post("/v1/chat/completions")
async def create_chat_completion(
    request: Request, 
    chat_request: dict[Any, Any]
) -> StreamingResponse: # | AsyncStream[ChatCompletionChunk]:
    """
    Create a chat completion using OpenAI API.
    """
    try:
        # Get the OpenAI client from app state
        openai_client = get_openai_client(request)
        assert chat_request.get('stream', False) is True, "Only streaming responses are supported currently"

        chat_request['model'] = full_deployment
        
        prompt = chat_request['messages'][-1]['content']
        
        # Do cleanup pass

        cleanup_prompt = f"""Given the prompt provided inside the <prompt> tags, improve the prompt and do no other actions like generate code or answer questions.
- Translate any text which is not English into English, whilst retaining the original meaning and keeping technical terms like "Python" or anything in backticks as-is.
- Fix any spelling or grammatical errors.
- If there are contradictory instructions, resolve them in a sensible way.
- If you cannot resolve contradictions, response with a question asking for clarification and the tag {NEEDS_CLARIFICATION} at the end of your response.
Respond with the original prompt if no improvements are needed.
        """
        cleanup_result = await openai_client.chat.completions.create(
            model=mini_deployment,
            messages=[
                {"role": "system", "content": cleanup_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            # max_tokens=1000,
            stream=False
        )

        print(f"🧹 Cleaned up prompt: {cleanup_result.choices[0].message.content}")

        if NEEDS_CLARIFICATION in cleanup_result.choices[0].message.content:
            print("❓ Needs clarification, stopping here.")
            async def clarification_generator():
                chunk = ChatCompletionChunk(
                    id=cleanup_result.id,
                    created=cleanup_result.created,
                    choices=[ChunkChoice(
                        index=i, 
                        delta=ChoiceDelta(content=choice.message.content.replace(NEEDS_CLARIFICATION, '')),
                        finish_reason='stop') for i, choice in enumerate(cleanup_result.choices)],
                    usage=cleanup_result.usage,
                    object='chat.completion.chunk',
                    model=mini_deployment
                )
                yield f"data: {chunk.model_dump_json()}\n\n"
            return StreamingResponse(
                content=clarification_generator(),
                media_type="text/event-stream"
            )

        chat_request['messages'][-1]['content'] = cleanup_result.choices[0].message.content

        # Extract content from <prompt> tags if present
        # extracted_prompt = extract_prompt_content(prompt)
        # if extracted_prompt is not None:
        #     # Clean the extracted content and update the message
        #     cleaned_prompt = clean_prompt_content(extracted_prompt)
        #     chat_request['messages'][-1]['content'] = cleaned_prompt
        #     print(f"📝 Extracted prompt from tags: {cleaned_prompt}")
        # else:
        #     print(f"📝 Original prompt (no tags): {prompt}")

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
