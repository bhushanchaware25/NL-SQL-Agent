"""
ChromaDB Few-Shot Memory Store.

Stores (question, sql) pairs in a persistent ChromaDB collection.
At query time, retrieves the top-k most semantically similar examples
to inject into the SQL Generator prompt, improving generation accuracy
(RAG-style few-shot prompting).

Pre-seeded with 25 e-commerce example pairs on first startup.
"""
from __future__ import annotations

import uuid
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings as app_settings

# ── Collection name ───────────────────────────────────────────────────────────
COLLECTION_NAME = "nl2sql_few_shots"

# ── Pre-seeded e-commerce examples ───────────────────────────────────────────
SEED_EXAMPLES: List[Dict[str, str]] = [
    {
        "question": "Show me all customers from New York",
        "sql": "SELECT * FROM customers WHERE city = 'New York';",
    },
    {
        "question": "What are the top 5 best-selling products by revenue?",
        "sql": (
            "SELECT p.name, SUM(oi.quantity * oi.unit_price) AS revenue "
            "FROM order_items oi "
            "JOIN products p ON oi.product_id = p.id "
            "GROUP BY p.name "
            "ORDER BY revenue DESC "
            "LIMIT 5;"
        ),
    },
    {
        "question": "How many orders were placed last month?",
        "sql": (
            "SELECT COUNT(*) AS order_count "
            "FROM orders "
            "WHERE created_at >= date_trunc('month', NOW() - INTERVAL '1 month') "
            "  AND created_at < date_trunc('month', NOW());"
        ),
    },
    {
        "question": "What is the average order value?",
        "sql": "SELECT ROUND(AVG(total_amount), 2) AS avg_order_value FROM orders;",
    },
    {
        "question": "List products with a rating below 3",
        "sql": (
            "SELECT p.name, ROUND(AVG(r.rating), 2) AS avg_rating "
            "FROM reviews r "
            "JOIN products p ON r.product_id = p.id "
            "GROUP BY p.name "
            "HAVING AVG(r.rating) < 3 "
            "ORDER BY avg_rating;"
        ),
    },
    {
        "question": "Which customers have spent more than $1000 in total?",
        "sql": (
            "SELECT c.first_name, c.last_name, SUM(o.total_amount) AS total_spent "
            "FROM customers c "
            "JOIN orders o ON o.customer_id = c.id "
            "GROUP BY c.id, c.first_name, c.last_name "
            "HAVING SUM(o.total_amount) > 1000 "
            "ORDER BY total_spent DESC;"
        ),
    },
    {
        "question": "Show monthly revenue for the past 6 months",
        "sql": (
            "SELECT date_trunc('month', created_at) AS month, "
            "       SUM(total_amount) AS revenue "
            "FROM orders "
            "WHERE created_at >= NOW() - INTERVAL '6 months' "
            "GROUP BY month "
            "ORDER BY month;"
        ),
    },
    {
        "question": "What products are in the Electronics category?",
        "sql": (
            "SELECT p.name, p.price "
            "FROM products p "
            "JOIN categories c ON p.category_id = c.id "
            "WHERE c.name = 'Electronics' "
            "ORDER BY p.price DESC;"
        ),
    },
    {
        "question": "How many customers do we have per city?",
        "sql": (
            "SELECT city, COUNT(*) AS customer_count "
            "FROM customers "
            "GROUP BY city "
            "ORDER BY customer_count DESC;"
        ),
    },
    {
        "question": "What is the total revenue by category?",
        "sql": (
            "SELECT c.name AS category, SUM(oi.quantity * oi.unit_price) AS revenue "
            "FROM order_items oi "
            "JOIN products p ON oi.product_id = p.id "
            "JOIN categories c ON p.category_id = c.id "
            "GROUP BY c.name "
            "ORDER BY revenue DESC;"
        ),
    },
    {
        "question": "Find orders that were placed but never shipped",
        "sql": (
            "SELECT id, customer_id, total_amount, created_at "
            "FROM orders "
            "WHERE status = 'pending' "
            "ORDER BY created_at;"
        ),
    },
    {
        "question": "Which product has received the most reviews?",
        "sql": (
            "SELECT p.name, COUNT(r.id) AS review_count "
            "FROM reviews r "
            "JOIN products p ON r.product_id = p.id "
            "GROUP BY p.name "
            "ORDER BY review_count DESC "
            "LIMIT 1;"
        ),
    },
    {
        "question": "Show the 10 most recent orders with customer names",
        "sql": (
            "SELECT o.id, c.first_name || ' ' || c.last_name AS customer, "
            "       o.total_amount, o.status, o.created_at "
            "FROM orders o "
            "JOIN customers c ON o.customer_id = c.id "
            "ORDER BY o.created_at DESC "
            "LIMIT 10;"
        ),
    },
    {
        "question": "What is the most popular payment method?",
        "sql": (
            "SELECT payment_method, COUNT(*) AS usage_count "
            "FROM orders "
            "GROUP BY payment_method "
            "ORDER BY usage_count DESC "
            "LIMIT 1;"
        ),
    },
    {
        "question": "List customers who haven't placed any orders",
        "sql": (
            "SELECT c.first_name, c.last_name, c.email "
            "FROM customers c "
            "LEFT JOIN orders o ON o.customer_id = c.id "
            "WHERE o.id IS NULL;"
        ),
    },
    {
        "question": "What is the average product price per category?",
        "sql": (
            "SELECT c.name AS category, ROUND(AVG(p.price), 2) AS avg_price "
            "FROM products p "
            "JOIN categories c ON p.category_id = c.id "
            "GROUP BY c.name "
            "ORDER BY avg_price DESC;"
        ),
    },
    {
        "question": "Show total number of products per category",
        "sql": (
            "SELECT c.name AS category, COUNT(p.id) AS product_count "
            "FROM products p "
            "JOIN categories c ON p.category_id = c.id "
            "GROUP BY c.name "
            "ORDER BY product_count DESC;"
        ),
    },
    {
        "question": "Which day of the week has the highest order volume?",
        "sql": (
            "SELECT TO_CHAR(created_at, 'Day') AS day_of_week, COUNT(*) AS orders "
            "FROM orders "
            "GROUP BY TO_CHAR(created_at, 'Day'), EXTRACT(DOW FROM created_at) "
            "ORDER BY EXTRACT(DOW FROM created_at);"
        ),
    },
    {
        "question": "Find all products that are out of stock",
        "sql": "SELECT name, price FROM products WHERE stock_quantity = 0;",
    },
    {
        "question": "What is the highest rated product?",
        "sql": (
            "SELECT p.name, ROUND(AVG(r.rating), 2) AS avg_rating "
            "FROM reviews r "
            "JOIN products p ON r.product_id = p.id "
            "GROUP BY p.name "
            "ORDER BY avg_rating DESC "
            "LIMIT 1;"
        ),
    },
]


