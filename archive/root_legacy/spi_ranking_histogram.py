import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
data = pd.read_csv('/home/albertovth/SPI/rankings/ranking_final.csv')

# Calculate the median for each column
medians = data[['off', 'def', 'spi']].median()

# Plot histograms for the specified columns
fig, axes = plt.subplots(3, 1, figsize=(8, 12))
columns = ['off', 'def', 'spi']

for i, col in enumerate(columns):
    axes[i].hist(data[col].dropna(), bins=20, alpha=0.75, color='blue')  # Adjust bin size as needed
    axes[i].axvline(medians[col], color='red', linestyle='dashed', linewidth=2)  # Add a line for the median
    axes[i].set_title(f'Histogram of {col}')
    axes[i].set_xlabel(col)
    axes[i].set_ylabel('Frequency')
    axes[i].text(medians[col], max(axes[i].get_ylim())*0.9, f'Median: {medians[col]:.2f}', color='red')  # Display median value

plt.tight_layout()
plt.show()
