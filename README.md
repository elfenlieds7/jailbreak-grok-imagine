# Jailbreak Grok Imagine

Security research on xAI's Grok Imagine - **sexual content filtering mechanisms** and bypass techniques.

**Research Scope**: Sexual content moderation ONLY. We do NOT study: politics, violence, hate speech, or other categories.

---

## Quick Start for AI Assistants

Read these files in order:

1. **[`data/results/RESEARCH_FINDINGS.md`](data/results/RESEARCH_FINDINGS.md)** - Core discoveries and analysis
2. **[`data/results/manual_tests.csv`](data/results/manual_tests.csv)** - Complete test history (90+ entries)
3. **`current_test_prompt.txt`** - Next prompt to test
4. **GitHub Discussions** - Session handoffs (use GraphQL to fetch)

---

## Key Discoveries

1. **Grok-Generated Image→Video Mode** ⭐: Weakest security (discovered 2025-12-06)
   - Text→Image (no prompt filter) → Image→Video (retry bypass) → Video editing (cache-based, minimal filtering)
   - **HIGH PRIORITY** for exploitation

2. **Three-Layer Security**: Prompt Filter + Model Alignment (RLHF) + Post-Generation Check

3. **Cache-Based Scoring**: Likely uses Sequential Hypothesis Testing (SPRT)
   - Once animated, edits rarely blocked (cached evidence score)
   - Exception: cache invalidation → re-evaluation fails

4. **Adaptive Moderation**: Filter rules update over time (Test 61c: 0 blocks → 4+ blocks)

5. **Semantic Understanding**: Grok 3 reasoning defeats syntactic tricks (Unicode normalization, word order flip all failed)

All findings: **sexual content filtering only**

---

## Grok Imagine Modes

| Mode | Workflow | Spicy | Security | Status |
|------|----------|-------|----------|--------|
| **Grok-Image→Video** ⭐ | Text→Image→Video | ✅ | **WEAKEST** | Not yet systematically tested |
| Text-to-Video | Prompt→Video | ✅ | Permissive | - |
| Upload-Image→Video | External→Video | ❌ | **STRICTEST** | All Tests 1-58b done here |

**Model**: Aurora (autoregressive mixture-of-experts)

---

## File Structure

```
jailbreak-grok-imagine/
├── README.md                       # This file
├── data/results/
│   ├── RESEARCH_FINDINGS.md        # Core analysis (282 lines, compressed 2025-12-06)
│   └── manual_tests.csv            # Test history (90+ entries)
├── current_test_prompt.txt         # Next test
└── data/images/                    # Test images (inputs/outputs)
```

---

## Manual Testing Workflow

1. Write prompt in `current_test_prompt.txt`
2. Test on Grok Imagine (x.com)
3. Record in `manual_tests.csv`: test_id, blocks, classification, notes
4. Update `RESEARCH_FINDINGS.md` if significant

**AI Copilot Role**: Analysis, hypothesis generation, documentation, experimental design

---

## Research Status

**Completed (Uploaded Image Mode)**:

- ✅ Tests 1-58b on strictest mode
- ✅ Bypass techniques: Character smuggling, word flip, abstraction, code-switching (all failed/partial)
- ✅ Best results: Extreme Abstraction (4 blocks), Phrase-Level Code-Switching (0 blocks, not reproducible)

**Next Priority**:

- 🔥 Grok-Generated Image→Video systematic testing
- 🔥 SPRT hypothesis validation (order dependency, context compound)

---

## References

**Core**:

- [Grok Image Generation | xAI](https://x.ai/news/grok-image-generation-release)
- [arXiv: Unmasking the Canvas](https://arxiv.org/html/2505.04146v1)

**2025 Research** (untested on Grok):

- [SEAL - Stacked Encryption](https://arxiv.org/html/2505.16241v1) - 80%+ ASR
- [Mousetrap - Iterative Chaos](https://arxiv.org/html/2502.15806v2) - 86-98% ASR
- [Embrace The Red - Grok Analysis](https://embracethered.com/blog/posts/2024/security-probllms-in-xai-grok/) - ASCII smuggling

---

## Disclaimer

**Authorized security research only**. Purpose: Improve AI safety, responsible disclosure to xAI, advance academic understanding of multimodal content moderation.

**Sexual content filtering research only** - not politics, violence, or other categories.

MIT License.
