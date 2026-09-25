import os
import json
from pathlib import Path
from blitzdev_agent.rules import scan_file

def run_scan(target_dir: str = "demo_api"):
    findings = []
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                path = os.path.join(root, file)
                findings.extend(scan_file(path))

    os.makedirs("output", exist_ok=True)
    
    # Save structured findings
    output_data = [f.__dict__ for f in findings]
    with open("output/findings.json", "w") as f:
        json.dump(output_data, f, indent=2)

    print("\n" + "=" * 80)
    print(f"🛡️  BLITZDEV FINTECH SECURITY SCAN RESULTS: {len(findings)} VULNERABILITIES FOUND")
    print("=" * 80)
    
    for f in findings:
        print(f"[{f.severity}] {f.rule_id} -> {f.file_path}:{f.line_number}")
        print(f"  Title: {f.title}")
        print(f"  Detail: {f.description}")
        print(f"  Fix:    {f.suggested_fix}\n")
        
    print(f"Audit report saved to output/findings.json")

if __name__ == "__main__":
    run_scan()
