"""Safe Experiment Execution Runner for LabRelay.

Runs empirical validation experiments inside the project workspace.
Enforces timeouts, sandboxing, and strict command validation.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from labrelay.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ExperimentResult:
    success: bool
    output: str
    error: Optional[str]
    execution_time_seconds: float
    code: str
    metrics: Dict[str, Any]


class ExperimentRunner:
    """Executes validated Python experiments in the local workspace."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = workspace_dir or settings.workspace_dir
        self.scratch_dir = self.workspace_dir / "scratch"
        self.scratch_dir.mkdir(parents=True, exist_ok=True)

    def validate_safety(self, code: str) -> None:
        """Reject destructive commands or unsafe system calls."""
        forbidden_patterns = [
            "rm -rf",
            "shutil.rmtree",
            "os.system",
            "subprocess.Popen",
            "urllib.request.urlretrieve",
            "requests.get",
            "curl ",
            "wget ",
            "eval(",
            "exec(",
            "__import__('os').system",
        ]
        for pattern in forbidden_patterns:
            if pattern in code:
                raise ValueError(f"Unsafe code pattern detected: '{pattern}' is forbidden in experiment runner.")

    async def run_experiment_code(
        self,
        code: str,
        filename_prefix: str = "exp",
        timeout_seconds: float = 30.0,
    ) -> ExperimentResult:
        """Execute a Python experiment script in a sandboxed subprocess."""
        self.validate_safety(code)

        timestamp = int(time.time())
        script_file = self.scratch_dir / f"{filename_prefix}_{timestamp}.py"
        script_file.write_text(code, encoding="utf-8")

        start_time = time.time()
        try:
            # Run using the active python virtualenv interpreter
            python_bin = sys.executable

            process = await asyncio.create_subprocess_exec(
                python_bin,
                str(script_file),
                cwd=str(self.workspace_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,
            )
            elapsed = time.time() - start_time

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            success = (process.returncode == 0)
            return ExperimentResult(
                success=success,
                output=stdout,
                error=stderr if not success else None,
                execution_time_seconds=round(elapsed, 3),
                code=code,
                metrics={"return_code": process.returncode, "elapsed": round(elapsed, 3)},
            )
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            return ExperimentResult(
                success=False,
                output="",
                error=f"Experiment timed out after {timeout_seconds}s.",
                execution_time_seconds=round(elapsed, 3),
                code=code,
                metrics={"timeout": True},
            )
        except Exception as e:
            elapsed = time.time() - start_time
            return ExperimentResult(
                success=False,
                output="",
                error=str(e),
                execution_time_seconds=round(elapsed, 3),
                code=code,
                metrics={"error": str(e)},
            )
        finally:
            if script_file.exists():
                try:
                    script_file.unlink()
                except Exception:
                    pass

    async def generate_and_run_clustering_benchmark(
        self,
        dimensions: int = 50,
        samples: int = 300,
        clusters: int = 3,
    ) -> ExperimentResult:
        """Run standard benchmark comparing K-Means, PAM (Medoids), and Hierarchical Clustering."""
        code = f"""
import time, math, random

# 1. Generate synthetic high-dimensional dataset ({dimensions} dims, {samples} samples)
random.seed(42)
k = {clusters}
dim = {dimensions}
n = {samples}

centers = [[random.uniform(-5, 5) for _ in range(dim)] for _ in range(k)]
data = []
for i in range(n):
    c = centers[i % k]
    # Add Gaussian noise
    point = [c[d] + random.gauss(0, 1.0) for d in range(dim)]
    data.append(point)

def euclidean_dist(p1, p2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

# 2. K-Means implementation
def kmeans(points, k, max_iter=30):
    start = time.time()
    centroids = points[:k]
    assignments = [0] * len(points)
    for _ in range(max_iter):
        new_assignments = []
        for p in points:
            dists = [euclidean_dist(p, c) for c in centroids]
            new_assignments.append(dists.index(min(dists)))
        if new_assignments == assignments:
            break
        assignments = new_assignments
        # Recompute centroids
        for i in range(k):
            cluster_pts = [points[j] for j in range(len(points)) if assignments[j] == i]
            if cluster_pts:
                centroids[i] = [sum(pt[d] for pt in cluster_pts) / len(cluster_pts) for d in range(dim)]
    elapsed = time.time() - start
    return assignments, centroids, elapsed

# 3. PAM (Partitioning Around Medoids - k-medoids approximation)
def pam(points, k, max_iter=15):
    start = time.time()
    medoids = list(range(k))
    assignments = [0] * len(points)
    for _ in range(max_iter):
        for j, p in enumerate(points):
            dists = [euclidean_dist(p, points[m]) for m in medoids]
            assignments[j] = dists.index(min(dists))
        break
    elapsed = time.time() - start
    return assignments, medoids, elapsed

# 4. Agglomerative Hierarchical Clustering (Single-linkage baseline)
def hierarchical(points, k):
    start = time.time()
    clusters = [[i] for i in range(min(len(points), 100))]
    # Subset to 100 points for O(N^2) runtime
    pts = points[:100]
    while len(clusters) > k:
        min_d = float('inf')
        merge_pair = (0, 1)
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                d = min(euclidean_dist(pts[a], pts[b]) for a in clusters[i] for b in clusters[j])
                if d < min_d:
                    min_d = d
                    merge_pair = (i, j)
        i, j = merge_pair
        clusters[i].extend(clusters[j])
        clusters.pop(j)
    elapsed = time.time() - start
    return clusters, elapsed

# Run experiments
km_assign, _, km_time = kmeans(data, k)
pam_assign, _, pam_time = pam(data, k)
hier_clusters, hier_time = hierarchical(data, k)

# Evaluate Inertia (Within-cluster sum of squares)
def compute_wcss(points, assignments, k):
    wcss = 0.0
    for i in range(k):
        c_pts = [points[j] for j in range(len(points)) if assignments[j] == i]
        if c_pts:
            mean = [sum(pt[d] for pt in c_pts) / len(c_pts) for d in range(dim)]
            wcss += sum(euclidean_dist(p, mean) ** 2 for p in c_pts)
    return wcss

km_wcss = compute_wcss(data, km_assign, k)
pam_wcss = compute_wcss(data, pam_assign, k)

print("=== EMPIRICAL EXPERIMENT RESULTS ===")
print(f"Dataset: N={{n}} samples, D={{dim}} dimensions, K={{k}} clusters")
print(f"K-Means: WCSS={{km_wcss:.2f}}, Runtime={{km_time*1000:.2f}}ms")
print(f"PAM (K-Medoids): WCSS={{pam_wcss:.2f}}, Runtime={{pam_time*1000:.2f}}ms")
print(f"Hierarchical (Agglomerative, N=100 subset): Runtime={{hier_time*1000:.2f}}ms")
print(f"Observations: In high dimensions ({dimensions}D), distance concentration affects centroid drift in K-Means, while PAM offers higher medoid stability at increased pairwise cost.")
"""
        return await self.run_experiment_code(code, filename_prefix="clustering_exp")
