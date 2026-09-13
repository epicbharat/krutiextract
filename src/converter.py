import re
from .chanakya_converter import chanakya_to_unicode

# KrutiDev to Unicode mapping arrays
array_one = [
    "ñ", "Q+Z", "sas", "aa", ")Z", "ZZ",
    "å", "ƒ", "„", "…", "†", "‡", "ˆ", "‰", "Š", "‹",
    "¶+", "d+", "[+k", "[+", "x+", "T+", "t+", "M+", "<+", "Q+", ";+", "j+", "u+",
    "Ùk", "Ù", "ä", "–", "—", "é", "™", "=kk", "f=k",
    "à", "á", "â", "ã", "ºz", "º", "í", "{k", "{", "=", "«",
    "Nî", "Vî", "Bî", "Mî", "<î", "|", "K", "}",
    "J", "Vª", "Mª", "<ªª", "Nª", "Ø", "Ý", "nzZ", "æ", "ç", "Á", "xz", "#", ":",
    "v‚", "vks", "vkS", "vk", "v", "b±", "Ã", "bZ", "b", "m", "Å", ",s", ",", "_",
    "ô", "d", "Dk", "D", "[k", "[", "x", "Xk", "X", "Ä", "?k", "?", "³",
    "pkS", "p", "Pk", "P", "N", "t", "Tk", "T", ">", "÷", "¥",
    "ê", "ë", "V", "B", "ì", "ï", "M+", "<+", "M", "<", ".k", ".",
    "r", "Rk", "R", "Fk", "F", ")", "n", "/k", "èk", "/", "Ë", "è", "u", "Uk", "U",
    "i", "Ik", "I", "Q", "¶", "c", "Ck", "C", "Hk", "H", "e", "Ek", "E",
    ";", "¸", "j", "y", "Yk", "Y", "G", "o", "Ok", "O",
    "'k", "'", "\"k", "\"", "l", "Lk", "L", "g",
    "È", "z",
    "Ì", "Í", "Î", "Ï", "Ñ", "Ò", "Ó", "Ô", "Ö", "Ø", "Ù", "Ük", "Ü",
    "‚", "ks", "kS", "k", "h", "q", "w", "`", "s", "S",
    "a", "¡", "%", "W", "•", "·", "∙", "·", "~j", "~", "\\", "+", " ः",
    "^", "*", "Þ", "ß", "(", "¼", "½", "¿", "À", "¾", "A", "-", "&", "&", "Œ", "]", "~ ", "@", "µ"
]

array_two = [
    "॰", "QZ+", "sa", "a", "र्द्ध", "Z",
    "०", "१", "२", "३", "४", "५", "६", "७", "८", "९",
    "फ़्", "क़", "ख़", "ख़्", "ग़", "ज़्", "ज़", "ड़", "ढ़", "फ़", "य़", "ऱ", "ऩ",
    "त्त", "त्त्", "क्त", "दृ", "कृ", "न्न", "न्न्", "=k", "f=",
    "ह्न", "ह्य", "हृ", "ह्म", "ह्र", "ह्", "द्द", "क्ष", "क्ष्", "त्र", "त्र्",
    "छ्य", "ट्य", "ठ्य", "ड्य", "ढ्य", "द्य", "ज्ञ", "द्व",
    "श्र", "ट्र", "ड्र", "ढ्र", "छ्र", "क्र", "फ्र", "र्द्र", "द्र", "प्र", "प्र", "ग्र", "रु", "रू",
    "ऑ", "ओ", "औ", "आ", "अ", "ईं", "ई", "ई", "इ", "उ", "ऊ", "ऐ", "ए", "ऋ",
    "क्क", "क", "क", "क्", "ख", "ख्", "ग", "ग", "ग्", "घ", "घ", "घ्", "ङ",
    "चै", "च", "च", "च्", "छ", "ज", "ज", "ज्", "झ", "झ्", "ञ",
    "ट्ट", "ट्ठ", "ट", "ठ", "ड्ड", "ड्ढ", "ड़", "ढ़", "ड", "ढ", "ण", "ण्",
    "त", "त", "त्", "थ", "थ्", "द्ध", "द", "ध", "ध", "ध्", "ध्", "ध्", "न", "न", "न्",
    "प", "प", "प्", "फ", "फ्", "ब", "ब", "ब्", "भ", "भ्", "म", "म", "म्",
    "य", "य्", "र", "ल", "ल", "ल्", "ळ", "व", "व", "व्",
    "श", "श्", "ष", "ष्", "स", "स", "स्", "ह",
    "ीं", "्र",
    "द्द", "ट्ट", "ट्ठ", "स्त्र", "कृ", "भ", "्य", "ड्ढ", "झ्", "क्र", "त्त्", "श", "श्",
    "ॉ", "ो", "ौ", "ा", "ी", "ु", "ू", "ृ", "े", "ै",
    "ं", "ँ", "ः", "ॅ", "ऽ", "ऽ", "ऽ", "ऽ", "्र", "्", "?", "़", ":",
    "'", "'", "\"", "\"", ";", "(", ")", "{", "}", "=", "।", ".", "-", "µ", "॰", ",", "् ", "/", "—"
]

