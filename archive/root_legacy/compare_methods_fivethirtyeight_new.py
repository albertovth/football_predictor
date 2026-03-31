import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import numpy as np

# Load datasets
file_new_path = '/home/albertovth/SPI/rankings/ranking_final.csv'
file_original_path = '/home/albertovth/SPI/spi_global_rankings_intl_25_5_2021.csv'
file_new = pd.read_csv(file_new_path)
file_original = pd.read_csv(file_original_path)

# Merge datasets on the 'name' column
merged_data = pd.merge(file_new, file_original, on='name', suffixes=('_new', '_original'))

# Create a function to plot and perform linear regression
def plot_regression(x, y, xlabel, ylabel, ax):
    # Scatter plot
    sns.scatterplot(x=x, y=y, ax=ax, color="blue")
    
    # Fit linear regression
    model = LinearRegression().fit(x[:, np.newaxis], y)
    xfit = np.linspace(x.min(), x.max(), 1000)
    yfit = model.predict(xfit[:, np.newaxis])
    ax.plot(xfit, yfit, color="red")
    
    # Add details
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(f'{ylabel} vs. {xlabel}')
    
    # Calculate R^2 value
    r2 = r2_score(y, model.predict(x[:, np.newaxis]))
    
    # Display regression equation and R^2
    slope, intercept = model.coef_[0], model.intercept_
    sign = '+' if intercept >= 0 else ''
    equation = f'y = {slope:.2f}x {sign}{intercept:.2f}\n$R^2 = {r2:.2f}$'
    ax.text(0.05, 0.95, equation, transform=ax.transAxes, fontsize=12, verticalalignment='top')


# Plotting
fig, axes = plt.subplots(3, 1, figsize=(10, 18))

# Variables for plotting
variables = [
    ('off_original', 'off_new', 'Off (Original)', 'Off (New)'),
    ('def_original', 'def_new', 'Def (Original)', 'Def (New)'),
    ('spi_original', 'spi_new', 'SPI (Original)', 'SPI (New)')
]

# Generate plots
for i, (x_var, y_var, xlabel, ylabel) in enumerate(variables):
    x = merged_data[x_var].values
    y = merged_data[y_var].values
    plot_regression(x, y, xlabel, ylabel, axes[i])

plt.tight_layout()
plt.show()
