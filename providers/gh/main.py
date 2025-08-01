#!/usr/bin/env python3
"""
GitHub Provider Main Runner
Runs the new GitHubProvider with the same interface as github_collector.py
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from pathlib import Path

from dotenv import load_dotenv
from providers.github.github_provider import GitHubProvider
from providers.github.models.report_models import GitHubReport
from constants import Providers

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GitHubProviderRunner:
    def __init__(self, config_file: str = "providers/github/github_config.json"):
        self.config = self.load_config(config_file)
        self.output_dir = Path("output/github")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata = self.prepare_metadata()

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(f"Loaded configuration from {config_file}")
                return config
        except FileNotFoundError:
            print(f"Configuration file {config_file} not found. Using default settings.")
            return {
                "github": {
                    "output_config": {
                        "repositories": True,
                        "actions": True,
                        "collaboration": True,
                        "security": True,
                        "organization": True,
                        "advanced_features": True
                    }
                },
                "features": {
                    "rate_limit_monitoring": True,
                    "detailed_logging": True
                }
            }
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return {}

    def prepare_metadata(self) -> Dict[str, Any]:
        """Prepare metadata for the GitHub provider"""
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        return {
            "GITHUB_TOKEN": github_token,
            "config": self.config,
            "output_dir": str(self.output_dir)
        }

    def collect_all_data(self) -> Dict[str, Any]:
        """Main method to collect all GitHub data using the provider"""
        try:
            # Initialize and connect the GitHub provider
            provider = GitHubProvider(self.metadata)
            provider.connect()
            
            # Collect all data into a GitHubReport model
            print("Starting comprehensive data collection...")
            github_report = provider.process()
            
            # Generate and save the comprehensive report
            report_file = self.save_report_to_file(github_report)
            
            # Generate summary information
            summary = github_report.get_summary()
            
            # Log final statistics
            self.log_final_statistics(summary, report_file)
            
            return summary
            
        except Exception as e:
            print(f"Error during data collection: {e}")
            logging.error(f"Data collection failed: {e}")
            raise

    def save_report_to_file(self, report: GitHubReport) -> str:
        """Save the complete GitHubReport to a single JSON file"""
        try:
            # Convert the Pydantic model to a dictionary
            report_data = {
                "collection_metadata": {
                    "collection_time": report.collection_time.isoformat(),
                    "authenticated_user": report.authenticated_user,
                    "total_repositories": report.total_repositories,
                    "framework_version": "2.0-pydantic",
                    "provider": "GitHub"
                },
                "overall_statistics": {
                    "total_repositories": report.total_repositories,
                    "total_workflows": report.total_workflows,
                    "total_issues": report.total_issues,
                    "total_pull_requests": report.total_pull_requests,
                    "total_security_alerts": report.total_security_alerts,
                    "total_collaborators": report.total_collaborators,
                    "total_tags": report.total_tags,
                    "total_active_webhooks": report.total_active_webhooks
                },
                "rate_limit_info": report.rate_limit_info,
                "repositories_data": [repo.model_dump() for repo in report.repositories_data],
                "actions_data": [actions.model_dump() for actions in report.actions_data],
                "collaboration_data": [collab.model_dump() for collab in report.collaboration_data],
                "security_data": [security.model_dump() for security in report.security_data],
                "organization_data": [org.model_dump() for org in report.organization_data],
                "advanced_features_data": [features.model_dump() for features in report.advanced_features_data]
            }
            
            # Save to single comprehensive file
            report_filename = f"github_comprehensive_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            report_file = self.output_dir / report_filename
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            print(f"✅ Comprehensive GitHub report saved to: {report_file}")
            
            # Also save a summary file for quick reference
            summary_file = self.output_dir / "github_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(report.get_summary(), f, indent=2, default=str)
            
            print(f"✅ Summary report saved to: {summary_file}")
            
            return str(report_file)
            
        except Exception as e:
            print(f"Error saving report: {e}")
            raise

    def log_final_statistics(self, summary: Dict[str, Any], report_file: str):
        """Log final collection statistics"""
        stats = summary.get("statistics", {})
        services_data = summary.get("services_data", {})
        
        print("\n" + "="*60)
        print("🎉 GITHUB DATA COLLECTION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"📅 Collection Time: {summary.get('collection_time')}")
        print(f"👤 Authenticated User: {summary.get('authenticated_user')}")
        print(f"📁 Report File: {report_file}")
        print("\n📊 OVERALL STATISTICS:")
        print(f"  🏗️  Total Repositories: {stats.get('total_repositories', 0)}")
        print(f"  ⚙️  Total Workflows: {stats.get('total_workflows', 0)}")
        print(f"  🐛 Total Issues: {stats.get('total_issues', 0)}")
        print(f"  🔄 Total Pull Requests: {stats.get('total_pull_requests', 0)}")
        print(f"  🛡️  Total Security Alerts: {stats.get('total_security_alerts', 0)}")
        print(f"  👥 Total Collaborators: {stats.get('total_collaborators', 0)}")
        print(f"  🏷️  Total Tags: {stats.get('total_tags', 0)}")
        print(f"  🪝 Active Webhooks: {stats.get('total_active_webhooks', 0)}")
        print("\n🔧 SERVICES DATA COLLECTED:")
        for service, count in services_data.items():
            print(f"  {service.title()}: {count} repositories")
        print("="*60)

def main():
    """Main entry point"""
    try:
        runner = GitHubProviderRunner()
        summary = runner.collect_all_data()
        
        print(f"\n✅ Data collection completed successfully!")
        print(f"📊 Summary: {json.dumps(summary['statistics'], indent=2)}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Collection interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Collection failed: {e}")
        logging.error(f"Main execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 