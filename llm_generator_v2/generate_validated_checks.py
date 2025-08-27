from llm_generator_v2.benchmark_and_checks_literature import (
    generate_benchmark_literature as gbl,
    extract_check_names as ecn,
    enrich_individual_checks as eic,
)
from llm_generator_v2.system_compatible_checks_literature import (
    add_targeted_literature as atl,
    consolidate_resource_wise_checks as crwc,
)
from llm_generator_v2.checks_with_python_logic import (
    generate_python_logic as gpl,
    validate_with_mock_data as vwmd,
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

# ============================================================================
# SECTION 2: System Compatible Checks Literature  
# ============================================================================

print(f"\n🔧 SECTION 2: System Compatible Checks Literature")

# Load provider mappings dynamically (following con_mon pattern)
from con_mon.utils.llm.generate import get_provider_resources_mapping
from con_mon.utils.llm.prompt import ProviderConfig
from collections import defaultdict

provider_resources = get_provider_resources_mapping()
print(f"   Loaded {len(provider_resources)} providers")

# Step 1: Add Targeted Literature (process first 2 checks for demo)
print(f"\nStep 4: Adding targeted literature for resources...")
atl_results = []

for i, check in enumerate(enriched_checks):  # Process first 2 for demo
    print(f"   Processing check {i+1}/{len(enriched_checks)+1}: {check.unique_id}")
    
    control_names = [ctrl.unique_id for ctrl in check.controls] if check.controls else []
    
    # Process each provider-resource combination (following con_mon pattern)
    for connector_type, resource_models in provider_resources.items():
        provider_config = ProviderConfig(connector_type)
        
        for resource_model_name in resource_models:  # First resource per provider for demo
            # Get field paths dynamically from the resource model
            field_paths = []
            if resource_model_name in provider_config.resource_wise_field_paths:
                field_paths = provider_config.resource_wise_field_paths[resource_model_name][:3]  # First 3 paths
            
            atl_input = atl.Input(
                check=atl.InputCheck(
                    unique_id=check.unique_id,
                    name=check.unique_id,
                    literature=check.literature,
                    category=check.category,
                    control_names=control_names,
                    provider=connector_type.value,
                    resource=atl.InputResource(
                        name=resource_model_name,
                        field_paths=field_paths
                    )
                )
            )
            
            atl_output = atl.service.execute(atl_input)
            atl_results.append((check, resource_model_name, atl_output))
            
            print(f"     {connector_type.value}/{resource_model_name}: {atl_output.resource.is_valid}")

# Step 2: Consolidate Resource-wise Checks
print(f"\nStep 5: Consolidating resource-wise checks...")

consolidation_data = defaultdict(list)

for check, resource_name, result in atl_results:
    if not result.resource.is_valid:
        continue

    consolidation_data[check.unique_id].append({
        "unique_id": check.unique_id,
        "is_valid": result.resource.is_valid,
        "reason": result.resource.reason,
        "resource": {
            "name": resource_name,
            "literature": result.resource.literature,
            "field_paths": result.resource.field_paths
        }
    })

from pdb import set_trace;set_trace()
crwc_results = []
for check_id, check_resources in consolidation_data.items():
    print(f"   Consolidating {len(check_resources)} resource(s) for: {check_id}")
    
    crwc_input = crwc.Input(check=check_resources)
    crwc_output = crwc.service.execute(crwc_input)
    crwc_results.append(crwc_output)
    
    print(f"   ✅ Valid: {len(crwc_output.check.valid_resources)}, Invalid: {len(crwc_output.check.invalid_resources)}")

# ============================================================================
# SECTION 3: Checks with Python Logic
# ============================================================================

print(f"\n🔧 SECTION 3: Checks with Python Logic")

# Step 1: Generate Python Logic (process all valid resources from Section 2)
print(f"\nStep 6: Generating Python logic for valid resources...")
gpl_results = []

for consolidated_check in crwc_results:
    print(f"   Processing check: {consolidated_check.check.unique_id}")
    
    # Generate logic for each valid resource
    for resource in consolidated_check.check.valid_resources:
        print(f"     Generating logic for: {resource.name}")
        
        gpl_input = gpl.Input(
            check=gpl.InputCheck(
                unique_id=consolidated_check.check.unique_id,
                name=consolidated_check.check.unique_id,
                literature="",  # Will be filled from enriched checks
                category="",  # Will be filled from enriched checks
                control_names=[],  # Will be filled from enriched checks
                resource=gpl.InputResource(
                    name=resource.name,
                    literature=resource.literature,
                    field_paths=resource.field_paths,
                    reason=resource.reason
                )
            )
        )
        
        # Fill in check details from enriched_checks
        for enriched_check in enriched_checks:
            if enriched_check.unique_id == consolidated_check.check.unique_id:
                gpl_input.check.literature = enriched_check.literature
                gpl_input.check.category = enriched_check.category
                gpl_input.check.control_names = [ctrl.unique_id for ctrl in enriched_check.controls] if enriched_check.controls else []
                break
        
        gpl_output = gpl.service.execute(gpl_input)
        gpl_results.append((consolidated_check.check.unique_id, resource.name, gpl_output))
        
        print(f"       ✅ Generated logic for field: {gpl_output.resource.field_path}")

# Step 2: Validate with Mock Data
print(f"\nStep 7: Validating Python logic with mock data...")
vwmd_results = []

for check_id, resource_name, gpl_result in gpl_results:
    print(f"   Validating {check_id} / {resource_name}")
    
    vwmd_input = vwmd.Input(
        check=vwmd.InputCheck(
            unique_id=check_id,
            name=check_id,
            resource=vwmd.InputResource(
                name=resource_name,
                field_path=gpl_result.resource.field_path,
                logic=gpl_result.resource.logic
            )
        )
    )
    
    vwmd_output = vwmd.service.execute(vwmd_input)
    vwmd_results.append(vwmd_output)
    
    error_count = len(vwmd_output.errors)
    print(f"     ✅ Validation: {error_count} errors found")

print(f"\n🎉 Pipeline completed successfully!")
print(f"   Literature generated: {len(gbl_output.benchmark.literature)} chars")  
print(f"   Checks extracted: {len(ecn_output.benchmark.check_names)}")
print(f"   Checks enriched: {len(enriched_checks)}")
print(f"   Resource analyses: {len(atl_results)}")
print(f"   Consolidated checks: {len(crwc_results)}")
print(f"   Python logic generated: {len(gpl_results)}")
print(f"   Mock validations: {len(vwmd_results)}")

# Show one enriched check in detail
if enriched_checks:
    sample_check = enriched_checks[0]
    print(f"\n📋 Sample enriched check: {sample_check.unique_id}")
    print(f"   Literature: {sample_check.literature[:100]}...")
    print(f"   Controls: {len(sample_check.controls)} mapped")
    print(f"   Benchmarks: {len(sample_check.benchmarks)} mapped") 
    print(f"   Tags: {', '.join(sample_check.tags)}")

if crwc_results:
    sample_result = crwc_results[0]
    print(f"\n🔧 Sample consolidated result: {sample_result.check.unique_id}")
    print(f"   Resources: {len(sample_result.check.valid_resources)} valid, {len(sample_result.check.invalid_resources)} invalid")

if vwmd_results:
    sample_validation = vwmd_results[0]
    error_count = len(sample_validation.errors)
    print(f"\n⚡ Sample validation result: {error_count} errors")
    if sample_validation.errors:
        print(f"   First error: {sample_validation.errors[0]}")
    else:
        print(f"   No errors - validation passed!")
