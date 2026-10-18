from abc import ABC, abstractmethod
import math
import re
import unicodedata
from collections import Counter
from enum import Enum
from typing import Callable, List, Optional, Sequence, Set, Tuple
from .nostril_impl.nonsense_detector import nonsense_score

class BaseDetector(ABC):
    """Abstract base class for email spam detectors."""

    @abstractmethod
    def is_spam(self, email: str) -> bool:
        """Determine if an email is spam."""
        pass

    def _get_local_part(self, email: str) -> Optional[str]:
        """Extract the local part of an email address."""
        parts = email.split('@')
        if not parts or not parts[0]:
            return None
        return parts[0]

class GibberishDetector(BaseDetector):
    """
    Detects spam based on gibberish/nonsense analysis of the local part.
    Uses n-gram analysis (nostril) and heuristic checks for alphanumeric randomness.
    """
    
    # Thresholds
    NOSTRIL_THRESHOLD = 7.8
    MIXED_SCORE_THRESHOLD = 6.0
    MIXED_TRANSITION_THRESHOLD = 1
    FALLBACK_LENGTH_THRESHOLD = 7
    FALLBACK_TRANSITION_THRESHOLD = 1

    def __init__(self, min_len_threshold: int = 6):
        self.min_len_threshold = min_len_threshold

    def is_spam(self, email: str) -> bool:
        local_part = self._get_local_part(email)
        if not local_part:
            return False
        
        if len(local_part) <= self.min_len_threshold:
            return False
            
        transitions = self._count_transitions(local_part)
        
        try:
            score = nonsense_score(local_part)
            
            # High nonsense score (standard random strings)
            if score > self.NOSTRIL_THRESHOLD:
                return True
                
            # Heuristic: borderline score + scrambled structure (mixed alpha/digits)
            if score > self.MIXED_SCORE_THRESHOLD and transitions > self.MIXED_TRANSITION_THRESHOLD:
                return True
                
            return False
        except Exception:
            # Fallback for strings that fail nostril (e.g. too short after sanitization)
            if len(local_part) >= self.FALLBACK_LENGTH_THRESHOLD and transitions > self.FALLBACK_TRANSITION_THRESHOLD:
                return True
            return False

    def _count_transitions(self, text: str) -> int:
        """Count transitions between alpha, digit, and other characters."""
        transitions = 0
        last_type = None # 'a' for alpha, 'd' for digit, 'o' for other
        
        for char in text:
            if char.isalpha():
                curr_type = 'a'
            elif char.isdigit():
                curr_type = 'd'
            else:
                curr_type = 'o'
            
            if curr_type != 'o':
                if last_type and last_type != curr_type:
                    transitions += 1
                last_type = curr_type
        return transitions

class KeywordDetector(BaseDetector):
    """Detects spam based on the presence of suspicious keywords in the local part."""

    DEFAULT_KEYWORDS = {"win", "prize", "offer", "discount", "free", "urgent", "money"}

    def __init__(self, keywords: Optional[List[str]] = None):
        self.keywords = set(keywords) if keywords else self.DEFAULT_KEYWORDS

    def is_spam(self, email: str) -> bool:
        local_part = self._get_local_part(email)
        if not local_part:
            return False
        
        local_part_lower = local_part.lower()
        return any(keyword in local_part_lower for keyword in self.keywords)

