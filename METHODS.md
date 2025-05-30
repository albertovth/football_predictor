# Methods

## Overview

This project uses a statistical model that follows a Bayesian-logic - starting with an initial belief (prior), incorporating new data (evidence), and updating the belief to form a new estimate (posterior). The approach proceeds through three key steps: 1) estimate offensive and defensive metrics for football national teams, based on prior rankings and historical data on match results; 2) predict football match outcomes, on the basis of these metrics, using Monte Carlo simulations; and 3) rank teams, according to their simulated performance. 

## Data Collection

The data is collected from publicly available sources, inspired by concepts from the Soccer Power Index (SPI), provided by FiveThirtyEight, until their project was paused in 2023. FiveThirtyEight's original SPI ranking from May 2021 is used as a starting point, and match results from that date onward are used with this project's method, to update offensive and defensive metrics and rankings.

### Sources
- Updated match data for the simulation comes from the public repository published by Martj42 in GitHub: <a href="https://github.com/martj42/international_results" target="_blank">Martj42 GitHub repository</a>, shared under the <a href="https://github.com/martj42/international_results/blob/master/LICENSE" target="_blank">Creative Commons Zero v1.0 Universal license</a>.

- The structure for the ranking, concepts, and initial ranking are borrowed from FiveThirtyEight data on the Soccer Power Index, shared with a <a href="https://github.com/fivethirtyeight/data/blob/master/LICENSE" target="_blank">CC-BY-4.0 license</a>. The dataset is available in the <a href="https://github.com/fivethirtyeight/data/blob/master/soccer-spi/README.md" target="_blank">FiveThirtyEight Soccer Power Index README</a>.


## Model Explanation

## Clarification of Metrics

It is important to note that in this project, the terms "xG" and "xGA" are used to denote offensive and defensive metrics that are based on the goals scored and conceded by a team, respectively, over a given period. These metrics are adjusted for opponent strength and other factors, rather than being derived from shot-based probabilities.

This usage is distinct from the conventional football analytics metrics "expected goals" (xG) and "expected goals against" (xGA), which are calculated based on the quality and quantity of individual shots taken and faced by a team. The latter metrics estimate the likelihood of scoring from a given shot or conceding from a given shot, considering various contextual factors such as shot location, type, and assist type.

The approach in this project, of using adjusted averages, provides a straightforward and computationally efficient way to evaluate team performance over time, and is particularly useful in the context of simulating match outcomes and ranking teams.

### Offensive and Defensive Metrics (xG and xGA)
- **Goals scored and goals received**: Goals scored and goals received are computed for each match and team, for the given period.
    
- **Reward Factor**: Goals are weighted based on the initial SPI ranking of the opponent. The reward factor multiplies goals scored by an adjustment factor, times the opponent team's SPI divided by the minimum SPI. The goal of this adjustment is to effectively weigh goals, based on the difficulty implied in scoring them. The reward factor has an adjustment factor, that is calculated to ensure that the weighted goals are within the range of the 95th percentile of goals scored in a match, once a levelling factor is considered.
  
- **Levelling Factor**: This is necessary because without this factor, low ranked teams get their goals against high ranked teams rewarded, but all goals against them are practically nullified. This would overvalue their defense disproportionally, making them climb too fast on the rankings. The levelling factor ensures that low ranked teams are rewarded for scoring against high ranked teams, but in a balanced manner. This factor implies subtracting the adjustment factor times the maximum SPI divided by the scoring team's SPI. This factor levels the reward factor, based on initial ranking, but still allowing lower ranked teams to be rewarded for scoring against higher ranked teams.

- **Correction Factor**: The correction factor adjusts for the expected number of goals, considering the strength of the opponents faced. While the reward and levelling factors account for the difficulty of actual goals scored, the correction factor ensures fairness by correcting for the number of goals that could be expected if all teams played a balanced set of opponents. This is necessary because not all teams play against each other equally. Without this correction, teams playing mostly high-ranked opponents would be unfairly penalized on defense, while those playing mostly low-ranked opponents would be unfairly rewarded. Similarly, high-ranked teams would also have scored more goals if they played more low-ranked teams, and low-ranked teams would have scored comparatively fewer goals if they played top-ranked ones. By correcting xG and xGA based on the average and median SPI of the opponents faced, the model accounts for these discrepancies, ensuring a more accurate and fair evaluation of team performance.
  
