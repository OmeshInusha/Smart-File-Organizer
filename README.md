# Smart File Organizer

Smart File Organizer is an intelligent, completely deterministic AI-powered script that scans a specific directory and categorizes your files logically based on their metadata (name, type, etc.) using Large Language Models (LLMs). It interfaces with either a local **Ollama** model or web-based models through the **OpenRouter API**.

## Features

* **LLM-Powered Organization:** Uses AI to semantically group your files into strictly structured, well-named subdirectories (e.g. `Images`, `Projects/Python`, `University`).
* **Flexible Model Choice:** Swap between keeping data 100% locally with an Ollama model or utilizing a far more advanced model via OpenRouter API (such as Gemini or Claude).
* **Smart Deduplication:** Scans the folder layer for identical files (via exact SHA256 hash generation) and offers an interactive prompt to delete copies directly and free up space.
* **Non-Destructive Defaults:** Previews the proposed folder structure as JSON for your explicit approval *before* applying any actual file moves.
* **Safe Operations & Revert:** Tracks every file move it makes during the execution phase and offers an easy **Revert** feature via log files in case you want to undo the newly organized structure.
* **Surface-level Organization:** Strictly limits its file indexing and deduplication logic to a single focal directory layer (`iterdir()`), preventing unintended modifications or scanning of existing organized subfolders.
* **Self-Healing LLM Validation:** Robust validation mechanism that dynamically retries the generation up to 5 times if the LLM output is malformed or invalid JSON.

## Prerequisites

- **Python 3.x**
- (Optional) **Ollama:** If you intend to use local models, ensure you have Ollama installed and your preferred model pulled (e.g. `llama3` or your defined `my-fixed-model`).
- (Optional) **OpenRouter API Key:** If using OpenRouter, you'll need to insert your API key into the `API_KEY` variable at the top of `main.py` or just let the interactive console prompt you.

### Recommended Packages

The application relies heavily on the local standard library (`json`, `urllib`, `pathlib`, `hashlib`), but if you use the local model pipeline, you need the Ollama Python SDK:

```bash
pip install ollama
```

## How To Use

1. Run the main processing script:
   ```bash
   python main.py
   ```
2. The interactive prompt will ask which language model provider you want to use (**local** or **openrouter**).
3. If OpenRouter is chosen, it will leverage the hardcoded key or prompt for it, defaulting to the `google/gemini-3.1-flash-lite-preview` model. If Local is chosen, you can define your local Ollama model name. 
4. Provide the absolute or relative path to the heavily cluttered directory you wish to organize.
5. You'll be dynamically asked if you'd like to perform a deduplication pass first. If `y`, it will aggressively scan matching file sizes and hashes, list out the clones, and safely prompt you to eliminate them.
6. The AI engine kicks in and drafts a new location map. Wait for the `--- Proposed Organization Plan ---` to print to your terminal.
7. Review the printed JSON plan thoroughly. Type `y` to execute the structural changes.
8. When completed, if you decide the results aren't what you expected, explicitly type `y` to revert the changes before the application closes.

## File Structure Reference

- `main.py` - The core application loop, LLM integration, and user prompt UI.
- `fileindex.py` - Single-layer filesystem traversal tools for metadata extraction and directory reads.
- `dedudplicate.py` - Sub-module dedicated to safely discovering, displaying, and terminating identical twin files.
- `file_engine.py` - The structural actuator that physically moves files into their new sub-homes, generates operations logs, and parses logs for reverting operations.
