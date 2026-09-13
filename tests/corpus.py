# -*- coding: utf-8 -*-
"""Known-good KrutiDev / Devlys -> Unicode Devanagari word pairs.

Every pair here is a regression anchor. A change to the converter that breaks
any of these is a regression, regardless of what else it improves.
"""

# (kruti_source, expected_unicode)
WORDS = [
    # --- bare vowels and independent signs ---
    ("v", "अ"), ("vk", "आ"), ("b", "इ"), ("bZ", "ई"), ("m", "उ"), ("Å", "ऊ"),
    (",", "ए"), (",s", "ऐ"), ("vks", "ओ"), ("vkS", "औ"), ("v‚", "ऑ"),
    ("_", "ऋ"),

    # --- consonant + aa matra ---
    ("dk", "का"), ("[kk", "खा"), ("xk", "गा"), ("?kk", "घा"),
    ("pk", "चा"), ("Nk", "छा"), ("tk", "जा"), (">k", "झा"),
    ("Vk", "टा"), ("Bk", "ठा"), ("Mk", "डा"), ("<k", "ढा"), (".kk", "णा"),
    ("rk", "ता"), ("Fkk", "था"), ("nk", "दा"), ("/kk", "धा"), ("uk", "ना"),
    ("ik", "पा"), ("Qk", "फा"), ("ck", "बा"), ("Hkk", "भा"), ("ek", "मा"),
    (";k", "या"), ("jk", "रा"), ("yk", "ला"), ("ok", "वा"),
    ("'kk", "शा"), ("\"kk", "षा"), ("lk", "सा"), ("gk", "हा"),

    # --- all matras on one consonant ---
    ("d", "क"), ("fd", "कि"), ("dh", "की"), ("dq", "कु"), ("dw", "कू"),
    ("d`", "कृ"), ("ds", "के"), ("dS", "कै"), ("dks", "को"), ("dkS", "कौ"),
    ("da", "कं"), ("d¡", "कँ"), ("d%", "कः"), ("d‚", "कॉ"),

    # --- common words ---
    ("vkSj", "और"), ("gS", "है"), ("gSa", "हैं"), ("Fkk", "था"), ("Fks", "थे"),
    ("esa", "में"), ("ls", "से"), ("ij", "पर"), ("ugha", "नहीं"),
    (";g", "यह"), ("og", "वह"), ("ge", "हम"), ("rqe", "तुम"), ("vki", "आप"),
    ("yksx", "लोग"), ("ns'k", "देश"), ("le;", "समय"), ("dke", "काम"),
    ("?kj", "घर"), ("lky", "साल"), ("jkr", "रात"), ("fnu", "दिन"),
    ("ckr", "बात"), ("gkFk", "हाथ"), ("uke", "नाम"), ("ikuh", "पानी"),
    ("thou", "जीवन"), ("ljdkj", "सरकार"), ("Hkkjr", "भारत"),
    ("fodkl", "विकास"), ("lekt", "समाज"), ("dkj.k", "कारण"),
    ("iqLrd", "पुस्तक"), ("vkneh", "आदमी"), ("fnYyh", "दिल्ली"),
    ("i`Foh", "पृथ्वी"), ("LokLF;", "स्वास्थ्य"), ("fo|ky;", "विद्यालय"),
    # KRDEV010 really renders these this way; the NCERT reading of the same
    # bytes is in corpus_walkman.py.
    ("vf/drj", "अध्कितर"), ("iQkLiQksjl", "पफास्पफोरस"),

    # --- conjuncts ---
    ("{ks=", "क्षेत्र"), ("f'k{kk", "शिक्षा"), ("Kku", "ज्ञान"),
    ("jkT;", "राज्य"), ("O;fDr", "व्यक्ति"), ("v/;kid", "अध्यापक"),
    ("fo'ks\"k", "विशेष"), ("iz'u", "प्रश्न"), ("izdkj", "प्रकार"),
    ("Je", "श्रम"), ("fo|k", "विद्या"), ("}kj", "द्वार"),
    ("mRiknu", "उत्पादन"), ("la[;k", "संख्या"), ("LFkku", "स्थान"),
    ("fLFkfr", "स्थिति"), ("i`"+"”", None),  # placeholder removed below

    # --- t-ra family (the =k rule) ---
    ("fe=", "मित्र"), ("lw=", "सूत्र"), ("pfj=", "चरित्र"),
    ("i=", "पत्र"), (";a=", "यंत्र"), ("jk\"Vª", "राष्ट्र"),
    ("=qfV", "त्रुटि"), ("f=dks.k", "त्रिकोण"), ("f=Hkqt", "त्रिभुज"),
    ("=kk.k", "त्राण"), ("Nk=k", "छात्रा"), ("{ks=iQy", "क्षेत्रपफल"),
    ("'kkL=", "शास्त्र"), ("ea=h", "मंत्री"),

    # --- reph (Z) ---
    ("dk;Z", "कार्य"), ("ppkZ", "चर्चा"), ("fuekZ.k", "निर्माण"),
    ("lEiw.kZ", "सम्पूर्ण"), ("i;kZoj.k", "पर्यावरण"), ("deZ", "कर्म"),
    ("vFkZ", "अर्थ"), ("/keZ", "धर्म"), ("iwoZ", "पूर्व"), ("ioZr", "पर्वत"),
    ("oxZ", "वर्ग"), ("vkn'kZ", "आदर्श"), ("lwoZ"[:0]+"lw;Z", "सूर्य"),

    # --- the o..Q / i..Q families belong to Walkman-Chanakya, not here.
    #     In KRDEV010 these really do render वेफ / पफ, so they live in
    #     tests/corpus_walkman.py instead.

    # --- nukta ---
    ("d+e", "क़म"), ("t+:jh", "ज़रूरी"), ("Q+t+Z", "फ़र्ज़"),

    # --- numerals and punctuation ---
    ("åƒ„", "०१२"), ("ukeA", "नाम।"), ("d][k", "क,ख"),
]

# drop the placeholder entry
WORDS = [(a, b) for a, b in WORDS if b is not None]
