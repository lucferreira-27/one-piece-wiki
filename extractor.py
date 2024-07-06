import re


def truncate_content_at_references(content):
    references_pattern = re.compile(r'==\s*References\s*==', re.IGNORECASE)
    match = references_pattern.search(content)
    
    if match:
        return content[:match.start()]
    else:
        return content



def extract_char_box(content):
    """Extracts data from the {{Char Box}} template."""
    char_box_match = re.search(r'\{\{Char Box(.*?)\}\}', content, re.DOTALL)
    if not char_box_match:
        return None

    char_box_content = char_box_match.group(1)

    char_info = {}
    for line in char_box_content.split("\n"):
        if "=" in line:
            field, value = line.split("=", 1)
            field = field.strip().strip('|').strip() 
            value = value.strip()
            value = clean_wiki_markup(value)
            # Special handling for certain fields
            if field == 'first':
                chapter_match = re.search(r'Chapter (\d+)', value)
                episode_match = re.search(r'Episode (\d+)', value)
                char_info[field] = {
                    'chapter': int(chapter_match.group(1)) if chapter_match else None,
                    'episode': int(episode_match.group(1)) if episode_match else None 
                }
            elif field == 'bounty':
                bounties = [b.strip() for b in value.split('<br />')]
                char_info[field] = bounties
            else:
                char_info[field] = value

    return char_info

def extract_sections(content):
    """Extracts content sections from the Wiki page."""
    sections = []
    current_section = None

    for line in content.split('\n'):
        if line.startswith('==') and line.endswith('=='):
            if current_section:
                sections.append(current_section)
            current_section = {"title": line.strip('= '), "content": []}
        elif current_section:
            if line.strip():
                cleaned_text = clean_wiki_markup(line)
                current_section["content"].append({"type": "paragraph", "text": cleaned_text})

    if current_section:
        sections.append(current_section)

    return sections

def clean_wiki_markup(text):
    """Removes Wiki markup from text."""
    text = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]|]*)\]\]', r'\1', text)
    text = re.sub(r'<ref.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'\{\{.*?\}\}', '', text, flags=re.DOTALL)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)  # Remove comments
    text = re.sub(r'<br />', ' ', text)  # Replace line breaks with spaces
    text = re.sub(r'\s+', ' ', text)   # Normalize whitespace
    return text.strip()

def extract_wiki_character_data(content):
    """Extracts character data from One Piece Wiki content."""
    character_data = {
        "character_info": extract_char_box(content),
        "description": "",
        "sections": extract_sections(content),
        "galleries": [], 
        "tables": []  
    }

    # Extract character description (first paragraph after the infobox)
    description_match = re.search(r'\}\}\s*\n\n(.+?)\n\n', content, re.DOTALL)
    if description_match:
        character_data["description"] = clean_wiki_markup(description_match.group(1))

    return character_data
