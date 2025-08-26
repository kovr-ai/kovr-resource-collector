"""
Check Generation Models - Section 3 Data Structures

Pydantic models for Section 3 implementation covering:
- ExecutableCheck: Generated Python logic with validation results
- ValidationResult: Execution outcomes and error tracking
- RepairContext: Context for iterative check improvement
- ImplementationCoverage: Metrics for Section 3 success rates
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from ..benchmark.models import Check


class ValidationStatus(str, Enum):
    """Status of check validation"""
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    UNABLE_TO_GENERATE = "UNABLE_TO_GENERATE"
    PENDING = "PENDING"


class ExecutionResult(BaseModel):
    """Individual execution result from resource validation"""
    resource_id: str = Field(description="Unique identifier for the resource")
    status: ValidationStatus = Field(description="Execution status")
    message: str = Field(description="Human readable message")
    error: Optional[str] = Field(default=None, description="Error details if failed")
    execution_time_ms: Optional[int] = Field(default=None, description="Execution time in milliseconds")


class ValidationResult(BaseModel):
    """Results from validating a check against real resources"""
    check_id: str = Field(description="Unique check identifier")
    provider: str = Field(description="Cloud provider (github, aws, azure, etc.)")
    resource_type: str = Field(description="Resource type (repo, ec2_instance, etc.)")
    total_resources: int = Field(description="Total resources evaluated")
    passed_count: int = Field(description="Number of resources that passed")
    failed_count: int = Field(description="Number of resources that failed")
    error_count: int = Field(description="Number of resources with execution errors")
    execution_results: List[ExecutionResult] = Field(description="Detailed per-resource results")
    validation_timestamp: datetime = Field(default_factory=datetime.now)
    
    @property
    def overall_status(self) -> ValidationStatus:
        """Calculate overall validation status"""
        if self.error_count == self.total_resources:
            return ValidationStatus.ERROR
        elif self.error_count > 0:
            return ValidationStatus.ERROR  # Any errors indicate problematic logic
        elif self.passed_count == 0 and self.failed_count == 0:
            return ValidationStatus.ERROR  # No valid results
        else:
            return ValidationStatus.PASS  # At least some valid results


class RepairContext(BaseModel):
    """Context information for repairing failed checks"""
    check_id: str = Field(description="Check being repaired")
    attempt_number: int = Field(description="Current repair attempt (1-based)")
    max_attempts: int = Field(description="Maximum allowed repair attempts")
    validation_results: List[ValidationResult] = Field(description="All validation attempts")
    error_patterns: List[str] = Field(description="Common error patterns identified")
    suggested_fixes: List[str] = Field(description="LLM suggested improvements")
    field_path_issues: List[str] = Field(description="Identified field path problems")


class GenerationTask(BaseModel):
    """Task definition for generating executable checks"""
    benchmark_check: Check = Field(description="Source benchmark check metadata")
    provider: str = Field(description="Target cloud provider")
    resource_type: str = Field(description="Target resource type")
    field_paths: List[str] = Field(default_factory=list, description="Available resource field paths")
    task_id: str = Field(description="Unique task identifier")
    created_at: datetime = Field(default_factory=datetime.now)


class ExecutableCheck(BaseModel):
    """Generated executable check with Python code and validation results"""
    check_id: str = Field(description="Unique check identifier")
    name: str = Field(description="Human readable check name")
    description: str = Field(description="Check description and purpose")
    
    # Source metadata
    benchmark_check_id: str = Field(description="Source benchmark check ID")
    provider: str = Field(description="Cloud provider (github, aws, azure)")
    resource_type: str = Field(description="Resource type (repo, ec2_instance)")
    
    # Generated code
    python_code: str = Field(description="Generated Python check function")
    function_name: str = Field(description="Name of the generated Python function")
    input_schema: Dict[str, Any] = Field(description="Expected resource object structure")
    field_paths_used: List[str] = Field(description="Resource field paths used in logic")
    
    # Validation results
    validation_status: ValidationStatus = Field(description="Overall validation status")
    validation_results: List[ValidationResult] = Field(description="All validation attempts")
    repair_attempts: int = Field(default=0, description="Number of repair attempts made")
    repair_context: Optional[RepairContext] = Field(default=None, description="Repair context if failed")
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    validated_at: Optional[datetime] = Field(default=None, description="When validation completed")
    saved_to_db: bool = Field(default=False, description="Whether saved to database")
    control_ids: List[int] = Field(default_factory=list, description="Mapped control IDs for database")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ImplementationCoverage(BaseModel):
    """Coverage metrics for Section 3 implementation success"""
    
    # Input metrics
    total_benchmark_checks: int = Field(description="Total benchmark checks processed")
    total_generation_tasks: int = Field(description="Total provider-resource tasks generated")
    
    # Generation metrics
    successfully_generated: int = Field(default=0, description="Checks with valid Python code generated")
    generation_failures: int = Field(default=0, description="Checks that failed initial code generation")
    
    # Validation metrics
    validation_passes: int = Field(default=0, description="Checks that passed validation on first try")
    validation_failures: int = Field(default=0, description="Checks that failed initial validation")
    
    # Repair metrics
    repair_attempts_made: int = Field(default=0, description="Total repair attempts across all checks")
    successful_repairs: int = Field(default=0, description="Checks successfully repaired")
    unable_to_repair: int = Field(default=0, description="Checks that couldn't be repaired after max attempts")
    
    # Database metrics
    saved_to_database: int = Field(default=0, description="Checks successfully saved to database")
    database_errors: int = Field(default=0, description="Database insertion failures")
    
    # Coverage percentages
    coverage_percentages: Dict[str, float] = Field(default_factory=dict, description="Calculated coverage percentages")
    
    # Provider breakdown
    provider_breakdown: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Success/failure by provider")
    
    # Error analysis
    common_errors: Dict[str, int] = Field(default_factory=dict, description="Most common error types and counts")
    
    # Timing metrics
    total_processing_time_seconds: float = Field(default=0.0, description="Total processing time")
    average_check_processing_time: float = Field(default=0.0, description="Average time per check")
    
    @property
    def overall_success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_generation_tasks == 0:
            return 0.0
        return (self.saved_to_database / self.total_generation_tasks) * 100
    
    @property
    def repair_success_rate(self) -> float:
        """Calculate repair success rate"""
        if self.validation_failures == 0:
            return 0.0
        return (self.successful_repairs / self.validation_failures) * 100


class Section3Results(BaseModel):
    """Complete results from Section 3 processing"""
    
    # Input data
    benchmark_name: str = Field(description="Source benchmark name")
    benchmark_version: str = Field(description="Source benchmark version")
    processing_start_time: datetime = Field(default_factory=datetime.now)
    processing_end_time: Optional[datetime] = Field(default=None)
    
    # Generated checks
    executable_checks: List[ExecutableCheck] = Field(description="All generated executable checks")
    
    # Coverage and metrics
    implementation_coverage: ImplementationCoverage = Field(description="Implementation success metrics")
    
    # Error tracking
    generation_errors: List[Dict[str, Any]] = Field(description="Detailed generation error logs")
    validation_errors: List[Dict[str, Any]] = Field(description="Detailed validation error logs")
    
    # Summary statistics
    summary: Dict[str, Any] = Field(description="High-level summary statistics")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @property
    def processing_duration_minutes(self) -> float:
        """Calculate total processing duration in minutes"""
        if not self.processing_end_time:
            return 0.0
        duration = self.processing_end_time - self.processing_start_time
        return duration.total_seconds() / 60
    
    def get_successful_checks(self) -> List[ExecutableCheck]:
        """Get all checks that were successfully validated and saved"""
        return [
            check for check in self.executable_checks 
            if check.validation_status == ValidationStatus.PASS and check.saved_to_db
        ]
    
    def get_failed_checks(self) -> List[ExecutableCheck]:
        """Get all checks that failed validation and couldn't be repaired"""
        return [
            check for check in self.executable_checks 
            if check.validation_status in [ValidationStatus.FAIL, ValidationStatus.ERROR, ValidationStatus.UNABLE_TO_GENERATE]
        ]
    
    def get_provider_summary(self) -> Dict[str, Dict[str, int]]:
        """Get summary statistics by provider"""
        provider_stats = {}
        
        for check in self.executable_checks:
            provider = check.provider
            if provider not in provider_stats:
                provider_stats[provider] = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'unable_to_generate': 0
                }
            
            provider_stats[provider]['total'] += 1
            
            if check.validation_status == ValidationStatus.PASS and check.saved_to_db:
                provider_stats[provider]['successful'] += 1
            elif check.validation_status == ValidationStatus.UNABLE_TO_GENERATE:
                provider_stats[provider]['unable_to_generate'] += 1
            else:
                provider_stats[provider]['failed'] += 1
        
        return provider_stats
