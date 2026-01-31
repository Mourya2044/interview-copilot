from nlp.classifier_types import ClassificationResult


class NLPClassifier:
    """
    Rule-based v1 classifier.
    Fast, deterministic, replaceable by LLM later.
    """

    async def classify(self, event) -> ClassificationResult:
        text = event.text.lower()
        words = text.split()

        # ----------------
        # FILLER / CONTEXT
        # ----------------
        if len(words) < 6:
            return ClassificationResult(
                intent="filler",
                action="ignore",
                confidence=0.8,
                reasoning="Utterance too short to be a question",
            )

        # ----------------
        # BEHAVIORAL
        # ----------------
        if any(k in text for k in (
            "experience",
            "worked on",
            "project",
            "role",
            "team",
            "challenge",
            "strength",
            "weakness",
            "background",
        )):
            return ClassificationResult(
                intent="behavioral",
                action="respond",
                confidence=0.75,
                reasoning="Behavioral keywords detected",
            )

        # ----------------
        # ALGORITHMIC
        # ----------------
        if any(k in text for k in (
            "array",
            "string",
            "tree",
            "graph",
            "dp",
            "dynamic programming",
            "binary",
            "search",
            "sort",
            "time complexity",
            "space complexity",
        )):
            return ClassificationResult(
                intent="algorithmic",
                action="respond",
                confidence=0.8,
                reasoning="Algorithmic keywords detected",
            )

        # ----------------
        # SYSTEM DESIGN
        # ----------------
        if any(k in text for k in (
            "design",
            "scalable",
            "architecture",
            "throughput",
            "latency",
            "distributed",
            "load",
        )):
            return ClassificationResult(
                intent="system_design",
                action="respond",
                confidence=0.75,
                reasoning="System design keywords detected",
            )

        # ----------------
        # CLARIFICATION
        # ----------------
        if any(k in text for k in (
            "clarify",
            "repeat",
            "can you explain",
            "what do you mean",
        )):
            return ClassificationResult(
                intent="clarification",
                action="wait",
                confidence=0.6,
                reasoning="Clarification request detected",
            )

        # ----------------
        # UNKNOWN
        # ----------------
        return ClassificationResult(
            intent="unknown",
            action="wait",
            confidence=0.3,
            reasoning="No strong signal detected",
        )
