"""
naming_rules.py — The "skill": a structured rule set for generating brandable
domain-name candidates.

Source grounding (per user request, methodology rebuilt in original wording
from confirmed video metadata/descriptions, NOT transcribed or quoted):

  [W] Rob Walling — "How To Choose a Name for Your Business, Startup, Brand,
      Product" (MicroConf, youtube.com/watch?v=ZxYPGWqSA2I)
      Confirmed via real video description/tags + a third-party recap that
      paraphrased specific stories from the video (a band that picked too
      clever a pun and confused everyone; a founder who renamed a
      hard-to-say analytics product to the clearer "MarketBeat.com").

  [B] Brand Master Academy — "How To Come Up With A Business Name (Brand
      Name Ideas, Examples & Strategy)" (youtube.com/watch?v=2GLXMZCGsZo)
      Confirmed via the real chapter list pulled from the video's own
      description, covering 7 named name-types and a 6-step naming process.

A third planned source (orenmeetsworld, "How to Name Your Brand") could not
be retrieved (repeated rate-limiting) and was deliberately excluded rather
than guessed at.
"""

# ---------------------------------------------------------------------------
# 1. Core principles — what makes a name "work" [W]
# ---------------------------------------------------------------------------
# Rob Walling's video frames good naming around being legally protectable,
# easy to say out loud, and easy to spell from hearing it once — and warns
# against being "too clever" (his band-name example) or picking something
# so vague/hard-to-say that you end up re-naming later (his MarketBeat
# example, where an unclear name had to be abandoned post-launch).

CORE_PRINCIPLES = [
    "Say it out loud test: if you'd struggle to say the name clearly in conversation, or someone would mishear "
    "it, it's a problem [W].",
    "Spell it from hearing it test: a name that sounds ambiguous when spoken (multiple plausible spellings) "
    "creates lost traffic and confusion [W].",
    "Avoid being 'too clever': wordplay or puns that require explanation usually fail in practice, even when "
    "they feel clever in the brainstorm [W].",
    "Avoid vague/unclear names: a name that doesn't give people any foothold on what the business does forces "
    "you to over-explain it every time, which is costly long-term [W].",
    "Must be legally protectable: avoid names that are purely descriptive/generic, since these are hard to "
    "trademark and defend [W].",
    "Short and simple beats long and clever: long, multi-word, or overly intricate names are harder to recall "
    "and harder to brand consistently [W].",
]

# ---------------------------------------------------------------------------
# 2. Name-type taxonomy [B] — Brand Master Academy's 7 categories
# ---------------------------------------------------------------------------
# Each maps to a different generation strategy.

NAME_TYPES = {
    "founder": "Built from a real or invented personal/founder name (e.g. company named after its creator).",
    "descriptive": "States plainly what the business does or sells.",
    "aligned": "Doesn't describe the product directly, but evokes the right feeling or association for it.",
    "invented": "A made-up word with no prior dictionary meaning, chosen for sound and feel.",
    "lexical": "A real dictionary word repurposed/blended in a way unrelated to its literal meaning.",
    "acronym": "Built from the initials of a longer descriptive name.",
    "geographical": "References a place — real or evocative — tied to the brand's origin or identity.",
}

# ---------------------------------------------------------------------------
# 3. The 6-step process [B]
# ---------------------------------------------------------------------------
# 1. Define the buyer persona (who you're naming this FOR)
# 2. Define your differentiator (what makes you not-generic)
# 3. Brainstorm keywords tied to persona + differentiator
# 4. Integrate, amalgamate & consolidate those keywords into name candidates
# 5. Quality filter — cut candidates against the core principles above
# 6. Real-world application — check how it reads in actual use (logo, url, said aloud)
#
# Our generator automates steps 3-5 computationally/via LLM; steps 1-2 are
# captured by the user's seed word(s) input, and step 6 is partially covered
# by the domain-availability check.

PROCESS_STEPS = [
    "buyer_persona",
    "differentiator",
    "brainstorm_keywords",
    "integrate_amalgamate_consolidate",
    "quality_filter",
    "real_world_application",
]

# ---------------------------------------------------------------------------
# 4. Construction techniques — the mechanics behind step 4 (Integrate,
#    Amalgamate & Consolidate) [B], refined by the say-it/spell-it tests [W]
# ---------------------------------------------------------------------------

