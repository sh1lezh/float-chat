import xarray as xr
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta

# Load NetCDF
ds = xr.open_dataset('20240101_prof.nc')
print("Variables:", list(ds.variables))

# Define variables (based on previous output)
time_var = 'JULD'
lat_var = 'LATITUDE'
lon_var = 'LONGITUDE'
pres_var = 'PRES'
temp_var = 'TEMP'
sal_var = 'PSAL'
float_id_var = 'PLATFORM_NUMBER'

# Convert to DataFrame
df = ds[[pres_var, temp_var, sal_var, lat_var, lon_var, time_var, float_id_var]].to_dataframe().reset_index()

# Check if JULD is datetime or numeric
if df[time_var].dtype == 'datetime64[ns]':
    df['TIME'] = df[time_var]
else:
    df['TIME'] = pd.to_datetime('1950-01-01') + pd.to_timedelta(df[time_var], unit='D')

# Rename columns
df = df.rename(columns={
    pres_var: 'PRES',
    temp_var: 'TEMP',
    sal_var: 'PSAL',
    lat_var: 'LATITUDE',
    lon_var: 'LONGITUDE',
    float_id_var: 'float_id',
    'N_PROF': 'profile_id'
})

# Select columns and drop missing data (minimal filtering)
df = df[['float_id', 'PRES', 'TEMP', 'PSAL', 'LATITUDE', 'LONGITUDE', 'TIME', 'profile_id']].dropna()

# Inspect DataFrame before saving
print("DataFrame before saving:")
print(df.head())
print("DataFrame size:", df.shape)
print("Years:", df['TIME'].dt.year.unique())
print("Latitude range:", df['LATITUDE'].min(), df['LATITUDE'].max())
print("Longitude range:", df['LONGITUDE'].min(), df['LONGITUDE'].max())

# Store in SQLite
engine = create_engine('sqlite:///argo.db')
df.to_sql('profiles', engine, if_exists='replace', index=False)
print("Data stored in SQLite: argo.db")

# Verify
with engine.connect() as conn:
    result = pd.read_sql("SELECT * FROM profiles LIMIT 5", conn)
    print("Sample data from SQLite:\n", result)