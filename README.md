# Jailbreak Grok Imagine

Security research on xAI's Grok Imagine - studying content filtering mechanisms and bypass techniques.

## Quick Start for AI Assistants

**To fully ramp-up, read these files in order:**

1. **`data/results/RESEARCH_FINDINGS.md`** - All research discoveries, bypass techniques, keyword effects
2. **`data/results/manual_tests.csv`** - Complete test history (90+ entries, Tests 1-57 + Test 61 series)
3. **`current_test_prompt.txt`** - Next prompt to test
4. **GitHub Discussions** - Session handoffs and detailed analysis (use GraphQL to fetch)

## Key Discoveries

1. **Three-Layer Security**: Prompt Filter + Model Alignment (RLHF) + Post-Generation Check
2. **Semantic Understanding**: Filter analyzes intent, not keywords (Unicode normalization confirmed)
3. **Adaptive Moderation**: Filter rules update over time - previously working prompts may fail later
4. **Image-to-Video Stricter**: Much stricter than text-only mode for clothing changes
5. **Best Bypass Results**: Extreme Abstraction (Test 55, 4 blocks) and Phrase-Level Code-Switching (Test 61c, 0 blocks but not reproducible)

## File Structure

```
jailbreak-grok-imagine/
├── README.md                          # This file (start here)
├── current_test_prompt.txt            # Next test prompt
├── data/
│   ├── results/
│   │   ├── manual_tests.csv           # Primary test record (90+ entries)
│   │   └── RESEARCH_FINDINGS.md       # All research findings
│   └── images/
│       ├── inputs/                    # Test input images
│       ├── outputs/                   # Generated screenshots
│       └── README.md                  # Image documentation
```

## Workflow

### Manual Testing Process

1. **Prepare**: Write test prompt in `current_test_prompt.txt`
2. **Test**: Copy prompt to Grok Imagine (x.com), run with Spicy mode ON
3. **Record**: Add results to `manual_tests.csv`
4. **Analyze**: Update findings in `RESEARCH_FINDINGS.md` if significant

### Recording Format (manual_tests.csv)

```csv
test_id,timestamp,mode,prompt,spicy,blocked,ui_status,classification,error_message,technique,retry_count,notes
```

Key fields:
- `retry_count`: Number of blocks before success (0 = first try success)
- `classification`: full_success / partial_success / failed / hard_block
- `technique`: Bypass technique used (if any)
- `notes`: Detailed observations

## Grok Imagine Overview

| Mode | Input | Output | NSFW Option |
|------|-------|--------|-------------|
| **Text-to-Video** | Prompt | Video | Spicy mode available |
| **Image-to-Video** | Image + Prompt | Video | No Spicy option currently |

**Model**: Aurora - autoregressive mixture-of-experts network

## GitHub Discussions

Access via GraphQL API or web:
- **Discussion #6**: Session handoff and progress summary
- **Discussion #5**: Bypass techniques catalog
- **Discussion #4**: Image-to-Video vs Text-to-Video filter differential
- **Discussion #3**: Fantasy escape mechanisms research

## Untested Techniques (from Web Research)

Based on 2024-2025 academic research, these techniques show promise but haven't been tested yet:

| Technique | Source | Reported ASR | Priority |
|-----------|--------|--------------|----------|
| **SEAL (Stacked Encryption)** | arXiv:2505.16241 | 80-85% on GPT/Claude | High |
| **Mousetrap (Chaos-of-Thought)** | arXiv:2502.15806 | 86-98% on Claude/Gemini | High |
| **ASCII Smuggling (Unicode Tags)** | Embrace The Red | Grok vulnerable | High |
| **SurrogatePrompt** | arXiv:2309.14122 | 88% on Midjourney | Medium |
| **Atlas (LLM Multi-Agent)** | arXiv:2408.00523 | ~100% on most filters | Medium |

## References

### Core References
- [Grok Image Generation Release | xAI](https://x.ai/news/grok-image-generation-release)
- [arXiv: Unmasking the Canvas](https://arxiv.org/html/2505.04146v1) - Image generation jailbreak benchmark
- [arXiv: Controlled-Release Prompting](https://arxiv.org/html/2510.01529v2) - Bypassing prompt guards

### New Research (2025)
- [arXiv: SEAL - Stacked Encryption Attack](https://arxiv.org/html/2505.16241v1) - 80%+ ASR on reasoning models
- [arXiv: Mousetrap - Chain of Iterative Chaos](https://arxiv.org/html/2502.15806v2) - 86-98% ASR on LRMs
- [Embrace The Red: Grok Security Analysis](https://embracethered.com/blog/posts/2024/security-probllms-in-xai-grok/) - ASCII smuggling, prompt injection
- [arXiv: SurrogatePrompt](https://arxiv.org/html/2309.14122v2) - 88% bypass on Midjourney
- [arXiv: Atlas LLM-Based Jailbreaking](https://arxiv.org/html/2408.00523v1) - Multi-agent T2I bypass

## License

MIT License - For authorized security research only.

## Disclaimer

This project is for **authorized security research purposes only**. All testing is conducted with proper authorization and in compliance with responsible disclosure practices. The goal is to improve AI safety, not to enable misuse.
