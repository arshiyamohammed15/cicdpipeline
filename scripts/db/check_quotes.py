from pathlib import Path

path = Path(__file__).with_name("apply_schema_pack.ps1")
text = path.read_text(encoding="utf-8", errors="replace")
lines = text.splitlines()
odd = []
for i, line in enumerate(lines, 1):
    if line.count('"') % 2 == 1:
        odd.append((i, line))

print("Odd-quote lines:", odd)

