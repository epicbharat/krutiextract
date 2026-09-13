import re
from .chanakya_map import array_one, array_two

def escape_regex(s):
    return re.escape(s)

def chanakya_to_unicode(text: str) -> str:
    """
    Converts a Chanakya encoded string into standard Devanagari Unicode.
    """
    if not text:
        return ""
    
    modified_substring = text

    # Apply base array replacements
    for i in range(len(array_one)):
        pattern = re.compile(escape_regex(array_one[i]))
        modified_substring = pattern.sub(array_two[i], modified_substring)

    # Chanakya special rules
    modified_substring = re.sub(r'Z', "üं", modified_substring)

    # Handle short 'i' matra (ç)
    position_of_f = modified_substring.find("ç")
    while position_of_f != -1:
        if position_of_f + 1 < len(modified_substring):
            character_right_to_f = modified_substring[position_of_f + 1]
            modified_substring = modified_substring.replace(
                "ç" + character_right_to_f,
                character_right_to_f + "ि"
            )
            # Handle half consonants after 'i' matra
            pos_temp = position_of_f + 1
            while pos_temp + 1 < len(modified_substring) and modified_substring[pos_temp + 1] == "्":
                if pos_temp + 2 < len(modified_substring):
                    string_to_be_replaced = modified_substring[pos_temp + 1] + modified_substring[pos_temp + 2]
                    modified_substring = modified_substring.replace("ि" + string_to_be_replaced, string_to_be_replaced + "ि")
                    pos_temp += 2
                else:
                    break
        position_of_f = modified_substring.find("ç", position_of_f + 1)

    # Reorder 'R' matras (ü -> र्)
    set_of_matras = "ा ि ी ु ू ृ े ै ो ौ ं ः ँ ॅ"
    position_of_Z = modified_substring.find("ü")
    
    while position_of_Z > 0:
        probable_position_of_half_r = position_of_Z - 1
        character_at_probable_position_of_half_r = modified_substring[probable_position_of_half_r]

        while character_at_probable_position_of_half_r in set_of_matras and probable_position_of_half_r >= 0:
            probable_position_of_half_r -= 1
            if probable_position_of_half_r >= 0:
                character_at_probable_position_of_half_r = modified_substring[probable_position_of_half_r]

        if probable_position_of_half_r >= 0:
            substring_to_be_replaced = modified_substring[probable_position_of_half_r:position_of_Z + 1]
            replace_with = "र्" + modified_substring[probable_position_of_half_r:position_of_Z]
            modified_substring = modified_substring.replace(substring_to_be_replaced, replace_with)

        position_of_Z = modified_substring.find("ü", position_of_Z + 1)

    # Final cleanup
    modified_substring = modified_substring.replace("ंे", "ें")
    modified_substring = modified_substring.replace("ंो", "ों")
    modified_substring = modified_substring.replace("ाे", "ो")

    return modified_substring
