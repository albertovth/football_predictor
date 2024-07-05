import streamlit as st
import streamlit.components.v1 as components
from typing import List, Any
import pandas as pd
import ssl
from googlesearch import search
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
import random
from scipy.stats import poisson
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import scipy.linalg as la
from itertools import product
from scipy import stats
import altair as alt
import time
import urllib
import wikipedia
import unicodedata
import math

st.title('Football Match Predictor')
st.title('National Teams')
ssl._create_default_https_context = ssl._create_unverified_context

spi_global_rankings_intl = pd.read_csv(
    "https://raw.githubusercontent.com/albertovth/football_predictor/main/ranking_final.csv")
spi_global_rankings_intl.columns = ['rank', 'name', 'confed', 'off', 'defe', 'spi']
print(spi_global_rankings_intl)

# Extract necessary columns
spi = spi_global_rankings_intl[['rank', 'name', 'off', 'defe', 'spi']]

spi.sort_values(by=['spi'], ascending=False, inplace=True)
spi = spi.reset_index(drop=True)


st.markdown("You can simulate matches by selecting teams with the drop-down lists provided under the table presented below.")

@st.cache_data
def load_data():
    return spi

df_pf=load_data()

Equipo_casa = df_pf['name']

Equipo_visita = df_pf['name']

# CSS to inject contained in a string
hide_dataframe_row_index = """
            <style>
            .row_heading.level0 {display:none}
            .blank {display:none}
            </style>
            """

# Inject CSS with Markdown
st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)

# Display an interactive table
st.dataframe(spi)

st.subheader('Simulate match\nSelect teams')
st.markdown("The system will automatically run a simulation\nonce you select teams. \nYou can also rerun the simulation\nwith the buttons provided below. You can also remove your selection, and start over.\nResults will appear at the bottom of the screen. In some cases this may take some time, depending on your connection.")

params={
    'equipo_casa' : st.selectbox('Home team', Equipo_casa),
    'equipo_visita' : st.selectbox('Visiting team', Equipo_visita)
}


if st.button("Run or rerun simulation, based on your selection"):
    equipo_casa_input = params['equipo_casa']
    equipo_visita_input = params['equipo_visita']
else:
    equipo_casa_input = "None"
    equipo_visita_input = "None"

if st.button("Remove selection"):
    equipo_casa_input = "None"
    equipo_visita_input = "None"
else:
    equipo_casa_input = params['equipo_casa']
    equipo_visita_input = params['equipo_visita']

st.markdown("You have registered the following home team: " + equipo_casa_input)
st.markdown("You have registered the following visiting team: " + equipo_visita_input)

latest_iteration = st.empty()
bar = st.progress(0)


latest_iteration2 = st.empty()
bar2 = st.progress(0)

