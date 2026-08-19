
"""
Bonus feature: Duplicate Complaint Detection.

Uses lightweight TF-IDF cosine similarity against previously committed
complaints. PostgreSQL remains the source of truth; this class is only
an in-memory working representation for comparison.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


SIMILARITY_THRESHOLD = 0.55


@dataclass
class CommittedComplaint:
    complaint_id: str
    product_name: str
    batch_number: Optional[str]
    complaint_description: str


class DuplicateComplaintStore:
    """In-memory working store for duplicate complaint comparison."""

    def __init__(self):
        self._items: List[CommittedComplaint] = []

    def add(self, complaint: CommittedComplaint):
        self._items.append(complaint)

    def load_from_records(
        self,
        records: List[Tuple[str, Optional[str], str, str]],
    ):
        """
        Replace the in-memory store with complaints loaded from PostgreSQL.

        PostgreSQL is the source of truth. This store is only a temporary
        representation used during duplicate comparison.
        """
        self._items = [
            CommittedComplaint(
                complaint_id=complaint_id,
                product_name=product_name or "",
                batch_number=batch_number,
                complaint_description=complaint_description or "",
            )
            for (
                complaint_id,
                product_name,
                batch_number,
                complaint_description,
            ) in records
        ]

    def check_duplicate(
        self,
        product_name: str,
        complaint_description: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Return whether the complaint is sufficiently similar to a
        previously committed complaint.
        """
        if not self._items or not complaint_description:
            return False, None

        corpus = [
            f"{c.product_name} {c.complaint_description}"
            for c in self._items
        ]

        query = f"{product_name or ''} {complaint_description}"

        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(corpus + [query])

        sims = cosine_similarity(
            matrix[-1],
            matrix[:-1],
        ).flatten()

        best_idx = sims.argmax()

        if sims[best_idx] >= SIMILARITY_THRESHOLD:
            match = self._items[best_idx]

            note = (
                f"Similar to a previously logged complaint for "
                f"{match.product_name} "
                f"(batch {match.batch_number or 'unknown'}), "
                f"similarity {sims[best_idx]:.2f}. "
                f"Consider linking as a recurring issue."
            )

            return True, note

        return False, None


# Module-level singleton.
duplicate_store = DuplicateComplaintStore()