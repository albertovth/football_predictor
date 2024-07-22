## Football Predictor

### Introduction
This repository contains Python scripts used to rank national football teams based on their historical performance, typically over a four-year period but adjustable in the script settings. The scripts are designed to generate updated Soccer Power Index (SPI - a term originally suggested by FiveThirtyEight, see full attribution below) rankings for national teams after FiveThirtyEight's equivalent repository ceased updates in 2023.

### Methodology
The ranking methodology accounts for goals scored and conceded to compute expected goals for and against, considering the match type and opponent quality. Friendlies contribute less to these calculations. Adjustments are made to normalize rewards and reduce biases, especially against lower-ranked teams. The calculations use an inverse Poisson distribution across 10,000 simulations to pit each team against all others. This process generates a Soccer Power Index (SPI) that informs rankings published in the accompanying CSV files, which also provide offensive and defensive metrics. These metrics are used in a Streamlit app to forecast individual matchups, through similarly extensive simulations, with outcomes assessed against a null hypothesis of a tie result, to determine the most likely scores.

### Data Sources and Attributions

#### Match Data Attribution
Updated match data for the simulation is sourced from the public repository by **Martj42** on GitHub, shared under the [Creative Commons Zero v1.0 Universal license](https://github.com/martj42/international_results/blob/master/LICENSE).
- **Repository Link**: [Martj42 GitHub Repository](https://github.com/martj42/international_results)
- **Data File**: [results.csv](https://raw.githubusercontent.com/martj42/international_results/master/results.csv)

#### Team Logos and Flags Attribution
The team logos and flags used are sourced from **Wikipedia**, shared under the [Creative Commons Attribution-ShareAlike License](https://creativecommons.org/licenses/by-sa/3.0/).
- **Source**: [Wikipedia](https://www.wikipedia.org)

#### Ranking Structure Attribution
The ranking concepts are based on **FiveThirtyEight's Soccer Power Index**, shared under a [CC-BY-4.0 license](https://creativecommons.org/licenses/by/4.0/).
- **Documentation and Data**: [FiveThirtyEight Soccer Power Index](https://github.com/fivethirtyeight/data/blob/master/soccer-spi/README.md)

#### Error handling and alternative approaches
OpenAI: The support and knowledge from the OpenAI platform have been instrumental in refining the model and exploring innovative approaches. OpenAI operates under a philosophy of open collaboration, fostering co-intelligence.

### Additional Information

- **Installation**: Backend data files are updated prior to significant international competitions. The match simulator is available at [Football Predictor](https://footballpredictor.streamlit.app/).

  To reproduce the process:
  1. Initialize the original SPI ranking by FiveThirtyEight using the initialization script (`init_from_spi_538.py`). Make sure to update file paths for your environment.
  2. Run the script to calculate xG and xGA (`calculate_xG_xGA.py`). Make sure to update file paths for your environment.
  3. Run the script to simulate matchups and calculate the updated SPI (`omnes_contra_omnium_spi.py`). Save the resulting ranking `spi_final.csv` as `ranking_final.csv`. Make sure to update file paths for your environment.
  4. Use `ranking_final.csv` (with an updated file path for your environment) in the script for the Streamlit app (`football_predictor.py`).

- **Contributing**: If interested in contributing, please contact [alberto@vthoresen.no](mailto:alberto@vthoresen.no).

### License
This project is open source and available under the [MIT License](https://opensource.org/licenses/MIT). The MIT License permits free use, modification, distribution, and private use of this software. It also ensures that the copyright notice and license text are included in any copies of the software or substantial portions of it. This license does not provide an express grant of patent rights from contributors.


