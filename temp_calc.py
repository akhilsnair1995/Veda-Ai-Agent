mbh_to_btu = 293.071 # BTU per MBH
kwh_to_btu = 3412.14 # BTU per kWh
therm_to_btu = 1000000 / 5280 # Therms to BTU (1 Therm = 100,000 BTU)
hours_per_day = 10 
days_per_week = 5
weeks_per_year = 52

cooling_capacity_mbh = 50

daily_energy_btu = cooling_capacity_mbh * mbh_to_btu * hours_per_day
weekly_energy_btu = daily_energy_btu * days_per_week
annual_energy_btu = weekly_energy_btu * weeks_per_year

annual_energy_kwh = annual_energy_btu / kwh_to_btu
carbon_footprint_electricity_lbs_co2 = annual_energy_kwh * 0.85
carbon_footprint_natural_gas_lbs_co2 = (annual_energy_btu / therm_to_btu) * 11.7

total_carbon_footprint_lbs_co2 = carbon_footprint_electricity_lbs_co2 + carbon_footprint_natural_gas_lbs_co2
total_carbon_footprint_tons_co2 = total_carbon_footprint_lbs_co2 / 2204.62
total_carbon_footprint_tons_co2