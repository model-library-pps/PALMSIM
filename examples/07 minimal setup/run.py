# to allow us to work with spreadsheets import the "pandas" library
import pandas as pd

# to allow us to import PalmSim, which is in a different folder
# append the path to this folder
import sys
sys.path.append('../../PalmSim')
sys.path.append('../..')
from PalmField import PalmField

# We load the weather data, here concerning North Sumatra.
weather_data = pd.read_csv('./input/north_sumatra.csv',index_col='Date')
weather_data.index = pd.to_datetime(weather_data.index)

# We set the year of planting
year_of_planting = weather_data.index.year[0]

# Now we run PalmSim
# 1. Initialize the model
p = PalmField(year_of_planting=year_of_planting)

# 2. Couple the weather data:
p.weather.radiation_series = weather_data['Solar (MJ/m2)']
p.weather.rainfall_series = weather_data['Precip (mm)']

# 3. Run the model
df = p.run(duration=360,)

# 4. The output is saved
filepath = 'output/result.csv'
df.to_csv(filepath)

# Done!
print()
print('Finished, see {:}'.format(filepath))