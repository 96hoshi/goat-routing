import csv

motis_mem = []
motis_cpu = []

with open("tests/results/benchmark_results.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row["service"] == "motis":
            try:
                mem = float(row["avg_mem_mb"])
                cpu = float(row["avg_cpu_s"])
                motis_mem.append(mem)
                motis_cpu.append(cpu)
            except ValueError:
                continue

avg_mem = sum(motis_mem) / len(motis_mem) if motis_mem else 0
avg_cpu = sum(motis_cpu) / len(motis_cpu) if motis_cpu else 0

print(f"Motis avg_mem_mb: {avg_mem:.4f}")
print(f"Motis avg_cpu_s: {avg_cpu:.4f}")
