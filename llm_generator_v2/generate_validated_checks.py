from llm_generator_v2.benchmark_and_checks_literature import (
    generate_benchmark_literature as gbl,
    extract_check_names as ecn,
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

print(ecn_output.benchmark.check_name)