def escape_regex(s):
    return re.escape(s)

def krutidev_to_unicode(text: str) -> str:
    """
    Converts a KrutiDev/Devlys encoded string into standard Devanagari Unicode.
    """
    if not text:
        return ""
    
    modified_substring = text
    modified_substring = modified_substring.replace("osQ", "के")
    modified_substring = modified_substring.replace("oSQ", "कै")

    # Step 1: Replace characters mapped directly in the arrays
    for i in range(len(array_one)):
        pattern = re.compile(escape_regex(array_one[i]))
        modified_substring = pattern.sub(array_two[i], modified_substring)

    # Step 2: Handle special combinations and rules
    modified_substring = re.sub(r'±', "Zं", modified_substring)
    modified_substring = re.sub(r'Æ', "र्f", modified_substring)

    # Fix short 'i' matra (ि)
    position_of_i = modified_substring.find("f")
    while position_of_i != -1:
        if position_of_i + 1 < len(modified_substring):
            character_next_to_i = modified_substring[position_of_i + 1]
            character_to_be_replaced = "f" + character_next_to_i
            modified_substring = modified_substring.replace(character_to_be_replaced, character_next_to_i + "ि")
        position_of_i = modified_substring.find("f", position_of_i + 1)

    modified_substring = re.sub(r'Ç', "fa", modified_substring)
    modified_substring = re.sub(r'É', "र्fa", modified_substring)
    modified_substring = re.sub(r'£', "र्f", modified_substring)
    modified_substring = re.sub(r'¯', "fa", modified_substring)
    modified_substring = modified_substring.replace("ð", "")

    position_of_i = modified_substring.find("fa")
    while position_of_i != -1:
        if position_of_i + 2 < len(modified_substring):
            character_next_to_ip2 = modified_substring[position_of_i + 2]
            character_to_be_replaced = "fa" + character_next_to_ip2
            modified_substring = modified_substring.replace(character_to_be_replaced, character_next_to_ip2 + "िं")
        position_of_i = modified_substring.find("fa", position_of_i + 2)

    modified_substring = re.sub(r'Ê', "ीZ", modified_substring)

    position_of_wrong_ee = modified_substring.find("ि्")
    while position_of_wrong_ee != -1:
        if position_of_wrong_ee + 2 < len(modified_substring):
            consonant_next_to_wrong_ee = modified_substring[position_of_wrong_ee + 2]
            character_to_be_replaced = "ि्" + consonant_next_to_wrong_ee
            modified_substring = modified_substring.replace(character_to_be_replaced, "्" + consonant_next_to_wrong_ee + "ि")
        position_of_wrong_ee = modified_substring.find("ि्", position_of_wrong_ee + 2)

    # Reorder 'R' matras (र्)
    set_of_matras = "अ आ इ ई उ ऊ ए ऐ ओ औ ा ि ी ु ू ृ े ै ो ौ ं : ँ ॅ"
    position_of_R = modified_substring.find("Z")
    
    while position_of_R > 0:
        probable_position_of_half_r = position_of_R - 1
        character_at_probable_position_of_half_r = modified_substring[probable_position_of_half_r]

        while character_at_probable_position_of_half_r in set_of_matras and probable_position_of_half_r >= 0:
            probable_position_of_half_r -= 1
            if probable_position_of_half_r >= 0:
                character_at_probable_position_of_half_r = modified_substring[probable_position_of_half_r]

        if probable_position_of_half_r >= 0:
            substring_to_be_replaced = modified_substring[probable_position_of_half_r:position_of_R + 1]
            replace_with = "र्" + modified_substring[probable_position_of_half_r:position_of_R]
            modified_substring = modified_substring.replace(substring_to_be_replaced, replace_with)

        position_of_R = modified_substring.find("Z", position_of_R + 1)

    # Final cleanup for common spacing/matra bugs
    modified_substring = modified_substring.replace("ंे", "ें")
    modified_substring = modified_substring.replace("ंो", "ों")
    modified_substring = modified_substring.replace("ाे", "ो")

    # Fix common KrutiDev typist visual hacks that become typos in Unicode
    modified_substring = modified_substring.replace("ध्कि", "धिक")
    modified_substring = modified_substring.replace("पफ", "फ")

    return modified_substring

