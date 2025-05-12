import re

def count_occurrences(text, patterns):
    return sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))

def evaluate_tapupas(text: str) -> dict:
    text = text.lower()

    return {
        "transparency": min(5, count_occurrences(text, [
            r"methodolog(y|ies)", r"we conducted", r"replicat(e|ion)", r"study design", r"procedure"
        ])),
        "accuracy": min(5, count_occurrences(text, [
            r"statistical (test|analysis)", r"confidence interval", r"validity", r"error margin", r"precision"
        ])),
        "purposivity": min(5, count_occurrences(text, [
            r"this study aim", r"the purpose", r"our objective", r"we propose", r"goal of this research"
        ])),
        "utility": min(5, count_occurrences(text, [
            r"policy implication", r"classroom use", r"practical relevance", r"recommendation"
        ])),
        "propriety": min(5, count_occurrences(text, [
            r"ethical approval", r"informed consent", r"IRB", r"research ethics"
        ])),
        "accessibility": min(5, count_occurrences(text, [
            r"open access", r"freely available", r"user-friendly", r"plain language"
        ])),
        "specificity": min(5, count_occurrences(text, [
            r"appropriate method", r"suitable approach", r"case study", r"mixed method", r"quantitative", r"qualitative"
        ])),
    }
