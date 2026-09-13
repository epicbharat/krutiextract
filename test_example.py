from src.converter import krutidev_to_unicode
from src.markdown_utils import protect_non_hindi_syntax, restore_non_hindi_syntax

def test_conversion():
    # A mix of markdown, english words, URLs, and scrambled-looking KrutiDev
    raw_input = "## **Chapter 1: The Beginning**\n\n![Image](http://example.com/img.png)\n;wjksi osQ jktuhfrd vkSj ekufld txr esa Hkkjh (System) cnyko gq,\n"
    
    # 1. Protect syntax
    protected, tokens = protect_non_hindi_syntax(raw_input)
    
    # 2. Convert
    converted = krutidev_to_unicode(protected)
    
    # 3. Restore syntax
    final_output = restore_non_hindi_syntax(converted, tokens)
    
    print("=== Original ===")
    print(raw_input)
    print("=== Converted ===")
    print(final_output)

if __name__ == "__main__":
    test_conversion()
