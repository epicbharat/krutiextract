# -*- coding: utf-8 -*-
"""Ground-truth pairs for Walkman-Chanakya 905 (NCERT Hindi textbooks).

Source: jhss101.pdf (NCERT, Samkalin Bharat 2, ch.1), page 3. Each raw string
is the logical character stream PyMuPDF extracts; each expected value was read
off the rendered page of that same PDF. These are observations, not guesses.
"""

WALKMAN_WORDS = [
    ("dh", "की"), ("vR;fèkd", "अत्यधिक"), ("deh", "कमी"), ("gSA", "है।"),
    ("mnkgj.kkFkZ", "उदाहरणार्थ"), (">kj[kaM", "झारखंड"), ("eè;izns'k", "मध्यप्रदेश"),
    ("vkSj", "और"), ("NÙkhlx<+", "छत्तीसगढ़"), ("vkfn", "आदि"),
    ("izkarksa", "प्रांतों"), ("esa", "में"), ("[kfutksa", "खनिजों"),
    ("dks;ys", "कोयले"), ("osQ", "के"), ("izpqj", "प्रचुर"), ("HkaMkj", "भंडार"),
    ("gSaA", "हैं।"), ("v#.kkpy", "अरुणाचल"), ("izns'k", "प्रदेश"), ("ty", "जल"),
    ("lalkèku", "संसाधन"), ("ek=kk", "मात्रा"), ("ik,", "पाए"), ("tkrs", "जाते"),
    ("ijarq", "परंतु"), ("ewy", "मूल"), ("fodkl", "विकास"),
    ("jktLFkku", "राजस्थान"), ("iou", "पवन"), ("lkSj", "सौर"),
    ("mQtkZ", "ऊर्जा"), ("lalkèkuksa", "संसाधनों"), ("cgqrk;r", "बहुतायत"),
    ("ysfdu", "लेकिन"), ("yík[k", "लद्दाख"), ("dk", "का"), ("'khr", "शीत"),
    ("e#LFky", "मरुस्थल"), ("ns'k", "देश"), ("vU;", "अन्य"), ("Hkkxksa", "भागों"),
    ("ls", "से"), ("vyx&Fkyx", "अलग-थलग"), ("iM+rk", "पड़ता"), (";g", "यह"),
    ("lkaLÑfrd", "सांस्कृतिक"), ("fojklr", "विरासत"), ("èkuh", "धनी"),
    ("gS", "है"), (";gk¡", "यहाँ"), ("vkèkkjHkwr", "आधारभूत"),
    ("volajpuk", "अवसंरचना"), ("rFkk", "तथा"), ("oqQN", "कुछ"),
    ("egÙoiw.kZ", "महत्त्वपूर्ण"), ("blfy,", "इसलिए"), ("jk\"Vªh;", "राष्ट्रीय"),
    ("izkarh;", "प्रांतीय"), ("izknsf'kd", "प्रादेशिक"), ("LFkkuh;", "स्थानीय"),
    ("Lrj", "स्तर"), ("ij", "पर"), ("larqfyr", "संतुलित"), ("fu;kstu", "नियोजन"),
    ("vko';drk", "आवश्यकता"), ("miyCèkrk", "उपलब्धता"), ("gh", "ही"),
    ("laHko", "संभव"), ("ugha", "नहीं"), ("cgqr", "बहुत"), ("{ks=k", "क्षेत्र"),
    ("tks", "जो"), ("le`¼", "समृद्ध"), ("gksrs", "होते"), ("gq,", "हुए"),
    ("Hkh", "भी"), ("vkfFkZd", "आर्थिक"), (":i", "रूप"), ("fiNM+s", "पिछड़े"),
    ("izns'kksa", "प्रदेशों"), ("fxurh", "गिनती"), ("vkrs", "आते"),
    ("blosQ", "इसके"), ("foijhr", "विपरीत"), (",sls", "ऐसे"),
    ("fodflr", "विकसित"), ("D;k", "क्या"), ("vki", "आप"), ("laiUu", "संपन्न"),
]

# Nukta letters borrowed from Perso-Arabic, kerning dummies, and spelling
# variants. Each was verified by rendering the source string in the
# Walkman-Chanakya subset embedded in jhss101.pdf.
WALKMAN_WORDS += [
    ("rs”k", "तेज़"),                                    # तेज़
    ("vaxzs”kh", "अंग्रेज़ी"),  # अंग्रेज़ी
    ("”;knk", "ज़्यादा"),                 # ज़्यादा
    ("feêðh", "मिट्टी"),                  # मिट्टी
    ("ifêð;ksa", "पट्टियों"),   # पट्टियों
    ("C;wVhI+kqQy", "ब्यूटीफुल"),    # ब्यूटीफुल
    ("lqy>k,¡_", "सुलझाएँ;"),             # सुलझाएँ;
    ("laca/", "संबंध"),                                  # संबंध
    ("ikS/ksa", "पौधों"),                                # पौधों
    ("vkWiQ", "ऑफ"),                                                    # ऑफ
    ("v/Z", "अर्ध"),                                          # अर्ध
]
