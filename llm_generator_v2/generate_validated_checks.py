from llm_generator_v2.benchmark_and_checks_literature import (
    generate_benchmark_literature as gbl,
    extract_check_names as ecn,
    enrich_individual_checks as eic,
)

# Step 1: Generate benchmark literature
print("Step 1: Generating benchmark literature...")
gbl_input = gbl.Input(
    benchmark=gbl.InputBenchmark(
        name='owasp',
        version='latest'
    )
)
gbl_output = gbl.service.execute(gbl_input)

print(f"✅ Generated literature: {len(gbl_output.benchmark.literature)} characters")
print(f"   Unique ID: {gbl_output.benchmark.unique_id}")

# Step 2: Extract check names from literature  
print("\nStep 2: Extracting check names...")
ecn_input = ecn.Input(
    benchmark=ecn.InputBenchmark(
        unique_id=gbl_output.benchmark.unique_id,
        name='owasp',
        version='latest', 
        literature=gbl_output.benchmark.literature,
    )
)
ecn_output = ecn.service.execute(ecn_input)

print(f"✅ Extracted {len(ecn_output.benchmark.check_names)} check names:")
for i, check_name in enumerate(ecn_output.benchmark.check_names[:5], 1):
    print(f"   {i}. {check_name}")
if len(ecn_output.benchmark.check_names) > 5:
    print(f"   ... and {len(ecn_output.benchmark.check_names) - 5} more")

# Step 3: Enrich individual checks (process first few checks as example)
print("\nStep 3: Enriching individual checks...")
enriched_checks = []

for i, check_name in enumerate(ecn_output.benchmark.check_names):  # Process first 3 checks
    print(f"   Enriching check {i+1}/{len(ecn_output.benchmark.check_names)+1}: {check_name}")
    
    eic_input = eic.Input(
        check=eic.InputCheck(name=check_name),
        benchmark=eic.InputBenchmark.model_validate(
            gbl_output.benchmark.model_dump()
        ),
    )
    
    eic_output = eic.service.execute(eic_input)
    enriched_checks.append(eic_output.check)
    
    print(f"   ✅ {eic_output.check.unique_id} - {eic_output.check.category} - {eic_output.check.severity}")

print(f"\n🎉 Pipeline completed successfully!")
print(f"   Literature generated: {len(gbl_output.benchmark.literature)} chars")  
print(f"   Checks extracted: {len(ecn_output.benchmark.check_names)}")
print(f"   Checks enriched: {len(enriched_checks)}")

# Show one enriched check in detail
if enriched_checks:
    sample_check = enriched_checks[0]
    print(f"\n📋 Sample enriched check: {sample_check.unique_id}")
    print(f"   Literature: {sample_check.literature[:100]}...")
    print(f"   Controls: {len(sample_check.controls)} mapped")
    print(f"   Benchmarks: {len(sample_check.benchmarks)} mapped") 
    print(f"   Tags: {', '.join(sample_check.tags)}")