def auto_detect_font(text: str) -> str:
    """
    Detects if the legacy font used is KrutiDev or Chanakya based on character frequencies.
    Returns 'krutidev', 'chanakya', or 'unicode' for modern English/Hinglish/Hindi text.
    """
    # KrutiDev features: 'vkSj' (और), 'gS' (है), 'gksrh' (होती), 'Hkkjr' (भारत)
    # Note: DO NOT use 'ds' or 'dh' as they trigger massive false-positives on English text (e.g. 'words', 'adhere')
    krutidev_score = text.count('vkSj') + text.count('gS') + text.count('osQ') + text.count('gksrh') + text.count('Hkkjr')
    
    # Chanakya features: '¥õÚ' / '¥æõÚ' (और), 'ãñ' (है), '·¤' (क), 'ß' (व), 'Ü' (ल)
    chanakya_score = text.count('¥') + text.count('ãñ') + text.count('·') + text.count('ß') + text.count('Ü')
    
    if chanakya_score == 0 and krutidev_score == 0:
        return 'unicode'
    if chanakya_score > krutidev_score * 1.5:
        return 'chanakya'
    return 'krutidev'

# Cache the English words so we only load it once
_ENGLISH_WORDS = None

def _get_english_words():
    global _ENGLISH_WORDS
    if _ENGLISH_WORDS is None:
        try:
            # We use the Brown corpus which is much smaller (~40k words) and prevents 
            # obscure valid KrutiDev strings like "tula" (जनसं) from being bypassed.
            nltk.download('brown', quiet=True)
            from nltk.corpus import brown
            _ENGLISH_WORDS = set(w.lower() for w in brown.words() if w.isalpha())
        except Exception:
            # Fallback to an empty set if NLTK fails
            _ENGLISH_WORDS = set()
    return _ENGLISH_WORDS

def is_english_word(word: str) -> bool:
    """Returns True if the word is found in our English dictionary."""
    if not word.strip():
        return False
    # If the word contains numbers or punctuation, don't treat it as a pure English dictionary word
    if not word.isalpha():
        return False
        
    return word.lower() in _get_english_words()

def convert_legacy_text(text: str, font: str = 'auto') -> str:
    if font == 'auto':
        font = auto_detect_font(text)
        
    if font == 'unicode' or font == 'english':
        return text
        
    if font == 'chanakya':
        return chanakya_to_unicode(text)
    else:
        # Defaults to krutidev (which also perfectly handles devlys)
        return krutidev_to_unicode(text)
