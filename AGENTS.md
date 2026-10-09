# Project Guidelines & Memory for Gyaan Setu

## Persistent Memory: Verified Available Models on Groq API

As probed directly from the live Groq API (`client.models.list()`) and verified via live inference:

### Active & Working Chat / Completion Models
1. **`openai/gpt-oss-120b`**
   - Developer: OpenAI
   - Parameters: 120B dense model
   - Context Window: 131,072 tokens
   - Role: Primary Generator (`GROQ_MODEL_GENERATOR`). High reasoning capacity, comprehensive academic explanations.
2. **`qwen/qwen3.8-27b`**
   - Developer: Alibaba Cloud
   - Parameters: 27B model
   - Context Window: 131,072 tokens
   - Role: Fast Generator / Multilingual reasoning (exceptional Hindi, Hinglish, and English performance).
3. **`openai/gpt-oss-20b`**
   - Developer: OpenAI
   - Parameters: 20B model
   - Context Window: 131,072 tokens
   - Role: Cross-Model Verifier (`GROQ_MODEL_VERIFIER`). Ultra-low latency verification of assessment questions and strict grounding checks.
4. **`allam-2-7b`**
   - Developer: SDAIA
   - Context Window: 4,096 tokens
5. **`openai/gpt-oss-safeguard-20b`**
   - Developer: OpenAI
   - Context Window: 131,072 tokens
   - Role: Moderation & Safeguard filter.

### Audio / Speech-to-Text Models
6. **`whisper-large-v3`**
   - Context Window: 448 tokens
   - Role: State-of-the-art multilingual speech-to-text.
7. **`whisper-large-v3-turbo`**
   - Context Window: 448 tokens
   - Role: High-throughput speech transcription.

### Guardrail & Security Models
8. **`meta-llama/llama-prompt-guard-2-86m`** (Context: 512 tokens)
9. **`meta-llama/llama-prompt-guard-2-22m`** (Context: 512 tokens)

### Models Requiring Organization Terms Acceptance
10. **`canopylabs/orpheus-v1-english`** (Context: 4,000 tokens)
11. **`canopylabs/orpheus-arabic-saudi`** (Context: 4,000 tokens)

---

### CRITICAL: Decommissioned / Inaccessible Models on Groq
Do NOT configure or call these models on Groq as they have been deprecated or removed:
- ❌ `llama-3.3-70b-versatile` (Not accessible / not found)
- ❌ `llama-3.1-70b-versatile` (Decommissioned)
- ❌ `llama-3.1-8b-instant` (Not accessible / not found)
- ❌ `llama3-70b-8192` (Decommissioned)
- ❌ `llama3-8b-8192` (Decommissioned)
- ❌ `gemma2-9b-it` (Decommissioned)
- ❌ `mixtral-8x7b-32768` (Decommissioned)
- ❌ `deepseek-r1-distill-llama-70b` (Decommissioned)
- ❌ `llama-3.2-11b-vision-preview` (Decommissioned)
- ❌ `llama-3.2-90b-vision-preview` (Decommissioned)