CONSTRUCTION_TECHNIQUES = [
    "compound: join two whole real words directly, preserving both as readable chunks.",
    "blend: overlap or merge two words at a shared sound so they fuse into one (portmanteau-style).",
    "affix: attach a short, common, brandable prefix or suffix to the seed word.",
    "truncate: cut a longer descriptive word down to its most distinctive, easy-to-say chunk.",
    "invented: build a new word purely for sound and feel, with no literal meaning (per the 'invented' name type) [B].",
    "lexical_shift: take a real word and apply it to an unrelated context so it reads fresh (per 'lexical' type) [B].",
]

PREFIXES = [
    "co", "go", "up", "re", "pro", "neo", "vox", "uni", "ad", "bi", "e", "hyper", "meta", "micro", "multi", "omni",
]

SUFFIXES = [
    "ify", "ly", "io", "able", "hub", "ster", "ity", "ate", "ix", "ar", "ent", "ory",
]

# ---------------------------------------------------------------------------
# 5. Quality filter [B] + say-it/spell-it tests [W] — applied before any
#    domain check, to discard low-quality candidates cheaply
# ---------------------------------------------------------------------------

MAX_LEN = 12
MIN_LEN = 4

# Letter clusters that tend to fail the "say it out loud" / "spell it from
# hearing it" tests [W].
HARD_TO_SAY_CLUSTERS = ["tzch", "schtr", "xqz", "ckq", "vvv", "jj", "qq", "zx", "qz"]


def passes_quality_filter(name: str) -> bool:
    """Cheap pre-filter implementing the Quality Filter step [B] plus the
    say-it/spell-it tests [W], run before any network/domain lookup."""
    n = name.lower().strip()
    if not n.isalpha():
        return False
    if not (MIN_LEN <= len(n) <= MAX_LEN):
        return False
    if any(cluster in n for cluster in HARD_TO_SAY_CLUSTERS):
        return False
    for i in range(len(n) - 2):
        if n[i] == n[i + 1] == n[i + 2]:
            return False
    return True


def build_llm_system_prompt() -> str:
    """System prompt for the LLM generation path (DigitalOcean inference
    endpoint), encoding the same taxonomy/process/principles so both the
    rule-based generator and the LLM stay consistent with each other."""
    principles = "\n".join(f"- {p}" for p in CORE_PRINCIPLES)
    types = "\n".join(f"- {k}: {v}" for k, v in NAME_TYPES.items())
    techniques = "\n".join(f"- {t}" for t in CONSTRUCTION_TECHNIQUES)
    return (
        "You are generating short, brandable, ownable domain-name candidates from a seed word or niche.\n\n"
        "Follow these principles when judging quality:\n" + principles + "\n\n"
        "Draw from this mix of name types:\n" + types + "\n\n"
        "Use these construction techniques to build candidates:\n" + techniques + "\n\n"
        "Output rules:\n"
        "- Return ONLY a JSON array of lowercase strings, nothing else (no markdown, no preamble, no explanation).\n"
        "- Each name must be a single word: letters only, no spaces, hyphens, or numbers.\n"
        f"- Each name must be between {MIN_LEN} and {MAX_LEN} letters long.\n"
        "- Do not return the seed word verbatim or a purely generic dictionary word on its own.\n"
        "- Favor names that pass a 'say it out loud' and 'spell it from hearing it' test.\n"
    )


# ---------------------------------------------------------------------------
# 6. Variation builder — when a name is taken, generate modified forms that
#    are more likely to be unregistered (prefixed / suffixed / pluralized).
# ---------------------------------------------------------------------------

BRAND_PREFIXES = ["get", "go", "try", "use", "my", "join", "hey", "the"]
BRAND_SUFFIXES = ["app", "hq", "ly", "hub", "now", "io", "labs", "co", "ai", "ify"]


def build_variations(base: str, limit: int = 24) -> list[str]:
    """Given a base name, build modified candidates more likely to be free."""
    base = base.lower().strip()
    if base.endswith(".com"):
        base = base[:-4]
    out = [p + base for p in BRAND_PREFIXES]
    out += [base + s for s in BRAND_SUFFIXES]
    out.append(base + "s")
    seen, clean = set(), []
    for n in out:
        if n.isalpha() and 4 <= len(n) <= 20 and n not in seen:
            seen.add(n)
            clean.append(n)
    return clean[:limit]