"""
Semantic Clustering - Vector-based comment grouping

Solves the noise problem by:
1. VECTORIZE: Convert comments to embeddings
2. CLUSTER: Find density clouds with DBSCAN
3. EXTRACT: Pick representative comment per cluster
"""

import os
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter

# Lazy imports for heavy libraries
_model = None
_clustering_available = False


def _load_embedding_model():
    """Lazy load sentence transformers model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, good quality
        except ImportError:
            print("Warning: sentence-transformers not installed. Using fallback.")
            _model = "fallback"
    return _model


def _check_clustering():
    """Check if sklearn is available."""
    global _clustering_available
    try:
        from sklearn.cluster import DBSCAN
        from sklearn.metrics.pairwise import cosine_distances
        _clustering_available = True
    except ImportError:
        _clustering_available = False
    return _clustering_available


# ============================================
# VECTORIZE: Convert to embeddings
# ============================================

def vectorize_comments(comments: List[Dict], model: Any = None) -> Tuple[np.ndarray, List[str]]:
    """
    Convert comment texts to vector embeddings.
    
    Args:
        comments: List of comment dicts
        model: Optional pre-loaded SentenceTransformer model
    
    Returns:
        (embeddings array, list of texts)
    """
    if model is None:
        model = _load_embedding_model()
    
    # Extract texts
    texts = [c.get('text', '')[:500] if isinstance(c, dict) else str(c)[:500] for c in comments]
    
    if model == "fallback":
        # Simple TF-IDF like fallback
        return _fallback_vectorize(texts), texts
    
    # Use sentence transformers
    embeddings = model.encode(texts, show_progress_bar=False)
    return np.array(embeddings), texts


def _fallback_vectorize(texts: List[str]) -> np.ndarray:
    """Simple bag-of-words fallback if sentence-transformers unavailable."""
    from collections import Counter
    import re
    
    # Build vocabulary
    all_words = []
    for text in texts:
        words = re.findall(r'\b\w+\b', text.lower())
        all_words.extend(words)
    
    vocab = list(set(all_words))[:1000]  # Limit vocab size
    word_to_idx = {w: i for i, w in enumerate(vocab)}
    
    # Create simple vectors
    vectors = []
    for text in texts:
        words = re.findall(r'\b\w+\b', text.lower())
        vec = np.zeros(len(vocab))
        for w in words:
            if w in word_to_idx:
                vec[word_to_idx[w]] += 1
        # Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        vectors.append(vec)
    
    return np.array(vectors)


# ============================================
# CLUSTER: Find density clouds
# ============================================

def cluster_embeddings(
    embeddings: np.ndarray,
    eps: float = 0.3,
    min_samples: int = 3
) -> np.ndarray:
    """
    Cluster embeddings using DBSCAN.
    
    Args:
        embeddings: Vector embeddings
        eps: Maximum distance between samples in cluster
        min_samples: Minimum samples to form a cluster
    
    Returns:
        Cluster labels (-1 = noise/outlier)
    """
    if not _check_clustering():
        # Fallback: no clustering
        return np.zeros(len(embeddings))
    
    from sklearn.cluster import DBSCAN
    from sklearn.metrics.pairwise import cosine_distances
    
    # Use cosine distance for text similarity
    distances = cosine_distances(embeddings)
    
    # DBSCAN clustering
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
    labels = clustering.fit_predict(distances)
    
    return labels


# ============================================
# EXTRACT: Get representative per cluster
# ============================================

def extract_centroids(
    embeddings: np.ndarray,
    labels: np.ndarray,
    texts: List[str],
    comments: List[Dict]
) -> List[Dict[str, Any]]:
    """
    Find the most representative comment for each cluster.
    
    Returns:
        List of cluster summaries with:
        - cluster_id
        - size (number of similar comments)
        - representative (centroid comment)
        - sample_texts
    """
    clusters = []
    unique_labels = set(labels)
    
    for label in unique_labels:
        if label == -1:
            continue  # Skip noise
        
        # Get all comments in this cluster
        mask = labels == label
        cluster_embeddings = embeddings[mask]
        cluster_texts = [texts[i] for i, m in enumerate(mask) if m]
        cluster_comments = [comments[i] for i, m in enumerate(mask) if m]
        
        if len(cluster_embeddings) == 0:
            continue
        
        # Find centroid (most representative)
        centroid = cluster_embeddings.mean(axis=0)
        
        # Find comment closest to centroid
        distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
        centroid_idx = np.argmin(distances)
        
        representative = cluster_texts[centroid_idx]
        rep_comment = cluster_comments[centroid_idx]
        
        # Get total votes in cluster
        def parse_votes(v):
            try:
                v = str(v).lower().strip()
                if 'k' in v:
                    return int(float(v.replace('k', '')) * 1000)
                if 'm' in v:
                    return int(float(v.replace('m', '')) * 1000000)
                return int(float(v))
            except:
                return 0
        
        total_votes = sum(
            parse_votes(c.get('votes', '0')) if isinstance(c, dict) else 0 
            for c in cluster_comments
        )
        
        clusters.append({
            'cluster_id': int(label),
            'size': len(cluster_texts),
            'representative': representative[:200],
            'sample_comments': cluster_texts[:3],
            'total_votes': total_votes,
            'avg_length': int(np.mean([len(t) for t in cluster_texts]))
        })
    
    # Sort by size (largest clusters first)
    clusters.sort(key=lambda x: x['size'], reverse=True)
    
    return clusters


# ============================================
# NOISE STATS: Analyze outliers
# ============================================

def analyze_noise(
    labels: np.ndarray,
    texts: List[str],
    comments: List[Dict]
) -> Dict[str, Any]:
    """Analyze comments that didn't fit into any cluster."""
    noise_mask = labels == -1
    noise_texts = [texts[i] for i, m in enumerate(noise_mask) if m]
    noise_comments = [comments[i] for i, m in enumerate(noise_mask) if m]
    
    return {
        'noise_count': len(noise_texts),
        'sample_noise': noise_texts[:5],
        'noise_percentage': round(len(noise_texts) / len(texts) * 100, 1) if texts else 0
    }


