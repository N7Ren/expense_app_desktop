import pandas as pd
import io
import time
import copy
import random

# Create a large dummy dataset
print("Generating dataset...")
num_transactions = 500000
categories = ['Groceries', 'Rent', 'Utilities', 'Entertainment', 'Transport', 'Healthcare', 'Insurance', 'Savings', 'Misc', 'Dining']
months = [f"2023-{str(i).zfill(2)}" for i in range(1, 13)] + [f"2024-{str(i).zfill(2)}" for i in range(1, 13)]

data = {
    'Month': [random.choice(months) for _ in range(num_transactions)],
    'category': [random.choice(categories) for _ in range(num_transactions)],
    'amount': [random.uniform(5.0, 500.0) for _ in range(num_transactions)]
}
expenses_df = pd.DataFrame(data)

def benchmark_current(df):
    start = time.perf_counter()
    excel_data = io.BytesIO()
    with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
        for month in sorted(df['Month'].unique()):
            month_df = df[df['Month'] == month]
            month_summary = month_df.groupby('category')['amount'].sum().reset_index()
            month_summary = month_summary.sort_values('amount', ascending=False)

            # Current approach
            total_row = pd.DataFrame([{'category': 'TOTAL', 'amount': month_summary['amount'].sum()}])
            month_summary = pd.concat([month_summary, total_row], ignore_index=True)

            month_summary.to_excel(writer, sheet_name=month, index=False)

    end = time.perf_counter()
    return end - start

def benchmark_optimized(df):
    start = time.perf_counter()
    excel_data = io.BytesIO()
    with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
        for month in sorted(df['Month'].unique()):
            month_df = df[df['Month'] == month]
            month_summary = month_df.groupby('category')['amount'].sum().reset_index()
            month_summary = month_summary.sort_values('amount', ascending=False)

            # Optimized approach
            month_summary.loc[len(month_summary)] = {'category': 'TOTAL', 'amount': month_summary['amount'].sum()}

            month_summary.to_excel(writer, sheet_name=month, index=False)

    end = time.perf_counter()
    return end - start

# Run benchmarks
print("Running current...")
t1 = benchmark_current(expenses_df)
print(f"Current approach: {t1:.4f}s")

print("Running optimized...")
t2 = benchmark_optimized(expenses_df)
print(f"Optimized approach: {t2:.4f}s")

print(f"Improvement: {(t1 - t2) / t1 * 100:.2f}%")