# ── Store class ───────────────────────────────────────────────────────────────

class FewShotStore:
    """ChromaDB-backed few-shot example store."""

    def __init__(self, persist_dir: Optional[str] = None) -> None:
        _dir = persist_dir or app_settings.chroma_persist_dir
        self._client = chromadb.PersistentClient(
            path=_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self._seed_if_empty()

    # ── Public methods ────────────────────────────────────────────────────────

    def add_example(self, question: str, sql: str) -> None:
        """Persist a new (question, sql) pair for future retrieval."""
        self._collection.add(
            ids=[str(uuid.uuid4())],
            documents=[question],
            metadatas=[{"sql": sql}],
        )

    def retrieve_similar(self, question: str, k: int = 3) -> List[Dict[str, str]]:
        """
        Return the top-k most similar (question, sql) pairs.

        Args:
            question: The user's natural language question.
            k: Number of examples to retrieve.

        Returns:
            List of dicts: [{"question": ..., "sql": ...}, ...]
        """
        count = self._collection.count()
        if count == 0:
            return []

        results = self._collection.query(
            query_texts=[question],
            n_results=min(k, count),
            include=["documents", "metadatas"],
        )

        examples = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        for doc, meta in zip(docs, metas):
            examples.append({"question": doc, "sql": meta.get("sql", "")})
        return examples

    def count(self) -> int:
        """Return total number of stored examples."""
        return self._collection.count()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _seed_if_empty(self) -> None:
        """Populate the store with seed examples if it is empty."""
        if self._collection.count() == 0:
            ids = [str(uuid.uuid4()) for _ in SEED_EXAMPLES]
            documents = [ex["question"] for ex in SEED_EXAMPLES]
            metadatas = [{"sql": ex["sql"]} for ex in SEED_EXAMPLES]
            self._collection.add(ids=ids, documents=documents, metadatas=metadatas)


# ── Module-level singleton ────────────────────────────────────────────────────

_store: Optional[FewShotStore] = None


def get_store() -> FewShotStore:
    """Return a module-level singleton FewShotStore."""
    global _store
    if _store is None:
        _store = FewShotStore()
    return _store
