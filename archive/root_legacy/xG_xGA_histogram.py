import pandas as pd
import matplotlib.pyplot as plt

# Load the data from the CSV file
file_path = '/home/albertovth/SPI/aggregated_xg_data.csv'  # Update the path as needed
data = pd.read_csv(file_path)

# Create histograms for the xG and xGA columns
plt.figure(figsize=(12, 6))

# Histogram for xG
plt.subplot(1, 2, 1)  # 1 row, 2 columns, 1st subplot
plt.hist(data['xG'], bins=20, color='blue', alpha=0.7)
plt.title('Histogram of xG (Adjusted Expected Goals)')
plt.xlabel('xG')
plt.ylabel('Frequency')

# Histogram for xGA
plt.subplot(1, 2, 2)  # 1 row, 2 columns, 2nd subplot
plt.hist(data['xGA'], bins=20, color='red', alpha=0.7)
plt.title('Histogram of xGA (Adjusted Expected Goals Against)')
plt.xlabel('xGA')

plt.tight_layout()
plt.show()
