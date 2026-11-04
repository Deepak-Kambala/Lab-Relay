import pytest
from labrelay.research.experiment_runner import ExperimentRunner


def test_experiment_safety_validation():
    runner = ExperimentRunner()
    
    # Safe code
    runner.validate_safety("x = 10\ny = 20\nprint(x + y)")

    # Unsafe codes
    with pytest.raises(ValueError):
        runner.validate_safety("import os\nos.system('rm -rf /')")

    with pytest.raises(ValueError):
        runner.validate_safety("import subprocess\nsubprocess.Popen(['curl', 'bad.com'])")


@pytest.mark.asyncio
async def test_experiment_execution_success():
    runner = ExperimentRunner()
    code = "import math\nprint(f'PI={math.pi:.4f}')"
    res = await runner.run_experiment_code(code)
    assert res.success is True
    assert "PI=3.1416" in res.output


@pytest.mark.asyncio
async def test_clustering_benchmark():
    runner = ExperimentRunner()
    res = await runner.generate_and_run_clustering_benchmark(dimensions=10, samples=50, clusters=2)
    assert res.success is True
    assert "EMPIRICAL EXPERIMENT RESULTS" in res.output
    assert "K-Means" in res.output
    assert "PAM" in res.output

