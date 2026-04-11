import time
import numpy as np
from ollama_client import OllamaClient
from config import EMBEDDING_MODEL
from menu import menu

# Define a list of popular embedding models for the menu
# These are common ones from the Ollama library
model_options = {
    "nomic-embed-text:latest": "Nomic Embed Text (High Quality)",
    "mxbai-embed-large:latest": "mxbai Embed Large",
    "all-minilm:latest": "All MiniLM L6",
    "snowflake-arctic-embed:latest": "Snowflake Arctic Embed",
    "bge-m3:latest": "BGE-M3 (Multilingual)",
    "embeddinggemma:300m": "embeddinggemma 300m",
    "qwen3-embedding:0.6b": "qwen3-embedding 0.6b"
}


class EmbeddingResearcher:
    def __init__(self, model_name):
        # We pass the chosen model name to OllamaClient
        self.ai = OllamaClient(embed_model=model_name)
        self.total_embedding_time = 0.0
        self.embedding_call_count = 0

    def get_embedding(self, text):
        start_time = time.perf_counter()
        result = np.array(self.ai.get_embedding(text), dtype=np.float32)
        end_time = time.perf_counter()
        self.total_embedding_time += (end_time - start_time)
        self.embedding_call_count += 1
        return result

    def calculate_l2(self, v1, v2):
        return np.linalg.norm(v1 - v2)

    def calculate_cosine_distance(self, v1, v2):
        # Cosine distance = 1 - Cosine Similarity
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 1.0
        similarity = np.dot(v1, v2) / (norm1 * norm2)
        return 1.0 - similarity

    def run_pairwise_test(self, test_cases):
        """
        test_cases: List of tuples (text1, text2, relation_type)
        """
        print(f"\n{'Text 1':<40} | {'Text 2':<40} | {'L2':<10} | {'Cosine':<10} | {'Relation'}")
        print("-" * 110)

        results = []
        for t1, t2, rel in test_cases:
            v1 = self.get_embedding(t1)
            v2 = self.get_embedding(t2)

            l2 = self.calculate_l2(v1, v2)
            cos = self.calculate_cosine_distance(v1, v2)

            print(f"{t1[:38]:<40} | {t2[:38]:<40} | {l2:<10.4f} | {cos:<10.4f} | {rel}")
            results.append({'l2': l2, 'cos': cos, 'rel': rel})

        return results

    def analyze_vector_lengths(self, test_cases):
        """
        Analyzes and prints the L2 norms (lengths) of vectors to check if normalization is needed.
        """
        print("\n--- Vector Magnitude Analysis (L2 Norms) ---")
        print(f"{'Text':<50} | {'L2 Length':<15}")
        print("-" * 65)

        lengths = []
        # Use a unique set of all texts from test cases to avoid duplicates
        unique_texts = set()
        for t1, t2, _ in test_cases:
            unique_texts.add(t1)
            unique_texts.add(t2)

        for text in sorted(list(unique_texts)):
            v = self.get_embedding(text)
            length = np.linalg.norm(v)
            lengths.append(length)
            print(f"{text[:48]:<50} | {length:<15.4f}")

        if lengths:
            print("-" * 65)
            print(f"Min length: {min(lengths):.4f}")
            print(f"Max length: {max(lengths):.4f}")
            print(f"Average length: {np.mean(lengths):.4f}")
            print(f"Std Dev: {np.std(lengths):.4f}")
        print("")

    def calculate_aggregate_score(self, results):
        """
        Calculates an aggregate Embedding Quality Score (EQS) from 0 to 100.

        The score measures:
        - Discrimination: How well positives (Strong/Synonym) are separated from negatives (Unrelated)
        - Ranking: Whether distances correlate with semantic relation strength
        - Calibration: Whether absolute distance values make sense

        Returns dict with detailed metrics and overall score.
        """
        # Define relation weights (expected semantic closeness, 1.0 = identical)
        relation_weights = {
            'Strong': 1.0,
            'Synonym': 0.9,
            'Related': 0.5,
            'Somewhat': 0.3,
            'Unrelated': 0.0
        }

        # Collect distances by category
        positives = [r['cos'] for r in results if r['rel'] in ['Strong', 'Synonym']]
        negatives = [r['cos'] for r in results if r['rel'] == 'Unrelated']
        all_distances = [(r['cos'], relation_weights.get(r['rel'], 0.5)) for r in results]

        if len(positives) < 2 or len(negatives) < 2:
            print("\nNot enough data to calculate aggregate score (need at least 2 positives and 2 negatives).")
            return None

        # 1. SEPARATION SCORE (0-40 points)
        # Measures how well positive and negative distributions are separated
        pos_mean = np.mean(positives)
        pos_std = np.std(positives)
        neg_mean = np.mean(negatives)
        neg_std = np.std(negatives)

        # Cohen's d effect size (larger = better separation)
        pooled_std = np.sqrt((pos_std**2 + neg_std**2) / 2)
        cohens_d = (neg_mean - pos_mean) / pooled_std if pooled_std > 0 else 0

        # Separation score: 0-40 based on Cohen's d
        # d=4.0 gives max score (very well separated distributions)
        separation_score = min(40, max(0, cohens_d * 10))

        # 2. RANKING SCORE (0-35 points)
        # Measures correlation between distance and expected semantic closeness
        distances = [d for d, _ in all_distances]
        weights = [w for _, w in all_distances]

        # Calculate Spearman rank correlation
        from scipy import stats
        if len(set(distances)) > 1 and len(set(weights)) > 1:
            correlation, pvalue = stats.spearmanr(distances, weights)
            correlation = -correlation  # Invert because higher weight = lower distance expected
            ranking_score = min(35, max(0, correlation * 35))
        else:
            ranking_score = 0
            correlation = 0

        # 3. DISCRIMINATION SCORE (0-25 points)
        # Measures ability to correctly classify with optimal threshold
        # Calculate ROC AUC-like metric
        correctly_ordered = 0
        total_pairs = 0
        for pos_dist in positives:
            for neg_dist in negatives:
                total_pairs += 1
                if pos_dist < neg_dist:  # Positive should have smaller distance
                    correctly_ordered += 1

        auc_estimate = correctly_ordered / total_pairs if total_pairs > 0 else 0.5
        discrimination_score = auc_estimate * 25

        # 4. OVERLAP PENALTY (0 to -20 points)
        # Penalize if distributions overlap significantly
        overlap_count = sum(1 for p in positives for n in negatives if abs(p - n) < 0.1)
        total_possible = len(positives) * len(negatives)
        overlap_ratio = overlap_count / total_possible if total_possible > 0 else 0
        overlap_penalty = -int(overlap_ratio * 20)

        # 5. CALIBRATION BONUS (0 to 10 points)
        # Bonus if positive pairs are very close (cosine < 0.2) and negatives are far (cosine > 0.5)
        calibration_bonus = 0
        if pos_mean < 0.2:
            calibration_bonus += 5
        if neg_mean > 0.5:
            calibration_bonus += 5

        # Calculate final score
        total_score = separation_score + ranking_score + discrimination_score + overlap_penalty + calibration_bonus
        total_score = min(100, max(0, total_score))

        return {
            'total_score': total_score,
            'separation': separation_score,
            'ranking': ranking_score,
            'discrimination': discrimination_score,
            'overlap_penalty': overlap_penalty,
            'calibration_bonus': calibration_bonus,
            'cohens_d': cohens_d,
            'correlation': correlation,
            'auc_estimate': auc_estimate,
            'pos_mean': pos_mean,
            'neg_mean': neg_mean
        }

    def print_speed_report(self, texts_processed):
        """
        Prints embedding generation speed statistics.
        """
        if self.embedding_call_count == 0 or self.total_embedding_time == 0:
            return

        print("\n--- Embedding Speed Statistics ---")
        print(f"  Total API calls:        {self.embedding_call_count}")
        print(f"  Total time:               {self.total_embedding_time:.3f}s")
        print(f"  Average time per call:    {(self.total_embedding_time / self.embedding_call_count) * 1000:.2f}ms")
        print(f"  Embeddings per second:    {self.embedding_call_count / self.total_embedding_time:.2f}")
        if len(texts_processed) > 0:
            # Estimate tokens (rough approximation: 1 token ≈ 4 characters for Latin, 1-2 for Cyrillic)
            # Using a conservative estimate of 3 chars per token average
            estimated_tokens = sum(len(t) for t in texts_processed) / 3
            print(f"  Estimated tokens:         {estimated_tokens:.0f}")
            print(f"  Tokens per second:        {estimated_tokens / self.total_embedding_time:.0f}")

    def print_aggregate_report(self, results):
        """
        Prints a comprehensive aggregate score report.
        """
        metrics = self.calculate_aggregate_score(results)
        if not metrics:
            return

        print("\n" + "=" * 70)
        print("EMBEDDING QUALITY REPORT")
        print("=" * 70)

        # Overall score with visual bar
        score = metrics['total_score']
        bar_length = 50
        filled = int(score / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        # Grade
        if score >= 90:
            grade = "EXCELLENT"
            color = "🟢"
        elif score >= 70:
            grade = "GOOD"
            color = "🟡"
        elif score >= 50:
            grade = "FAIR"
            color = "🟠"
        else:
            grade = "POOR"
            color = "🔴"

        print(f"\n{color} OVERALL SCORE: {score:.1f}/100 [{grade}]")
        print(f"   [{bar}]")

        print("\n--- Component Breakdown ---")
        print(f"  Separation Score:      {metrics['separation']:.1f}/40  (Cohen's d: {metrics['cohens_d']:.2f})")
        print(f"  Ranking Score:         {metrics['ranking']:.1f}/35  (Correlation: {metrics['correlation']:.2f})")
        print(f"  Discrimination Score:  {metrics['discrimination']:.1f}/25  (AUC estimate: {metrics['auc_estimate']:.2f})")
        print(f"  Calibration Bonus:    +{metrics['calibration_bonus']:.1f}/10")
        print(f"  Overlap Penalty:       {metrics['overlap_penalty']:.1f}")

        print("\n--- Distribution Stats ---")
        print(f"  Positive pairs (Strong/Synonym): mean={metrics['pos_mean']:.4f}")
        print(f"  Negative pairs (Unrelated):      mean={metrics['neg_mean']:.4f}")
        print(f"  Gap between means:               {metrics['neg_mean'] - metrics['pos_mean']:.4f}")

        print("\n--- Interpretation ---")
        if score >= 80:
            print("  ✓ Model discriminates well between similar and dissimilar texts")
            print("  ✓ Distances correlate strongly with semantic relationships")
            print("  ✓ Suitable for semantic search and clustering")
        elif score >= 60:
            print("  ~ Model shows reasonable discrimination")
            print("  ~ Some overlap between similar/dissimilar pairs")
            print("  ~ May need threshold tuning for production use")
        else:
            print("  ✗ Poor discrimination between similar and dissimilar texts")
            print("  ✗ Consider using a different embedding model")
            print("  ✗ Check if the model is properly loaded in Ollama")

        print("=" * 70)

    def suggest_thresholds(self, results):
        """
        Analyzes results to suggest a cut-off for L2 and Cosine.
        """
        positives = [r['l2'] for r in results if r['rel'] in ['Strong', 'Synonym']]
        negatives = [r['l2'] for r in results if r['rel'] == 'Unrelated']

        if not positives or not negatives:
            print("\nNot enough data to suggest thresholds.")
            return

        max_pos = max(positives)
        min_neg = min(negatives)

        print("\n--- Threshold Analysis (L2) ---")
        print(f"Max distance for strong positives: {max_pos:.4f}")
        print(f"Min distance for unrelated: {min_neg:.4f}")
        print(f"Suggested L2 Threshold: { (max_pos + min_neg) / 2:.4f}")

def main():

    print("\n--- Select Embedding Model for Research ---")
    selected_model = menu(model_options)

    if not selected_model:
        print("No model selected. Exiting.")
        return

    researcher = EmbeddingResearcher(selected_model)

    # Test set: (Text 1, Text 2, Relation)
    test_cases = [
        # Strong / Synonyms
        ("Как приготовить пиццу", "Рецепт приготовления пиццы", "Strong"),
        ("Инструкция по установке Linux", "Как установить Линукс на компьютер", "Strong"),
        ("Вася", "Телефон Васи +123457674", "Strong"),
        ("Телефон Васи", "Телефон Васи +123457674", "Strong"),
        ("Номер телефона", "Телефон Васи +123457674", "Strong"),
        ("Кот сидит на коврике", "Кошка находится на коврике", "Synonym"),

        # Long variations of "Strong"
        ("Как приготовить классическую итальянскую пиццу в домашних условиях с использованием традиционной печи", "Пошаговое руководство по приготовлению настоящей пиццы из Италии с правильным тестом и начинкой", "Strong"),
        ("Linux", "Операционная система Линукс", "Strong"),

        # Thematically Related (Weak)
        ("Рецепт пиццы", "Итальянская паста", "Related"),
        ("Программирование на Python", "Разработка на JavaScript", "Related"),
        ("Я люблю готовить еду", "Вчера я купил новую сковороду и решил попробовать приготовить что-то необычное на ужин", "Related"),
        ("Python", "pip install package", "Related"),
        ("Вася", "Маша", "Somewhat"),

        # Unrelated
        ("Рецепт пиццы", "Квантовая физика и черные дыры", "Unrelated"),
        ("Как установить Linux", "История Древнего Рима", "Unrelated"),
        ("Погода в Москве", "Свойства золотого сечения", "Unrelated"),
        ("Краткий ответ", "Это очень длинное предложение, которое описывает совершенно разные вещи, чтобы проверить, как модель справляется с разным объемом текста в одном запросе", "Unrelated"),
    ]

    print(f"\nUsing model: {selected_model}")
    researcher.analyze_vector_lengths(test_cases)
    results = researcher.run_pairwise_test(test_cases)
    researcher.suggest_thresholds(results)
    researcher.print_aggregate_report(results)

    # Collect unique texts for speed report
    unique_texts = set()
    for t1, t2, _ in test_cases:
        unique_texts.add(t1)
        unique_texts.add(t2)
    researcher.print_speed_report(unique_texts)

if __name__ == "__main__":
    main()
