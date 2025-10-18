import json
import os

# Load coverage data
with open('coverage.json', 'r') as f:
    data = json.load(f)

# Overall totals
totals = data['totals']
print("=" * 80)
print("OVERALL COVERAGE REPORT")
print("=" * 80)
print(f"Total Coverage: {totals['percent_covered']:.2f}%")
print(f"Total Statements: {totals['num_statements']}")
print(f"Covered Lines: {totals['covered_lines']}")
print(f"Missing Lines: {totals['missing_lines']}")
print()

# Files with <50% coverage
low_coverage = []
medium_coverage = []
good_coverage = []

for filename, filedata in data['files'].items():
    if 'apps' + os.sep in filename and not filename.endswith('__init__.py'):
        pct = filedata['summary']['percent_covered']
        covered = filedata['summary']['covered_lines']
        total = filedata['summary']['num_statements']
        missing = filedata['summary']['missing_lines']

        # Clean up filename for display
        rel_path = filename.replace(os.getcwd() + os.sep, '')

        if pct < 50:
            low_coverage.append((rel_path, pct, covered, total, missing))
        elif pct < 80:
            medium_coverage.append((rel_path, pct, covered, total, missing))
        else:
            good_coverage.append((rel_path, pct, covered, total, missing))

# Sort by coverage percentage
low_coverage.sort(key=lambda x: x[1])
medium_coverage.sort(key=lambda x: x[1])
good_coverage.sort(key=lambda x: x[1], reverse=True)

# Print low coverage files
print("=" * 80)
print(f"FILES WITH <50% COVERAGE ({len(low_coverage)} files)")
print("=" * 80)
for fname, pct, covered, total, missing in low_coverage:
    print(f"{pct:5.1f}% - {covered:4d}/{total:4d} lines ({missing:4d} missing) - {fname}")

print()
print("=" * 80)
print(f"FILES WITH 50-80% COVERAGE ({len(medium_coverage)} files)")
print("=" * 80)
for fname, pct, covered, total, missing in medium_coverage[:10]:  # Top 10
    print(f"{pct:5.1f}% - {covered:4d}/{total:4d} lines ({missing:4d} missing) - {fname}")

print()
print("=" * 80)
print(f"FILES WITH >80% COVERAGE ({len(good_coverage)} files) - Top 10")
print("=" * 80)
for fname, pct, covered, total, missing in good_coverage[:10]:
    print(f"{pct:5.1f}% - {covered:4d}/{total:4d} lines ({missing:4d} missing) - {fname}")

print()
print("=" * 80)
print("SUMMARY BY APP")
print("=" * 80)

apps = {}
for filename, filedata in data['files'].items():
    if 'apps' + os.sep in filename:
        parts = filename.split(os.sep)
        try:
            app_idx = parts.index('apps')
            app_name = parts[app_idx + 1]
            if app_name not in apps:
                apps[app_name] = {'statements': 0, 'covered': 0, 'missing': 0}
            apps[app_name]['statements'] += filedata['summary']['num_statements']
            apps[app_name]['covered'] += filedata['summary']['covered_lines']
            apps[app_name]['missing'] += filedata['summary']['missing_lines']
        except (ValueError, IndexError):
            pass

for app_name in sorted(apps.keys()):
    app_data = apps[app_name]
    if app_data['statements'] > 0:
        pct = (app_data['covered'] / app_data['statements']) * 100
        print(f"{app_name:20s} - {pct:5.1f}% - {app_data['covered']:4d}/{app_data['statements']:4d} lines")
