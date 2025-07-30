import argparse
from datetime import datetime
from collector import Collector
import json

from rule_engine import RuleEngine

def datetime_json_encoder(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", type=str, required=True)
    parser.add_argument("--metadata", type=str, required=True)
    args = parser.parse_args()

    collector = Collector(args.provider, args.metadata)
    response = collector.process()

    rule_engine = RuleEngine(args.provider, response)
    report = rule_engine.process()

    print(json.dumps(report, indent=4, default=datetime_json_encoder))

    # with open("response.json", "w") as f:
    #     json.dump(response, f, indent=4, default=datetime_json_encoder)