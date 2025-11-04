import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

app = FastAPI(title="Emotion Voice AI - LLM", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LLM_BACKEND = os.getenv("LLM_BACKEND", "huggingface")  
HF_TOKEN = os.getenv("HF_TOKEN", None)


try:
    if LLM_BACKEND == "huggingface":
        MODEL_ID = os.getenv("LLAMA_MODEL_ID", "meta-llama/Meta-Llama-3-8B-Instruct")
        print(f"🦙 Loading LLaMA model: {MODEL_ID}")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_auth_token=HF_TOKEN)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            use_auth_token=HF_TOKEN
        )
        print(" LLaMA model loaded successfully.")
    else:
        model = None
except Exception as e:
    print(f"⚠️ Failed to load LLaMA: {e}")
    model = None



class LLMInput(BaseModel):
    context: str
    emotion: str
    policy: str


class LLMOutput(BaseModel):
    action: str
    message: str
    priority: int


@app.post("/generate", response_model=LLMOutput)
async def generate_response(data: LLMInput):
    try:
        context_prompt = (
            f"You are an empathetic AI assistant.\n"
            f"User emotion: {data.emotion}\n"
            f"Policy: {data.policy}\n"
            f"Context: {data.context}\n"
            f"Generate a warm, concise, and emotionally appropriate response."
        )

        
        if model is None:
            message = f"I understand you're feeling {data.emotion}. Let's handle this calmly together."
            return LLMOutput(action=data.policy, message=message, priority=1)

        inputs = tokenizer(context_prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=True,
            temperature=0.7,
            top_p=0.9
        )
        text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        return LLMOutput(action=data.policy, message=text.strip(), priority=1)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")


@app.get("/")
def root():
    return {"service": "llm", "backend": LLM_BACKEND, "status": "ready"}
