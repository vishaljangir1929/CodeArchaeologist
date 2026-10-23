# Upstream components and model sources

The application integrates pretrained models. It does not claim to have trained or fine-tuned them.

| Component | Source | License / notes |
| --- | --- | --- |
| Qwen2.5-Coder-1.5B-Instruct GGUF Q2_K | https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF | Apache-2.0, official Qwen repository; pinned revision and SHA-256 in `scripts/setup_ai.py` and `.models/llm-manifest.json`. |
| BGE-small-en-v1.5 ONNX | https://huggingface.co/Qdrant/bge-small-en-v1.5-onnx-Q | MIT, distributed through FastEmbed; local cache and readiness metadata in `.models/`. |
| llama.cpp CPU runtime | https://github.com/ggml-org/llama.cpp | MIT; Windows CPU release b11827, ZIP checksum verified during setup. |
| FastEmbed | https://github.com/qdrant/fastembed | Apache-2.0; uses ONNX Runtime for CPU embedding inference. |
| FastAPI | https://github.com/fastapi/fastapi | MIT. |
| Uvicorn | https://github.com/encode/uvicorn | BSD-3-Clause. |
| HTTPX | https://github.com/encode/httpx | BSD-3-Clause. |
| NumPy | https://numpy.org | BSD-3-Clause. |
| ONNX Runtime | https://github.com/microsoft/onnxruntime | MIT. |
| React | https://github.com/facebook/react | MIT. |
| Lucide | https://github.com/lucide-icons/lucide | ISC. |
| remark-gfm | https://github.com/remarkjs/remark-gfm | MIT; GitHub-style Markdown tables. |
| react-markdown | https://github.com/remarkjs/react-markdown | MIT. |
| esbuild | https://github.com/evanw/esbuild | MIT. |

Python and frontend package lock files retain the selected dependency versions. Installed packages retain their upstream license metadata. Downloaded model/runtime files are excluded from the portable source ZIP and are obtained from their official sources by the setup script.
