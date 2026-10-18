from email_spam_detector.detectors import GibberishDetector, KeywordDetector, HeuristicDetector, EnsembleDetector, TokeniserDetector, GibberishClassification

def test_gibberish_detector():
    detector = GibberishDetector()
    
    # Legit emails
    assert detector.is_spam("jane.doe@example.com") == False
    assert detector.is_spam("john.doe@gmail.com") == False
    assert detector.is_spam("support@github.com") == False
    assert detector.is_spam("bob@example.com") == False # Short
    
    # Gibberish emails
    assert detector.is_spam("fdasfjaklsd@gmail.com") == True
    assert detector.is_spam("faiwtlwexu@hotmail.com") == True
    assert detector.is_spam("zxcvbnmlkjhgfdsa@yahoo.com") == True
    
    # Alphanumeric spam
    assert detector.is_spam("wp762v2sjj@outlook.com") == True

def test_short_local_part():
    detector = GibberishDetector(min_len_threshold=3)
    # Even if gibberish, if it's very short it might be missed by nostril or excluded by threshold
    assert detector.is_spam("abc@def.com") == False 

def test_keyword_detector():
    detector = KeywordDetector()
    
    # Contains keywords
    assert detector.is_spam("win.prize@gmail.com") == True
    assert detector.is_spam("free.money@spam.com") == True
    assert detector.is_spam("urgent.offer@yahoo.com") == True
    
    # No keywords
    assert detector.is_spam("jane.doe@gmail.com") == False
    assert detector.is_spam("info@company.com") == False

def test_heuristic_detector():
    detector = HeuristicDetector()
    
    # Consonant clusters
    assert detector.is_spam("zkjxcv@gmail.com") == True
    
    # Keyboard mashing (short strings are ignored now, so need long one)
    # "asdfghjkl" is 9 chars -> too short for current threshold (12)
    # "qazwsxedcrfvtgb" -> 15 chars, distance should be low
    assert detector.is_spam("qazwsxedcrfvtgb@gmail.com") == True
    
    # High entropy / low vowel density
    # "02986u2qr" -> 9 chars -> too short for current threshold (12)
    # Need longer random string with unique characters for high entropy
    # "02986u2qrxzw" -> 12 unique chars
    assert detector.is_spam("02986u2qrxzw@gmail.com") == True

    # Legit
    assert detector.is_spam("jane.doe@gmail.com") == False
    assert detector.is_spam("support@github.com") == False

def test_ensemble_detector():
    g = GibberishDetector()
    k = KeywordDetector()
    h = HeuristicDetector()
    ensemble = EnsembleDetector([g, k, h])
    
    # Caught by Gibberish
    assert ensemble.is_spam("fdasfjaklsd@gmail.com") == True
    
    # Caught by Keyword
    assert ensemble.is_spam("win.prize@gmail.com") == True
    
    # Caught by Heuristic
    assert ensemble.is_spam("qazwsxedcrfvtgb@gmail.com") == True
    
    # Legit
    assert ensemble.is_spam("jane.doe@gmail.com") == False

def test_tokeniser_detector():
    detector = TokeniserDetector()

    # Legit
    assert detector.is_spam("jane.doe@example.com") == False
    assert detector.is_spam("john.doe@gmail.com") == False
    assert detector.is_spam("jose.garcia1987@gmail.com") == False

    # Gibberish
    assert detector.is_spam("fdasfjaklsd@gmail.com") == True
    assert detector.is_spam("xkqzvjwplt@yahoo.com") == True
    assert detector.is_spam("ew9g31h1ataepsz@hotmail.com") == True

def test_tokeniser_detector_classification():
    detector = TokeniserDetector()
    assert detector.classify("john.doe@gmail.com") is GibberishClassification.NOT_GIBBERISH
    assert detector.classify("xkqzvjwplt@yahoo.com") is GibberishClassification.GIBBERISH

    # Non-Latin or letterless local parts can't be scored
    assert detector.classify("李小龙@qq.com") is GibberishClassification.NON_LATIN
    assert detector.classify("владимир@mail.ru") is GibberishClassification.NON_LATIN
    assert detector.classify("123456@qq.com") is GibberishClassification.NON_LATIN
    assert detector.is_spam("李小龙@qq.com") == False

def test_tokeniser_detector_custom_tokeniser():
    # One token per letter -> score 1.0, above any sensible threshold
    detector = TokeniserDetector(tokenise=lambda s: s.replace(" ", ""), threshold=0.5)
    assert detector.is_spam("john.doe@gmail.com") == True
    assert detector.score("john.doe") == 1.0