class HeuristicDetector(BaseDetector):
    """
    Detects spam based on various structural heuristics:
    1. High entropy with low vowel density.
    2. Long consecutive consonant chains.
    3. Keyboard mashing patterns (QWERTY distance).
    """

    # Constants
    VOWELS = set('aeiou')
    KEYBOARD_LAYOUT = {
        '1': (-1, 0), '2': (-1, 1), '3': (-1, 2), '4': (-1, 3), '5': (-1, 4), 
        '6': (-1, 5), '7': (-1, 6), '8': (-1, 7), '9': (-1, 8), '0': (-1, 9),
        'q': (0, 0), 'w': (0, 1), 'e': (0, 2), 'r': (0, 3), 't': (0, 4), 'y': (0, 5), 'u': (0, 6), 'i': (0, 7), 'o': (0, 8), 'p': (0, 9),
        'a': (1, 0.5), 's': (1, 1.5), 'd': (1, 2.5), 'f': (1, 3.5), 'g': (1, 4.5), 'h': (1, 5.5), 'j': (1, 6.5), 'k': (1, 7.5), 'l': (1, 8.5),
        'z': (2, 1), 'x': (2, 2), 'c': (2, 3), 'v': (2, 4), 'b': (2, 5), 'n': (2, 6), 'm': (2, 7)
    }

    # Thresholds
    ENTROPY_MIN_LEN = 12
    ENTROPY_HIGH_THRESHOLD = 0.98
    ENTROPY_MIXED_THRESHOLD = 0.92
    VOWEL_DENSITY_LOW_THRESHOLD = 0.20
    
    CONSONANT_MAX_CONSECUTIVE = 5
    
    QWERTY_MIN_LEN = 12
    QWERTY_MAPPED_RATIO = 0.8
    QWERTY_DIST_THRESHOLD = 0.7

    def is_spam(self, email: str) -> bool:
        local_part = self._get_local_part(email)
        if not local_part:
            return False
        
        local_part_lower = local_part.lower()
        
        if self._check_entropy_and_vowels(local_part_lower):
            return True
            
        if self._check_consonants(local_part_lower):
            return True
            
        if self._check_keyboard_mashing(local_part_lower):
            return True

        return False

    def _check_entropy_and_vowels(self, text: str) -> bool:
        if len(text) < self.ENTROPY_MIN_LEN:
            return False
            
        ent = self._entropy(text)
        max_ent = math.log2(len(text)) if len(text) > 0 else 0
        norm_ent = ent / max_ent if max_ent > 0 else 0
        vowel_dens = self._vowel_density(text)
        
        if norm_ent > self.ENTROPY_HIGH_THRESHOLD:
            return True
        if norm_ent > self.ENTROPY_MIXED_THRESHOLD and vowel_dens < self.VOWEL_DENSITY_LOW_THRESHOLD:
            return True
        return False

    def _check_consonants(self, text: str) -> bool:
        return self._max_consecutive_consonants(text) > self.CONSONANT_MAX_CONSECUTIVE

    def _check_keyboard_mashing(self, text: str) -> bool:
        mapped_chars = sum(1 for c in text if c in self.KEYBOARD_LAYOUT)
        if len(text) >= self.QWERTY_MIN_LEN and (mapped_chars / len(text) > self.QWERTY_MAPPED_RATIO):
            dist = self._qwerty_distance(text)
            if dist < self.QWERTY_DIST_THRESHOLD: 
                return True
        return False

    def _entropy(self, text: str) -> float:
        if not text: return 0.0
        counts = Counter(text)
        length = len(text)
        return -sum((c/length) * math.log2(c/length) for c in counts.values())

    def _max_consecutive_consonants(self, text: str) -> int:
        max_cons = 0
        current_cons = 0
        for char in text:
            if char in self.VOWELS:
                current_cons = 0
            elif char.isalpha():
                current_cons += 1
                max_cons = max(max_cons, current_cons)
            else:
                current_cons = 0 
        return max_cons
    
    def _vowel_density(self, text: str) -> float:
        if not text: return 0.0
        v_count = sum(1 for c in text if c in self.VOWELS)
        return v_count / len(text)

    def _qwerty_distance(self, text: str) -> float:
        coords = [self.KEYBOARD_LAYOUT[c] for c in text if c in self.KEYBOARD_LAYOUT]
        
        if len(coords) < 2:
            return 10.0 

        total_dist = 0.0
        count = 0
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i+1]
            dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            total_dist += dist
            count += 1
        
        return total_dist / count if count > 0 else 10.0

class GibberishClassification(Enum):
    GIBBERISH = "gibberish"
    NOT_GIBBERISH = "not_gibberish"
    NON_LATIN = "non_latin"

class TokeniserDetector(BaseDetector):
    """
    Detects gibberish by how badly a subword tokeniser fragments the local part.
    Real names compress into few tokens; random strings split into many.
    Score = tokens per letter, over the letter-only words of the local part.

    Pass any tokeniser as a function returning tokens, e.g.
    sentencepiece.SentencePieceProcessor(model_file=...).encode or
    transformers.AutoTokenizer.from_pretrained(...).tokenize.
    Retune the threshold when switching tokenisers.
    """

    # Tuned on generated data for tiktoken cl100k_base
    DEFAULT_THRESHOLD = 0.47

    def __init__(self, tokenise: Optional[Callable[[str], Sequence]] = None, threshold: float = DEFAULT_THRESHOLD):
        if tokenise is None:
            import tiktoken
            tokenise = tiktoken.get_encoding("cl100k_base").encode
        self.tokenise = tokenise
        self.threshold = threshold

    def is_spam(self, email: str) -> bool:
        return self.classify(email) is GibberishClassification.GIBBERISH

    def classify(self, email: str) -> GibberishClassification:
        local_part = self._get_local_part(email)
        letters = [c for c in local_part or "" if c.isalpha()]
        if not letters or not all("LATIN" in unicodedata.name(c, "") for c in letters):
            return GibberishClassification.NON_LATIN

        score = self.score(local_part)
        if score > self.threshold:
            return GibberishClassification.GIBBERISH
        return GibberishClassification.NOT_GIBBERISH

    def score(self, local_part: str) -> float:
        words = re.findall(r"[^\W\d_]+", local_part)
        return len(self.tokenise(" ".join(words))) / sum(len(w) for w in words)

class EnsembleDetector(BaseDetector):
    """Combines multiple detectors using an OR strategy."""

    def __init__(self, detectors: List[BaseDetector]):
        self.detectors = detectors

    def is_spam(self, email: str) -> bool:
        return any(d.is_spam(email) for d in self.detectors)

def main():
    gibberish = GibberishDetector()
    keyword = KeywordDetector()
    heuristic = HeuristicDetector()
    tokeniser = TokeniserDetector()
    ensemble = EnsembleDetector([gibberish, keyword, heuristic, tokeniser])
    
    test_emails = [
        "michael.kao@airwallex.com",
        "fdasfjaklsd@gmail.com",
        "bob@gmail.com",
        "win.free.money@spam.com",
        "asdfghjkl@yahoo.com",
        "qazwsxedc@hotmail.com",
        "60d2ejbsurw@yahoo.com"
    ]
    for email in test_emails:
        res_g = "S" if gibberish.is_spam(email) else "H"
        res_k = "S" if keyword.is_spam(email) else "H"
        res_h = "S" if heuristic.is_spam(email) else "H"
        res_t = "S" if tokeniser.is_spam(email) else "H"
        res_e = "S" if ensemble.is_spam(email) else "H"
        print(f"{email:30} | G:{res_g} K:{res_k} H:{res_h} T:{res_t} | Ensemble:{res_e}")

if __name__ == "__main__":
    main()