input = ['Afghanistan', 'Albania', 'Algeria', 'Samoa', 'Andorra', 'Angola', 'Anguilla', 'Antigua and Barbuda', 'Argentina', 'Armenia', 'Aruba', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados', 'Basque Country', 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bermuda', 'Bhutan', 'Bolivia', 'Bonaire', 'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'British Virgin Islands', 'Brunei', 'Bulgaria', 'Burkina Faso', 'Burundi', 'Cambodia', 'Cameroon', 'Canada', 'Cape Verde Islands', 'Cayman Islands', 'Central African Republic', 'Chad', 'Chile', 'China PR', 'Chinese Taipei', 'Colombia', 'Comoros', 'Congo', 'Congo DR', 'Cook Islands', 'Costa Rica', 'Croatia', 'Cuba', 'Curacao', 'Cyprus', 'Czech Republic', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador', 'England', 'Equatorial Guinea', 'Eritrea', 'Estonia', 'Ethiopia', 'Faroe Islands', 'Fiji', 'Finland', 'France', 'French Guiana', 'Gabon', 'Gambia', 'Georgia', 'Germany', 'Ghana', 'Gibraltar', 'Greece', 'Grenada', 'Guadeloupe', 'Guam', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti', 'Honduras', 'Hong Kong', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran', 'Iraq', 'Israel', 'Italy', 'Ivory Coast', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kosovo', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Latvia', 'Lebanon', 'Lesotho', 'Liberia', 'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Macau', 'Madagascar', 'Malawi', 'Malaysia', 'Maldives', 'Mali', 'Malta', 'Martinique', 'Mauritania', 'Mauritius', 'Mexico', 'Moldova', 'Mongolia', 'Montenegro', 'Montserrat', 'Morocco', 'Mozambique', 'Myanmar', 'Namibia', 'Nepal', 'Netherlands', 'New Caledonia', 'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'North Korea', 'North Macedonia', 'Northern Ireland', 'Northern Mariana Islands', 'Norway', 'Oman', 'Pakistan', 'Palestine', 'Panama', 'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines', 'Poland', 'Portugal', 'Puerto Rico', 'Qatar', 'Rep of Ireland', 'Romania', 'Russia', 'Rwanda', 'San Marino', 'Sao Tome and Principe', 'Saudi Arabia', 'Scotland', 'Senegal', 'Serbia', 'Seychelles', 'Sierra Leone', 'Singapore', 'Sint Maarten', 'Slovakia', 'Slovenia', 'Solomon Islands', 'Somalia', 'South Africa', 'South Korea', 'South Sudan', 'Spain', 'Sri Lanka', 'St. Kitts and Nevis', 'St. Lucia', 'St. Martin', 'St. Vincent and the Grenadines', 'Sudan', 'Suriname', 'Swaziland', 'Sweden', 'Switzerland', 'Syria', 'Tahiti', 'Tajikistan', 'Tanzania', 'Thailand', 'Timor-Leste', 'Togo', 'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Turks and Caicos Islands', 'Tuvalu', 'Uganda', 'Ukraine', 'United Arab Emirates', 'Uruguay', 'US Virgin Islands', 'USA', 'Uzbekistan', 'Vanuatu', 'Venezuela', 'Vietnam', 'Wales', 'Yemen', 'Zambia', 'Zanzibar', 'Zimbabwe', 'Bayern Munich', 'Manchester City', 'Paris Saint-Germain', 'Liverpool', 'Barcelona', 'Real Madrid', 'Ajax', 'Tottenham Hotspur', 'FC Salzburg', 'Chelsea', 'Arsenal', 'Internazionale', 'Atletico Madrid', 'FC Porto', 'Napoli', 'Borussia Dortmund', 'Villarreal', 'AC Milan', 'RB Leipzig', 'Sporting CP', 'Benfica', 'Brighton and Hove Albion', 'Celtic', 'PSV', 'Zenit St Petersburg', 'Manchester United', 'Real Sociedad', 'Athletic Bilbao', 'Bayer Leverkusen', 'Lyon', 'Newcastle', 'Atalanta', 'Stade Rennes', 'Marseille', 'AS Roma', 'Feyenoord', 'Real Betis', 'West Ham United', '1. FC Union Berlin', 'SC Freiburg', 'Aston Villa', 'Crystal Palace', 'Valencia', 'Borussia Monchengladbach', 'Club Brugge', 'Juventus', 'Lazio', 'Brentford', 'AS Monaco', 'Celta Vigo', 'Flamengo', 'TSG Hoffenheim', 'FC Cologne', 'Lille', 'Rangers', 'Eintracht Frankfurt', 'Lens', 'Osasuna', 'Mainz', 'Sevilla FC', 'Braga', 'Wolverhampton', 'Leicester City', 'Fiorentina', 'VfB Stuttgart', 'VfL Wolfsburg', 'Strasbourg', 'Fenerbahce', 'AZ', 'FC Twente', 'Slavia Prague', 'Leeds United', 'Monterrey', 'Nice', 'Southampton', 'Club América', 'Everton', 'Dinamo Zagreb', 'Torino', 'Palmeiras', 'Genk', 'Udinese', 'Young Boys', 'Rayo Vallecano', 'Atletico Mineiro', 'Werder Bremen', 'Internacional', 'Shakhtar Donetsk', 'Fulham', 'Hertha Berlin', 'Espanyol', 'Getafe', 'Girona FC', 'Norwich City', 'Philadelphia Union', 'Sassuolo', 'Almeria', 'Slovácko', 'Verona', 'São Paolo', 'Nantes', 'Schalke 04', 'Fluminense', 'Tigres UANL', 'Mallorca', 'Pachuca', 'CSKA Moscow', 'Steaua Bucuresti', 'Olympiacos', 'Sheffield United', 'River Plate', 'Red Star Belgrade', 'Real Valladolid', 'Reims', 'Trabzonspor', 'FC Augsburg', 'Spartak Moscow', 'FC Utrecht', 'Anderlecht', 'Antwerp', 'West Bromwich Albion', 'VfL Bochum', 'Cadiz', 'Corinthians', 'Ferencvaros', 'SC Dnipro-1', 'Lorient', 'Molde', 'Istanbul Basaksehir', 'Bodo/Glimt', 'Bragantino', 'Dynamo Kiev', 'Nottingham Forest', 'Watford', 'Bologna', 'Los Angeles FC', 'Viktoria Plzen', 'AFC Bournemouth', 'KAA Gent', 'FC Sheriff Tiraspol', 'Elche', 'FC Copenhagen', 'Kawasaki Frontale', 'Montpellier', 'SK Sturm Graz', 'Besiktas', 'Troyes', 'Toulouse', 'Burnley', 'Yokohama F. Marinos', 'Vitesse', 'Sampdoria', 'Guimaraes', 'Gil Vicente', 'Lecce', 'Brest', 'Angers', 'FC Krasnodar', 'Santos', 'Galatasaray', 'Ceará', 'Dinamo Moscow', 'Guadalajara', 'FC Midtjylland', 'Levante', 'AC Ajaccio', 'FK Partizan Belgrade', 'LASK Linz', 'Fortaleza', 'Santos Laguna', 'Union Saint Gilloise', 'Atlético Paranaense', 'Urawa Red Diamonds', 'Clermont Foot', 'Sochi', 'Cremonese', 'Empoli', 'Heerenveen', 'New York City FC', 'Middlesbrough', 'Konyaspor', 'Salernitana', 'Lech Poznan', 'Auxerre', 'NEC', 'Montreal Impact', 'América Mineiro', 'Portimonense', 'Monza', 'Famalicao', 'Rostov', "Hapoel Be'er", 'Basel', 'Spezia', 'St Etienne', 'Chaves', 'Vizela', 'Cuiaba', 'Rosenborg', 'León', 'Boca Juniors', 'Apollon Limassol', 'Estoril Praia', 'Cagliari', 'St Gallen', 'Bordeaux', 'Hamburg SV', 'Metz', 'Santa Clara', 'Botafogo', 'PAOK Salonika', 'Puebla', 'Maccabi Haifa', 'Granada', 'Boavista', 'New York Red Bulls', 'FK Austria Vienna', 'Rio Ave', 'Nashville SC', 'Adana Demirspor', 'Panathinaikos', 'Sparta', 'Los Angeles Galaxy', 'Atlas', 'Silkeborg', 'FC Groningen', 'RKC', 'Cruz Azul', 'Parma', 'Sochaux', 'Casa Pia', 'Rapid Vienna', 'Atlanta United FC', 'Sporting de Charleroi', 'Lokomotiv Moscow', 'AEK Athens', 'Millwall', 'Randers FC', 'Huracán', 'Luton Town', 'Preston North End', 'Austin FC', 'Toluca', 'Sanfrecce Hiroshima', 'Emmen', 'FK Qarabag', 'Stoke City', 'Pumas Unam', 'Velez Sarsfield', 'AEK Larnaca', 'Alanyaspor', 'FC Nordsjaelland', 'Genoa', 'Go Ahead Eagles', 'Bristol City', 'Antalyaspor', 'Wolfsberger AC', 'Seattle Sounders FC', 'Racing Club', 'St. Truidense', 'Cerezo Osaka', 'Valerenga', 'Queens Park Rangers', 'Coventry City', 'CFR 1907 Cluj', 'Cambuur Leeuwarden', 'Aberdeen', 'Necaxa', 'Caen', 'Estudiantes', 'Columbus Crew', 'Kashima Antlers', 'FC Dallas', 'Terek Grozny', 'Orlando City SC', 'Djurgardens IF', 'Tijuana', 'Atlético Goianiense', 'Talleres de Córdoba', 'Tigre', 'Gazisehir Gaziantep', 'Kasimpasa', 'Swansea City', 'Argentinos Juniors', 'Brondby', 'Krylia Sovetov', 'New England Revolution', 'FC Volendam', 'Maritimo', 'SV Darmstadt 98', 'Hammarby', 'Ludogorets', 'Portland Timbers', 'Goiás', 'San Lorenzo', 'FC Cincinnati', 'Lillestrom', 'FC Arouca', 'Cardiff City', 'Blackburn', 'CA Independiente', 'Minnesota United FC', 'Excelsior', 'OH Leuven', 'Eibar', 'Alavés', 'Hearts', 'Real Salt Lake', 'Coritiba', 'KV Mechelen', 'Blackpool', 'Chicago Fire', 'FC Zurich', 'BK Hacken', 'Pacos Ferreira', 'Brescia', 'Viborg', 'Sheffield Wednesday', 'Sunderland', 'SC Paderborn', 'Fortuna Düssseldorf', 'Las Palmas', 'Benevento', 'Ipswich Town', 'Frosinone', 'Standard Liege', 'Fortuna Sittard', 'Querétaro', 'FC Luzern', 'Colorado Rapids', 'Huddersfield Town', 'Avaí', 'Hibernian', 'Slovan Bratislava', 'FC St. Pauli', 'FC Juárez', 'Sporting Kansas City', 'Gimnasia La Plata', "Newell's Old Boys", 'Kayserispor', 'Aris Salonika', 'Paris FC', 'FK Nizhny Novgorod', 'Mamelodi Sundowns', 'Union Santa Fe', 'Toronto FC', 'Hull City', 'Viking FK', 'Derby County', 'Real Oviedo', 'AaB', 'Omonia Nicosia', 'Guingamp', 'Le Havre', 'Juventude', 'Defensa y Justicia', 'Wigan', 'Real Zaragoza', 'F.B.C Unione Venezia', 'Lanus', 'Arminia Bielefeld', 'Servette', 'Malmo FF', 'Fatih Karagümrük', 'IFK Goteborg', 'IF Elfsborg', 'Mazatlán FC', 'Sagan Tosu', 'FC Tokyo', 'SD Huesca', 'KVC Westerlo', 'Rosario Central', 'Reading', 'Karlsruher SC', 'Atlético San Luis', 'Amiens', 'SK Austria Klagenfurt', 'Inter Miami CF', 'Austria Lustenau', 'AGF Aarhus', 'WSG Swarovski Wattens', 'Cercle Brugge', 'Sivasspor', 'Sporting Gijón', 'Nagoya Grampus Eight', 'Birmingham', 'Godoy Cruz', 'Livingston', 'Dijon FCO', 'FC Lugano', 'FC Cartagena', 'Rigas Futbola Skola', 'Banfield', '1. FC Heidenheim 1846', 'Rotherham United', 'Platense', 'Hatayspor', 'FC Sion', 'Hartberg', 'Central Córdoba Santiago del Estero', 'Grasshoppers Zürich', 'Stromsgodset', 'Ballkani', 'FC Khimki', 'AIK', 'Leganes', 'Motherwell', 'Vancouver Whitecaps', 'Colon Santa Fe', 'Charlotte FC', 'Ascoli', 'San Jose Earthquakes', 'Vissel Kobe', 'Tenerife', 'Sarmiento', 'Zalgiris Vilnius', 'Patronato', 'Cittadella', 'Atlético Tucumán', 'Portsmouth', 'KV Oostende', 'KV Kortrijk', 'Barnsley', '1. FC Nürnberg', 'DC United', 'Shimizu S-Pulse', 'Spal', 'Odense BK', 'Arsenal Sarandi', 'Fakel Voronezh', 'Hannover 96', 'Nimes', 'Ross County', 'Houston Dynamo', 'Ternana', 'Haugesund', 'SV Ried', 'Reggina', 'Pisa', 'Giresunspor', 'Holstein Kiel', 'Bari', 'Ural Sverdlovsk Oblast', 'Sarpsborg', 'Barracas Central', 'Kashiwa Reysol', 'SpVgg Greuther Fürth', 'Melbourne City', 'Kilmarnock', 'Gazovik Orenburg', 'AC Horsens', 'Ankaragucu', 'St Mirren', 'Tromso', 'Volos NFC', 'SD Ponferradina', 'Valenciennes', 'Burgos', 'Perugia', 'SV Zulte Waregem', 'Tampa Bay Rowdies', 'Umraniyespor', 'St Johnstone', 'Kalmar FF', 'Villarreal B', 'Peterborough United', 'Consadole Sapporo', 'Mirandes', 'Atromitos', 'UD Ibiza', 'Bastia', 'IFK Norrkoping', 'Louisville City FC', 'Bolton', 'Dundee Utd', 'Málaga', 'Guangzhou Evergrande', 'HJK Helsinki', 'Albacete', 'Cashpoint SC Rheindorf Altach', 'Odd BK', 'Grenoble', 'Eupen', 'Ionikos FC', 'Milton Keynes Dons', 'Wycombe Wanderers', 'FC Vaduz', 'Lyngby', 'Kyoto Purple Sanga', 'Asteras Tripolis', 'Como', 'Istanbulspor', 'Panetolikos', 'Hansa Rostock', 'FC Andorra', 'Avispa Fukuoka', 'Shonan Bellmare', 'Racing Santander', 'Plymouth Argyle', 'Lugo', 'Modena', 'Torpedo Moskow', 'San Diego Loyal SC', 'Aalesund', 'Sydney FC', 'Oxford United', 'Annecy', 'Hamarkamaratene', 'Pau', 'Aldosivi', 'Palermo', 'Laval', 'Melbourne Victory', 'Beijing Guoan', 'Kristiansund BK', 'Gamba Osaka', 'Giannina', 'San Antonio FC', 'Birmingham Legion FC', 'Niort', 'Mjallby', 'Jahn Regensburg', 'Cosenza', 'Shanghai SIPG', 'SV Sandhausen', 'RFC Seraing', 'Charlton Athletic', 'Rodez', 'OFI Crete', 'Sudtirol', '1. FC Kaiserslautern', 'Salford City', 'Orlando Pirates', 'US Quevilly', 'Sandefjord', 'Levadiakos', 'Rio Grande Valley FC Toros', 'Pittsburgh Riverhounds', 'Pyunik Yerevan', 'Memphis 901 FC', 'Western Sydney FC', 'Western United', 'Adelaide United', 'IK Sirius', 'Central Coast Mariners', 'Sacramento Republic FC', 'Kaizer Chiefs', 'SuperSport United', 'Newcastle Jets', 'Shrewsbury Town', 'Shamrock Rovers', 'Eintracht Braunschweig', 'Oakland Roots', 'Miami FC', 'New Mexico United', 'Colorado Springs Switchbacks FC', '1. FC Magdeburg', 'IFK Värnamo', 'Lincoln City', 'Jubilo Iwata', 'Shandong Luneng', 'Jiangsu Suning FC', 'Black Aces', 'Mansfield Town', 'Fleetwood Town', 'Exeter City', 'Lamia', 'Winterthur', 'Cambridge United', 'Varbergs BoIS FC', 'Brisbane Roar', 'El Paso Locomotive FC', 'Cheltenham Town', 'Leyton Orient', 'Doncaster Rovers', 'Bristol Rovers', 'Macarthur FC', 'Stellenbosch FC', 'Accrington Stanley', 'Arizona United', 'Northampton Town', 'Detroit City FC', 'Swindon Town', 'Port Vale', 'Orange County SC', 'AmaZulu', 'Golden Arrows', 'Degerfors IF', 'Colchester United', 'Forest Green Rovers', 'Tulsa Roughnecks', 'Wellington Phoenix', 'FK Jerv', 'Royal AM', 'Burton Albion', 'LA Galaxy II', 'Moroka Swallows', 'Hartford Athletic', 'Charleston Battery', 'Helsingborgs IF', 'Tianjin Teda', 'Tranmere Rovers', 'Monterey Bay', 'Morecambe', 'Sekhukhune United', 'Shanghai Greenland', 'Richards Bay', 'Chippa United', 'Bradford City', 'Newport County', 'Sutton United', 'TS Galaxy', 'Stevenage', 'Crewe Alexandra', 'Hebei China Fortune FC', 'Tshakhuma Tsha Madzivhandila', 'Maritzburg Utd', 'Henan Jianye', 'AFC Wimbledon', 'Indy Eleven', 'Dalian Aerbin', 'Guangzhou RF', 'Perth Glory', 'Wuhan Zall', 'Stockport County', 'GIF Sundsvall', 'Barrow', 'Gillingham', 'Grimsby Town', 'Rochdale', 'Tianjin Quanujian', 'Shenzhen FC', 'Crawley Town', 'Chongqing Lifan', 'Las Vegas Lights FC', 'Walsall', 'Loudoun United FC', 'Harrogate Town', 'Carlisle United', 'Atlanta United 2', 'Hartlepool', 'Guizhou Renhe', 'New York Red Bulls II', 'None']

new_input = ['File:Flag_of_the_Taliban.svg', 'File:Flag_of_Albania.svg', 'File:Flag_of_Algeria.svg', 'File:Flag_of_American_Samoa.svg', 'File:Flag_of_Andorra.svg', 'File:Flag_of_Angola.svg', 'File:Flag_of_Anguilla.svg', 'File:Flag_of_Antigua_and_Barbuda.svg', 'File:Flag_of_Argentina.svg', 'File:Flag_of_Armenia.svg', 'File:Flag_of_Aruba.svg', 'File:Flag_of_Australia.svg', 'File:Flag_of_Austria.svg', 'File:Flag_of_Azerbaijan.svg', 'File:Flag_of_Bahamas.svg', 'File:Flag_of_Bahrain.svg', 'File:Flag_of_Bangladesh.svg', 'File:Flag_of_Barbados.svg', 'File:Flag_of_the_Basque_Country.svg', 'File:Flag_of_Belarus.svg', 'File:Flag_of_Belgium.svg', 'File:Flag_of_Belize.svg', 'File:Flag_of_Benin.svg', 'File:Flag_of_Bermuda.svg', 'File:Flag_of_Bhutan.svg', 'File:Flag_of_Bolivia.svg', 'File:Flag_of_Bonaire.svg', 'File:Flag_of_Bosnia_and_Herzegovina.svg', 'File:Flag_of_Botswana.svg', 'File:Flag_of_Brazil.svg', 'File:Flag_of_the_British_Virgin_Islands.svg', 'File:Flag_of_Brunei.svg', 'File:Flag_of_Bulgaria.svg', 'File:Flag_of_Burkina_Faso.svg', 'File:Flag_of_Burundi.svg', 'File:Flag_of_Cambodia.svg', 'File:Flag_of_Cameroon.svg', 'File:Flag_of_Canada.svg', 'File:Flag_of_Cape_Verde.svg', 'File:Flag_of_the_Cayman_Islands.svg', 'File:Flag_of_the_Central_African_Republic.svg', 'File:Flag_of_Chad.svg', 'File:Flag_of_Chile.svg', "File:Flag_of_the_People%27s_Republic_of_China.svg", 'File:Flag_of_the_Republic_of_China.svg', 'File:Flag_of_Colombia.svg', 'File:Flag_of_Comoros.svg', 'File:Flag_of_the_Republic_of_the_Congo.svg', 'File:Flag_of_the_Democratic_Republic_of_the_Congo.svg', 'File:Flag_of_the_Cook_Islands.svg', 'File:Flag_of_Costa_Rica.svg', 'File:Flag_of_Croatia.svg', 'File:Flag_of_Cuba.svg', 'File:Flag_of_Curaçao.svg', 'File:Flag_of_Cyprus.svg', 'File:Flag_of_the_Czech_Republic.svg', 'File:Flag_of_Denmark.svg', 'File:Flag_of_Djibouti.svg', 'File:Flag_of_Dominica.svg', 'File:Flag_of_the_Dominican_Republic.svg', 'File:Flag_of_Ecuador.svg', 'File:Flag_of_Egypt.svg', 'File:Flag_of_El_Salvador.svg', 'File:Flag_of_England.svg', 'File:Flag_of_Equatorial_Guinea.svg', 'File:Flag_of_Eritrea.svg', 'File:Flag_of_Estonia.svg', 'File:Flag_of_Ethiopia.svg', 'File:Flag_of_the_Faroe_Islands.svg', 'File:Flag_of_Fiji.svg', 'File:Flag_of_Finland.svg', 'File:Flag_of_France.svg', 'File:Flag_of_French_Guiana.svg', 'File:Flag_of_Gabon.svg', 'File:Flag_of_The_Gambia.svg', 'File:Flag_of_Georgia.svg', 'File:Flag_of_Germany.svg', 'File:Flag_of_Ghana.svg', 'File:Flag_of_Gibraltar.svg', 'File:Flag_of_Greece.svg', 'File:Flag_of_Grenada.svg', 'File:Flag_of_Guadeloupe_%28local%29_variant.svg', 'File:Flag_of_Guam.svg', 'File:Flag_of_Guatemala.svg', 'File:Flag_of_Guinea.svg', 'File:Flag_of_Guinea-Bissau.svg', 'File:Flag_of_Guyana.svg', 'File:Flag_of_Haiti.svg', 'File:Flag_of_Honduras.svg', 'File:Flag_of_Hong_Kong.svg', 'File:Flag_of_Hungary.svg', 'File:Flag_of_Iceland.svg', 'File:Flag_of_India.svg', 'File:Flag_of_Indonesia.svg', 'File:Flag_of_Iran.svg', 'File:Flag_of_Iraq.svg', 'File:Flag_of_Israel.svg', 'File:Flag_of_Italy.svg', 'File:Flag_of_Côte_d%27Ivoire.svg', 'File:Flag_of_Jamaica.svg', 'File:Flag_of_Japan.svg', 'File:Flag_of_Jordan.svg', 'File:Flag_of_Kazakhstan.svg', 'File:Flag_of_Kenya.svg', 'File:Flag_of_Kosovo.svg', 'File:Flag_of_Kuwait.svg', 'File:Flag_of_Kyrgyzstan.svg', 'File:Flag_of_Laos.svg', 'File:Flag_of_Latvia.svg', 'File:Flag_of_Lebanon.svg', 'File:Flag_of_Lesotho.svg', 'File:Flag_of_Liberia.svg', 'File:Flag_of_Libya.svg', 'File:Flag_of_Liechtenstein.svg', 'File:Flag_of_Lithuania.svg', 'File:Flag_of_Luxembourg.svg', 'File:Flag_of_Macau.svg', 'File:Flag_of_Madagascar.svg', 'File:Flag_of_Malawi.svg', 'File:Flag_of_Malaysia.svg', 'File:Flag_of_Maldives.svg', 'File:Flag_of_Mali.svg', 'File:Flag_of_Malta.svg', 'File:Flag_of_the_Territorial_Collectivity_of_Martinique.svg', 'File:Flag_of_Mauritania.svg', 'File:Flag_of_Mauritius.svg', 'File:Flag_of_Mexico.svg', 'File:Flag_of_Moldova.svg', 'File:Flag_of_Mongolia.svg', 'File:Flag_of_Montenegro.svg', 'File:Flag_of_Montserrat.svg', 'File:Flag_of_Morocco.svg', 'File:Flag_of_Mozambique.svg', 'File:Flag_of_Myanmar.svg', 'File:Flag_of_Namibia.svg', 'File:Flag_of_Nepal.svg', 'File:Flag_of_the_Netherlands.svg', 'File:Flag_of_FLNKS.svg', 'File:Flag_of_New_Zealand.svg', 'File:Flag_of_Nicaragua.svg', 'File:Flag_of_Niger.svg', 'File:Flag_of_Nigeria.svg', 'File:Flag_of_North_Korea.svg', 'File:Flag_of_North_Macedonia.svg', 'File:Flag_of_Northern_Ireland_(1953–1972).svg', 'File:Flag_of_the_Northern_Mariana_Islands.svg', 'File:Flag_of_Norway.svg', 'File:Flag_of_Oman.svg', 'File:Flag_of_Pakistan.svg', 'File:Flag_of_Palestine.svg', 'File:Flag_of_Panama.svg', 'File:Flag_of_Papua_New_Guinea.svg', 'File:Flag_of_Paraguay.svg', 'File:Flag_of_Peru.svg', 'File:Flag_of_the_Philippines.svg', 'File:Flag_of_Poland.svg', 'File:Flag_of_Portugal.svg', 'File:Flag_of_Puerto_Rico.svg', 'File:Flag_of_Qatar.svg', 'File:Flag_of_Ireland.svg', 'File:Flag_of_Romania.svg', 'File:Flag_of_Russia.svg', 'File:Flag_of_Rwanda.svg', 'File:Flag_of_San_Marino.svg', 'File:Flag_of_Sao_Tome_and_Principe.svg', 'File:Flag_of_Saudi_Arabia.svg', 'File:Flag_of_Scotland.svg', 'File:Flag_of_Senegal.svg', 'File:Flag_of_Serbia.svg', 'File:Flag_of_Seychelles.svg', 'File:Flag_of_Sierra_Leone.svg', 'File:Flag_of_Singapore.svg', 'File:Flag_of_Sint_Maarten.svg', 'File:Flag_of_Slovakia.svg', 'File:Flag_of_Slovenia.svg', 'File:Flag_of_Solomon_Islands.svg', 'File:Flag_of_Somalia.svg', 'File:Flag_of_South_Africa.svg', 'File:Flag_of_South_Korea.svg', 'File:Flag_of_South_Sudan.svg', 'File:Flag_of_Spain.svg', 'File:Flag_of_Sri_Lanka.svg', 'File:Flag_of_Saint_Kitts_and_Nevis.svg', 'File:Flag_of_Saint_Lucia.svg', 'File:Coat_of_arms_of_the_Collectivity_of_Saint_Martin.svg', 'File:Flag_of_Saint_Vincent_and_the_Grenadines.svg', 'File:Flag_of_Sudan.svg', 'File:Flag_of_Suriname.svg', 'File:Flag_of_Eswatini.svg', 'File:Flag_of_Sweden.svg', 'File:Flag_of_Switzerland.svg', 'File:Flag_of_Syria.svg', 'File:Flag_of_Tahiti.svg', 'File:Flag_of_Tajikistan.svg', 'File:Flag_of_Tanzania.svg', 'File:Flag_of_Thailand.svg', 'File:Flag_of_East_Timor.svg', 'File:Flag_of_Togo.svg', 'File:Flag_of_Tonga.svg', 'File:Flag_of_Trinidad_and_Tobago.svg', 'File:Flag_of_Tunisia.svg', 'File:Flag_of_Turkey.svg', 'File:Flag_of_Turkmenistan.svg', 'File:Flag_of_the_Turks_and_Caicos_Islands.svg', 'File:Flag_of_Tuvalu.svg', 'File:Flag_of_Uganda.svg', 'File:Flag_of_Ukraine.svg', 'File:Flag_of_the_United_Arab_Emirates.svg', 'File:Flag_of_Uruguay.svg', 'File:Flag_of_the_United_States_Virgin_Islands.svg', 'File:Flag_of_the_United_States.svg', 'File:Flag_of_Uzbekistan.svg', 'File:Flag_of_Vanuatu.svg', 'File:Flag_of_Venezuela.svg', 'File:Flag_of_Vietnam.svg', 'File:Flag_of_Wales.svg', 'File:Flag_of_Yemen.svg', 'File:Flag_of_Zambia.svg', 'File:Flag_of_Zanzibar.svg', 'File:Flag_of_Zimbabwe.svg', 'Bayern Munich', 'Manchester City', 'Paris Saint-Germain', 'Liverpool', 'Barcelona', 'Real Madrid', 'Ajax', 'Tottenham Hotspur', 'Salzburg FC', 'Chelsea', 'Arsenal', 'Football Club Internazionale Milano', 'Atletico Madrid', 'Porto FC', 'Napoli', 'Borussia Dortmund', 'Villarreal', 'Milan AC', 'Leipzig RB', 'Sporting CP', 'Benfica', 'Brighton and Hove', 'Celtic', 'Eindhoven PSV', 'Zenit St Petersburg', 'Manchester United', 'Real Sociedad', 'Athletic Bilbao', 'Bayer Leverkusen', 'Lyon', 'Newcastle', 'Atalanta', 'Stade Rennes', 'Marseille', 'Roma AS', 'Feyenoord', 'Real Betis', 'West Ham United', 'Union Berlin FC 1.', 'Freiburg SC', 'Aston Villa', 'Crystal Palace', 'Valencia', 'Borussia Monchengladbach', 'Club Brugge', 'Juventus', 'Lazio', 'Brentford', 'Monaco AS', 'Celta Vigo', 'Flamengo', 'Hoffenheim TSG', 'Cologne FC', 'Lille', 'Rangers', 'Eintracht Frankfurt', 'Lens', 'Osasuna', 'Mainz', 'Sevilla FC', 'Braga', 'Wolverhampton', 'Leicester City', 'Fiorentina', 'Stuttgart VfB', 'Wolfsburg VfL', 'Strasbourg', 'Fenerbahce', 'Alkmaar AZ', 'Twente FC', 'Slavia Prague', 'Leeds United', 'Monterrey', 'Nice', 'Southampton', 'Club America', 'Everton', 'Dinamo Zagreb', 'Torino', 'Palmeiras', 'Genk', 'Udinese', 'Young Boys', 'Rayo Vallecano', 'Club Atletico Mineiro', 'Werder Bremen', 'Sport Club Internacional', 'Shakhtar Donetsk', 'Fulham', 'Hertha Berlin', 'Espanyol', 'Getafe', 'Girona FC', 'Norwich City', 'Philadelphia Union', 'Sassuolo', 'Almeria', 'Slovacko', 'Verona', 'Sao Paulo', 'Nantes', 'Schalke 4', 'Fluminense', 'Tigres UANL', 'Mallorca', 'Pachuca', 'Moscow CSKA', 'Steaua Bucuresti', 'Olympiacos', 'Sheffield United', 'River Plate', 'Red Star Belgrade', 'Real Valladolid', 'Reims', 'Trabzonspor', 'Augsburg FC', 'Spartak Moscow', 'Utrecht FC', 'Anderlecht', 'Antwerp', 'West Bromwich Albion', 'Bochum VfL', 'Cadiz', 'Corinthians', 'Ferencvaros', 'Dnipro-1 SC', 'Lorient', 'Molde', 'Istanbul Basaksehir', 'Bodo/Glimt', 'Bragantino', 'Dynamo Kiev', 'Nottingham Forest', 'Watford', 'Bologna', 'Los Angeles FC', 'Viktoria Plzen', 'Bournemouth AFC', 'Gent KAA', 'Sheriff Tiraspol FC', 'Elche', 'Copenhagen FC', 'Kawasaki Frontale', 'Montpellier', 'Sturm Graz FK', 'Besiktas', 'Troyes', 'Toulouse', 'Burnley', 'Yokohama F. Marinos', 'Vitesse', 'Sampdoria', 'Guimaraes', 'Gil Vicente', 'Lecce', 'Brest', 'Angers', 'Krasnodar FC', 'Santos', 'Galatasaray', 'Ceara Sporting Club', 'Dinamo Moscow', 'Guadalajara', 'Midtjylland FC', 'Levante', 'Ajaccio AC', 'Partizan Belgrade FK', 'Linz LASK', 'Fortaleza', 'Santos Laguna', 'Union Saint Gilloise', 'Atletico Paranaense', 'Urawa Red Diamonds', 'Clermont Foot', 'Sochi', 'Cremonese', 'Empoli', 'Heerenveen', 'New York City FC', 'Middlesbrough', 'Konyaspor', 'Salernitana', 'Lech Poznan', 'Auxerre', 'NEC', 'Montreal Impact', 'America Futebol Clube MG', 'Portimonense', 'Monza', 'Famalicao', 'Rostov', "Hapoel Be'er", 'Basel', 'Spezia', 'Etienne', 'Chaves', 'Vizela', 'Cuiaba', 'Rosenborg', 'Leon', 'Boca Juniors', 'Apollon Limassol', 'Estoril Praia', 'Cagliari', 'Gallen', 'Bordeaux', 'Hamburg SV', 'Metz', 'Santa Clara', 'Botafogo', 'Salonika PAOK', 'Puebla', 'Maccabi Haifa', 'Granada', 'Boavista', 'New York Red Bulls', 'Austria Vienna FK', 'Rio Ave', 'Nashville SC', 'Adana Demirspor', 'Panathinaikos', 'Sparta', 'Galaxy Los Angeles', 'Atlas', 'Silkeborg', 'Groningen FC', 'Waalwijk RKC', 'Cruz Azul', 'Parma', 'Sochaux', 'Casa Pia', 'Rapid Vienna', 'Atlanta United FC', 'Sporting de Charleroi', 'Lokomotiv Moscow', 'Athens AEK', 'Millwall', 'Randers FC', 'Huracan', 'Luton Town', 'Preston North End', 'Austin FC', 'Toluca', 'Sanfrecce Hiroshima', 'Emmen', 'Qarabag FK', 'Stoke City', 'Club Pumas Unam', 'Velez Sarsfield', 'Larnaca AEK', 'Alanyaspor', 'Nordsjaelland FC', 'Genoa', 'Go Ahead Eagles', 'Bristol City', 'Antalyaspor', 'Wolfsberger AC', 'Seattle Sounders FC', 'Racing Club', 'Truidense', 'Cerezo Osaka', 'Valerenga', 'Queens Park Rangers', 'Coventry City', 'Cluj 1907 CFR', 'Cambuur Leeuwarden', 'Aberdeen', 'Necaxa', 'Caen', 'Estudiantes', 'Columbus Crew', 'Kashima Antlers', 'Dallas FC', 'Terek Grozny', 'Orlando City SC', 'Djurgardens IF', 'Tijuana', 'Atletico Goianiense', 'Talleres de Cordoba', 'Tigre', 'Gazisehir Gaziantep', 'Kasimpasa', 'Swansea City', 'Argentinos Juniors', 'Brondby', 'Krylia Sovetov', 'New England Revolution', 'Volendam FC', 'Maritimo', 'Darmstadt SV 98', 'Hammarby', 'Ludogorets', 'Portland Timbers', 'Goias', 'San Lorenzo', 'Cincinnati FC', 'Lillestrom', 'Arouca FC', 'Cardiff City', 'Blackburn', 'Independiente CA', 'Minnesota United FC', 'Excelsior', 'Leuven OH', 'Eibar', 'Alaves', 'Hearts', 'Real Salt Lake', 'Coritiba', 'Mechelen KV', 'Blackpool', 'Chicago Fire', 'Zurich FC', 'Hacken BK', 'Pacos Ferreira', 'Brescia', 'Viborg', 'Sheffield Wednesday', 'Sunderland', 'Paderborn SC', 'Fortuna Dusseldorf', 'Las Palmas', 'Benevento', 'Ipswich Town', 'Frosinone', 'Standard Liege', 'Fortuna Sittard', 'Queretaro', 'Luzern FC', 'Colorado Rapids', 'Huddersfield Town', 'Avai', 'Hibernian', 'Slovan Bratislava', 'St Pauli FC', 'Juarez FC', 'Sporting Kansas City', 'Gimnasia La Plata', "Newell's Old Boys", 'Kayserispor', 'Aris Salonika', 'Paris FC', 'Nizhny Novgorod FK', 'Mamelodi Sundowns', 'Union Santa Fe', 'Toronto FC', 'Hull City', 'Viking FK', 'Derby County', 'Real Oviedo', 'Fodbold AaB', 'Omonia Nicosia', 'Guingamp', 'Havre Le', 'Juventude', 'Defensa y Justicia', 'Wigan', 'Real Zaragoza', 'Venezia Unione Venezia F.B.C.', 'Lanus', 'Arminia Bielefeld', 'Servette', 'Malmo FF', 'Fatih Karagümrük', 'Goteborg IFK', 'Elfsborg IF', 'Mazatlan FC', 'Sagan Tosu', 'Tokyo FC', 'Huesca SD', 'Westerlo KVC', 'Rosario Central', 'Reading', 'Karlsruher SC', 'Atletico San Luis', 'Amiens', 'Austria Klagenfurt SK', 'Inter Miami CF', 'Austria Lustenau', 'Aarhus AGF', 'Swarovski Wattens WSG', 'Cercle Brugge', 'Sivasspor', 'Sporting Gijón', 'Nagoya Grampus Eight', 'Birmingham', 'Godoy Cruz', 'Livingston', 'Dijon FCO', 'Lugano FC', 'Cartagena FC', 'Rigas Futbola Skola', 'Banfield', 'Heidenheim FC 1. 1846', 'Rotherham United', 'Platense', 'Hatayspor', 'Sion FC', 'Hartberg', 'Central Cordoba Santiago del Estero', 'Grasshoppers Zurich', 'Stromsgodset', 'Ballkani', 'Khimki FC', 'Fotboll AIK', 'Leganes', 'Motherwell', 'Vancouver Whitecaps', 'Colon Santa Fe', 'Charlotte FC', 'Ascoli', 'San Jose Earthquakes', 'Vissel Kobe', 'Tenerife', 'Sarmiento', 'Zalgiris Vilnius', 'Patronato', 'Cittadella', 'Atletico Tucuman', 'Portsmouth', 'Oostende KV', 'Kortrijk KV', 'Barnsley', 'Nurnberg FC 1.', 'D.C. United', 'Shimizu S-Pulse', 'Spal', 'Odense BK', 'Arsenal Sarandi', 'Fakel Voronezh', 'Hannover 96', 'Nimes', 'Ross County', 'Houston Dynamo', 'Ternana', 'Haugesund', 'Ried SV', 'Reggina', 'Pisa', 'Giresunspor', 'Holstein Kiel', 'Bari', 'Ural Sverdlovsk Oblast', 'Sarpsborg', 'Barracas Central', 'Kashiwa Reysol', 'SpVgg Greuther Furth', 'Melbourne City', 'Kilmarnock', 'Gazovik Orenburg', 'Horsens AC', 'Ankaragucu', 'Mirren', 'Tromso', 'Volos NFC', 'Ponferradina SD', 'Valenciennes', 'Burgos', 'Perugia', 'Zulte SV Waregem', 'Tampa Bay Rowdies', 'Umraniyespor', 'Johnstone', 'Kalmar FF', 'Villarreal B', 'Peterborough United', 'Consadole Sapporo', 'Mirandes', 'Atromitos', 'Ibiza UD', 'Bastia', 'Norrkoping IFK', 'Louisville City FC', 'Bolton', 'Dundee Utd', 'Malaga', 'Guangzhou Evergrande', 'Helsinki HJK', 'Albacete', 'Cashpoint SC Rheindorf', 'Odd BK', 'Grenoble', 'Eupen', 'Ionikos FC', 'Milton Keynes Dons', 'Wycombe Wanderers', 'Vaduz FC', 'Lyngby', 'Kyoto Purple Sanga', 'Asteras Tripolis', 'Como', 'Istanbulspor', 'Panetolikos', 'Hansa Rostock', 'Andorra FC', 'Avispa Fukuoka', 'Shonan Bellmare', 'Racing Santander', 'Plymouth Argyle', 'Lugo', 'Modena', 'Torpedo Moskow', 'San Diego Loyal', 'Aalesund', 'Sydney FC', 'Oxford United', 'Annecy', 'Hamarkamaratene', 'Pau', 'Aldosivi', 'Palermo', 'Laval', 'Melbourne Victory', 'Beijing Guoan', 'Kristiansund BK', 'Gamba Osaka', 'Giannina', 'San Antonio FC', 'Birmingham Legion FC', 'Niort', 'Mjallby', 'Jahn Regensburg', 'Cosenza', 'Shanghai SIPG', 'Sandhausen SV', 'Seraing RFC', 'Charlton Athletic', 'Rodez', 'Crete OFI', 'Sudtirol', 'Kaiserslautern FC 1.', 'Salford City', 'Orlando Pirates', 'Quevilly US', 'Sandefjord', 'Levadiakos', 'Rio Grande Valley Toros FC', 'Pittsburgh Riverhounds', 'Pyunik Yerevan', 'Memphis 901 FC', 'Western Sydney FC', 'Western United', 'Adelaide United', 'Sirius IK', 'Central Coast Mariners', 'Sacramento Republic FC', 'Kaizer Chiefs', 'SuperSport United', 'Newcastle Jets', 'Shrewsbury Town', 'Shamrock Rovers', 'Eintracht Braunschweig', 'Oakland Roots', 'Miami FC', 'New Mexico United', 'Colorado Springs Switchbacks FC', 'Magdeburg FC 1.', 'Varnamo IFK', 'Lincoln City', 'Jubilo Iwata', 'Shandong Luneng', 'Jiangsu Suning FC', 'Black Aces', 'Mansfield Town', 'Fleetwood Town', 'Exeter City', 'Lamia', 'Winterthur', 'Cambridge United', 'Varbergs BoIS FC', 'Brisbane Roar', 'El Paso Locomotive FC', 'Cheltenham Town', 'Leyton Orient', 'Doncaster Rovers', 'Bristol Rovers', 'Macarthur FC', 'Stellenbosch FC', 'Accrington Stanley', 'Arizona United', 'Northampton Town', 'Detroit City FC', 'Swindon Town', 'Port Vale', 'Orange County SC', 'AmaZulu', 'Golden Arrows', 'Degerfors IF', 'Colchester United', 'Forest Green Rovers', 'Tulsa Roughnecks', 'Wellington Phoenix', 'Jerv FK', 'Royal AM', 'Burton Albion', 'Galaxy LA II', 'Moroka Swallows', 'Hartford Athletic', 'Charleston Battery', 'Helsingborgs IF', 'Tianjin Teda', 'Tranmere Rovers', 'Monterey Bay', 'Morecambe', 'Sekhukhune United', 'Shanghai Greenland', 'Richards Bay', 'Chippa United', 'Bradford City', 'Newport County', 'Sutton United', 'Galaxy TS', 'Stevenage', 'Crewe Alexandra', 'Hebei China Fortune FC', 'Tshakhuma Tsha Madzivhandila', 'Maritzburg Utd', 'Henan Jianye', 'Wimbledon AFC', 'Indy Eleven', 'Dalian Aerbin', 'Guangzhou RF', 'Perth Glory', 'Wuhan Zall', 'Stockport County', 'Sundsvall GIF', 'Barrow', 'Gillingham', 'Grimsby Town', 'Rochdale', 'Tianjin Quanujian', 'Shenzhen FC', 'Crawley Town', 'Chongqing Lifan', 'Las Vegas Lights FC', 'Walsall', 'Loudoun United FC', 'Harrogate Town', 'Carlisle United', 'Atlanta United 2', 'Hartlepool', 'Guizhou Renhe', 'New York Red Bulls II','None']

countries = ['File:Flag_of_the_Taliban.svg', 'File:Flag_of_Albania.svg', 'File:Flag_of_Algeria.svg', 'File:Flag_of_American_Samoa.svg', 'File:Flag_of_Andorra.svg', 'File:Flag_of_Angola.svg', 'File:Flag_of_Anguilla.svg', 'File:Flag_of_Antigua_and_Barbuda.svg', 'File:Flag_of_Argentina.svg', 'File:Flag_of_Armenia.svg', 'File:Flag_of_Aruba.svg', 'File:Flag_of_Australia.svg', 'File:Flag_of_Austria.svg', 'File:Flag_of_Azerbaijan.svg', 'File:Flag_of_Bahamas.svg', 'File:Flag_of_Bahrain.svg', 'File:Flag_of_Bangladesh.svg', 'File:Flag_of_Barbados.svg', 'File:Flag_of_the_Basque_Country.svg', 'File:Flag_of_Belarus.svg', 'File:Flag_of_Belgium.svg', 'File:Flag_of_Belize.svg', 'File:Flag_of_Benin.svg', 'File:Flag_of_Bermuda.svg', 'File:Flag_of_Bhutan.svg', 'File:Flag_of_Bolivia.svg', 'File:Flag_of_Bonaire.svg', 'File:Flag_of_Bosnia_and_Herzegovina.svg', 'File:Flag_of_Botswana.svg', 'File:Flag_of_Brazil.svg', 'File:Flag_of_the_British_Virgin_Islands.svg', 'File:Flag_of_Brunei.svg', 'File:Flag_of_Bulgaria.svg', 'File:Flag_of_Burkina_Faso.svg', 'File:Flag_of_Burundi.svg', 'File:Flag_of_Cambodia.svg', 'File:Flag_of_Cameroon.svg', 'File:Flag_of_Canada.svg', 'File:Flag_of_Cape_Verde.svg', 'File:Flag_of_the_Cayman_Islands.svg', 'File:Flag_of_the_Central_African_Republic.svg', 'File:Flag_of_Chad.svg', 'File:Flag_of_Chile.svg', "File:Flag_of_the_People%27s_Republic_of_China.svg", 'File:Flag_of_the_Republic_of_China.svg', 'File:Flag_of_Colombia.svg', 'File:Flag_of_Comoros.svg', 'File:Flag_of_the_Republic_of_the_Congo.svg', 'File:Flag_of_the_Democratic_Republic_of_the_Congo.svg', 'File:Flag_of_the_Cook_Islands.svg', 'File:Flag_of_Costa_Rica.svg', 'File:Flag_of_Croatia.svg', 'File:Flag_of_Cuba.svg', 'File:Flag_of_Curaçao.svg', 'File:Flag_of_Cyprus.svg', 'File:Flag_of_the_Czech_Republic.svg', 'File:Flag_of_Denmark.svg', 'File:Flag_of_Djibouti.svg', 'File:Flag_of_Dominica.svg', 'File:Flag_of_the_Dominican_Republic.svg', 'File:Flag_of_Ecuador.svg', 'File:Flag_of_Egypt.svg', 'File:Flag_of_El_Salvador.svg', 'File:Flag_of_England.svg', 'File:Flag_of_Equatorial_Guinea.svg', 'File:Flag_of_Eritrea.svg', 'File:Flag_of_Estonia.svg', 'File:Flag_of_Ethiopia.svg', 'File:Flag_of_the_Faroe_Islands.svg', 'File:Flag_of_Fiji.svg', 'File:Flag_of_Finland.svg', 'File:Flag_of_France.svg', 'File:Flag_of_French_Guiana.svg', 'File:Flag_of_Gabon.svg', 'File:Flag_of_The_Gambia.svg', 'File:Flag_of_Georgia.svg', 'File:Flag_of_Germany.svg', 'File:Flag_of_Ghana.svg', 'File:Flag_of_Gibraltar.svg', 'File:Flag_of_Greece.svg', 'File:Flag_of_Grenada.svg', 'File:Flag_of_Guadeloupe_%28local%29_variant.svg', 'File:Flag_of_Guam.svg', 'File:Flag_of_Guatemala.svg', 'File:Flag_of_Guinea.svg', 'File:Flag_of_Guinea-Bissau.svg', 'File:Flag_of_Guyana.svg', 'File:Flag_of_Haiti.svg', 'File:Flag_of_Honduras.svg', 'File:Flag_of_Hong_Kong.svg', 'File:Flag_of_Hungary.svg', 'File:Flag_of_Iceland.svg', 'File:Flag_of_India.svg', 'File:Flag_of_Indonesia.svg', 'File:Flag_of_Iran.svg', 'File:Flag_of_Iraq.svg', 'File:Flag_of_Israel.svg', 'File:Flag_of_Italy.svg', 'File:Flag_of_Côte_d%27Ivoire.svg', 'File:Flag_of_Jamaica.svg', 'File:Flag_of_Japan.svg', 'File:Flag_of_Jordan.svg', 'File:Flag_of_Kazakhstan.svg', 'File:Flag_of_Kenya.svg', 'File:Flag_of_Kosovo.svg', 'File:Flag_of_Kuwait.svg', 'File:Flag_of_Kyrgyzstan.svg', 'File:Flag_of_Laos.svg', 'File:Flag_of_Latvia.svg', 'File:Flag_of_Lebanon.svg', 'File:Flag_of_Lesotho.svg', 'File:Flag_of_Liberia.svg', 'File:Flag_of_Libya.svg', 'File:Flag_of_Liechtenstein.svg', 'File:Flag_of_Lithuania.svg', 'File:Flag_of_Luxembourg.svg', 'File:Flag_of_Macau.svg', 'File:Flag_of_Madagascar.svg', 'File:Flag_of_Malawi.svg', 'File:Flag_of_Malaysia.svg', 'File:Flag_of_Maldives.svg', 'File:Flag_of_Mali.svg', 'File:Flag_of_Malta.svg', 'File:Flag_of_the_Territorial_Collectivity_of_Martinique.svg', 'File:Flag_of_Mauritania.svg', 'File:Flag_of_Mauritius.svg', 'File:Flag_of_Mexico.svg', 'File:Flag_of_Moldova.svg', 'File:Flag_of_Mongolia.svg', 'File:Flag_of_Montenegro.svg', 'File:Flag_of_Montserrat.svg', 'File:Flag_of_Morocco.svg', 'File:Flag_of_Mozambique.svg', 'File:Flag_of_Myanmar.svg', 'File:Flag_of_Namibia.svg', 'File:Flag_of_Nepal.svg', 'File:Flag_of_the_Netherlands.svg', 'File:Flag_of_FLNKS.svg', 'File:Flag_of_New_Zealand.svg', 'File:Flag_of_Nicaragua.svg', 'File:Flag_of_Niger.svg', 'File:Flag_of_Nigeria.svg', 'File:Flag_of_North_Korea.svg', 'File:Flag_of_North_Macedonia.svg', 'File:Flag_of_Northern_Ireland_(1953–1972).svg', 'File:Flag_of_the_Northern_Mariana_Islands.svg', 'File:Flag_of_Norway.svg', 'File:Flag_of_Oman.svg', 'File:Flag_of_Pakistan.svg', 'File:Flag_of_Palestine.svg', 'File:Flag_of_Panama.svg', 'File:Flag_of_Papua_New_Guinea.svg', 'File:Flag_of_Paraguay.svg', 'File:Flag_of_Peru.svg', 'File:Flag_of_the_Philippines.svg', 'File:Flag_of_Poland.svg', 'File:Flag_of_Portugal.svg', 'File:Flag_of_Puerto_Rico.svg', 'File:Flag_of_Qatar.svg', 'File:Flag_of_Ireland.svg', 'File:Flag_of_Romania.svg', 'File:Flag_of_Russia.svg', 'File:Flag_of_Rwanda.svg', 'File:Flag_of_San_Marino.svg', 'File:Flag_of_Sao_Tome_and_Principe.svg', 'File:Flag_of_Saudi_Arabia.svg', 'File:Flag_of_Scotland.svg', 'File:Flag_of_Senegal.svg', 'File:Flag_of_Serbia.svg', 'File:Flag_of_Seychelles.svg', 'File:Flag_of_Sierra_Leone.svg', 'File:Flag_of_Singapore.svg', 'File:Flag_of_Sint_Maarten.svg', 'File:Flag_of_Slovakia.svg', 'File:Flag_of_Slovenia.svg', 'File:Flag_of_Solomon_Islands.svg', 'File:Flag_of_Somalia.svg', 'File:Flag_of_South_Africa.svg', 'File:Flag_of_South_Korea.svg', 'File:Flag_of_South_Sudan.svg', 'File:Flag_of_Spain.svg', 'File:Flag_of_Sri_Lanka.svg', 'File:Flag_of_Saint_Kitts_and_Nevis.svg', 'File:Flag_of_Saint_Lucia.svg', 'File:Coat_of_arms_of_the_Collectivity_of_Saint_Martin.svg', 'File:Flag_of_Saint_Vincent_and_the_Grenadines.svg', 'File:Flag_of_Sudan.svg', 'File:Flag_of_Suriname.svg', 'File:Flag_of_Eswatini.svg', 'File:Flag_of_Sweden.svg', 'File:Flag_of_Switzerland.svg', 'File:Flag_of_Syria.svg', 'File:Flag_of_Tahiti.svg', 'File:Flag_of_Tajikistan.svg', 'File:Flag_of_Tanzania.svg', 'File:Flag_of_Thailand.svg', 'File:Flag_of_East_Timor.svg', 'File:Flag_of_Togo.svg', 'File:Flag_of_Tonga.svg', 'File:Flag_of_Trinidad_and_Tobago.svg', 'File:Flag_of_Tunisia.svg', 'File:Flag_of_Turkey.svg', 'File:Flag_of_Turkmenistan.svg', 'File:Flag_of_the_Turks_and_Caicos_Islands.svg', 'File:Flag_of_Tuvalu.svg', 'File:Flag_of_Uganda.svg', 'File:Flag_of_Ukraine.svg', 'File:Flag_of_the_United_Arab_Emirates.svg', 'File:Flag_of_Uruguay.svg', 'File:Flag_of_the_United_States_Virgin_Islands.svg', 'File:Flag_of_the_United_States.svg', 'File:Flag_of_Uzbekistan.svg', 'File:Flag_of_Vanuatu.svg', 'File:Flag_of_Venezuela.svg', 'File:Flag_of_Vietnam.svg', 'File:Flag_of_Wales.svg', 'File:Flag_of_Yemen.svg', 'File:Flag_of_Zambia.svg', 'File:Flag_of_Zanzibar.svg', 'File:Flag_of_Zimbabwe.svg']

clubs = ['Bayern Munich', 'Manchester City', 'Paris Saint-Germain', 'Liverpool', 'Barcelona', 'Real Madrid', 'Ajax', 'Tottenham Hotspur', 'Salzburg FC', 'Chelsea', 'Arsenal', 'Football Club Internazionale Milano', 'Atletico Madrid', 'Porto FC', 'Napoli', 'Borussia Dortmund', 'Villarreal', 'Milan AC', 'Leipzig RB', 'Sporting CP', 'Benfica', 'Brighton and Hove', 'Celtic', 'Eindhoven PSV', 'Zenit St Petersburg', 'Manchester United', 'Real Sociedad', 'Athletic Bilbao', 'Bayer Leverkusen', 'Lyon', 'Newcastle', 'Atalanta', 'Stade Rennes', 'Marseille', 'Roma AS', 'Feyenoord', 'Real Betis', 'West Ham United', 'Union Berlin FC 1.', 'Freiburg SC', 'Aston Villa', 'Crystal Palace', 'Valencia', 'Borussia Monchengladbach', 'Club Brugge', 'Juventus', 'Lazio', 'Brentford', 'Monaco AS', 'Celta Vigo', 'Flamengo', 'Hoffenheim TSG', 'Cologne FC', 'Lille', 'Rangers', 'Eintracht Frankfurt', 'Lens', 'Osasuna', 'Mainz', 'Sevilla FC', 'Braga', 'Wolverhampton', 'Leicester City', 'Fiorentina', 'Stuttgart VfB', 'Wolfsburg VfL', 'Strasbourg', 'Fenerbahce', 'Alkmaar AZ', 'Twente FC', 'Slavia Prague', 'Leeds United', 'Monterrey', 'Nice', 'Southampton', 'Club America', 'Everton', 'Dinamo Zagreb', 'Torino', 'Palmeiras', 'Genk', 'Udinese', 'Young Boys', 'Rayo Vallecano', 'Club Atletico Mineiro', 'Werder Bremen', 'Sport Club Internacional', 'Shakhtar Donetsk', 'Fulham', 'Hertha Berlin', 'Espanyol', 'Getafe', 'Girona FC', 'Norwich City', 'Philadelphia Union', 'Sassuolo', 'Almeria', 'Slovacko', 'Verona', 'Sao Paulo', 'Nantes', 'Schalke 4', 'Fluminense', 'Tigres UANL', 'Mallorca', 'Pachuca', 'Moscow CSKA', 'Steaua Bucuresti', 'Olympiacos', 'Sheffield United', 'River Plate', 'Red Star Belgrade', 'Real Valladolid', 'Reims', 'Trabzonspor', 'Augsburg FC', 'Spartak Moscow', 'Utrecht FC', 'Anderlecht', 'Antwerp', 'West Bromwich Albion', 'Bochum VfL', 'Cadiz', 'Corinthians', 'Ferencvaros', 'Dnipro-1 SC', 'Lorient', 'Molde', 'Istanbul Basaksehir', 'Bodo/Glimt', 'Bragantino', 'Dynamo Kiev', 'Nottingham Forest', 'Watford', 'Bologna', 'Los Angeles FC', 'Viktoria Plzen', 'Bournemouth AFC', 'Gent KAA', 'Sheriff Tiraspol FC', 'Elche', 'Copenhagen FC', 'Kawasaki Frontale', 'Montpellier', 'Sturm Graz FK', 'Besiktas', 'Troyes', 'Toulouse', 'Burnley', 'Yokohama F. Marinos', 'Vitesse', 'Sampdoria', 'Guimaraes', 'Gil Vicente', 'Lecce', 'Brest', 'Angers', 'Krasnodar FC', 'Santos', 'Galatasaray', 'Ceara Sporting Club', 'Dinamo Moscow', 'Guadalajara', 'Midtjylland FC', 'Levante', 'Ajaccio AC', 'Partizan Belgrade FK', 'Linz LASK', 'Fortaleza', 'Santos Laguna', 'Union Saint Gilloise', 'Atletico Paranaense', 'Urawa Red Diamonds', 'Clermont Foot', 'Sochi', 'Cremonese', 'Empoli', 'Heerenveen', 'New York City FC', 'Middlesbrough', 'Konyaspor', 'Salernitana', 'Lech Poznan', 'Auxerre', 'NEC', 'Montreal Impact', 'America Futebol Clube MG', 'Portimonense', 'Monza', 'Famalicao', 'Rostov', "Hapoel Be'er", 'Basel', 'Spezia', 'Etienne', 'Chaves', 'Vizela', 'Cuiaba', 'Rosenborg', 'Leon', 'Boca Juniors', 'Apollon Limassol', 'Estoril Praia', 'Cagliari', 'Gallen', 'Bordeaux', 'Hamburg SV', 'Metz', 'Santa Clara', 'Botafogo', 'Salonika PAOK', 'Puebla', 'Maccabi Haifa', 'Granada', 'Boavista', 'New York Red Bulls', 'Austria Vienna FK', 'Rio Ave', 'Nashville SC', 'Adana Demirspor', 'Panathinaikos', 'Sparta', 'Galaxy Los Angeles', 'Atlas', 'Silkeborg', 'Groningen FC', 'Waalwijk RKC', 'Cruz Azul', 'Parma', 'Sochaux', 'Casa Pia', 'Rapid Vienna', 'Atlanta United FC', 'Sporting de Charleroi', 'Lokomotiv Moscow', 'Athens AEK', 'Millwall', 'Randers FC', 'Huracan', 'Luton Town', 'Preston North End', 'Austin FC', 'Toluca', 'Sanfrecce Hiroshima', 'Emmen', 'Qarabag FK', 'Stoke City', 'Club Pumas Unam', 'Velez Sarsfield', 'Larnaca AEK', 'Alanyaspor', 'Nordsjaelland FC', 'Genoa', 'Go Ahead Eagles', 'Bristol City', 'Antalyaspor', 'Wolfsberger AC', 'Seattle Sounders FC', 'Racing Club', 'Truidense', 'Cerezo Osaka', 'Valerenga', 'Queens Park Rangers', 'Coventry City', 'Cluj 1907 CFR', 'Cambuur Leeuwarden', 'Aberdeen', 'Necaxa', 'Caen', 'Estudiantes', 'Columbus Crew', 'Kashima Antlers', 'Dallas FC', 'Terek Grozny', 'Orlando City SC', 'Djurgardens IF', 'Tijuana', 'Atletico Goianiense', 'Talleres de Cordoba', 'Tigre', 'Gazisehir Gaziantep', 'Kasimpasa', 'Swansea City', 'Argentinos Juniors', 'Brondby', 'Krylia Sovetov', 'New England Revolution', 'Volendam FC', 'Maritimo', 'Darmstadt SV 98', 'Hammarby', 'Ludogorets', 'Portland Timbers', 'Goias', 'San Lorenzo', 'Cincinnati FC', 'Lillestrom', 'Arouca FC', 'Cardiff City', 'Blackburn', 'Independiente CA', 'Minnesota United FC', 'Excelsior', 'Leuven OH', 'Eibar', 'Alaves', 'Hearts', 'Real Salt Lake', 'Coritiba', 'Mechelen KV', 'Blackpool', 'Chicago Fire', 'Zurich FC', 'Hacken BK', 'Pacos Ferreira', 'Brescia', 'Viborg', 'Sheffield Wednesday', 'Sunderland', 'Paderborn SC', 'Fortuna Dusseldorf', 'Las Palmas', 'Benevento', 'Ipswich Town', 'Frosinone', 'Standard Liege', 'Fortuna Sittard', 'Queretaro', 'Luzern FC', 'Colorado Rapids', 'Huddersfield Town', 'Avai', 'Hibernian', 'Slovan Bratislava', 'St Pauli FC', 'Juarez FC', 'Sporting Kansas City', 'Gimnasia La Plata', "Newell's Old Boys", 'Kayserispor', 'Aris Salonika', 'Paris FC', 'Nizhny Novgorod FK', 'Mamelodi Sundowns', 'Union Santa Fe', 'Toronto FC', 'Hull City', 'Viking FK', 'Derby County', 'Real Oviedo', 'Fodbold AaB', 'Omonia Nicosia', 'Guingamp', 'Havre Le', 'Juventude', 'Defensa y Justicia', 'Wigan', 'Real Zaragoza', 'Venezia Unione Venezia F.B.C.', 'Lanus', 'Arminia Bielefeld', 'Servette', 'Malmo FF', 'Fatih Karagümrük', 'Goteborg IFK', 'Elfsborg IF', 'Mazatlan FC', 'Sagan Tosu', 'Tokyo FC', 'Huesca SD', 'Westerlo KVC', 'Rosario Central', 'Reading', 'Karlsruher SC', 'Atletico San Luis', 'Amiens', 'Austria Klagenfurt SK', 'Inter Miami CF', 'Austria Lustenau', 'Aarhus AGF', 'Swarovski Wattens WSG', 'Cercle Brugge', 'Sivasspor', 'Sporting Gijón', 'Nagoya Grampus Eight', 'Birmingham', 'Godoy Cruz', 'Livingston', 'Dijon FCO', 'Lugano FC', 'Cartagena FC', 'Rigas Futbola Skola', 'Banfield', 'Heidenheim FC 1. 1846', 'Rotherham United', 'Platense', 'Hatayspor', 'Sion FC', 'Hartberg', 'Central Cordoba Santiago del Estero', 'Grasshoppers Zurich', 'Stromsgodset', 'Ballkani', 'Khimki FC', 'Fotboll AIK', 'Leganes', 'Motherwell', 'Vancouver Whitecaps', 'Colon Santa Fe', 'Charlotte FC', 'Ascoli', 'San Jose Earthquakes', 'Vissel Kobe', 'Tenerife', 'Sarmiento', 'Zalgiris Vilnius', 'Patronato', 'Cittadella', 'Atletico Tucuman', 'Portsmouth', 'Oostende KV', 'Kortrijk KV', 'Barnsley', 'Nurnberg FC 1.', 'D.C. United', 'Shimizu S-Pulse', 'Spal', 'Odense BK', 'Arsenal Sarandi', 'Fakel Voronezh', 'Hannover 96', 'Nimes', 'Ross County', 'Houston Dynamo', 'Ternana', 'Haugesund', 'Ried SV', 'Reggina', 'Pisa', 'Giresunspor', 'Holstein Kiel', 'Bari', 'Ural Sverdlovsk Oblast', 'Sarpsborg', 'Barracas Central', 'Kashiwa Reysol', 'SpVgg Greuther Furth', 'Melbourne City', 'Kilmarnock', 'Gazovik Orenburg', 'Horsens AC', 'Ankaragucu', 'Mirren', 'Tromso', 'Volos NFC', 'Ponferradina SD', 'Valenciennes', 'Burgos', 'Perugia', 'Zulte SV Waregem', 'Tampa Bay Rowdies', 'Umraniyespor', 'Johnstone', 'Kalmar FF', 'Villarreal B', 'Peterborough United', 'Consadole Sapporo', 'Mirandes', 'Atromitos', 'Ibiza UD', 'Bastia', 'Norrkoping IFK', 'Louisville City FC', 'Bolton', 'Dundee Utd', 'Malaga', 'Guangzhou Evergrande', 'Helsinki HJK', 'Albacete', 'Cashpoint SC Rheindorf', 'Odd BK', 'Grenoble', 'Eupen', 'Ionikos FC', 'Milton Keynes Dons', 'Wycombe Wanderers', 'Vaduz FC', 'Lyngby', 'Kyoto Purple Sanga', 'Asteras Tripolis', 'Como', 'Istanbulspor', 'Panetolikos', 'Hansa Rostock', 'Andorra FC', 'Avispa Fukuoka', 'Shonan Bellmare', 'Racing Santander', 'Plymouth Argyle', 'Lugo', 'Modena', 'Torpedo Moskow', 'San Diego Loyal', 'Aalesund', 'Sydney FC', 'Oxford United', 'Annecy', 'Hamarkamaratene', 'Pau', 'Aldosivi', 'Palermo', 'Laval', 'Melbourne Victory', 'Beijing Guoan', 'Kristiansund BK', 'Gamba Osaka', 'Giannina', 'San Antonio FC', 'Birmingham Legion FC', 'Niort', 'Mjallby', 'Jahn Regensburg', 'Cosenza', 'Shanghai SIPG', 'Sandhausen SV', 'Seraing RFC', 'Charlton Athletic', 'Rodez', 'Crete OFI', 'Sudtirol', 'Kaiserslautern FC 1.', 'Salford City', 'Orlando Pirates', 'Quevilly US', 'Sandefjord', 'Levadiakos', 'Rio Grande Valley Toros FC', 'Pittsburgh Riverhounds', 'Pyunik Yerevan', 'Memphis 901 FC', 'Western Sydney FC', 'Western United', 'Adelaide United', 'Sirius IK', 'Central Coast Mariners', 'Sacramento Republic FC', 'Kaizer Chiefs', 'SuperSport United', 'Newcastle Jets', 'Shrewsbury Town', 'Shamrock Rovers', 'Eintracht Braunschweig', 'Oakland Roots', 'Miami FC', 'New Mexico United', 'Colorado Springs Switchbacks FC', 'Magdeburg FC 1.', 'Varnamo IFK', 'Lincoln City', 'Jubilo Iwata', 'Shandong Luneng', 'Jiangsu Suning FC', 'Black Aces', 'Mansfield Town', 'Fleetwood Town', 'Exeter City', 'Lamia', 'Winterthur', 'Cambridge United', 'Varbergs BoIS FC', 'Brisbane Roar', 'El Paso Locomotive FC', 'Cheltenham Town', 'Leyton Orient', 'Doncaster Rovers', 'Bristol Rovers', 'Macarthur FC', 'Stellenbosch FC', 'Accrington Stanley', 'Arizona United', 'Northampton Town', 'Detroit City FC', 'Swindon Town', 'Port Vale', 'Orange County SC', 'AmaZulu', 'Golden Arrows', 'Degerfors IF', 'Colchester United', 'Forest Green Rovers', 'Tulsa Roughnecks', 'Wellington Phoenix', 'Jerv FK', 'Royal AM', 'Burton Albion', 'Galaxy LA II', 'Moroka Swallows', 'Hartford Athletic', 'Charleston Battery', 'Helsingborgs IF', 'Tianjin Teda', 'Tranmere Rovers', 'Monterey Bay', 'Morecambe', 'Sekhukhune United', 'Shanghai Greenland', 'Richards Bay', 'Chippa United', 'Bradford City', 'Newport County', 'Sutton United', 'Galaxy TS', 'Stevenage', 'Crewe Alexandra', 'Hebei China Fortune FC', 'Tshakhuma Tsha Madzivhandila', 'Maritzburg Utd', 'Henan Jianye', 'Wimbledon AFC', 'Indy Eleven', 'Dalian Aerbin', 'Guangzhou RF', 'Perth Glory', 'Wuhan Zall', 'Stockport County', 'Sundsvall GIF', 'Barrow', 'Gillingham', 'Grimsby Town', 'Rochdale', 'Tianjin Quanujian', 'Shenzhen FC', 'Crawley Town', 'Chongqing Lifan', 'Las Vegas Lights FC', 'Walsall', 'Loudoun United FC', 'Harrogate Town', 'Carlisle United', 'Atlanta United 2', 'Hartlepool', 'Guizhou Renhe', 'New York Red Bulls II', 'None']

logos = ['https://upload.wikimedia.org/wikipedia/commons/1/1b/FC_Bayern_München_logo_%282017%29.svg','https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a7/Paris_Saint-Germain_F.C..svg', 'https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona_%28crest%29.svg', 'https://upload.wikimedia.org/wikipedia/en/5/56/Real_Madrid_CF.svg', 'https://upload.wikimedia.org/wikipedia/en/7/79/Ajax_Amsterdam.svg', 'https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg', 'https://upload.wikimedia.org/wikipedia/en/7/77/FC_Red_Bull_Salzburg_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg', 'https://upload.wikimedia.org/wikipedia/commons/0/05/FC_Internazionale_Milano_2021.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f4/Atletico_Madrid_2017_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f1/FC_Porto.svg', 'https://upload.wikimedia.org/wikipedia/commons/2/2d/SSC_Neapel.svg', 'https://upload.wikimedia.org/wikipedia/commons/6/67/Borussia_Dortmund_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/b/b9/Villarreal_CF_logo-en.svg', 'https://upload.wikimedia.org/wikipedia/commons/d/d0/Logo_of_AC_Milan.svg', 'https://upload.wikimedia.org/wikipedia/en/0/04/RB_Leipzig_2014_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/3/33/Sporting_Clube_de_Portugal.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a2/SL_Benfica_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/35/Celtic_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/0/05/PSV_Eindhoven.svg', 'https://upload.wikimedia.org/wikipedia/commons/9/96/FC_Zenit_1_star_2015_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f1/Real_Sociedad_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/98/Club_Athletic_Bilbao_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/59/Bayer_04_Leverkusen_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/12/Logo_Olympique_Lyonnais_2022.png', 'https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/66/AtalantaBC.svg', 'https://upload.wikimedia.org/wikipedia/en/9/9e/Stade_Rennais_FC.svg', 'https://upload.wikimedia.org/wikipedia/commons/d/d8/Olympique_Marseille_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f7/AS_Roma_logo_%282017%29.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e3/Feyenoord_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/17/Real_Betis_Balompi%C3%A9.png', 'https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/4/44/1._FC_Union_Berlin_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/6d/SC_Freiburg_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f9/Aston_Villa_FC_crest_%282016%29.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a2/Crystal_Palace_FC_logo_%282022%29.svg', 'https://upload.wikimedia.org/wikipedia/en/c/ce/Valenciacf.svg', 'https://upload.wikimedia.org/wikipedia/commons/8/81/Borussia_M%C3%B6nchengladbach_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d0/Club_Brugge_KV_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/b/bc/Juventus_FC_2017_icon_%28black%29.svg', 'https://upload.wikimedia.org/wikipedia/en/c/ce/S.S._Lazio_badge.svg', 'https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg', 'https://upload.wikimedia.org/wikipedia/commons/4/41/AS_Monaco_FC_Logo_2021.svg', 'https://upload.wikimedia.org/wikipedia/en/1/12/RC_Celta_de_Vigo_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/2/2e/Flamengo_braz_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/e/e7/Logo_TSG_Hoffenheim.svg', 'https://upload.wikimedia.org/wikipedia/en/5/53/FC_Cologne_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/3f/Lille_OSC_2018_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/4/43/Rangers_FC.svg', 'https://upload.wikimedia.org/wikipedia/commons/0/04/Eintracht_Frankfurt_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/c/cc/RC_Lens_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/db/Osasuna_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/9/9e/Logo_Mainz_05.svg', 'https://upload.wikimedia.org/wikipedia/en/3/3b/Sevilla_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/79/S.C._Braga_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/fc/Wolverhampton_Wanderers.svg', 'https://upload.wikimedia.org/wikipedia/en/2/2d/Leicester_City_crest.svg', 'https://upload.wikimedia.org/wikipedia/commons/f/f2/2022_ACF_Fiorentina_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/e/eb/VfB_Stuttgart_1893_Logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/f/f3/Logo-VfL-Wolfsburg.svg', 'https://upload.wikimedia.org/wikipedia/en/8/80/Racing_Club_de_Strasbourg_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/39/Fenerbah%C3%A7e.svg', 'https://upload.wikimedia.org/wikipedia/commons/e/e0/AZ_Alkmaar.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e3/FC_Twente.svg', 'https://upload.wikimedia.org/wikipedia/commons/9/90/Slavia-symbol-nowordmark-RGB.png', 'https://upload.wikimedia.org/wikipedia/en/5/54/Leeds_United_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/3/35/Club_de_F%C3%BAtbol_Monterrey_2019_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/2e/OGC_Nice_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c9/FC_Southampton.svg', 'https://upload.wikimedia.org/wikipedia/en/b/b6/Club_Am%C3%A9rica_logo.png', 'https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/7/73/Dinamo_Zagreb_logo.png', 'https://upload.wikimedia.org/wikipedia/en/2/2e/Torino_FC_Logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/1/10/Palmeiras_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/f/f6/KRC_Genk_Logo_2016.svg', 'https://upload.wikimedia.org/wikipedia/en/c/ce/Udinese_Calcio_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/6b/BSC_Young_Boys_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/17/Rayo_Vallecano_logo.png', 'https://upload.wikimedia.org/wikipedia/en/5/5f/Clube_Atl%C3%A9tico_Mineiro_crest.svg', 'https://upload.wikimedia.org/wikipedia/commons/b/be/SV-Werder-Bremen-Logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/f/f1/Escudo_do_Sport_Club_Internacional.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a1/FC_Shakhtar_Donetsk.svg', 'https://upload.wikimedia.org/wikipedia/en/e/eb/Fulham_FC_%28shield%29.svg', 'https://upload.wikimedia.org/wikipedia/commons/8/81/Hertha_BSC_Logo_2012.svg', 'https://upload.wikimedia.org/wikipedia/commons/b/ba/Club_Espanyol_de_Foot-ball_1901.png', 'https://upload.wikimedia.org/wikipedia/en/4/46/Getafe_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/b/b5/Shield_of_Girona_football_club.png', 'https://upload.wikimedia.org/wikipedia/en/1/17/Norwich_City_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/4/46/Philadelphia_Union_2018_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/1c/US_Sassuolo_Calcio_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/13/UD_Almer%C3%ADa_logo.png', 'https://upload.wikimedia.org/wikipedia/en/c/ce/1FC_Slovacko.png', 'https://upload.wikimedia.org/wikipedia/en/9/92/Hellas_Verona_FC_logo_%282020%29.svg', 'https://upload.wikimedia.org/wikipedia/commons/6/6f/Brasao_do_Sao_Paulo_Futebol_Clube.svg', 'https://upload.wikimedia.org/wikipedia/commons/4/45/Logo_FC_Nantes_%28avec_fond%29_-_2019.svg', 'https://upload.wikimedia.org/wikipedia/commons/6/6d/FC_Schalke_04_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/9e/Fluminense_fc_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/82/Tigres_UANL_logo_%28crest%29.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e0/Rcd_mallorca.svg', 'https://upload.wikimedia.org/wikipedia/en/9/93/Pachuca_Tuzos_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/26/PFK_CSKA_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/9e/Steaua_Bucure%C8%99ti.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f1/Olympiacos_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/9c/Sheffield_United_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/f/f3/River_plate_logo_2022.svg', 'https://upload.wikimedia.org/wikipedia/commons/0/07/Grb-fk-crvena-zvezda.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c5/Shield_of_Real_Valladolid.png', 'https://upload.wikimedia.org/wikipedia/en/1/19/Stade_de_Reims_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c7/Trabzonspor_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c5/FC_Augsburg_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/9/91/FC_Spartak_Moscow_Logotype.png', 'https://upload.wikimedia.org/wikipedia/commons/5/5d/Logo_FC_Utrecht.svg', 'https://upload.wikimedia.org/wikipedia/en/7/71/RSC_Anderlecht_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/0b/Royal_Antwerp_Football_Club_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/8b/West_Bromwich_Albion.svg', 'https://upload.wikimedia.org/wikipedia/commons/7/72/VfL_Bochum_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/58/C%C3%A1diz_CF_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/5a/Sport_Club_Corinthians_Paulista_crest.svg', 'https://upload.wikimedia.org/wikipedia/commons/5/5c/Ferencv%C3%A1rosiTClog%C3%B3.png', 'https://upload.wikimedia.org/wikipedia/commons/9/93/SC_Dnipro-1_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/4/4c/FC_Lorient_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/5/57/Molde_Fotball_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e1/%C4%B0stanbul_Ba%C5%9Fak%C5%9Fehir_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/8d/FK_Bodo_Glimt_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/2e/Red_Bull_Bragantino_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/d/df/FC_Dynamo_Kyiv_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e5/Nottingham_Forest_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e2/Watford.svg', 'https://upload.wikimedia.org/wikipedia/en/5/5b/Bologna_F.C._1909_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/8/86/Los_Angeles_Football_Club.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e3/Viktoria_Plzen_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e5/AFC_Bournemouth_%282013%29.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f4/KAA_Gent_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/27/FC_Sheriff.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a7/Elche_CF_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/26/FC_Copenhagen_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/9d/Kawasaki_Frontale_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a8/Montpellier_HSC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/c/c5/SK_Sturm_Graz.svg', 'https://upload.wikimedia.org/wikipedia/commons/d/da/BesiktasJK-Logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/b/bf/ES_Troyes_AC.svg', 'https://upload.wikimedia.org/wikipedia/en/6/63/Toulouse_FC_2018_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/62/Burnley_F.C._Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/65/Yokohama_F_Marinos_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c8/SBV_Vitesse_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d2/U.C._Sampdoria_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d5/Vitória_Guimarães.svg', 'https://upload.wikimedia.org/wikipedia/en/8/8f/Gil_Vicente_F.C.png', 'https://upload.wikimedia.org/wikipedia/en/8/85/Us_lecce.svg', 'https://upload.wikimedia.org/wikipedia/en/8/8f/FC_Dynamo_Brest_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/6c/Angers_SCO.png', 'https://upload.wikimedia.org/wikipedia/en/3/30/FC_Krasnodar_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/3b/Santos_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/7/79/Galatasaray_4_Sterne_Logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/3/38/Cear%C3%A1_Sporting_Club_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/38/FC_Dinamo_Tbilisi_logo.png', 'https://upload.wikimedia.org/wikipedia/en/f/f0/Guadalajara_CD.svg', 'https://upload.wikimedia.org/wikipedia/en/d/dd/FC_Midtjylland_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/7b/Levante_Uni%C3%B3n_Deportiva%2C_S.A.D._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/1f/AC_Ajaccio_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/ed/FK_Partizan.svg', 'https://upload.wikimedia.org/wikipedia/commons/5/5d/FC_Stahl_Linz_2014.svg', 'https://upload.wikimedia.org/wikipedia/en/4/45/Fortaleza_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/96/Santos_Laguna_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/02/Royale_Union_Saint-Gilloise_logo.png', 'https://upload.wikimedia.org/wikipedia/en/5/5f/Clube_Atl%C3%A9tico_Mineiro_crest.svg', 'https://upload.wikimedia.org/wikipedia/en/a/ae/Urawa_Red_Diamonds_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/52/Clermont_Foot_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/70/PFC_Sochi_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e1/US_Cremonese_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e9/Empoli_F.C._logo_%282021%29.png', 'https://upload.wikimedia.org/wikipedia/en/e/e1/SC_Heerenveen_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f9/New_York_City_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/2/2c/Middlesbrough_FC_crest.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d1/Konyaspor_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/85/US_Salernitana_1919_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d8/KKS_Lech_Pozna%C5%84%27s_100th_anniversary_crest.png', 'https://upload.wikimedia.org/wikipedia/commons/2/2f/Nouveau_logo_aja.png', 'https://upload.wikimedia.org/wikipedia/en/5/53/Logo_of_NEC_Nijmegen.svg', 'https://upload.wikimedia.org/wikipedia/en/0/04/CFMontreal.svg', 'https://upload.wikimedia.org/wikipedia/commons/a/ac/Escudo_do_America_Futebol_Clube.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c0/Portimonense_Sporting_Clube_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/1c/A.C._Monza_logo_%282019%29.svg', 'https://upload.wikimedia.org/wikipedia/en/0/0e/F.C._Famalic%C3%A3o_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a2/FC_Rostov_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e9/Hapoel_Be%27er_Sheva.png', 'https://upload.wikimedia.org/wikipedia/en/c/c1/FC_Basel_crest.svg', 'https://upload.wikimedia.org/wikipedia/commons/a/aa/Spezia_Calcio.svg', 'https://upload.wikimedia.org/wikipedia/en/2/25/AS_Saint-%C3%89tienne_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/05/G_D_Chaves.png', 'https://upload.wikimedia.org/wikipedia/en/e/e3/F.C._Vizela_logo.png', 'https://upload.wikimedia.org/wikipedia/en/f/fc/Cuiab%C3%A1_Esporte_Clube_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/f/f5/Rosenborg_Trondheim_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/13/Club_Le%C3%B3n_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/e/e3/Boca_Juniors_logo18.svg', 'https://upload.wikimedia.org/wikipedia/en/0/0e/Apollon_Limassol_Logo.png', 'https://upload.wikimedia.org/wikipedia/en/9/94/GD_Estoril_Praia_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/61/Cagliari_Calcio_1920.svg', 'https://upload.wikimedia.org/wikipedia/commons/e/e3/FC_St._Gallen_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/5d/F.C._Girondins_de_Bordeaux_logo.png', 'https://upload.wikimedia.org/wikipedia/commons/f/f7/Hamburger_SV_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/4/4a/FC_Metz_2021_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/37/C.D._Santa_Clara_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/5/52/Botafogo_de_Futebol_e_Regatas_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/4/48/Paok_logo.png', 'https://upload.wikimedia.org/wikipedia/en/5/5d/Club_Puebla_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/db/Maccabi_Haifa_FC_Logo_2020.png', 'https://upload.wikimedia.org/wikipedia/en/d/d5/Logo_of_Granada_Club_de_F%C3%BAtbol.svg', 'https://upload.wikimedia.org/wikipedia/en/4/40/Boavista_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/51/New_York_Red_Bulls_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/d/d7/FK_Austria_Wien_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/0c/Rio_Ave_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/3/3d/Nashville_SC_MLS_2020.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d1/Adana_Demirspor_logo.png', 'https://upload.wikimedia.org/wikipedia/en/8/84/Panathinaikos_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/55/Sparta_Praha_logo.png', 'https://upload.wikimedia.org/wikipedia/commons/7/70/Los_Angeles_Galaxy_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/d/d2/F%C3%BAtbol_Club_Atlas.svg', 'https://upload.wikimedia.org/wikipedia/en/0/05/Silkeborg_IF_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/2c/FC_Groningen_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/67/RKC_Waalwijk_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d2/Cruz_Azul_2022.png', 'https://upload.wikimedia.org/wikipedia/commons/9/97/Logo_Parma_Calcio_1913_%28adozione_2016%29.svg', 'https://upload.wikimedia.org/wikipedia/en/7/7c/FC_Sochaux-Montbeliard_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/c/c2/Casa_PiaAC.png', 'https://upload.wikimedia.org/wikipedia/en/7/71/SK_Rapid_Wien.svg', 'https://upload.wikimedia.org/wikipedia/commons/b/bb/Atlanta_MLS.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e1/Royal_Charleroi_Sporting_Club_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/93/FC_Lokomotiv_Moscow_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/04/AEK_Athens_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e7/This_is_the_logo_for_Millwall_Football_Club.png', 'https://upload.wikimedia.org/wikipedia/en/b/b7/Randers_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/1e/Club_huracan_logo.png', 'https://upload.wikimedia.org/wikipedia/en/8/8b/LutonTownFC2009.png', 'https://upload.wikimedia.org/wikipedia/en/8/82/Preston_North_End_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/8/85/Austin_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/a/a4/Club_Toluca_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e9/Sanfrecce_Hiroshima_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/83/FC_Emmen_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/fe/Qaraba%C4%9F_FK_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/29/Stoke_City_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/3/39/Club_Universidad_Nacional_Pumas_UNAM_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/2/21/Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f9/AEK_Larnaca_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/4/40/Alanyaspor_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/23/FC_Nordsj%C3%A6lland_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/25/Genoa_C.F.C._logo.png', 'https://upload.wikimedia.org/wikipedia/en/d/d4/Go_Ahead_Eagles_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f5/Bristol_City_crest.svg', 'https://upload.wikimedia.org/wikipedia/en/8/83/Antalyaspor_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/c/cd/Wolfsberger_AC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/27/Seattle_Sounders_FC.svg', 'https://upload.wikimedia.org/wikipedia/commons/5/56/Escudo_de_Racing_Club_%282014%29.svg', 'https://upload.wikimedia.org/wikipedia/en/7/7a/K._Sint-Truidense_V.V._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/85/Cerezo_Osaka_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/7/7d/V%C3%A5lerenga_Oslo_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/31/Queens_Park_Rangers_crest.svg', 'https://upload.wikimedia.org/wikipedia/en/1/1a/Coventry_City_F.C._logo.png', 'https://upload.wikimedia.org/wikipedia/en/7/7e/CFR_Cluj_badge.svg', 'https://upload.wikimedia.org/wikipedia/en/c/cb/SC_Cambuur_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d4/Aberdeen_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/b/b5/Club_Necaxa_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/a/aa/SM_Caen_2016_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/d/da/Escudo_de_Estudiantes_de_La_Plata.svg', 'https://upload.wikimedia.org/wikipedia/commons/d/dc/Columbus_Crew_logo_2021.svg', 'https://upload.wikimedia.org/wikipedia/en/3/37/Kashima_Antlers.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c9/FC_Dallas_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/36/Akhmat_Grozny_logo.png', 'https://upload.wikimedia.org/wikipedia/en/6/6a/Orlando_City_2014.svg', 'https://upload.wikimedia.org/wikipedia/commons/e/e6/Djurgardens_IF_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/29/Club_Tijuana_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/0a/Atl%C3%A9tico_Clube_Goianiense_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/9/9b/Escudo_Talleres_2015.svg', 'https://upload.wikimedia.org/wikipedia/commons/4/47/Escudo_del_Club_Atl%C3%A9tico_Tigre_-_2019.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c6/Gazişehir_Gaziantep_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/18/Kasimpasa_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/16/Swansea_City_AFC_logo.png', 'https://upload.wikimedia.org/wikipedia/commons/1/1b/Escudo_de_la_Asociaci%C3%B3n_Atl%C3%A9tica_Argentinos_Juniors.svg', 'https://upload.wikimedia.org/wikipedia/en/b/b5/Brondby_IF_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/8d/Krylia_sovetov_logo.png', 'https://upload.wikimedia.org/wikipedia/en/3/38/New_England_Revolution_%282021%29_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/0e/FC_Volendam_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/10/Classic_Maritimo_Logo.png', 'https://upload.wikimedia.org/wikipedia/en/9/92/SV_Darmstadt_98_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/0a/Hammarby_IF_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/81/PFC_Ludogorets_Razgrad_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/35/Portland_Timbers_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/4/4a/Goi%C3%A1s_Esporte_Clube_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/5/56/San_lorenzo_almagro_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/78/FC_Cincinnati_primary_logo_2018.svg', 'https://upload.wikimedia.org/wikipedia/commons/0/04/Lillestrom_SK_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/b/b4/FC_Arouca.png', 'https://upload.wikimedia.org/wikipedia/en/3/3c/Cardiff_City_crest.svg', 'https://upload.wikimedia.org/wikipedia/en/0/0f/Blackburn_Rovers.svg', 'https://upload.wikimedia.org/wikipedia/commons/d/db/Escudo_del_Club_Atl%C3%A9tico_Independiente.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e8/Minnesota_United_FC_%28MLS%29_Primary_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/c/c3/Excelsior_Rotterdam_Logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/8/8b/Oud-Heverlee_Löwen.svg', 'https://upload.wikimedia.org/wikipedia/en/3/3b/SD_Eibar_logo_2016.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f8/Deportivo_Alaves_logo_%282020%29.svg', 'https://upload.wikimedia.org/wikipedia/en/6/61/Heart_of_Midlothian_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/54/Real_Salt_Lake_2010.svg', 'https://upload.wikimedia.org/wikipedia/commons/3/38/Coritiba_FBC_%282011%29_-_PR.svg', 'https://upload.wikimedia.org/wikipedia/en/2/28/KV_Mechelen_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/df/Blackpool_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/e/e0/CHI_Logo-2021.svg', 'https://upload.wikimedia.org/wikipedia/en/4/41/FC_Z%C3%BCrich_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/5d/BK_Hacken_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/73/F.C._Pa%C3%A7os_de_Ferreira.svg', 'https://upload.wikimedia.org/wikipedia/en/1/17/Brescia_calcio_badge.svg', 'https://upload.wikimedia.org/wikipedia/en/1/14/Viborg_FF.png', 'https://upload.wikimedia.org/wikipedia/en/8/88/Sheffield_Wednesday_badge.svg', 'https://upload.wikimedia.org/wikipedia/en/7/77/Logo_Sunderland.svg', 'https://upload.wikimedia.org/wikipedia/en/b/b3/SC_Paderborn_07_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/9/94/Fortuna_D%C3%BCsseldorf.svg', 'https://upload.wikimedia.org/wikipedia/en/2/20/UD_Las_Palmas_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/61/Benevento_Calcio_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/4/43/Ipswich_Town.svg', 'https://upload.wikimedia.org/wikipedia/en/0/0b/Frosinone_Calcio_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/7c/Royal_Standard_de_Liege.svg', 'https://upload.wikimedia.org/wikipedia/en/2/2d/Fortuna_Sittard_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/11/Quer%C3%A9taro_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/12/FC_Luzern_crest.svg', 'https://upload.wikimedia.org/wikipedia/en/2/2b/Colorado_Rapids_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/7d/Huddersfield_Town_A.F.C._logo.png', 'https://upload.wikimedia.org/wikipedia/commons/f/fe/Avai_FC_%2805-E%29_-_SC.svg', 'https://upload.wikimedia.org/wikipedia/en/3/37/Hibernian_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/0/01/SK_Slovan_Bratislava_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/8f/FC_St._Pauli_logo_%282018%29.svg', 'https://upload.wikimedia.org/wikipedia/en/9/9d/FC_Ju%C3%A1rez_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/09/Sporting_Kansas_City_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/6d/Gimnasia_Esgrima_LP_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/6/69/Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys_de_Rosario.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f4/Kayserispor_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e4/Aris_Thessaloniki_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/9f/Paris_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/24/FC_Nizhny_Novgorod_emblem.svg', 'https://upload.wikimedia.org/wikipedia/en/5/55/The_logo_of_Mamelodi_Sundowns_F.C.png', 'https://upload.wikimedia.org/wikipedia/commons/8/8e/Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n.svg', 'https://upload.wikimedia.org/wikipedia/en/7/7c/Toronto_FC_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/54/Hull_City_A.F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/13/Viking_FK_logo_2020.svg', 'https://upload.wikimedia.org/wikipedia/en/4/4a/Derby_County_crest.svg', 'https://upload.wikimedia.org/wikipedia/en/6/6e/Real_Oviedo_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/c/c1/Aalborg_Boldspilklub_%28logo%29.svg', 'https://upload.wikimedia.org/wikipedia/en/3/3d/AC_Omonia_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/56/En_Avant_Guingamp_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/fc/Le_Havre_AC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/f/fa/Ec-juventude-logo-escudo.png', 'https://upload.wikimedia.org/wikipedia/commons/7/70/Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg', 'https://upload.wikimedia.org/wikipedia/en/4/43/Wigan_Athletic.svg', 'https://upload.wikimedia.org/wikipedia/en/6/69/Real_Zaragoza_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/7/74/2022_Venezia_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/b/b0/Club_lanus_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/2/26/Arminia-wappen-2021.svg', 'https://upload.wikimedia.org/wikipedia/commons/8/84/Servette_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/e/ef/Malmo_FF_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/ea/Fatih_Karag%C3%BCmr%C3%BCk_S.K..png', 'https://upload.wikimedia.org/wikipedia/en/a/a6/IFK_Goteborg_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/37/IF_Elfsborg_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/da/Mazatl%C3%A1n_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c1/Sagan_Tosu_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/9d/FC_Tokyo_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/8a/Logo_of_SD_Huesca.svg', 'https://upload.wikimedia.org/wikipedia/en/1/17/K.V.C._Westerlo_logo.png', 'https://upload.wikimedia.org/wikipedia/en/c/ce/Rosario_Central_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/11/Reading_FC.svg', 'https://upload.wikimedia.org/wikipedia/commons/c/c8/Karlsruher_SC_Logo_2.svg', 'https://upload.wikimedia.org/wikipedia/en/b/b6/Atl%C3%A9tico_San_Luis_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/90/Amiens_SC_logo.png', 'https://upload.wikimedia.org/wikipedia/en/7/7b/SK_Austria_Klagenfurt_New_Logo.png', 'https://upload.wikimedia.org/wikipedia/en/5/5c/Inter_Miami_CF_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f6/Lustenau.png', 'https://upload.wikimedia.org/wikipedia/en/a/ac/AGF_Aarhus_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/5/59/Swarovski_Wattens-_Logo_Gesamtverein.svg', 'https://upload.wikimedia.org/wikipedia/commons/b/bd/Logo_Cercle_Brugge_2022.png', 'https://upload.wikimedia.org/wikipedia/en/2/20/Sivasspor_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/4/48/Real_Sporting_de_Gijon.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f3/Nagoya_Grampus_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/68/Birmingham_City_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/4/4b/GCAT.png', 'https://upload.wikimedia.org/wikipedia/en/f/f8/Livingston_FC_club_badge_new.png', 'https://upload.wikimedia.org/wikipedia/en/f/f7/Dijon_FCO_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/a/ac/FC_Lugano_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/13/FC_Cartagena_escudo.png', 'https://upload.wikimedia.org/wikipedia/en/6/6d/FK_RFS_logo.png', 'https://upload.wikimedia.org/wikipedia/commons/4/42/Escudo_de_Banfield.png', 'https://upload.wikimedia.org/wikipedia/commons/9/9d/1._FC_Heidenheim_1846.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c0/Rotherham_United_FC.svg', 'https://upload.wikimedia.org/wikipedia/commons/e/e1/Escudo_del_Club_Alt%C3%A9tico_Platense.svg', 'https://upload.wikimedia.org/wikipedia/en/7/7b/Hatayspor.gif', 'https://upload.wikimedia.org/wikipedia/en/0/02/FC_Sion.png', 'https://upload.wikimedia.org/wikipedia/en/8/81/TSV_Hartberg.png', 'https://upload.wikimedia.org/wikipedia/commons/2/27/Escudo_del_Club_Central_C%C3%B3rdoba_de_Santiago_del_Estero.svg', 'https://upload.wikimedia.org/wikipedia/en/8/84/Grasshopper_Club_Zürich_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/30/Str%C3%B8msgodset_IF_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/00/FC_Ballkani.svg', 'https://upload.wikimedia.org/wikipedia/en/3/3b/Fckhimkiforwiki.png', 'https://upload.wikimedia.org/wikipedia/en/5/5f/AIK_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/b/b8/Club_Deportivo_Legan%C3%A9s_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/c/c8/Motherwell_FC_crest.svg', 'https://upload.wikimedia.org/wikipedia/en/5/5d/Vancouver_Whitecaps_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/6/68/Escudo_Colon_Con_Estrella.png', 'https://upload.wikimedia.org/wikipedia/en/9/91/Charlotte_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/23/Ascoli_Calcio_1898_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/98/San_Jose_Earthquakes_2014.svg', 'https://upload.wikimedia.org/wikipedia/commons/8/8a/Vissel_Kobe_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f9/CD_Tenerife_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/9/92/Escudo_del_Club_Atl%C3%A9tico_Sarmiento_de_Jun%C3%ADn.svg', 'https://upload.wikimedia.org/wikipedia/en/7/7f/FK_%C5%BDalgiris_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/5/55/C.A._Patronato_ESCUDO_OFICIAL.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e3/AS_Cittadella_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/e/e0/Logo_del_Club_Atl%C3%A9tico_Tucum%C3%A1n_-_2017.svg', 'https://upload.wikimedia.org/wikipedia/en/3/38/Portsmouth_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/87/KV_Oostende_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/17/KV_Kortrijk_logo_2016.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c9/Barnsley_FC.svg', 'https://upload.wikimedia.org/wikipedia/commons/f/fa/1._FC_N%C3%BCrnberg_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/32/D.C._United_logo_%282016%29.svg', 'https://upload.wikimedia.org/wikipedia/en/6/60/Shimizu_S-Pulse_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/e/e7/SPAL_Ferrara.svg', 'https://upload.wikimedia.org/wikipedia/commons/0/0b/Odense_Boldklub.svg', 'https://upload.wikimedia.org/wikipedia/en/6/60/Arsenal_Sarand%C3%AD_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/96/Logo_of_FC_Fakel_Voronezh.png', 'https://upload.wikimedia.org/wikipedia/commons/c/cd/Hannover_96_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/05/N%C3%AEmes_Olympique_2018_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/57/Ross_County_F.C._logo.png', 'https://upload.wikimedia.org/wikipedia/en/6/66/Houston_Dynamo_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d4/Ternana_logo.png', 'https://upload.wikimedia.org/wikipedia/en/0/06/FK_Haugesund_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c3/SV_Ried_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/56/Urbs_Reggina_1914_%282019_logo%29.png', 'https://upload.wikimedia.org/wikipedia/en/1/10/Pisa_S.C._logo.png', 'https://upload.wikimedia.org/wikipedia/en/c/c1/Giresunspor.png', 'https://upload.wikimedia.org/wikipedia/commons/3/30/Holstein_Kiel_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/0a/S.S.C._Bari_logo.png', 'https://upload.wikimedia.org/wikipedia/en/8/8f/FC_Ural_Yekaterinburg_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e4/Sarpsborg_08_FF_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/26/Barracas_Central_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/99/Kashiwa_Reysol_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f2/SpVgg_Greuther_F%C3%BCrth_logo_%282017%29.svg', 'https://upload.wikimedia.org/wikipedia/en/0/0f/Melbourne_City_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/3/32/KilmarnockLogo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f9/FC_Orenburg_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/7a/AC_Horsens_logo_2017.svg', 'https://upload.wikimedia.org/wikipedia/en/3/3a/Ankaragucu_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/32/St_Mirren_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/57/Troms%C3%B8_IL_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/c/cb/Volos_Logo.png', 'https://upload.wikimedia.org/wikipedia/en/0/01/SD_Ponferradina_logo.png', 'https://upload.wikimedia.org/wikipedia/en/8/8c/Valenciennes_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/0/00/Burgos_CF_escudo.png', 'https://upload.wikimedia.org/wikipedia/en/0/08/Ac_Perugia_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/67/Zulte-Waregem_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/7/7d/Tampa_Bay_Rowdies_logo_%28with_Tampa_Bay%2C_two_gold_stars%29.svg', 'https://upload.wikimedia.org/wikipedia/en/3/32/%C3%9Cmraniyespor_logo.png', 'https://upload.wikimedia.org/wikipedia/en/f/f5/StJohnstoneFC_crest_new.png', 'https://upload.wikimedia.org/wikipedia/en/a/af/Kalmar_FF_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/b/b9/Villarreal_CF_logo-en.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d4/Peterborough_United.svg', 'https://upload.wikimedia.org/wikipedia/en/9/92/Hokkaido_Consadole_Sapporo_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/b/b8/CD_Mirand%C3%A9s_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e9/Atromitos.png', 'https://upload.wikimedia.org/wikipedia/en/a/a8/Shield_of_UD_Ibiza.png', 'https://upload.wikimedia.org/wikipedia/en/6/6e/SC_Bastia_%28shield%29.png', 'https://upload.wikimedia.org/wikipedia/en/0/0f/IFK_Norrkoping_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/01/Louisville_City_FC_%282020%29_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/82/Bolton_Wanderers_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/09/DUFCcrest2022.png', 'https://upload.wikimedia.org/wikipedia/en/6/6d/M%C3%A1laga_CF.svg', 'https://upload.wikimedia.org/wikipedia/en/9/98/Guangzhou_Evergrande_Taobao_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/02/HJK_Helsinki_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/37/Albacete_balompie.svg', 'https://upload.wikimedia.org/wikipedia/en/7/78/SC_Rheindorf_Altach_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/34/Odds_BK_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/de/Grenoble_Foot_38_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d3/Kas_Eupen_Logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/1/16/Ionikos_Nikaia_%28logo%29.svg', 'https://upload.wikimedia.org/wikipedia/en/b/bf/MK_Dons.png', 'https://upload.wikimedia.org/wikipedia/en/f/fb/Wycombe_Wanderers_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c5/FC_Vaduz_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/29/Lyngby_BK_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a2/Kyoto_Sanga_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/4/4c/Asteras_Tripolis_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/2/2c/Logo_Como_1907_2019.png', 'https://upload.wikimedia.org/wikipedia/en/6/69/Istanbulspor.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f2/Panetolikos_new_emblem.png', 'https://upload.wikimedia.org/wikipedia/commons/8/8f/F.C._Hansa_Rostock_Logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/f/fb/FC_Andorra_logo.png', 'https://upload.wikimedia.org/wikipedia/en/b/bc/Avispa_Fukuoka_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c8/Shonan_Bellmare_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f5/Racing_de_Santander_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a8/Plymouth_Argyle_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/09/CD_Lugo_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/87/Modena_FC_Logo.png', 'https://upload.wikimedia.org/wikipedia/commons/9/9b/FC_Torpedo_Moscow_Logotype.png', 'https://upload.wikimedia.org/wikipedia/en/3/38/San_Diego_Loyal_SC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/b/b2/Aalesunds_FK_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/7a/Logo_of_Western_Sydney_Wanderers_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/3/3e/Oxford_United_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/a/a2/FC_Annecy_2022_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/4/46/Hamarkameratene_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/94/PauFC_logo.png', 'https://upload.wikimedia.org/wikipedia/en/2/2a/Aldosivi_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/df/Palermo_Calcio_logo_%282019%29.svg', 'https://upload.wikimedia.org/wikipedia/commons/2/2b/Stade_Lavallois_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/95/Melbourne_Victory.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f6/Beijing_Guoan_F.C..png', 'https://upload.wikimedia.org/wikipedia/en/a/a6/Kristiansund_BK_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/e/e2/Gamba_Osaka_2022_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/4/45/PAS_Giannina_emblem_2017.png', 'https://upload.wikimedia.org/wikipedia/en/d/d7/San_Antonio_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/53/Birmingham_Legion_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/68/Chamois_Niortais_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a5/Mjallby_AIF_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/3/3d/Jahn_Regensburg_logo2014.svg', 'https://upload.wikimedia.org/wikipedia/en/6/64/Cosenza_Calcio_logo.png', 'https://upload.wikimedia.org/wikipedia/en/b/b4/Shanghai_Port_FC.png', 'https://upload.wikimedia.org/wikipedia/commons/d/d3/SV_Sandhausen.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e6/RFC_Seraing_logo.png', 'https://upload.wikimedia.org/wikipedia/commons/6/6a/CharltonBadge_30Jan2020.png', 'https://upload.wikimedia.org/wikipedia/en/7/70/Rodez_AF_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e9/OFI_FC_Logo_2020.png', 'https://upload.wikimedia.org/wikipedia/en/c/c3/FC_Sudtirol_logo_2016.png', 'https://upload.wikimedia.org/wikipedia/commons/d/d3/Logo_1_FC_Kaiserslautern.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f3/Salford_City_FC_Logo.png', 'https://upload.wikimedia.org/wikipedia/en/9/95/Orlando_Pirates_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/6/63/US_Quevilly_Rouen_M%C3%A9tropole_Club_Crest.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e6/Sandefjord_Fotball_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/b/bb/APO_Levadiakos_%28logo%29.svg', 'https://upload.wikimedia.org/wikipedia/en/3/38/Rio_Grande_Valley_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/4/4e/Pittsburgh_Riverhounds_SC_2018_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a3/FC_Pyunik_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/23/Memphis_901_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/7a/Logo_of_Western_Sydney_Wanderers_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/7/78/Western_United_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/4/49/Adelaide_Crows_logo_2010.svg', 'https://upload.wikimedia.org/wikipedia/en/c/cf/IK_Sirius_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/c/cc/Central_Coast_Mariners_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f6/Sacramento_Republic_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/1/16/Kaizer_Chiefs_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e2/SuperSport_United_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d5/Newcastle_United_Jets_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/1b/Shrewsbury_Town_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/fb/Shamrock_Rovers_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/60/Eintracht_Braunschweig_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/e6/Oakland_Roots_SC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/76/Miami_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d1/New_Mexico_United_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/73/Colorado_Springs_Switchbacks_FC_%282020%29_logo.svg', 'https://upload.wikimedia.org/wikipedia/commons/8/84/1._FC_Magdeburg.svg', 'https://upload.wikimedia.org/wikipedia/en/1/12/IFK_Varnamo_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f1/Lincoln_City_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/b/b1/Jubilo_Iwata_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a0/Shandong_Taishan_2022_logo.jpg', 'https://upload.wikimedia.org/wikipedia/en/3/3b/Jiangsu_Suning_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/fe/Mpumalanga_Black_Aces_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/7d/Mansfield_Town_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/e/ed/Fleetwood_Town_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/71/Exeter_City_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f8/PAS_Lamia_1964_logo.png', 'https://upload.wikimedia.org/wikipedia/en/a/a9/FC_Winterthur_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/8f/Cambridge_United_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/d/da/Varbergs_BoIS_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/88/Brisbane_Roar_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/00/El_Paso_Locomotive_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c3/Cheltenham_Town_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a8/Leyton_Orient_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c5/Doncaster_Rovers_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/4/47/Bristol_Rovers_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/b/bd/Macarthur_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/25/Stellenbosch_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/b/ba/Accrington_Stanley_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/93/Phoenix_Rising_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/2d/Northampton_Town_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/0/03/Detroit_City_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a3/Swindon_Town_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/5/5f/Port_Vale_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/2d/Orange_County_SC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/26/AmaZulu_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/61/Lamontville_Golden_Arrows_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/9/90/Degerfors_IF_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/4/48/Colchester_United_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/8/85/Forest_Green_Rovers_crest.svg', 'https://upload.wikimedia.org/wikipedia/en/2/2d/TulsaRoughnecks.png', 'https://upload.wikimedia.org/wikipedia/en/d/de/Wellington_Phoenix_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/ef/FK_Jerv_logo.svg', 'https://upload.wikimedia.org/wikipedia/fr/a/a3/Royal_AM_logo.png', 'https://upload.wikimedia.org/wikipedia/en/5/53/Burton_Albion_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/1/18/LA_Galaxy_II_logo.svg', 'https://upload.wikimedia.org/wikipedia/de/5/52/Moroka_Swallows_Logo.jpg', 'https://upload.wikimedia.org/wikipedia/en/3/34/Hartford_Athletic_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/24/Charleston_Battery_%282020%29_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/7/75/Helsingborgs_IF_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/6/6e/Tianjin_Jinmen_Tiger_F.C..png', 'https://upload.wikimedia.org/wikipedia/en/e/e6/Tranmere_Rovers_FC_logo.png', 'https://upload.wikimedia.org/wikipedia/en/4/49/Monterey_Bay_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/b/bd/Morecambe_FC.png', 'https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg', 'https://upload.wikimedia.org/wikipedia/en/7/79/Shanghai_Shenhua_F.C.png', 'https://upload.wikimedia.org/wikipedia/en/b/b2/Richards_Bay_F.C._logo.png', 'https://upload.wikimedia.org/wikipedia/en/0/0c/Chippa_United_FC_logo.png', 'https://upload.wikimedia.org/wikipedia/en/3/32/Bradford_City_AFC.png', 'https://upload.wikimedia.org/wikipedia/en/b/b0/Newport_County_crest.png', 'https://upload.wikimedia.org/wikipedia/en/8/8f/Sutton_United_F.C._logo.png', 'https://upload.wikimedia.org/wikipedia/en/6/65/TS_Galaxy.png', 'https://upload.wikimedia.org/wikipedia/commons/9/91/Stevenage_FC_Crest.jpg', 'https://upload.wikimedia.org/wikipedia/en/9/9d/Crewe_Alexandra.svg', 'https://upload.wikimedia.org/wikipedia/en/c/c8/Hebei_F.C._logo.jpg', 'https://upload.wikimedia.org/wikipedia/en/e/ea/Tshakhuma_Tsha_Madzivhandila_F.C._logo.png', 'https://upload.wikimedia.org/wikipedia/en/2/28/Maritzburg_United_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/f/f8/Henan_Songshan_Longmen_F.C.png', 'https://upload.wikimedia.org/wikipedia/en/1/1b/AFC_Wimbledon_%282020%29_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/2f/Indy_Eleven_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/a/a3/Dalian_Professional_FC_logo.png', 'https://upload.wikimedia.org/wikipedia/en/4/4a/Guangzhou_City_F.C..png', 'https://upload.wikimedia.org/wikipedia/en/e/ea/25_anniversy_perth_glory_logo.jpg', 'https://upload.wikimedia.org/wikipedia/en/e/ec/Wuhan_Yangtze_River_F.C..png', 'https://upload.wikimedia.org/wikipedia/en/4/43/Stockport_County_FC_logo_2020.svg', 'https://upload.wikimedia.org/wikipedia/en/9/99/GIF_Sundsvall_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/2/28/Barrow_AFC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/5/5e/FC_Gillingham_Logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/db/Grimsby_Town_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d5/Rochdale_badge.png', 'https://upload.wikimedia.org/wikipedia/fr/5/50/Tianjin_Quanjian.jpg', 'https://upload.wikimedia.org/wikipedia/en/3/3d/Shenzhen_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/8/8b/Crawley_Town_FC_logo.png', 'https://upload.wikimedia.org/wikipedia/en/f/f4/Chongqing_Liangjiang_Athletic_F.C.png', 'https://upload.wikimedia.org/wikipedia/en/3/34/Las_Vegas_Lights_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/e/ef/Walsall_FC.svg', 'https://upload.wikimedia.org/wikipedia/en/3/32/Loudoun_United_FC_logo.svg', 'https://upload.wikimedia.org/wikipedia/en/d/d1/Harrogate_town_badge.png', 'https://upload.wikimedia.org/wikipedia/en/6/63/Carl_Badge.png', 'https://upload.wikimedia.org/wikipedia/en/0/05/Atlanta_United_2_crest.svg', 'https://upload.wikimedia.org/wikipedia/en/3/37/Hartlepool_United_FC_logo_2017.png', 'https://upload.wikimedia.org/wikipedia/en/5/52/Beijing_Renhe_F.C._logo.svg', 'https://upload.wikimedia.org/wikipedia/en/3/31/New_York_Red_Bulls_II_crest.svg', 'https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg']

clubs_df=pd.DataFrame()

countries_df=pd.DataFrame()

clubs_df['clubs']=clubs

countries_df['countries']=countries
    
def equipo_casa_input_():
    if equipo_casa_input in input:
        i=input.index(equipo_casa_input)
        return(new_input[i])
    else:
        return equipo_casa_input
    
def equipo_visita_input_():
    if equipo_visita_input in input:
        i=input.index(equipo_visita_input)
        return(new_input[i])
    else:
        return equipo_visita_input

def club_logo_home():
    
    try:
        l=clubs.index(str(equipo_casa_input_()))
        logo_ht=logos[l]
        return logo_ht
    except IndexError:
        logo_ht="https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"
        return logo_ht

    print(logo_ht)

def country_flag_home():

    var_b_="https://commons.wikimedia.org/wiki/"+str(equipo_casa_input_())

    var_b=urllib.parse.quote(var_b_,safe=':/.%')

    try:
        html_page = urlopen(str(var_b))
    except OSError as e:
        html_page = urlopen("https://commons.wikimedia.org/wiki/File:No_image_available.svg")


    soup = bs(html_page, features='html.parser')
    images = []

    for img in soup.findAll('img'):
        images.append(img.get('src'))

    flag_list: List[Any] = [k for k in images if "Flag_of_" or "Coat_of_arms" in k]
        
    print(flag_list)

    import unidecode

    unaccented_flag_list=[]

    for i in flag_list:
        j=unidecode.unidecode(i)
        unaccented_flag_list.append(j)

    my_string=str(equipo_casa_input_())
    first_word=my_string.partition("File:")[2]

    unaccented_first_word = unidecode.unidecode(first_word)

    try:
        index = [idx for idx, s in enumerate(unaccented_flag_list) if str(unaccented_first_word) in s][0]
        flag_ht=flag_list[index]
        return flag_ht
    except IndexError:
        flag_ht="https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"
        return flag_ht

    print(flag_ht)
    
def print_team_logo_home():
    if countries_df['countries'].eq(str(equipo_casa_input_())).any():
        return country_flag_home()
    else:
        return club_logo_home()

def club_logo_road():
     try:
        l=clubs.index(str(equipo_visita_input_()))
        logo_rt=logos[l]
        return logo_rt
     except IndexError:
        logo_rt = "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"
        return logo_rt

     print(logo_rt)

def country_flag_road():
 
    var_d_="https://commons.wikimedia.org/wiki/"+str(equipo_visita_input_())

    var_d=urllib.parse.quote(var_d_,safe=':/.%')

    try:
        html_page = urlopen(str(var_d))
    except OSError as e:
        html_page = urlopen("https://commons.wikimedia.org/wiki/File:No_image_available.svg")

    soup = bs(html_page, features='html.parser')
    images = []

    for img in soup.findAll('img'):
        images.append(img.get('src'))

    flag_list: List[Any] = [k for k in images if "Flag_of_" or "Coat_of_arms" in k]

    import unidecode

    unaccented_flag_list=[]

    for i in flag_list:
        j=unidecode.unidecode(i)
        unaccented_flag_list.append(j)

    my_string=str(equipo_visita_input_())
    first_word=my_string.partition("File:")[2]

    unaccented_first_word = unidecode.unidecode(first_word)

    try:
        index = [idx for idx, s in enumerate(unaccented_flag_list) if str(unaccented_first_word) in s][0]
        flag_rt=flag_list[index]
        return flag_rt
    except IndexError:
        flag_rt = "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"
        return flag_rt

def print_team_logo_road():
    if countries_df['countries'].eq(str(equipo_visita_input_())).any():
        return country_flag_road()
    else:
        return club_logo_road()

enlace = "http"
team_logo_home = print_team_logo_home()
team_logo_road = print_team_logo_road()

def logo_home():
    if "http" not in str(team_logo_home):
        return "https:"+print_team_logo_home()
    else:
        return print_team_logo_home()

def logo_road():
    if "http" not in str(team_logo_road):
        return "https:"+print_team_logo_road()
    else:
        return print_team_logo_road()

try:
    col1, mid1, col2, mid2, col3, mid3, col4 = st.columns([1,1,5,5,1,1,5])
    with col1:
        try:
            st.image(logo_home(), width=60)
        except OSError as e:
            st.image("https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg",width=60)
    with col2:
        st.write(equipo_casa_input)
    with mid2:
        st.markdown("against")
    with col3:
        try:
            st.image(logo_road(), width=60)
        except OSError as e:
            st.image("https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg",width=60)
    with col4:
        st.markdown(equipo_visita_input)
except TypeError:
    st.markdown("Please select teams")

st.write("Match simulation")

latest_iteration3 = st.empty()
bar3= st.progress(0)

try:
    index_casa_equipo = df_pf.index[df_pf['name'] == equipo_casa_input]
    index_visita_equipo = df_pf.index[df_pf['name'] == equipo_visita_input]

    equipo_casa_of = df_pf.at[index_casa_equipo[0], 'off']
    equipo_casa_def = df_pf.at[index_casa_equipo[0], 'defe']

    equipo_visita_of = df_pf.at[index_visita_equipo[0], 'off']
    equipo_visita_def = df_pf.at[index_visita_equipo[0], 'defe']

    goles_esperados_equipo_casa = ((equipo_casa_of) + (equipo_visita_def)) / 2
    goles_esperados_equipo_visita = ((equipo_visita_of) + (equipo_casa_def)) / 2

    goles_esperados_equipo_casa_redondeado = (math.ceil(goles_esperados_equipo_casa * 100) / 100.0)

    goles_esperados_equipo_visita_redondeado = (math.ceil(goles_esperados_equipo_visita * 100) / 100.0)

except IndexError:
    goles_esperados_equipo_casa_redondeado = 1
    goles_esperados_equipo_visita_redondeado= 1
    goles_esperados_equipo_casa=1
    goles_esperados_equipo_visita=1

col5, mid4, col6, mid5, col7, mid5, col8 = st.columns([1,1,5,5,1,1,5])

with col6:
    st.write('Expected goals in the match')

with col8:
    st.write('Expected goals in the match')

col9, mid6, col10, mid7, col11, mid5, col12 = st.columns([1,1,5,5,1,1,5])

with col10:
    st.write(goles_esperados_equipo_casa_redondeado)

with col12:
    st.write(goles_esperados_equipo_visita_redondeado)

latest_iteration4 = st.empty()
bar4 = st.progress(0)

probabilidad_casa = [random.random()]

for x in range(0, 9999):
    probabilidad_casa.append(random.random())

probabilidad_visita = [random.random()]

for x in range(0, 9999):
    probabilidad_visita.append(random.random())

random_marcadores_equipo_casa = poisson.ppf(probabilidad_casa, goles_esperados_equipo_casa)
random_marcadores_equipo_visita = poisson.ppf(probabilidad_visita, goles_esperados_equipo_visita)
random_marcadores_partido = [str(x[0])+" - " + str(x[1]) for x in zip(random_marcadores_equipo_casa, random_marcadores_equipo_visita)]

results = list()

for i, j in zip(random_marcadores_equipo_casa, random_marcadores_equipo_visita):
    if i > j:
        results.append("home team wins")
    elif i < j:
        results.append("visiting team wins")
    else:
        results.append("tie")

resultados_posibles_equipo_casa = list(range(0, 11))
resultados_posibles_equipo_visita = list(range(0, 11))

probabilidad_marcadores_final_casa = [((random_marcadores_equipo_casa == 0).sum()) / 10000,
                                      ((random_marcadores_equipo_casa == 1).sum()) / 10000,
                                      ((random_marcadores_equipo_casa == 2).sum()) / 10000,
                                      ((random_marcadores_equipo_casa == 3).sum()) / 10000,
                                      ((random_marcadores_equipo_casa == 4).sum()) / 10000,
                                      ((random_marcadores_equipo_casa == 5).sum()) / 10000,
                                      ((random_marcadores_equipo_casa == 6).sum()) / 10000,
                                      ((random_marcadores_equipo_casa == 7).sum()) / 10000,
                                      ((random_marcadores_equipo_casa == 8).sum()) / 10000,
                                      ((random_marcadores_equipo_casa == 9).sum()) / 10000,
                                      ((random_marcadores_equipo_casa == 10).sum()) / 10000]

probabilidad_marcadores_final_visita = [((random_marcadores_equipo_visita == 0).sum()) / 10000,
                                        ((random_marcadores_equipo_visita == 1).sum()) / 10000,
                                        ((random_marcadores_equipo_visita == 2).sum()) / 10000,
                                        ((random_marcadores_equipo_visita == 3).sum()) / 10000,
                                        ((random_marcadores_equipo_visita == 4).sum()) / 10000,
                                        ((random_marcadores_equipo_visita == 5).sum()) / 10000,
                                        ((random_marcadores_equipo_visita == 6).sum()) / 10000,
                                        ((random_marcadores_equipo_visita == 7).sum()) / 10000,
                                        ((random_marcadores_equipo_visita == 8).sum()) / 10000,
                                        ((random_marcadores_equipo_visita == 9).sum()) / 10000,
                                        ((random_marcadores_equipo_visita == 10).sum()) / 10000]

probabilidad_marcadores_final_partido = [a * b for a, b in zip(probabilidad_casa, probabilidad_visita)]

equipo_casa_gana = equipo_casa_input + " wins a " + str(round(((results.count("home team wins") / 10000) * 100),2)) + " % of the 10 000 simulations of the match"
equipo_visita_gana= equipo_visita_input + " wins a " + str(round(((results.count("visiting team wins") / 10000) * 100),2)) + " % of the 10 000 simulations of the match"
empate = "The match results in a tie " + str(round(((results.count("tie") / 10000) * 100),2)) + " % of the 10 000 simulations of the match"

datalinea_casa = pd.DataFrame({'Team':[equipo_casa_input, equipo_casa_input, equipo_casa_input, equipo_casa_input, equipo_casa_input,
                                         equipo_casa_input, equipo_casa_input, equipo_casa_input, equipo_casa_input, equipo_casa_input, equipo_casa_input],
                               'Probability of score': probabilidad_marcadores_final_casa, 'Possible results': resultados_posibles_equipo_casa},
                              index=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
datalinea_visita = pd.DataFrame({'Team':[equipo_visita_input, equipo_visita_input, equipo_visita_input, equipo_visita_input,equipo_visita_input, equipo_visita_input,
                                           equipo_visita_input, equipo_visita_input,equipo_visita_input, equipo_visita_input, equipo_visita_input],
                                 'Probability of score': probabilidad_marcadores_final_visita, 'Possible results': resultados_posibles_equipo_visita},
                                index=[12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22])

marco = [datalinea_casa, datalinea_visita]

datalinea_partido = pd.concat(marco)

datalinea_partido_grafico= alt.Chart(datalinea_partido).mark_line().encode(
    x='Possible results',
    y='Probability of score',
    color=alt.Color('Team',
                    scale=alt.Scale(
                        domain=[equipo_casa_input,equipo_visita_input],
                        range=['red',
                               'blue'])
                    )
).properties(
)

latest_iteration5 = st.empty()
bar5 = st.progress(0)


st.altair_chart(datalinea_partido_grafico)

etiquetas = equipo_casa_input + ' wins', equipo_visita_input + ' wins', 'Tie'
proporciones = [results.count("home team wins"), results.count("visiting team wins"), results.count("tie")]
colores = ['green', 'red', 'gold']

st.markdown(equipo_casa_gana)
st.markdown(equipo_visita_gana)
st.markdown(empate)

fig1, ax1 = plt.subplots()
ax1.pie(proporciones, labels=etiquetas, colors=colores, autopct='%1.1f%%',
        shadow=True, startangle=140)
ax1.axis('equal')

st.pyplot(fig1)

lista_marcadores_casa = [0.0,
                         0.0,
                         0.0,
                         0.0,
                         0.0,
                         0.0,
                         0.0,
                         0.0,
                         0.0,
                         0.0,
                         0.0,
                         1.0,
                         1.0,
                         1.0,
                         1.0,
                         1.0,
                         1.0,
                         1.0,
                         1.0,
                         1.0,
                         1.0,
                         1.0,
                         2.0,
                         2.0,
                         2.0,
                         2.0,
                         2.0,
                         2.0,
                         2.0,
                         2.0,
                         2.0,
                         2.0,
                         2.0,
                         3.0,
                         3.0,
                         3.0,
                         3.0,
                         3.0,
                         3.0,
                         3.0,
                         3.0,
                         3.0,
                         3.0,
                         3.0,
                         4.0,
                         4.0,
                         4.0,
                         4.0,
                         4.0,
                         4.0,
                         4.0,
                         4.0,
                         4.0,
                         4.0,
                         4.0,
                         5.0,
                         5.0,
                         5.0,
                         5.0,
                         5.0,
                         5.0,
                         5.0,
                         5.0,
                         5.0,
                         5.0,
                         5.0,
                         6.0,
                         6.0,
                         6.0,
                         6.0,
                         6.0,
                         6.0,
                         6.0,
                         6.0,
                         6.0,
                         6.0,
                         6.0,
                         7.0,
                         7.0,
                         7.0,
                         7.0,
                         7.0,
                         7.0,
                         7.0,
                         7.0,
                         7.0,
                         7.0,
                         7.0,
                         8.0,
                         8.0,
                         8.0,
                         8.0,
                         8.0,
                         8.0,
                         8.0,
                         8.0,
                         8.0,
                         8.0,
                         8.0,
                         9.0,
                         9.0,
                         9.0,
                         9.0,
                         9.0,
                         9.0,
                         9.0,
                         9.0,
                         9.0,
                         9.0,
                         9.0,
                         10.0,
                         10.0,
                         10.0,
                         10.0,
                         10.0,
                         10.0,
                         10.0,
                         10.0,
                         10.0,
                         10.0,
                         10.0]

lista_marcadores_visita = [0.0,
                           1.0,
                           2.0,
                           3.0,
                           4.0,
                           5.0,
                           6.0,
                           7.0,
                           8.0,
                           9.0,
                           10.0,
                           0.0,
                           1.0,
                           2.0,
                           3.0,
                           4.0,
                           5.0,
                           6.0,
                           7.0,
                           8.0,
                           9.0,
                           10.0,
                           0.0,
                           1.0,
                           2.0,
                           3.0,
                           4.0,
                           5.0,
                           6.0,
                           7.0,
                           8.0,
                           9.0,
                           10.0,
                           0.0,
                           1.0,
                           2.0,
                           3.0,
                           4.0,
                           5.0,
                           6.0,
                           7.0,
                           8.0,
                           9.0,
                           10.0,
                           0.0,
                           1.0,
                           2.0,
                           3.0,
                           4.0,
                           5.0,
                           6.0,
                           7.0,
                           8.0,
                           9.0,
                           10.0,
                           0.0,
                           1.0,
                           2.0,
                           3.0,
                           4.0,
                           5.0,
                           6.0,
                           7.0,
                           8.0,
                           9.0,
                           10.0,
                           0.0,
                           1.0,
                           2.0,
                           3.0,
                           4.0,
                           5.0,
                           6.0,
                           7.0,
                           8.0,
                           9.0,
                           10.0,
                           0.0,
                           1.0,
                           2.0,
                           3.0,
                           4.0,
                           5.0,
                           6.0,
                           7.0,
                           8.0,
                           9.0,
                           10.0,
                           0.0,
                           1.0,
                           2.0,
                           3.0,
                           4.0,
                           5.0,
                           6.0,
                           7.0,
                           8.0,
                           9.0,
                           10.0,
                           0.0,
                           1.0,
                           2.0,
                           3.0,
                           4.0,
                           5.0,
                           6.0,
                           7.0,
                           8.0,
                           9.0,
                           10.0,
                           0.0,
                           1.0,
                           2.0,
                           3.0,
                           4.0,
                           5.0,
                           6.0,
                           7.0,
                           8.0,
                           9.0,
                           10.0]

# Create list of bins.

marcadores_posibles_partido = [str(x[0])+" - " + str(x[1]) for x in zip(lista_marcadores_casa, lista_marcadores_visita)]

# Construct array of frequency of possible scores.

frecuencia_de_marcadores_posibles = list()

for i in marcadores_posibles_partido:
    result = random_marcadores_partido.count(i)
    frecuencia_de_marcadores_posibles.append(result)

# Create bar chart to visualize score frequencies in the 10 000 simulations.

plt.style.use('ggplot')

objects = marcadores_posibles_partido
y_pos = np.arange(len(objects))
desempeño = frecuencia_de_marcadores_posibles

fig2, ax2 = plt.subplots()
ax2.bar(y_pos, frecuencia_de_marcadores_posibles, align='center', alpha=0.5)
plt.xticks(y_pos, marcadores_posibles_partido, fontsize= 3, rotation='vertical')
plt.ylabel('Frequency')
plt.title('Frequency of possible scores ' + equipo_casa_input + ' against ' + equipo_visita_input)

st.pyplot(fig2)

# Define forecast algorithm in a function.
# Forecast the result that has a higher frequency, given that the multinomial distribution is significantly different from the null distributions expected_x
# Retrieve most likely score for the result that is forecast

latest_iteration6 = st.empty()
bar6 = st.progress(0)


from scipy.stats import chi2

simulated=[results.count("home team wins"),results.count("tie"),results.count("visiting team wins")]

simulations =list(range(1,5000))
simulations_=[]

for i in simulations:
  j=2*i
  simulations_.append(j)

import scipy
from scipy.stats import chi2

alpha = 0.05

df = 2

cr=chi2.ppf(q=1-alpha,df=df)

x_list=[]

expected_a= [[(5000-(i/2)),(5000-(i/2)),i] for i in simulations_ if i<3334]

for i in expected_a:
    x_a = sum([(o-e)**2./e for o,e in zip(simulated,i)])
    x_list.append(x_a)

expected_b = [[(5000-(i/2)),i,(5000-(i/2))] for i in simulations_ if i<3334]
  
for j in expected_b:
    x_b = sum([(o-e)**2./e for o,e in zip(simulated,j)])
    x_list.append(x_b)

expected_c = [[i,(5000-(i/2)),(5000-(i/2))] for i in simulations_ if i<3334]

for k in expected_c:
    x_c = sum([(o-e)**2./e for o,e in zip(simulated,k)])
    x_list.append(x_c)

expected_d= [[(10000-(2*i)),i,i] for i in simulations if i>3333]

for l in expected_d:
    x_d = sum([(o-e)**2./e for o,e in zip(simulated,l)])
    x_list.append(x_d)

expected_e= [[i,(10000-(2*i)),i] for i in simulations if i>3333]

for m in expected_e:
    x_e = sum([(o-e)**2./e for o,e in zip(simulated,m)])
    x_list.append(x_e)

expected_f= [[i,i,(10000-(2*i))] for i in simulations if i>3333]

for n in expected_f:
    x_f = sum([(o-e)**2./e for o,e in zip(simulated,n)])
    x_list.append(x_f)

def forecast():
    if all(i>cr for i in x_list):
        if ((results.count("home team wins")) / 10000) > ((results.count("visiting team wins")) / 10000)+0.02 and ((results.count("home team wins")) / 10000) > ((results.count("tie"))/10000)+0.02: return(str(equipo_casa_input) + " wins:")
        elif ((results.count("visiting team wins")) / 10000) > ((results.count("home team wins")) / 10000)+0.02 and ((results.count("visiting team wins")) / 10000) > ((results.count("tie"))/10000)+0.02: return(str(equipo_visita_input) + " wins:")
        else: return("the match results in a tie:")
    else:
        return("the match results in a tie:")

Results = results
Scores = random_marcadores_partido

forecast_scores_dataframe=pd.DataFrame(
    {'Results': Results,
     'Scores': Scores})


scores_home_team_wins = forecast_scores_dataframe.loc[forecast_scores_dataframe.Results == "home team wins"]
scores_road_team_wins = forecast_scores_dataframe.loc[forecast_scores_dataframe.Results == "visiting team wins"]
scores_tie = forecast_scores_dataframe.loc[forecast_scores_dataframe.Results == "tie"]

idxmax_score_home_team_wins = scores_home_team_wins['Scores'].value_counts().sort_index().idxmax()
idxmax_score_road_team_wins = scores_road_team_wins['Scores'].value_counts().sort_index().idxmax()
idxmax_score_tie = scores_tie['Scores'].value_counts().sort_index().idxmax()

def score_forecast():
    if all(i>cr for i in x_list):
        if ((results.count("home team wins")) / 10000) > ((results.count("visiting team wins")) / 10000)+0.02 and (
                (results.count("home team wins")) / 10000) > ((results.count("tie"))/10000)+0.02:
            return(idxmax_score_home_team_wins)
        elif ((results.count("visiting team wins")) / 10000) > ((results.count("home team wins")) / 10000)+0.02 and (
                (results.count("visiting team wins")) / 10000) > ((results.count("tie"))/10000)+0.02:
            return(idxmax_score_road_team_wins)
        else:
            return(idxmax_score_tie)
    else:
        return(idxmax_score_tie)

st.subheader("Result of the simulations")

st.markdown("After 10 000 simulations of\nthe match, and considering the lastest\noffensive and defensive indicators\nof the teams, the forecast is\nthat " + str(forecast()) + "\n" + str(score_forecast()))

st.subheader("Sources")

st.markdown("Updated match data for the simulation comes from the public repository published by Martj42\nin GitHub, available at:")
link='Martj42 Github repository [link](https://raw.githubusercontent.com/martj42/international_results/master/results.csv)'
st.markdown(link,unsafe_allow_html=True)

st.markdown("The team logos and the flags are images in the public domain,\navailable at:")
link2='Wikipedia [link](https://www.Wikipedia.org)'
st.markdown(link2,unsafe_allow_html=True)