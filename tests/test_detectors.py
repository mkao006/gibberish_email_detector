from email_spam_detector.detectors import GibberishDetector, KeywordDetector, HeuristicDetector, EnsembleDetector

def test_gibberish_detector():
    detector = GibberishDetector()
    
    # Legit emails
    assert detector.is_spam("michael.kao@airwallex.com") == False
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
    assert detector.is_spam("michael.kao@gmail.com") == False
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
    assert detector.is_spam("michael.kao@gmail.com") == False
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
    assert ensemble.is_spam("michael.kao@gmail.com") == False