- **Low SPI Teams Matches**: The model separates matches between teams that both have an SPI under a cutoff percentile, to avoid creating xG and xGA metrics that give too much importance to these matches. Goals against in such matches are set to the 95th percentile goals scored per match, and goals for to the inverse of the 95th percentile. This means that teams under the cutoff percentile must play and score against better ranked teams, in order to make progress in the ranking. This might seem too unfair, but it reflects the difficulty in practice of making progress in the ranking, once a team is in the bottom end, in terms of SPI. This also avoids that teams that only play teams in the bottom of the ranking get unfairly high offensive and unfairly low defensive metrics. The cutoff percentile (the 7th, for the original dataset) is calculated to ensure that no teams with xG under 1 also get xGA under 1, which indicates the imbalance that arises for teams under the cutoff percentile who mostly play teams under the cutoff percentile SPI. 
   
### Considerations for Weighting Goals in xG and xGA Calculations

In the calculation of offensive (xG) and defensive (xGA) metrics, goals are weighted based on the opponent's Soccer Power Index (SPI), for the reward factor, and the scoring team’s SPI, for the leveling factor. This approach was chosen, for several reasons:

1. **Comprehensive Measure**: SPI is a combined measure of a team's offensive and defensive capabilities. By using SPI, the model accounts for the overall strength and dynamics of the team, rather than isolating offensive or defensive metrics.

2. **Dynamic Interactions**: Football matches are complex, with dynamic interactions between a team's offensive and defensive strengths. A team with a strong offense can indirectly bolster its defense, by maintaining control of the game. Using SPI helps capture these interactions, providing a holistic view of team strength.

3. **Simplicity and Consistency**: Using SPI simplifies the calculations, making the model more straightforward and easier to understand. It ensures consistency in how goals are weighted across different matches.

### Alternative Approach Considered

An alternative approach considered was to calculate the reward factor, based on the opponent's defensive metrics, and the leveling factor, based on the scoring team's offensive metrics. While this might seem to offer more precision, by specifically targeting each team's strengths and weaknesses, it was decided against for the following reasons:

- **Dynamic Complexity**: A team's defensive strength can be influenced by its offensive capabilities and vice versa. By using separate metrics, the model might miss out on capturing these interdependencies.
- **Over-Simplification**: Using only defensive metrics for the reward factor might oversimplify the evaluation, not fully acknowledging the combined effect of a team's overall strength as reflected in the SPI.

By prioritizing a combined measure through SPI, the model aims to balance precision with a comprehensive view of team dynamics. This decision ensures that both offensive and defensive strengths are considered, reflecting a truer nature of football matches.

### Monte Carlo Simulations
The Monte Carlo simulation method is used to predict match outcomes by running thousands of simulations for each match.

1. **Inverse Poisson Distribution with 10,000 random numbers**: This method is employed to simulate the number of goals scored in 10,000 matches between two teams at a time. The Monte Carlo simulations employ a univariate Poisson distribution to estimate the goal probabilities for each team. This process is informed by the expected goals for each team.
   
2. **Expected Goals Calculation**: In the simulations, the additive method is employed to calculate expected goals. This method involves averaging the number of goals a team might score against an average team and the number of goals the opponent typically concedes to an average team. This approach provides a central tendency that serves effectively as the lambda for the Poisson distribution used in the simulation. Given that offensive (off) and defensive (def) metrics are scaled to the median goals scored, they reflect the relative strengths of the teams. Additionally, these metrics are capped based on the distribution of observed goals in real matches. The additive method, therefore, offers a balanced and realistic estimate of expected goals, taking into account both the scoring potential and defensive capabilities of the teams involved.
   
