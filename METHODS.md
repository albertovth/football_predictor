# Methods

## Overview

This project uses an advanced statistical model to predict football match outcomes and rank teams. The model utilizes historical match data and calculates offensive (xG) and defensive (xGA) metrics, which are then used in Monte Carlo simulations to forecast match results.

## Data Collection

The data is collected from publicly available sources, inspired by concepts from the Soccer Power Index (SPI) provided by FiveThirtyEight, until their project was paused. FiveThirtyEight's original SPI ranking from May 2021 is used as a starting point, and match results from that date onward are used with this project's method to update offensive and defensive methods and rankings.

### Sources
- Updated match data for the simulation comes from the public repository published by Martj42 in GitHub: [Martj42 GitHub repository](https://github.com/martj42/international_results), shared under the [Creative Commons Zero v1.0 Universal license](https://github.com/martj42/international_results/blob/master/LICENSE).

- The structure for the ranking, concepts, and initial ranking are borrowed from FiveThirtyEight data on the Soccer Power Index, shared with a [CC-BY-4.0 license](https://github.com/fivethirtyeight/data/blob/master/soccer-spi/README.md).

## Model Explanation

### Offensive and Defensive Metrics (xG and xGA)
- **Offensive (xG) and Defensive (xGA) Metrics**: These metrics represent the average goals for and against each team, respectively.
- **Reward Factor**: Goals are weighted based on the initial SPI ranking of the opponent. The reward factor multiplies goals scored by 2 times the opponent team's SPI divided by the 25th percentile SPI. This effectively weights goals from the lowest ranked team to the highest roughly as the 95th percentile max goals scored in the period (6).
- **Levelling Factor**: This is necessary because without this factor, low ranked teams get their goals against high ranked teams rewarded, but all goals against them are practically nullified. The levelling factor ensures that low ranked teams are rewarded for scoring against high ranked teams, but in a balanced manner. This factor implies subtracting 2 times the median SPI divided by the scoring team's SPI. The factor parallels the reward factor, but still allowing lower ranked teams to be rewarded for scoring against higher ranked teams.
- **Low SPI Teams Matches**: The code separates matches between teams that both have an SPI under the 25th percentile to avoid creating xG and xGA metrics that give too much importance to these matches. Goals against in such matches are set to 6 (95th percentile) and goals for to 1/6, the inverse of the 95th percentile.

### Monte Carlo Simulations
The Monte Carlo simulation method is used to predict match outcomes by running thousands of simulations for each match.

**Inverse Poisson Distribution with 10,000 random numbers**: This method is employed to simulate the number of goals scored in 10,000 matches between two teams at a time.
**Expected Goals Calculation**: The multiplicative method is used to calculate expected goals based on offensive and defensive metrics, factored by the median goals scored. Expected goals work as lambda for the Poisson distributions, obtained with random numbers and inverse Poisson.
**Simulation Runs**: Each match is simulated 10,000 times to ensure robustness of the predictions.
**Calculation of Soccer Power Index (SPI)**: Paralleling the concept developed by FiveThirtyEight, the Soccer Power Index (SPI) is calculated as the percentage of available points a team would get through the match simulations, when all teams play against all. Available points are 3 for wins and 1 for ties, for n-1 available teams. 
**Ranking based on SPI**: Teams are ranked from high to low, based on SPI. Most of the time a higher ranked team in terms of SPI will beat a lower ranked team in terms of SPI in the simulations. However, this relationship is not completely linear. Therefore, the project also includes a Streamlit-app, to simulate individual matchups.
**Streamlit-app to simulate matchups**: The Streamlit app is available [here](https://footballpredictor.streamlit.app/) This app uses the same methodology, based on an random numbers, inverse Poisson and expected goals, based on a multiplicative method. The starting point for the simulation is the offensive and defensive metrics in the team ranking. Each offensive and defensive metric is presented, factored by the median of goals scored by all teams during the given period.
**Hypotehsis testing in the Streamlit-app**: The null hypothesis is that a simulated match ends up in a tie, which is roughly equivalent to an equal amount of wins, ties and lossess in the 10,000 simulations, or [3333,3333,3334] (and permutations). The chi-squared statistic is used to test for significantly different results. If the simulations render a distribution that is significant, the team with most wins is chosen as a winner.
**Forecast Result**: The most frequent score for the selected outcome with hypothesis testing is used in the forecast result.

## Interpretations and Limitations
The model does not consider the number of games played and does not reward teams that qualify to later phases of tournaments. The result is that teams who do not qualify to final phases (like Mali, who did not qualify to the World Cup 2022, or Russia, who played fewer competitive matches due to a ban since 2022), might have a strong rating but based on fewer matches. However, this does not mean that the ranking of these teams is wrong. If other teams really are better because they have qualified and played more matches, this will reflect in the statistics. But care has to be taken when trying to forecast matches between teams that have more or less amount of historical data in the ranking. The model does not consider other external factors that might affect the outcome of matches. These factors can be home advantage, changes in team management, injuries and similar. These factors would considerably complicate the model, introducing bias and less availability of data. When interpreting results, it is therefore crucial to consider the possible effects that these factors can have. Please contact alberto@vthoresen.no if you have suggestions on how to enhance the model to consider more factors in balanced, empirical and unbiased ways. 
