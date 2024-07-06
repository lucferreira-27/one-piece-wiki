import json
import requests
from extractor import extract_wiki_character_data, truncate_content_at_references
from ai_processor import process_with_ai
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
import time

console = Console()

def fetch_character_content(character_name):
    api_url = f"https://onepiece.fandom.com/api.php?action=visualeditor&format=json&paction=wikitext&page={character_name}&uselang=en&formatversion=2"
    with console.status(f"[bold blue]Fetching content for {character_name}...", spinner="dots"):
        response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        return data.get('visualeditor', '').get('content')
    else:
        console.print(f"[bold red]Error: Unable to fetch content for {character_name}")
        return None

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
    table.add_row("Throughput", f"{total_tokens / latency:.2f} tokens/s" if latency > 0 else "N/A")
    return table

def process_character(character_name):
    console.print(Panel(f"[bold green]Processing character: {character_name}", expand=False))
    
    content = fetch_character_content(character_name)
    
    if not content:
        return

    initial_data = truncate_content_at_references(content)

    with Live(create_stats_table(0, 0, 0, 0), refresh_per_second=4) as live:
        full_json, total_tokens, input_tokens, output_tokens, latency = process_with_ai(initial_data, live)

    try:
        json_start = full_json.index('<json>') + 6
        json_end = full_json.index('</json>')
        json_content = full_json[json_start:json_end].strip()

        parsed_json = json.loads(json_content)
        formatted_json = json.dumps(parsed_json, indent=2)
        
        output_filename = f"{character_name}_content.json"
        with open(output_filename, 'w', encoding='utf-8') as json_file:
            json_file.write(formatted_json)
        
        console.print(f"\n[bold green]Conversion completed. JSON content saved to {output_filename}")
    except (json.JSONDecodeError, ValueError):
        console.print("\n[bold yellow]Warning: The generated content is not valid JSON or missing tags. Manual review may be needed.")
        raw_filename = f"{character_name}_content_raw.txt"
        with open(raw_filename, 'w', encoding='utf-8') as raw_file:
            raw_file.write(full_json)
        console.print(f"[bold yellow]Raw content saved to {raw_filename} for review.")

    # Display final processing statistics
    #console.print(create_stats_table(total_tokens, input_tokens, output_tokens, latency))

if __name__ == "__main__":
    character_name = "Nami"
    process_character(character_name)
