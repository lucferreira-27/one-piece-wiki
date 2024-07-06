from openai import OpenAI
import tiktoken
import json
import time
from rich.table import Table

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

tokenizer = tiktoken.get_encoding("cl100k_base")

def read_system_prompt():
    with open('system_prompt.txt', 'r', encoding='utf-8') as f:
        return f.read()

system_prompt = read_system_prompt()

def create_stats_table(total_tokens, input_tokens, output_tokens, latency):
    table = Table(title="Processing Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Total Tokens", str(total_tokens))
    table.add_row("Input Tokens", str(input_tokens))
    table.add_row("Output Tokens", str(output_tokens))
    table.add_row("Input Cost", f"${input_tokens * 0.00000025:.6f}")
    table.add_row("Output Cost", f"${output_tokens * 0.00000125:.6f}")
    table.add_row("Total Cost", f"${(input_tokens * 0.00000025) + (output_tokens * 0.00000125):.6f}")
    table.add_row("Latency", f"{latency:.2f}s")
    table.add_row("Throughput", f"{output_tokens / latency:.2f} tokens/s" if latency > 0 else "N/A")
    return table

def generate_json(full_text, live):
    user_prompt = f"Convert the following One Piece character wiki content into a structured JSON format:\n\n<wiki_content>\n{full_text}\n</wiki_content>"

    start_time = time.time()
    response = client.chat.completions.create(
        model="anthropic/claude-3-haiku:beta",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        stream=True,
        max_tokens=4096
    )

    json_buffer = ''
    max_tokens = 4096
    input_tokens = len(tokenizer.encode(system_prompt + user_prompt))
    total_tokens = input_tokens 
    output_tokens = 0
  
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            json_buffer += content
            
            tokens = len(tokenizer.encode(content))
            total_tokens += tokens
            output_tokens += tokens
            
            current_time = time.time()
            latency = current_time - start_time
            
            live.update(create_stats_table(total_tokens, input_tokens, output_tokens, latency))
            
            if output_tokens > max_tokens:
                print("\nApproaching token limit. Continuing in next request.")
                break

    end_time = time.time()
    latency = end_time - start_time

    return json_buffer, total_tokens, input_tokens, output_tokens, latency

def process_with_ai(content, live):
    full_json, total_tokens, input_tokens, output_tokens, latency = generate_json(content, live)
    return full_json, total_tokens, input_tokens, output_tokens, latency