3. **Simulation Runs**: Each match is simulated 10,000 times to ensure robustness of the predictions.
   
4. **Calculation of Soccer Power Index (SPI)**: Paralleling the concept developed by FiveThirtyEight, the Soccer Power Index (SPI) is calculated as the percentage of available points a team would get through the match simulations, when all teams play against all. Available points are 3 for wins and 1 for ties, for (n-1) available teams.
   
5. **Ranking based on SPI**: Teams are ranked from high to low, based on SPI. Most of the time, a higher ranked team in terms of SPI will beat a lower ranked team in terms of SPI in the simulations. However, this relationship is not completely linear. Therefore, the project also includes a Streamlit-app, to simulate individual matchups.
   
6. **Streamlit-app to simulate matchups**: The Streamlit app is available <a href="https://footballpredictor.streamlit.app/" target="_blank">here</a>. This app uses the same methodology, based on random numbers, inverse Poisson and expected goals. The starting point for the simulation is the offensive and defensive metrics in the team ranking. Each offensive and defensive metric is presented in a table, together with each team's SPI.
    
7. **Hypothesis testing in the Streamlit-app**: The null hypothesis is that a simulated match ends up in a tie, which is roughly equivalent to an equal amount of wins, ties and losses in the 10,000 simulations, or [3333,3333,3334] (and permutations). The chi-squared statistic is used to test for significantly different results. If the simulations render a distribution that is significantly different from a tie, the team with most wins is chosen as a winner.
    
