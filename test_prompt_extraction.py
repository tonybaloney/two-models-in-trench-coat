"""
Test script for the robust prompt extraction functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhance_forward.prompt_utils import extract_prompt_content, extract_all_prompt_contents, clean_prompt_content


def test_prompt_extraction():
    """Test various prompt extraction scenarios."""
    
    print("🧪 Testing Robust Prompt Extraction\n")
    
    # Test cases
    test_cases = [
        # Basic single line
        {
            "name": "Basic single line",
            "input": "<prompt>Hello, world!</prompt>",
            "expected": "Hello, world!"
        },
        
        # Multi-line content
        {
            "name": "Multi-line content",
            "input": """<prompt>
This is a multi-line
prompt that spans
several lines.
</prompt>""",
            "expected": """
This is a multi-line
prompt that spans
several lines.
"""
        },
        
        # Case insensitive
        {
            "name": "Case insensitive tags",
            "input": "<PROMPT>Uppercase tags work too</PROMPT>",
            "expected": "Uppercase tags work too"
        },
        
        # Mixed case
        {
            "name": "Mixed case tags",
            "input": "<Prompt>Mixed case also works</prompt>",
            "expected": "Mixed case also works"
        },
        
        # With attributes
        {
            "name": "Tags with attributes",
            "input": '<prompt id="test" class="example">Content with attributes</prompt>',
            "expected": "Content with attributes"
        },
        
        # Nested content (should extract outer)
        {
            "name": "Nested HTML-like content",
            "input": "<prompt>This has <em>nested</em> <strong>tags</strong> inside</prompt>",
            "expected": "This has <em>nested</em> <strong>tags</strong> inside"
        },
        
        # Multiple prompts
        {
            "name": "Multiple prompt tags",
            "input": "<prompt>First prompt</prompt> Some text in between <prompt>Second prompt</prompt>",
            "expected": "First prompt"  # extract_prompt_content returns first match
        },
        
        # No prompt tags
        {
            "name": "No prompt tags",
            "input": "This text has no prompt tags at all",
            "expected": None
        },
        
        # Empty prompt
        {
            "name": "Empty prompt",
            "input": "<prompt></prompt>",
            "expected": ""
        },
        
        # Whitespace handling
        {
            "name": "Whitespace preservation",
            "input": "<prompt>   Content with spaces   </prompt>",
            "expected": "   Content with spaces   "
        },
        
        # Real-world example
        {
            "name": "Real-world example",
            "input": """Please process this request: <prompt>
You are an AI assistant. Please help me write a Python function that:
1. Takes a list of numbers
2. Returns the sum of even numbers
3. Handles empty lists gracefully

Please include proper error handling and documentation.
</prompt> Thank you!""",
            "expected": """
You are an AI assistant. Please help me write a Python function that:
1. Takes a list of numbers
2. Returns the sum of even numbers
3. Handles empty lists gracefully

Please include proper error handling and documentation.
"""
        }
    ]
    
    # Run tests
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Input: {repr(test_case['input'][:50])}{'...' if len(test_case['input']) > 50 else ''}")
        
        result = extract_prompt_content(test_case['input'])
        expected = test_case['expected']
        
        if result == expected:
            print("✅ PASSED")
            passed += 1
        else:
            print("❌ FAILED")
            print(f"Expected: {repr(expected)}")
            print(f"Got:      {repr(result)}")
            failed += 1
        
        print("-" * 60)
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    # Test multiple extractions
    print("\n🔍 Testing Multiple Prompt Extraction")
    multi_input = "<prompt>First</prompt> and <prompt>Second</prompt> and <prompt>Third</prompt>"
    all_prompts = extract_all_prompt_contents(multi_input)
    print(f"Input: {multi_input}")
    print(f"All prompts extracted: {all_prompts}")
    
    # Test cleaning
    print("\n🧹 Testing Content Cleaning")
    messy_content = "   \n  This has lots of whitespace  \n   "
    print(f"Original: {repr(messy_content)}")
    print(f"Cleaned:  {repr(clean_prompt_content(messy_content))}")
    print(f"Uncleaned: {repr(clean_prompt_content(messy_content, strip_whitespace=False))}")


if __name__ == "__main__":
    test_prompt_extraction()