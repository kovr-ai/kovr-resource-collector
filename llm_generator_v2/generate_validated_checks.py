import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collections import defaultdict

from con_mon.utils.llm.generate import get_provider_resources_mapping
from con_mon.utils.llm.prompt import ProviderConfig

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
    # repair_loop_execution_errors as rlee,
    # consolidate_repaired_checks as crc,
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
# DEBUGGING
# ecn_output.benchmark.check_names = ecn_output.benchmark.check_names[:2]

print(f"✅ Extracted {len(ecn_output.benchmark.check_names)} check names:")
for i, check_name in enumerate(ecn_output.benchmark.check_names[:5], 1):
    print(f"   {i}. {check_name}")
if len(ecn_output.benchmark.check_names) > 5:
    print(f"   ... and {len(ecn_output.benchmark.check_names) - 5} more")

# Step 3: Enrich individual checks (process first few checks as example)
print("\nStep 3: Enriching individual checks...")
eic_inputs = [
    eic.Input(
        check=eic.InputCheck(
            name=check_name,
            unique_id=check_name
        ),
        benchmark=eic.InputBenchmark.model_validate(
            gbl_output.benchmark.model_dump()
        ),
    )
    for check_name in ecn_output.benchmark.check_names
]

eic_outputs = eic.service.execute(eic_inputs, threads=8)
enriched_checks = [
    eic_output.check
    for eic_output in eic_outputs
]

provider_resources = get_provider_resources_mapping()
print(f"   Loaded {len(provider_resources)} providers")

# Step 4: Add Targeted Literature
print(f"\nStep 4: Adding targeted literature for resources...")
atl_inputs = []
for i, check in enumerate(enriched_checks):
    print(f"   Processing check {i+1}/{len(enriched_checks)}: {check.unique_id}")
    
    control_names = [ctrl.unique_id for ctrl in check.controls] if check.controls else []
    
    # Process each provider-resource combination (following con_mon pattern)
    for connector_type, resource_models in provider_resources.items():
        provider_config = ProviderConfig(connector_type)
        
        for resource_model_name in resource_models:  # First resource per provider for demo
            # Get field paths dynamically from the resource model
            field_paths = []
            if resource_model_name in provider_config.resource_wise_field_paths:
                field_paths = provider_config.resource_wise_field_paths[resource_model_name]

            atl_input = atl.Input(
                check=atl.InputCheck(
                    unique_id=check.unique_id,
                    name=check.unique_id,
                    literature=check.literature,
                    category=check.category,
                    control_names=control_names,
                    provider=connector_type.value,
                    resource=dict(
                        name=resource_model_name,
                        field_paths=field_paths
                    )
                )
            )
            atl_inputs.append(atl_input)
            print(f"     {connector_type.value}/{resource_model_name}: Prepared")

atl_outputs = atl.service.execute(atl_inputs, threads=8)

# Step 5: Consolidate Resource-wise Checks
print("\nStep 5: Consolidating resource-wise checks...")

consolidation_data = defaultdict(list)

for alt_output in atl_outputs:
    if not alt_output.resource.is_valid:
        continue

    consolidation_data[alt_output.resource.check.unique_id].append({
        "unique_id": alt_output.resource.check.unique_id,
        "is_valid": alt_output.resource.is_valid,
        "reason": alt_output.resource.reason,
        "name": alt_output.resource.name,
        "literature": alt_output.resource.literature,
        "field_paths": alt_output.resource.field_paths
    })

crwc_outputs = []
for check_id, check_resources in consolidation_data.items():
    print(f"   Consolidating {len(check_resources)} resource(s) for: {check_id}")

    crwc_input = crwc.Input(check=dict(
        unique_id=check_id,
        resources=check_resources,
    ))
    crwc_output = crwc.service.execute(crwc_input)
    crwc_outputs.append(crwc_output)
    
    print(f"   ✅ Valid: {len(crwc_output.check.valid_resources)}, Invalid: {len(crwc_output.check.invalid_resources)}")

# Step 6: Generate Python Logic (process all valid resources from Section 2)
print(f"\nStep 6: Generating Python logic for valid resources...")
gpl_inputs = []

