import json
import sys
import os
import urllib.request
from pathlib import Path
from ollama import chat, ChatResponse

from dedudplicate import delete_duplicates
from fileindex import scan_directory
from file_engine import execute_plan, revert_changes

API_KEY = "PASTE YOUR OPENROUTER API KEY HERE"

PROMPT = """You are an advanced, totally deterministic file organization system. Your ONLY job is to analyze a list of files and group them logically into folders based on their file types, names, and context.

EXTREMELY CRITICAL RULES - FAILURE IS NOT AN OPTION:
1. OUTPUT STRICTLY AND ONLY VALID JSON. Do NOT include ANY explanations, context, markdown formatting (no ```json or ``` blocks), greetings, or conversational text before or after the JSON.
2. Ensure every single file from the input array is processed and exactly mapped in the "moves" array. Do not miss or skip any file.
3. NEVER invent, guess, or create files. ONLY use the exact filenames provided in the input.
4. Group related files into clear, concise directory names (e.g., "Images", "Documents", "Projects/Python"). Ensure destination paths are valid relative paths.
5. Do NOT change the original filenames in the "to" field, only prepend the new directory structure.
6. The output MUST perfectly match this exact JSON schema structure and be machine-readable valid JSON:
{
  "moves": [
    {"from": "original_filename.ext", "to": "Folder_Name/original_filename.ext"}
  ]
}

INPUT FILES EXAMPLE:
[
  {"name": "math_assignment_v2.pdf", "extension": ".pdf", "size_kb": 1024},
  {"name": "IMG_20231015.jpg", "extension": ".jpg", "size_kb": 4050},
  {"name": "main.py", "extension": ".py", "size_kb": 12}
]

EXPECTED JSON OUTPUT EXAMPLE:
{
  "moves": [
    {"from": "math_assignment_v2.pdf", "to": "University/math_assignment_v2.pdf"},
    {"from": "IMG_20231015.jpg", "to": "Photos/IMG_20231015.jpg"},
    {"from": "main.py", "to": "Code/main.py"}
  ]
}

Now, process the following input files and generate ONLY the raw JSON object:


"""

def get_structure(data, provider="local", api_key=API_KEY, model="my-fixed-model"):
    provider_name = "OpenRouter" if provider == 'openrouter' else "local"
    print(f"\nGenerating organization plan with {provider_name} LLM ({model})...")
    
    messages = [
        {
            'role': 'user',
            'content': f"{PROMPT} \n {data}",
        }
    ]

    if provider == "openrouter":
        if not api_key:
            print("Error: OpenRouter API key is required.")
            sys.exit(1)
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "FileOrganizer",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages
        }
        
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode('utf-8'),
            headers=headers
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error calling OpenRouter API: {e}")
            if hasattr(e, 'read'):
                print(f"Response: {e.read().decode('utf-8')}")
            sys.exit(1)
    else:
        # Local Ollama
        response = chat(model=model, messages=messages)
        return response['message']['content']

def main():
    print("Welcome to Smart File Organizer!")
    
    provider_choice = input("Would you like to use a local model (Ollama) or OpenRouter API? (local/openrouter) [local]: ").strip().lower()
    provider = "openrouter" if provider_choice == "openrouter" else "local"
    
    api_key = None
    model = "my-fixed-model"
    
    if provider == "openrouter":
        api_key = API_KEY
        if not api_key:
            api_key = input("Enter your OpenRouter API Key: ").strip()
        model = "google/gemini-3.1-flash-lite-preview"
    else:
        model_input = input(f"Enter local Ollama model name (default: {model}): ").strip()
        if model_input:
            model = model_input

    folder = input("Enter the folder path to organize: ").strip()

    if not Path(folder).exists():
        print("Invalid path!")
        sys.exit(1)

    # 1. Deduplication
    remove_dups = input("Do you want to scan for and remove duplicate files first? (y/n): ").strip().lower()
    if remove_dups == 'y':
        delete_duplicates(folder)

    # 2. File Indexing
    print("\nScanning directory for file metadata...")
    files_metadata = scan_directory(folder)
    if not files_metadata:
        print("No files found or unable to read files.")
        sys.exit(1)
        
    print(f"Found {len(files_metadata)} files to organize.")

    # 3 & 4. Call LLM and Parse Output with Retries
    data_str = json.dumps(files_metadata, indent=2)
    max_retries = 5
    plan = None

    for attempt in range(max_retries):
        if attempt > 0:
            print(f"\nRetrying... (Attempt {attempt + 1} of {max_retries})")
            
        llm_output = get_structure(data_str, provider=provider, api_key=api_key, model=model)

        clean_json = llm_output.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        elif clean_json.startswith("```"):
            clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()

        try:
            plan = json.loads(clean_json)
            # Basic validation to ensure the expected structure exists
            if isinstance(plan, dict) and "moves" in plan:
                break
            else:
                print("Error: JSON is valid but missing the 'moves' array.")
                plan = None
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from LLM: {e}")
            print("Raw LLM Output Snippet:")
            print(llm_output[:200] + "..." if len(llm_output) > 200 else llm_output)

    if not plan or "moves" not in plan:
        print("\nExceeded maximum retries. Failed to get a valid organization plan from the LLM.")
        sys.exit(1)

    # 5. Prompt user to approve JSON
    print("\n--- Proposed Organization Plan ---")
    print(json.dumps(plan, indent=2))
    approve = input("\nDo you want to apply this file movement plan? (y/n): ").strip().lower()
    
    if approve != 'y':
        print("Operation cancelled. No files were moved.")
        sys.exit(0)

    # 6. Execute Plan
    log_path = execute_plan(folder, plan)

    # 7. Revert Option
    if log_path:
        undo = input("\nDo you want to revert these changes? (y/n): ").strip().lower()
        if undo == 'y':
            revert_changes(log_path)


if __name__ == "__main__":
    main()
