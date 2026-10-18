# Email Spam Detector

Flags spam email addresses by looking at the local part (before the `@`).
It combines a few lightweight detectors in an ensemble, with no trained model.

```
jane.doe@example.com        -> legitimate
fdasfjaklsd@gmail.com       -> gibberish spam
win.free.money@spam.com     -> keyword spam
```

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest
```

## Detectors

All detectors live in `src/email_spam_detector/detectors.py` and share one interface: `is_spam(email) -> bool`.

| Detector | Signal | Catches |
|---|---|---|
| `GibberishDetector` | Character n-gram nonsense score (vendored [nostril](https://github.com/casics/nostril), in `nostril_impl/`), plus letter/digit transitions | Random strings, alphanumeric noise like `wp762v2sjj` |
| `TokeniserDetector` | Tokens per letter from a subword tokeniser | Random strings, including short ones nostril can't score |
| `HeuristicDetector` | Character entropy, vowel density, consonant runs, QWERTY key distance | Keyboard mashing, consonant clusters |
| `KeywordDetector` | Spam words (`win`, `free`, `money`, ...) in the local part | Keyword spam |
| `EnsembleDetector` | Flags spam if any of its detectors does | All of the above |

```python
from email_spam_detector.detectors import (
    GibberishDetector, KeywordDetector, HeuristicDetector, TokeniserDetector, EnsembleDetector,
)

ensemble = EnsembleDetector([GibberishDetector(), KeywordDetector(), HeuristicDetector(), TokeniserDetector()])
ensemble.is_spam("fdasfjaklsd@gmail.com")  # True
```

### TokeniserDetector

Real names are built from character sequences a tokeniser has seen often, so they compress into few tokens.
Random strings fragment into many. The detector:

1. Returns `NON_LATIN` if the local part has no letters or any non-Latin letter (Chinese, Cyrillic, Arabic, ...).
2. Splits the local part into letter-only words (`jose.garcia1987` -> `jose garcia`) and tokenises them.
3. Scores tokens per letter. Above the threshold is `GIBBERISH`, otherwise `NOT_GIBBERISH`.

```python
from email_spam_detector.detectors import TokeniserDetector, GibberishClassification

detector = TokeniserDetector()
detector.classify("xkqzvjwplt@yahoo.com")   # GibberishClassification.GIBBERISH
detector.classify("john.doe@gmail.com")     # GibberishClassification.NOT_GIBBERISH
detector.classify("李小龙@qq.com")            # GibberishClassification.NON_LATIN
detector.score("xkqzvjwplt")                # raw tokens-per-letter score
```

`is_spam` is true only for `GIBBERISH`; `NON_LATIN` counts as not spam.

**Choosing a tokeniser.** The default is tiktoken's `cl100k_base`. Any function that maps a string to a list of tokens works:

```python
import tiktoken
TokeniserDetector(tiktoken.get_encoding("o200k_base").encode)

import sentencepiece as spm   # uv add sentencepiece
TokeniserDetector(spm.SentencePieceProcessor(model_file="names.model").encode)

from transformers import AutoTokenizer   # uv add transformers
TokeniserDetector(AutoTokenizer.from_pretrained("xlm-roberta-base").tokenize)
```

The default threshold (0.47) was tuned for `cl100k_base` on generated emails, so pass a new `threshold=` when you switch tokenisers.
A multilingual tokeniser (e.g. XLM-R) or a SentencePiece model trained on real names should score non-English names more fairly.

## Data and evaluation

```bash
uv run python scripts/generate_data.py 120   # writes data/emails.csv: 1/3 legit, 1/3 random strings, 1/3 keyword spam
uv run python scripts/evaluate.py            # accuracy, precision, recall, F1 per detector
```

Results on the bundled 120-email dataset (`data/emails.csv`):

| Detector | Precision | Recall | F1 |
|---|---|---|---|
| Gibberish | 1.00 | 0.49 | 0.66 |
| Tokeniser | 0.97 | 0.47 | 0.64 |
| Keyword | 1.00 | 0.50 | 0.67 |
| Heuristic | 0.89 | 0.10 | 0.18 |
| Ensemble (Gibberish + Keyword + Heuristic) | 0.99 | 0.99 | 0.99 |
| Ensemble + Tokeniser | 0.99 | 1.00 | 0.99 |

Single detectors top out near 0.5 recall because each targets one kind of spam: the gibberish detectors miss keyword spam, and vice versa.
The dataset is small and synthetic, so treat these numbers as a sanity check, not a benchmark.

## Limitations

- **Synthetic data.** Legitimate emails are `faker` names, and gibberish is uniformly random characters. Real spam, and real non-English names, will look different.
- **Keyboard mashing.** Common keyboard runs like `asdfghjkl` tokenise cheaply, so `TokeniserDetector` misses them. `GibberishDetector` and `HeuristicDetector` cover that case.
- **Short local parts.** `GibberishDetector` ignores local parts of 6 characters or fewer.

## Development

- Manage the environment with `uv`.
- Write minimal code without premature abstraction; only add classes and abstractions when necessary.
- See `spec.md` for the original brief and `todo.md` for the development log.
