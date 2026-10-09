from sentence_transformers import SentenceTransformer, util

from playbook_loader import load_playbook


MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_THRESHOLD = 0.50


class SemanticMatcher:
    """
    Matches contract clauses to relevant playbook rules
    using Sentence Transformers and clause category.
    """

    def __init__(self, model_name=MODEL_NAME):
        print(f"Loading embedding model: {model_name}")

        self.model = SentenceTransformer(model_name)
        self.rules = load_playbook()

        self.rule_texts = [
            self._build_rule_text(rule)
            for rule in self.rules
        ]

        self.rule_embeddings = self.model.encode(
            self.rule_texts,
            convert_to_tensor=True
        )

    @staticmethod
    def _build_rule_text(rule):
        """
        Combine important playbook fields into text
        for semantic matching.
        """

        return (
            f"Category: {rule['category']}. "
            f"Requirement: {rule['requirement']}. "
            f"Description: {rule['description']}"
        )

    @staticmethod
    def _normalize_category(category):
        """
        Convert category names into a consistent format.

        Example:
            Intellectual Property
            -> INTELLECTUAL_PROPERTY
        """

        return (
            category
            .strip()
            .upper()
            .replace(" ", "_")
        )

    def match_clause(
        self,
        clause,
        top_k=3,
        threshold=DEFAULT_THRESHOLD
    ):
        """
        Find the most relevant playbook rules for a contract clause.

        Matching uses:

        1. Semantic similarity
        2. Clause category

        If the clause category is known, a rule from a
        different category cannot be marked as matched.

        Expected clause:

        {
            "section": "2",
            "clause_type": "Termination",
            "page": 2,
            "text": "Either party may terminate..."
        }
        """

        clause_text = clause["text"]

        clause_category = self._normalize_category(
            clause.get("clause_type", "Other")
        )

        clause_embedding = self.model.encode(
            clause_text,
            convert_to_tensor=True
        )

        scores = util.cos_sim(
            clause_embedding,
            self.rule_embeddings
        )[0]

        candidate_results = []

        for index, score in enumerate(scores):

            rule = self.rules[index]

            similarity_score = round(
                float(score),
                4
            )

            rule_category = self._normalize_category(
                rule["category"]
            )

            category_match = (
                clause_category != "OTHER"
                and clause_category == rule_category
            )

            # Start with the original semantic score.
            adjusted_score = similarity_score

            # Give a small boost when the clause category
            # matches the playbook category.
            if category_match:
                adjusted_score = round(
                    min(similarity_score + 0.15, 1.0),
                    4
                )

            # Decide whether the rule is actually matched.
            if category_match:
                match_reason = "semantic + category"
                matched = adjusted_score >= threshold

            elif clause_category != "OTHER":
                # Known clause category but different
                # playbook category = NOT a match.
                match_reason = "category mismatch"
                matched = False

            else:
                # Unknown clause category.
                # Fall back to semantic similarity.
                match_reason = "semantic"
                matched = adjusted_score >= threshold

            candidate_results.append(
                {
                    "rule_id": rule["rule_id"],
                    "category": rule["category"],
                    "requirement": rule["requirement"],
                    "severity": rule["severity"],
                    "similarity_score": similarity_score,
                    "adjusted_score": adjusted_score,
                    "category_match": category_match,
                    "matched": matched,
                    "match_reason": match_reason
                }
            )

        # Sort by adjusted score.
        candidate_results.sort(
            key=lambda result: result["adjusted_score"],
            reverse=True
        )

        return candidate_results[:top_k]


if __name__ == "__main__":

    matcher = SemanticMatcher()

    test_clauses = [
        {
            "section": "1",
            "clause_type": "Payment",
            "page": 1,
            "text": (
                "The Customer shall pay the Supplier "
                "within 30 days of receiving an invoice."
            )
        },
        {
            "section": "2",
            "clause_type": "Termination",
            "page": 2,
            "text": (
                "Either party may terminate this agreement "
                "by providing 30 days written notice."
            )
        }
    ]

    for test_clause in test_clauses:

        print("\n" + "=" * 60)

        print(
            f"Testing section {test_clause['section']} "
            f"({test_clause['clause_type']})"
        )

        print("=" * 60)

        results = matcher.match_clause(
            test_clause,
            top_k=3
        )

        for result in results:

            print(
                f"{result['rule_id']} | "
                f"{result['category']} | "
                f"Similarity: {result['similarity_score']} | "
                f"Adjusted: {result['adjusted_score']} | "
                f"Category Match: {result['category_match']} | "
                f"Matched: {result['matched']} | "
                f"Reason: {result['match_reason']}"
            )