# ============================================
# ORCHESTRATOR: Full clustering pipeline
# ============================================

def semantic_cluster_analysis(
    comments: List[Dict],
    eps: float = 0.35,
    min_samples: int = 3,
    model: Any = None
) -> Dict[str, Any]:
    """
    Full semantic clustering pipeline.
    
    Args:
        comments: List of comment dicts
        eps: DBSCAN epsilon (lower = tighter clusters)
        min_samples: Minimum cluster size
        model: Optional pre-loaded SentenceTransformer model
    
    Returns:
        {
            'clusters': [...],
            'noise': {...},
            'summary': "X comments → Y clusters"
        }
    """
    if len(comments) < 5:
        return {
            'status': 'skipped',
            'reason': 'Too few comments for clustering',
            'clusters': [],
            'noise': {'noise_count': len(comments)}
        }
    
    print(f"🔮 Semantic Clustering: {len(comments)} comments...")
    
    # Step 1: Vectorize
    print("  → Vectorizing comments...")
    embeddings, texts = vectorize_comments(comments, model=model)
    
    # Step 2: Cluster
    print("  → Finding density clouds...")
    labels = cluster_embeddings(embeddings, eps=eps, min_samples=min_samples)
    
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    print(f"  → Found {n_clusters} clusters")
    
    # Step 3: Extract centroids
    print("  → Extracting representatives...")
    clusters = extract_centroids(embeddings, labels, texts, comments)
    
    # Step 4: Analyze noise
    noise = analyze_noise(labels, texts, comments)
    
    # Generate summary
    total_clustered = sum(c['size'] for c in clusters)
    summary = f"{len(comments)} comments → {n_clusters} clusters ({total_clustered} clustered, {noise['noise_count']} unique)"
    
    print(f"✅ {summary}")
    
    return {
        'status': 'success',
        'total_comments': len(comments),
        'clusters': clusters,
        'cluster_count': n_clusters,
        'noise': noise,
        'summary': summary,
        'config': {'eps': eps, 'min_samples': min_samples}
    }


def get_top_clusters(result: Dict, n: int = 5) -> List[Dict]:
    """Get top N clusters by size."""
    return result.get('clusters', [])[:n]


def format_clusters_for_display(clusters: List[Dict]) -> str:
    """Format clusters for human-readable display."""
    lines = []
    for i, c in enumerate(clusters[:10]):
        lines.append(f"**Cluster {i+1}** ({c['size']} comments)")
        lines.append(f"  \"{c['representative'][:100]}...\"")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    # Test
    test_comments = [
        {"text": "The battery drains so fast"},
        {"text": "Battery life is terrible"},
        {"text": "Power runs out quickly"},
        {"text": "Great camera quality!"},
        {"text": "Camera is amazing"},
        {"text": "Photos look incredible"},
        {"text": "Random unique comment"},
    ]
    
    result = semantic_cluster_analysis(test_comments, min_samples=2)
    print(f"\nClusters found: {result['cluster_count']}")
    for c in result['clusters']:
        print(f"  - {c['representative'][:50]}... ({c['size']} similar)")