8. **Forecast Result**: The most frequent score for the selected outcome with hypothesis testing is used in the forecast result. Note that the differences in frequencies between possible scores are often small, and probably not significant. The exact score forecast will therefore not be significantly confident, but it is a starting point. It is important to remember that the result forecast (winner or tie) is indeed significant, as explained above. However, it will generally be useful to see different possible and probable scores, intepret these results, and consider the effect of other external variables. Rather than the diagonal inflated bivariate Poisson regression to estimate the probability of different scores, [purportedly used by FiveThirtyEight](https://fivethirtyeight.com/features/its-brazils-world-cup-to-lose/), the approach in this project is to calculate univariate Poisson distributions for each team. This is used to compare scores. Additionally, the univariate Poisson distributions are used to calculate a joint Poisson distribution, for all possible scores. In this approach, the probability of each score is calculated as the joint probability of each team's score, `p1 * p2`, treating the scores as independent events. But this does not mean that the probabilities are completely independent, considering that the adjusted expected goals already account for interactions between the opposing teams' offensive and defensive ratings. This method simplifies the comparison of team strengths, introducing less complexity and reducing potential biases from additional parameters.
   
Some critics might argue that not using the bivariate inflated Poisson model can give undue importance to ties, as referenced in [Karlis and Ntzoufras (2003)](https://doi.org/10.1111/1467-9884.00366), who noted that using a bivariate Poisson distribution can improve model fit and the prediction of the number of draws in football games. However, even when the [suitability of the bivariate Poisson is demonstrated](https://www.jstor.org/stable/43965722), it is not evident that this is necessarily better in practice, than using univariate Poisson models, which have also [been demonstrated as a good approximation for football scores](https://doi.org/10.1111/j.1467-9574.1982.tb00782.x), and then calculating a joint distribution, as suggested in this project's approach. Therefore, the simplicity and transparency of the univariate Poisson approach are prioritized here. When predicting individual matchups, ties are addressed through significance testing, as explained above, to ensure the robustness and reliability of the predictions.

### Rationale for Using Univariate Poisson Models

The model employs univariate Poisson distributions for modeling the number of goals scored by each team, rather than the diagonal inflated bivariate Poisson regression. This decision is based on several considerations:

1. **Complexity and Assumptions**: Bivariate Poisson models introduce a correlation parameter to capture interdependencies between the number of goals scored by two teams. However, the direction and magnitude of this correlation are not always straightforward and can vary depending on match context, team strategies, and other factors. According to [Karlis and Ntzoufras, 2003](http://www2.stat-athens.aueb.gr/~karlis/Bivariate%20Poisson%20Regression.pdf), "empirical evidence shows small and not significant correlation (usually less than 0.05)", they go on to say that "even so small correlation can have impact to the results", but it is unclear why this should be "more realistic", when we do not know the exact direction and form of the proposed correlation.

2. **Dynamic Nature of Football**: The dynamics within a football match are complex and not easily captured by simple correlations. Teams might change their strategies based on the match situation, player conditions, and tactical decisions. Introducing a correlation parameter might overcomplicate the model, without necessarily improving its predictive power.

3. **Simplicity and Transparency**: Treating the number of goals scored by each team as independent events simplifies the model and makes it more transparent. This approach focuses on the core probabilistic events without adding layers of assumptions that may not be supported by empirical data. This priorizes the attitude summarized in the motto "plurality should not be posited without necessity", often referred to as [Occam's razor](https://en.wikipedia.org/wiki/Occam%27s_razor)

4. **Empirical Evidence**: Simple Poisson models have been demonstrated as a good approximation for football scores (Maher, 1982). While some studies suggest that bivariate Poisson models can improve fit and prediction of draws (Karlis & Ntzoufras, 2003), the empirical advantage of such models over simpler ones is not always clear-cut. Additionally, [Karlis and Ntzoufras (2003)](https://doi.org/10.1111/1467-9884.00366) acknowledge that the inflated bivariate Poisson model attempts to correct overdispersion as well, even when this is negligible in practice. Introducing overdispersion correction unnecessarily adds another layer of complexity, and requires robust empirical data to estimate accurately, which may not always be available. 

By prioritizing simplicity and transparency, the model aims to provide robust and interpretable predictions without introducing unnecessary complexity. When predicting individual matchups, ties are addressed through significance testing, as explained above, to ensure the robustness and reliability of the predictions.

## Interpretations and Limitations
- **Number of matches by team in historical data:** The model does not consider the number of matches played by a team, and does not reward teams that qualify to later phases of tournaments. The result is that teams who do not qualify to final phases (like Mali, who did not qualify to the World Cup 2022, or Russia, who played fewer competitive matches, due to a ban since 2022), might get a strong rating, but based on fewer matches. This limitation is however mitigated with the correction factor, if these teams do not get to meet higher ranked teams (see explanation under "Clarification of metrics" and below, which is repeated below, for clarity).

- **External factors:** The model does not consider other external factors that might affect the outcome of matches. Such external factors can include home advantage, changes in team management, injuries and similar. These factors would considerably complicate the model, introducing bias and less availability of data. When interpreting results, it is therefore crucial to consider the possible effects that these factors can have for individual match ups.

- **Fair consideration of low- and mid-tier teams:** The model is based on a theoretical assumption that all teams get to play all teams. In practice, this is not the case, and it is unlikely that very low-ranked teams get to play very high-ranked teams. Therefore, the model corrects for low-ranked teams, under the 7th percentile, that mostly play low-ranked teams, under the 7th percentile. The purpose of this correction is to avoid rewarding very low-ranked teams unfairly, with too low defensive metrics, that would inevitably result from the low weight given to the scores of the very low-ranked opponents. This makes it so that very low ranked teams must play and perform consistently well with teams above the 7th percentile, in order to start climbing on the ranking. This makes the ranking more realistic.

- **Correction Factor**: The correction factor ensures fairness by correcting for the number of goals that could be expected if all teams played a balanced set of opponents. This is necessary because not all teams play against each other equally. Without this correction, teams playing mostly high-ranked opponents would be unfairly penalized on defense, while those playing mostly low-ranked opponents would be unfairly rewarded. Similarly, high-ranked teams would also have scored more goals if they played more low-ranked teams, and low-ranked teams would have comparatively scored fewer goals if they played top-ranked ones. By correcting xG and xGA based on the average and median SPI of the opponents faced, the model accounts for these discrepancies, ensuring a more accurate and fair evaluation of team performance.

Please contact alberto@vthoresen.no if you have suggestions on how to enhance the model, to consider more factors in balanced, empirical and unbiased ways.
