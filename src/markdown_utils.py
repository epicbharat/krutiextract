import re
import nltk
from nltk.corpus import words

# Ensure nltk words are downloaded
try:
    nltk.data.find('corpora/words')
except LookupError:
    nltk.download('words')

english_vocab = set(w.lower() for w in words.words())

def is_english_word(word: str) -> bool:
    if len(word) < 4 and word.lower() not in {"the", "and", "for", "of", "to", "in", "is", "it", "on", "as", "at", "by", "an", "be", "or", "we"}:
        return False
    return word.lower() in english_vocab

def protect_non_hindi_syntax(raw_text: str) -> tuple[str, list]:
    """
    Replaces Markdown syntax, English words, numbers, and URLs with a safe token 
    ($$$INDEX$$$) so that the KrutiDev font converter does not mangle them.
    Returns the protected text and the list of preserved chunks.
    """
    preserved = []
    
    def preserve_match(m):
        preserved.append(m.group(0))
        return f"$$${len(preserved)-1}$$$"

    # 1. Bold text markers
    text = re.sub(r'\*\*', preserve_match, raw_text)

    # 1.5 Italics marker (only if it surrounds text like _text_)
    # Match _ at start of word/string, and _ at end of word/string
    def preserve_italics(m):
        preserved.append("_")
        idx = len(preserved) - 1
        return f"{m.group(1)}$$${idx}$$${m.group(2)}$$${idx}$$${m.group(3)}"
    
    text = re.sub(r'(^|\s)_(.*?)_(\s|$|[.,?!\-\]])', preserve_italics, text)
    
    # 2. Markdown Headings
    text = re.sub(r'(?m)^(#+)\s', preserve_match, text)

    # 2.5 HTML Tags (e.g., <br>, <img>)
    text = re.sub(r'<[^>]+>', preserve_match, text)

    # 3. Images syntax ![alt](url)
    text = re.sub(r'!\[.*?\]\(.*?\)', preserve_match, text)

    # 4. Brackets containing English letters or digits
    def preserve_bracket(m):
        inner = m.group(1)
        if re.search(r'[A-Za-z0-9]', inner):
            preserved.append(m.group(0))
            return f"$$${len(preserved)-1}$$$"
        return m.group(0)

    text = re.sub(r'\(([^)]+)\)', preserve_bracket, text)
    
    # 5. Isolated English words >= 4 chars or pure numbers
    def preserve_word(m):
        w = m.group(0)
        collapsed = re.sub(r'(.)\1+', r'\1', w)
        if is_english_word(w) or (len(collapsed) >= 4 and is_english_word(collapsed)) or (len(w) >= 4 and w.isupper()) or w.isdigit():
            preserved.append(w)
            return f"$$${len(preserved)-1}$$$"
        return w
        
    text = re.sub(r'\b[A-Za-z0-9]{2,}\b', preserve_word, text)

    return text, preserved

def restore_non_hindi_syntax(text: str, preserved: list) -> str:
    """
    Restores the preserved English and Markdown chunks back into the converted text.
    """
    for i in range(len(preserved)):
        text = text.replace(f"$$${i}$$$", preserved[i])
    return text
