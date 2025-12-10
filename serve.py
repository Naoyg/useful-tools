# server_openai_compatible.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Literal
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from datetime import datetime
import json

app = FastAPI(
    title="Gemini OpenAI Compatible API",
    version="1.0",
)

# OpenAI互換のリクエストモデル
class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False

def convert_to_langchain_messages(messages: List[Message]):
    """OpenAI形式のメッセージをLangChainのメッセージに変換"""
    lc_messages = []
    for msg in messages:
        if msg.role == "system":
            lc_messages.append(SystemMessage(content=msg.content))
        elif msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            lc_messages.append(AIMessage(content=msg.content))
    return lc_messages

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    try:
        # ChatVertexAIのモデルを初期化（VMの認証情報を自動使用）
        model = ChatVertexAI(
            model_name=request.model,
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
        )
        
        # メッセージを変換
        lc_messages = convert_to_langchain_messages(request.messages)
        
        if request.stream:
            # ストリーミングレスポンス
            async def generate():
                async for chunk in model.astream(lc_messages):
                    chunk_data = {
                        "id": f"chatcmpl-{datetime.now().timestamp()}",
                        "object": "chat.completion.chunk",
                        "created": int(datetime.now().timestamp()),
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": chunk.content},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # 終了チャンク
                final_chunk = {
                    "id": f"chatcmpl-{datetime.now().timestamp()}",
                    "object": "chat.completion.chunk",
                    "created": int(datetime.now().timestamp()),
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(final_chunk)}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        else:
            # 通常のレスポンス
            response = await model.ainvoke(lc_messages)
            
            return {
                "id": f"chatcmpl-{datetime.now().timestamp()}",
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.content
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    """OpenAI互換のモデルリスト"""
    return {
        "object": "list",
        "data": []
    }

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)