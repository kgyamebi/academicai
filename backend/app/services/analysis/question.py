from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

COMMANDS = {
    "critically evaluate": "Judge the strengths and limitations of the topic using evidence and criteria, not just description.",
    "critically discuss": "Examine competing views, weigh evidence, and reach a reasoned judgement.",
    "critically analyse": "Break the topic into parts, question assumptions, and assess the quality of evidence.",
    "compare and contrast": "Identify meaningful similarities and differences, then explain why they matter.",
    "compare and evaluate": "Set items side by side and then judge their relative significance or effectiveness.",
    "compare": "Identify similarities and differences between the specified items or cases.",
    "contrast": "Focus on meaningful differences.",
    "evaluate": "Make a judgement against criteria and support it with evidence.",
    "assess": "Weigh the importance, quality, or impact of the topic.",
    "analyse": "Break the topic into components and explain relationships between them.",
    "analyze": "Break the topic into components and explain relationships between them.",
    "discuss": "Examine the topic from more than one angle and develop a reasoned position.",
    "explain": "Make the topic clear by showing how or why it works.",
    "describe": "Give a clear account of the main features. Description alone is usually not enough at university level.",
    "examine": "Look closely at the topic and consider its implications.",
    "explore": "Investigate the topic with attention to complexity and uncertainty.",
    "justify": "Give reasons and evidence for a position.",
    "to what extent": "Judge how far a claim is true, usually by weighing supporting and limiting evidence.",
    "how far": "Judge the degree to which a claim holds.",
    "account for": "Explain the reasons or causes.",
    "illustrate": "Clarify the point with examples.",
    "outline": "Present the main points without lengthy detail.",
    "summarise": "Restate the main points concisely.",
    "summarize": "Restate the main points concisely.",
    "review": "Survey and comment on the main literature or evidence.",
    "argue": "Take a position and defend it with reasoning and evidence.",
    "critique": "Identify strengths and weaknesses of a claim, method, or text.",
    "recommend": "Propose a course of action and justify it against criteria.",
    "reflect": "Examine your own reasoning or practice; still support claims with evidence.",
    "determine": "Reach a reasoned conclusion after weighing the available evidence.",
}


@dataclass
class QuestionAnalysis:
    raw_text: str
    command_words: list[str] = field(default_factory=list)
    command_explanations: dict[str, str] = field(default_factory=dict)
    topic: str = ""
    scope: str = ""
    geographic_scope: str = ""
    time_period: str = ""
    required: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    required_depth: str = "undergraduate analysis"
    interpretation: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_question(text: str, academic_level: str = "undergraduate") -> QuestionAnalysis:
    raw = (text or "").strip()
    lowered = raw.lower()
    found: list[str] = []
    explanations: dict[str, str] = {}
    for command, meaning in sorted(COMMANDS.items(), key=lambda x: len(x[0]), reverse=True):
        if command in lowered and command not in found:
            # Avoid adding both "compare" and "compare and evaluate" as if they were independent.
            if any(command in existing for existing in found):
                continue
            if command == "explain" and any(c in found for c in ("to what extent", "how far")):
                if not lowered.lstrip().startswith("explain"):
                    continue
            found.append(command)
            explanations[command] = meaning

    topic = _topic(raw, found)
    geo = _geographic_scope(raw)
    period = _time_period(raw)
    scope_bits = [bit for bit in [geo, period] if bit]
    required = []
    for cmd in found:
        if "compare" in cmd:
            required.append("Comparison")
        if "contrast" in cmd:
            required.append("Contrast")
        if "evaluate" in cmd or "assess" in cmd or "to what extent" in cmd or "how far" in cmd:
            required.append("Evaluation / judgement")
        if "critically" in cmd or "critique" in cmd:
            required.append("Critical analysis")
        if "discuss" in cmd:
            required.append("Discussion of more than one perspective")
        if "analyse" in cmd or "analyze" in cmd:
            required.append("Analysis rather than description")
        if "justify" in cmd or "argue" in cmd:
            required.append("A defended position")
    required = list(dict.fromkeys(required))
    if "definition" not in " ".join(required).lower() and any(
        w in lowered for w in ("define", "what is", "meaning of")
    ):
        required.append("Definition")

    constraints = []
    word_limit = re.search(r"(\d{3,5})\s*(words|word)", lowered)
    if word_limit:
        constraints.append(f"Word guidance around {word_limit.group(1)} words")
    if "using" in lowered and "example" in lowered:
        constraints.append("Examples appear to be required")
    if any(w in lowered for w in ("peer-reviewed", "scholarly", "journal")):
        constraints.append("Scholarly sources appear to be expected")

    depth = {
        "high_school": "Clear explanation with some evaluation",
        "undergraduate": "Argument, evidence, and evaluation beyond description",
        "masters": "Critical engagement with scholarship and a distinctive position",
        "phd": "Original contribution, methodological awareness, and deep critique",
        "researcher": "Publication-level argument, evidence, and scholarly conversation",
    }.get(academic_level, "Argument, evidence, and evaluation beyond description")

    interpretation = (
        "Based on the wording of the question, these appear to be the main requirements. "
        "This is an interpretation of the prompt, not a claim about any particular marker's expectations. "
    )
    if found:
        interpretation += f"The command word(s) {', '.join(found)} suggest the work should go beyond summary. "
    if topic:
        interpretation += f"The central topic appears to be: {topic}. "
    if scope_bits:
        interpretation += f"The scope appears limited to {', '.join(scope_bits)}. "
    if required:
        interpretation += f"A complete answer would normally include: {', '.join(required)}."

    return QuestionAnalysis(
        raw_text=raw,
        command_words=found,
        command_explanations=explanations,
        topic=topic,
        scope="; ".join(scope_bits) or topic,
        geographic_scope=geo,
        time_period=period,
        required=required,
        constraints=constraints,
        required_depth=depth,
        interpretation=interpretation.strip(),
    )


def _topic(raw: str, commands: list[str]) -> str:
    text = raw
    for cmd in sorted(commands, key=len, reverse=True):
        text = re.sub(re.escape(cmd), "", text, flags=re.I)
    text = re.sub(r"^(the|a|an|of|on|how|why|what|to)\s+", "", text.strip(), flags=re.I)
    text = re.sub(r"[?!.]+$", "", text).strip(" ,")
    return text[:240]


def _geographic_scope(text: str) -> str:
    patterns = [
        r"\b(developing economies|developing countries|global south|sub-saharan africa|"
        r"west africa|east africa|latin america|south asia|southeast asia|european union|"
        r"united states|united kingdom|ghana|nigeria|kenya|south africa|india|china)\b"
    ]
    matches = []
    for pat in patterns:
        matches.extend(re.findall(pat, text, flags=re.I))
    return ", ".join(dict.fromkeys(m.lower() for m in matches))


def _time_period(text: str) -> str:
    years = re.findall(r"\b(1[89]\d{2}|20\d{2})\b", text)
    if len(years) >= 2:
        return f"{years[0]}–{years[-1]}"
    if years:
        return years[0]
    m = re.search(r"\b(post-?war|twenty-first century|21st century|since the \d{4}s|colonial period)\b", text, re.I)
    return m.group(0) if m else ""
