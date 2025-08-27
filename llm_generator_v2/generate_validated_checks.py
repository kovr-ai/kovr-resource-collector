from llm_generator_v2.benchmark_and_checks_literature import (
    extract_check_names as ecn,
    generate_benchmark_literature as gbl,
    # enrich_individual_checks as eic,
)

gbl_input = gbl.Input(
        benchmark=gbl.InputBenchmark(
        name='owasp',
        version='latest'
    )
)
gbl_output = gbl.service.execute(
    gbl_input,
)
print(f'Literature found for {gbl_output.benchmark.literature}')

ecn_input = ecn.Input(
    benchmark=ecn.InputBenchmark(
        name='owasp',
        version='latest',
        literature=gbl_output.benchmark.literature,
    )
)
ecn_output = ecn.service.execute(
    ecn_input,
)

print(f'Check Names found {ecn_output.benchmark.check_names}')