for consolidated_check in crwc_outputs:
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
                resource=dict(
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

        gpl_inputs.append(gpl_input)
        print(f"       ✅ Prepared logic generation for: {resource.name}")

gpl_outputs = gpl.service.execute(gpl_inputs, threads=8)
# Step 7: Validate with Mock Data
print(f"\nStep 7: Validating Python logic with mock data...")
vwmd_inputs = []

# for check_id, resource_name, gpl_result in gpl_results:
for gpl_output in gpl_outputs:
    resource_name = gpl_output.resource.name
    check_id = gpl_output.resource.check.unique_id
    print(f"   Validating {check_id} / {resource_name}")

    vwmd_input = vwmd.Input(
        check=vwmd.InputCheck(
            unique_id=check_id,
            name=check_id,
            resource=dict(
                name=resource_name,
                field_path=gpl_output.resource.field_path,
                logic=gpl_output.resource.logic
            )
        )
    )

    vwmd_inputs.append(vwmd_input)
    print(f"     ✅ Prepared validation for: {resource_name}")

vwmd_outputs = vwmd.service.execute(vwmd_inputs)
#
# # Step 8: Repair Loop Execution Errors (for failed validations)
# print(f"\nStep 8: Repairing failed Python logic...")
# rlee_inputs = []
#
# for vwmd_output in vwmd_outputs:
#     if vwmd_output.errors:  # Only repair if there are errors
#         check_id = vwmd_output.check.unique_id
#         resource_name = vwmd_output.resource.name
#         print(f"   Repairing {check_id} / {resource_name} ({len(vwmd_output.errors)} errors)")
#
#         # Find the corresponding gpl output to get the original logic
#         original_logic = ""
#         original_field_path = ""
#         for gpl_output in gpl_outputs:
#             if (gpl_output.check.unique_id == check_id and
#                 gpl_output.resource.name == resource_name):
#                 original_logic = gpl_output.resource.logic
#                 original_field_path = gpl_output.resource.field_path
#                 break
#
#         rlee_input = rlee.Input(
#             check=rlee.InputCheck(
#                 unique_id=check_id,
#                 name=check_id,
#                 literature="",  # Will be filled from enriched checks
#                 category="",  # Will be filled from enriched checks
#                 control_names=[],  # Will be filled from enriched checks
#                 resource=rlee.InputResource(
#                     name=resource_name,
#                     field_paths=[original_field_path],  # Available field paths
#                     reason="Repair needed due to validation errors",
#                     literature="Repairing logic based on validation errors",
#                     errors=vwmd_output.errors
#                 )
#             )
#         )
#
#         # Fill in check details from enriched_checks
#         for enriched_check in enriched_checks:
#             if enriched_check.unique_id == check_id:
#                 rlee_input.check.literature = enriched_check.literature
#                 rlee_input.check.category = enriched_check.category
#                 rlee_input.check.control_names = [ctrl.unique_id for ctrl in enriched_check.controls] if enriched_check.controls else []
#                 break
#
#         rlee_inputs.append(rlee_input)
#         print(f"     ✅ Prepared repair for: {resource_name}")
#
# rlee_outputs = rlee.service.execute(rlee_inputs) if rlee_inputs else []
#
# # Step 9: Consolidate Repaired Checks
# print(f"\nStep 9: Consolidating repaired checks...")
# crc_inputs = []
#
# for rlee_output in rlee_outputs:
#     check_id = rlee_output.resource.check.unique_id
#     resource_name = rlee_output.resource.name
#     print(f"   Consolidating repaired check: {check_id} / {resource_name}")
#
#     crc_input = crc.Input(
#         check=crc.InputCheck(
#             unique_id=check_id
#         ),
#         resource=crc.InputResource(
#             name=resource_name,
#             field_path=rlee_output.resource.field_path,
#             logic=rlee_output.resource.logic
#         )
#     )
#
#     crc_inputs.append(crc_input)
#     print(f"     ✅ Prepared consolidation for: {resource_name}")
#
# crc_outputs = crc.service.execute(crc_inputs) if crc_inputs else []

print(f"\n🎉 Pipeline completed successfully!")
# Show one enriched check in detail
if enriched_checks:
    sample_check = enriched_checks[0]
    print(f"\n📋 Sample enriched check: {sample_check.unique_id}")
    print(f"   Literature: {sample_check.literature[:100]}...")
    print(f"   Controls: {len(sample_check.controls)} mapped")
    print(f"   Benchmarks: {len(sample_check.benchmarks)} mapped") 
    print(f"   Tags: {', '.join(sample_check.tags)}")

if crwc_outputs:
    sample_result = crwc_outputs[0]
    print(f"\n🔧 Sample consolidated result: {sample_result.check.unique_id}")
    print(f"   Resources: {len(sample_result.check.valid_resources)} valid, {len(sample_result.check.invalid_resources)} invalid")

total_errors = 0
total_failed_checks = 0
if vwmd_outputs:
    for validation in vwmd_outputs:
        error_count = len(validation.errors)
        total_errors += error_count
        print(f"\n⚡ Validation result: {error_count} errors")
        if validation.errors:
            total_failed_checks += 1
            # for validation_error in validation.errors:
            #     print(f"   Resource Name: {validation_error.resource.name}")
            #     print(f"   Field Path: {validation_error.resource.field_path}")
            #     print(f"   Logic:\n{validation_error.resource.logic}")
            #     print(f"   Error:\n{validation_error.error}")
            #     # from pdb import set_trace;set_trace()
        else:
            print(f"   No errors - validation passed!")

# if rlee_outputs:
#     sample_repair = rlee_outputs[0]
#     print(f"\n🔧 Sample repaired logic: {sample_repair.resource.check.unique_id}")
#     print(f"   Field path: {sample_repair.resource.field_path}")
#     print(f"   Logic length: {len(sample_repair.resource.logic)} chars")
#
# if crc_outputs:
#     sample_consolidated = crc_outputs[0]
#     print(f"\n📋 Sample consolidated repaired check: {sample_consolidated.checks.unique_id}")
#     print(f"   Name: {sample_consolidated.checks.name}")
#     print(f"   Category: {sample_consolidated.checks.category}")
#     print(f"   Severity: {sample_consolidated.checks.severity}")

print(f"   Literature generated: {len(gbl_output.benchmark.literature)} chars")
print(f"   Checks extracted: {len(ecn_output.benchmark.check_names)}")
print(f"   Checks enriched: {len(enriched_checks)}")
print(f"   Resource analyses: {len(atl_outputs)}")
print(f"   Consolidated checks: {len(crwc_outputs)}")
print(f"   Python logic generated: {len(gpl_outputs)}")
print(f"   Mock validations: {len(vwmd_outputs)}")
print(f"   Failed checks: {total_failed_checks}")
# print(f"   Logic repairs: {len(rlee_outputs)}")
# print(f"   Repaired checks consolidated: {len(crc_outputs)}")
