"""
Utility functions for extracting and processing prompt content from text.

This module provides robust regex-based functions to extract text content
from <prompt>...</prompt> tags, handling various edge cases and formats.
"""

import re
from typing import Optional, List


def extract_prompt_content(text: str) -> Optional[str]:
    """
    Extract text content from <prompt>...</prompt> tags using robust regex.
    
    This function handles:
    - Multi-line content spanning multiple lines
    - Whitespace preservation within tags
    - Case-insensitive tags (prompt, PROMPT, Prompt, etc.)
    - Tags with attributes (e.g., <prompt id="1" class="test">)
    - Nested HTML-like content within prompt tags
    - Returns first match if multiple prompt tags exist
    
    Args:
        text (str): The input text containing prompt tags
        
    Returns:
        Optional[str]: The extracted content, or None if no prompt tags found
        
    Examples:
        >>> extract_prompt_content("<prompt>Hello world</prompt>")
        'Hello world'
        
        >>> extract_prompt_content("<prompt>\\nMulti\\nLine\\nText\\n</prompt>")
        '\\nMulti\\nLine\\nText\\n'
        
        >>> extract_prompt_content("<PROMPT>Case insensitive</PROMPT>")
        'Case insensitive'
        
        >>> extract_prompt_content('<prompt id="1">With attributes</prompt>')
        'With attributes'
        
        >>> extract_prompt_content("No prompt tags here")
        None
        
        >>> extract_prompt_content("<prompt>First</prompt><prompt>Second</prompt>")
        'First'
    """
    # Robust regex pattern explanation:
    # <prompt[^>]*>  - Opening tag that:
    #                  - Starts with <prompt
    #                  - Followed by any characters except > (handles attributes)
    #                  - Ends with >
    # (.*?)          - Non-greedy capture group for content (stops at first </prompt>)
    # </prompt>      - Closing tag
    # re.DOTALL      - Makes . match newlines too (for multi-line content)
    # re.IGNORECASE  - Case-insensitive matching (PROMPT, prompt, Prompt all work)
    
    pattern = r'<prompt[^>]*>(.*?)</prompt>'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    
    return match.group(1) if match else None


def extract_all_prompt_contents(text: str) -> List[str]:
    """
    Extract all text contents from multiple <prompt>...</prompt> tags.
    
    Unlike extract_prompt_content() which returns only the first match,
    this function returns all prompt contents found in the text.
    
    Args:
        text (str): The input text containing prompt tags
        
    Returns:
        List[str]: List of all extracted contents (empty list if none found)
        
    Examples:
        >>> extract_all_prompt_contents("<prompt>First</prompt> and <prompt>Second</prompt>")
        ['First', 'Second']
        
        >>> extract_all_prompt_contents("No prompts here")
        []
        
        >>> extract_all_prompt_contents("<prompt>Only one</prompt>")
        ['Only one']
    """
    pattern = r'<prompt[^>]*>(.*?)</prompt>'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    
    return matches


def clean_prompt_content(content: str, strip_whitespace: bool = True) -> str:
    """
    Clean extracted prompt content by optionally stripping whitespace.
    
    This function helps normalize extracted content by removing leading
    and trailing whitespace while preserving internal formatting.
    
    Args:
        content (str): The extracted content to clean
        strip_whitespace (bool): Whether to strip leading/trailing whitespace.
                               Defaults to True.
        
    Returns:
        str: Cleaned content
        
    Examples:
        >>> clean_prompt_content("  Hello world  ")
        'Hello world'
        
        >>> clean_prompt_content("  Hello world  ", strip_whitespace=False)
        '  Hello world  '
        
        >>> clean_prompt_content("\\n  Multi\\n  Line  \\n")
        'Multi\\n  Line'
    """
    if strip_whitespace:
        return content.strip()
    return content


def has_prompt_tags(text: str) -> bool:
    """
    Check if text contains any <prompt>...</prompt> tags.
    
    Args:
        text (str): The text to check
        
    Returns:
        bool: True if prompt tags are found, False otherwise
        
    Examples:
        >>> has_prompt_tags("<prompt>Hello</prompt>")
        True
        
        >>> has_prompt_tags("No tags here")
        False
        
        >>> has_prompt_tags("<other>Not a prompt tag</other>")
        False
    """
    pattern = r'<prompt[^>]*>.*?</prompt>'
    return bool(re.search(pattern, text, re.DOTALL | re.IGNORECASE))


def remove_prompt_tags(text: str, keep_content: bool = True) -> str:
    """
    Remove <prompt>...</prompt> tags from text.
    
    Args:
        text (str): The input text
        keep_content (bool): If True, keeps the content inside tags.
                           If False, removes tags and content.
        
    Returns:
        str: Text with prompt tags removed
        
    Examples:
        >>> remove_prompt_tags("Before <prompt>content</prompt> after")
        'Before content after'
        
        >>> remove_prompt_tags("Before <prompt>content</prompt> after", keep_content=False)
        'Before  after'
    """
    if keep_content:
        # Replace <prompt>content</prompt> with just content
        pattern = r'<prompt[^>]*>(.*?)</prompt>'
        return re.sub(pattern, r'\\1', text, flags=re.DOTALL | re.IGNORECASE)
    else:
        # Remove entire <prompt>content</prompt> blocks
        pattern = r'<prompt[^>]*>.*?</prompt>'
        return re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)


def extract_and_clean_prompt(text: str, fallback_to_original: bool = False) -> str:
    """
    Extract prompt content and clean it, with optional fallback.
    
    This is a convenience function that combines extraction and cleaning
    in one call, with the option to return the original text if no
    prompt tags are found.
    
    Args:
        text (str): The input text
        fallback_to_original (bool): If True and no prompt tags found,
                                   returns original text. If False,
                                   returns empty string.
        
    Returns:
        str: Extracted and cleaned prompt content, or fallback
        
    Examples:
        >>> extract_and_clean_prompt("<prompt>  Hello  </prompt>")
        'Hello'
        
        >>> extract_and_clean_prompt("No tags", fallback_to_original=True)
        'No tags'
        
        >>> extract_and_clean_prompt("No tags", fallback_to_original=False)
        ''
    """
    extracted = extract_prompt_content(text)
    
    if extracted is not None:
        return clean_prompt_content(extracted)
    elif fallback_to_original:
        return text
    else:
        return ""


# Convenience aliases for common use cases
extract_prompt = extract_prompt_content
extract_all_prompts = extract_all_prompt_contents
clean_prompt = clean_prompt_content