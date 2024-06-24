import pandas as pd
from datetime import datetime, timedelta

# Load the match data
url = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
df = pd.read_csv(url)

# Load the confederations data
confed_df = pd.read_csv('/home/albertovth/SPI/confederations.csv')
confed_df.columns = ['team', 'confed']  # Make sure the columns are named correctly
print("Confederations DataFrame:")
print(confed_df.head())

# Filter data for the last two years
today = datetime.today()
two_years_ago = today - timedelta(days=2*365)
df['date'] = pd.to_datetime(df['date'])
filtered_df = df[df['date'] >= two_years_ago]

# Adjust goal counts based on match type
def adjust_goals(row):
    if row['tournament'] == 'Friendly':
        return row['home_score'] * 0.5, row['away_score'] * 0.5
    else:
        return row['home_score'], row['away_score']

filtered_df[['home_score', 'away_score']] = filtered_df.apply(lambda row: pd.Series(adjust_goals(row)), axis=1)

# Only include teams from the specified confederations
filtered_df = filtered_df[(filtered_df['home_team'].isin(confed_df['team'])) & (filtered_df['away_team'].isin(confed_df['team']))]

# Calculate proxy xG and xGA
xg_data = []

for index, row in filtered_df.iterrows():
    home_team = row['home_team']
    away_team = row['away_team']
    home_goals = row['home_score']
    away_goals = row['away_score']

    xg_data.append({'team': home_team, 'xG': home_goals, 'xGA': away_goals})
    xg_data.append({'team': away_team, 'xG': away_goals, 'xGA': home_goals})

xg_df = pd.DataFrame(xg_data)

# Aggregate data to get average xG and xGA per team
aggregated_data = xg_df.groupby('team').agg({
    'xG': 'mean',
    'xGA': 'mean'
}).reset_index()

# Merge with confederations data to filter out only the relevant teams
aggregated_data = aggregated_data.merge(confed_df, on='team')

# Save the aggregated data to a new CSV file
aggregated_data.to_csv('aggregated_xg_data.csv', index=False)

# Separate and save data for each confederation, without the 'confed' column
conmebol_teams = aggregated_data[aggregated_data['confed'] == 'CONMEBOL'].drop(columns=['confed'])
uefa_teams = aggregated_data[aggregated_data['confed'] == 'UEFA'].drop(columns=['confed'])
concacaf_teams = aggregated_data[aggregated_data['confed'] == 'CONCACAF'].drop(columns=['confed'])

conmebol_teams.to_csv('CONMEBOL.csv', index=False)
uefa_teams.to_csv('UEFA.csv', index=False)
concacaf_teams.to_csv('CONCACAF.csv', index=False)

print("Aggregated xG Data:")
print(aggregated_data.head())
print("Data saved to CONMEBOL.csv, UEFA.csv, and CONCACAF.csv.")