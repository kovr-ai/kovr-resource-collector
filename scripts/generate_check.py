#!/usr/bin/env python3
"""
Script to generate compliance checks from controls using LLM.
"""

import pandas as pd
from pathlib import Path
from con_mon_v2.compliance.models import Control
from con_mon_v2.utils.llm.generate import generate_check_for_control


def load_controls_from_csv():
    """Load controls directly from CSV file."""
    csv_path = Path("data/csv/control.csv")
    if not csv_path.exists():
        print(f"❌ Control CSV file not found: {csv_path}")
        return []
    
    print(f"📁 Loading controls from {csv_path}")
    df = pd.read_csv(csv_path)
    
    controls = []
    for _, row in df.iterrows():
        try:
            # Convert pandas row to dict and create Control instance
            control_data = row.to_dict()
            control = Control.from_row(control_data)
            controls.append(control)
        except Exception as e:
            print(f"⚠️ Failed to create control from row: {e}")
            continue
    
    print(f"✅ Loaded {len(controls)} controls from CSV")
    return controls


if __name__ == "__main__":
    controls = load_controls_from_csv()
    if controls:
        print(f"🔄 Processing first control: {controls[0].control_name}")
        generate_check_for_control(controls[0])
        print("✅ Check generation completed for first control")
    else:
        print("❌ No controls loaded")
