from llm_generator_v2.benchmark_and_checks_literature import (
    generate_benchmark_literature,
    extract_check_names,
    enrich_individual_checks,
)

benchmark_input = generate_benchmark_literature.models.Benchmark(
    name='owasp',
    version='latest'
)
generate_benchmark_literature.service.execute(
    benchmark_input,
)