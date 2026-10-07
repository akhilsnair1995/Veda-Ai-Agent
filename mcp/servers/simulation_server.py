# mcp/servers/simulation_server.py
# Comprehensive MEP Engineering Simulation & Calculation Server for Veda
# Covers HVAC, Psychrometrics, Hydronics, Plumbing, Electrical, and Fire Protection

import sys
import math
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

server = MCPServer(name="simulation", version="2.0.0")

# ─────────────────────────────────────────────────────────────
# 1. PSYCHROMETRICS (ASHRAE Fundamentals)
# ─────────────────────────────────────────────────────────────

def calc_psychrometrics(dry_bulb_f: float, relative_humidity_pct: float = None, wet_bulb_f: float = None, dew_point_f: float = None, pressure_psi: float = 14.696) -> str:
    """
    Calculate comprehensive psychrometric properties of moist air at given atmospheric pressure (default 14.696 psi sea level).
    Requires dry_bulb_f and at least one moisture parameter (relative_humidity_pct, wet_bulb_f, or dew_point_f).
    """
    try:
        t_f = float(dry_bulb_f)
        t_r = t_f + 459.67  # Rankine
        p = float(pressure_psi)
        
        # Saturation vapor pressure over liquid water (ASHRAE formula approximation, psi)
        # log(Pws) = C8/T + C9 + C10*T + C11*T^2 + C12*T^3 + C13*log(T)
        c8 = -1.0440397e4
        c9 = -1.1294650e1
        c10 = -2.7022355e-2
        c11 = 1.2890360e-5
        c12 = -2.4780681e-9
        c13 = 6.5459673
        
        def get_pws(temp_r):
            ln_pws = (c8 / temp_r) + c9 + (c10 * temp_r) + (c11 * (temp_r**2)) + (c12 * (temp_r**3)) + (c13 * math.log(temp_r))
            return math.exp(ln_pws)

        pws = get_pws(t_r)

        # Determine vapor pressure (pw) based on available input
        if relative_humidity_pct is not None:
            rh = float(relative_humidity_pct) / 100.0
            rh = max(0.001, min(1.0, rh))
            pw = rh * pws
        elif dew_point_f is not None:
            dp_r = float(dew_point_f) + 459.67
            pw = get_pws(dp_r)
            rh = min(1.0, pw / pws)
        elif wet_bulb_f is not None:
            twb_f = float(wet_bulb_f)
            twb_r = twb_f + 459.67
            pws_wb = get_pws(twb_r)
            ws_wb = 0.621945 * pws_wb / (p - pws_wb)
            # Carrier equation
            w = ((1093 - 0.556 * twb_f) * ws_wb - 0.240 * (t_f - twb_f)) / (1093 + 0.444 * t_f - twb_f)
            pw = (p * w) / (0.621945 + w)
            rh = min(1.0, max(0.001, pw / pws))
        else:
            return "Error: You must provide either relative_humidity_pct, wet_bulb_f, or dew_point_f along with dry_bulb_f."

        # Humidity ratio (W, lb water / lb dry air)
        w = 0.621945 * pw / (p - pw)
        grains = w * 7000.0

        # Enthalpy (h, Btu / lb dry air)
        h = 0.240 * t_f + w * (1061.0 + 0.444 * t_f)

        # Specific volume (v, cu ft / lb dry air)
        # v = R_da * T / (P - Pw), R_da = 0.37048 psi*ft3/(lb*R)
        v = (0.37048 * t_r) / (p - pw)

        # Dew point approximation from vapor pressure
        alpha = math.log(pw)
        dp_f = 100.45 + 33.193 * alpha + 2.319 * (alpha**2) + 0.17074 * (alpha**3) + 1.2063 * (pw**0.1984)

        # Wet bulb estimation via Stull polynomial if not directly provided
        if wet_bulb_f is None:
            rh_percent = rh * 100.0
            t_c = (t_f - 32.0) * 5.0 / 9.0
            tw_c = t_c * math.atan(0.151977 * math.sqrt(rh_percent + 8.313659)) + \
                   math.atan(t_c + rh_percent) - math.atan(rh_percent - 1.676331) + \
                   0.00391838 * (rh_percent**1.5) * math.atan(0.023101 * rh_percent) - 4.686035
            twb_f = (tw_c * 9.0 / 5.0) + 32.0

        return (
            f"=== ASHRAE PSYCHROMETRIC ANALYSIS ===\n"
            f"Pressure: {p:.3f} psi (Elevation: Sea Level / Standard)\n"
            f"Dry Bulb Temp:      {t_f:.2f} °F\n"
            f"Wet Bulb Temp:      {twb_f:.2f} °F\n"
            f"Dew Point Temp:     {dp_f:.2f} °F\n"
            f"Relative Humidity:  {rh * 100.0:.1f} %\n"
            f"Humidity Ratio (W): {w:.5f} lb_w/lb_da ({grains:.1f} grains/lb)\n"
            f"Enthalpy (h):       {h:.2f} Btu/lb_da\n"
            f"Specific Volume:    {v:.3f} cu.ft/lb_da\n"
            f"Vapor Pressure:     {pw:.4f} psi"
        )
    except Exception as e:
        return f"Psychrometric calculation error: {e}"


# ─────────────────────────────────────────────────────────────
# 2. HVAC LOADS & AIRFLOW SIZING (ASHRAE RTS / FUNDAMENTALS)
# ─────────────────────────────────────────────────────────────

def calc_hvac_loads(area_sqft: float, 
                    sensible_heat_gain_btuh: float = None, 
                    latent_heat_gain_btuh: float = 0.0, 
                    space_temp_f: float = 75.0, 
                    supply_temp_f: float = 55.0, 
                    occupancy_people: int = 0, 
                    outdoor_cfm_per_person: float = 20.0,
                    outdoor_cfm_per_sqft: float = 0.06) -> str:
    """
    Calculate HVAC cooling airflow (CFM), sensible/latent capacity in Tons, 
    and minimum ventilation airflow requirements per ASHRAE 62.1.
    If sensible_heat_gain_btuh is omitted, an estimate of 30 Btu/hr/sqft is used.
    """
    try:
        area = float(area_sqft)
        delta_t = float(space_temp_f) - float(supply_temp_f)
        if delta_t <= 0:
            return "Error: space_temp_f must be strictly greater than supply_temp_f."

        if sensible_heat_gain_btuh is None:
            # Rule of thumb commercial baseline
            sensible_btuh = area * 30.0
        else:
            sensible_btuh = float(sensible_heat_gain_btuh)

        latent_btuh = float(latent_heat_gain_btuh)
        total_btuh = sensible_btuh + latent_btuh

        # Sensible heat formula: Qs = 1.08 * CFM * delta_T (standard air density)
        supply_cfm = sensible_btuh / (1.08 * delta_t)

        # Tons of refrigeration (1 Ton = 12,000 Btu/hr = 3.517 kW)
        cooling_tons = total_btuh / 12000.0
        cooling_kw = cooling_tons * 3.51685
        shr = sensible_btuh / total_btuh if total_btuh > 0 else 1.0

        # ASHRAE 62.1 Ventilation Standard: Vbz = (Rp * Pz) + (Ra * Az)
        people = int(occupancy_people)
        ventilation_cfm = (people * float(outdoor_cfm_per_person)) + (area * float(outdoor_cfm_per_sqft))
        ventilation_pct = (ventilation_cfm / supply_cfm * 100.0) if supply_cfm > 0 else 0.0

        return (
            f"=== HVAC COOLING & AIRFLOW SIZING ===\n"
            f"Conditioned Area:        {area:,.0f} sq.ft\n"
            f"Design Space / Supply:   {space_temp_f:.1f} °F / {supply_temp_f:.1f} °F (delta_T = {delta_t:.1f} °F)\n"
            f"Sensible Heat Gain:      {sensible_btuh:,.0f} Btu/hr ({sensible_btuh/area:.1f} Btu/hr/sq.ft)\n"
            f"Latent Heat Gain:        {latent_btuh:,.0f} Btu/hr\n"
            f"Total Heat Load:         {total_btuh:,.0f} Btu/hr\n"
            f"Sensible Heat Ratio:     {shr:.2f}\n"
            f"-----------------------------------------\n"
            f"REQUIRED SUPPLY AIRFLOW: {supply_cfm:,.0f} CFM ({supply_cfm/area:.2f} CFM/sq.ft)\n"
            f"TOTAL COOLING CAPACITY:  {cooling_tons:.2f} Tons ({cooling_kw:.2f} kW)\n"
            f"Square Feet per Ton:     {area/cooling_tons:.0f} sq.ft/Ton\n"
            f"-----------------------------------------\n"
            f"ASHRAE 62.1 OUTDOOR AIR: {ventilation_cfm:,.0f} CFM ({ventilation_pct:.1f}% of total supply)\n"
            f"  - Occupant Component:  {people * outdoor_cfm_per_person:,.0f} CFM ({people} occupants @ {outdoor_cfm_per_person} CFM/p)\n"
            f"  - Building Component:  {area * outdoor_cfm_per_sqft:,.0f} CFM ({area:,.0f} sq.ft @ {outdoor_cfm_per_sqft} CFM/sq.ft)"
        )
    except Exception as e:
        return f"HVAC load calculation error: {e}"


# ─────────────────────────────────────────────────────────────
# 3. DUCT SIZING & EQUAL FRICTION (ASHRAE / HUEBSCHER)
# ─────────────────────────────────────────────────────────────

def calc_duct_sizing(airflow_cfm: float, 
                     target_friction_loss: float = 0.08, 
                     max_velocity_fpm: float = 1200.0, 
                     aspect_ratio_limit: float = 3.0) -> str:
    """
    Size supply/return/exhaust ducts using the Equal Friction method (typically 0.08-0.10 in. wg / 100 ft).
    Calculates circular duct diameter, velocity, and converts to equivalent rectangular duct dimensions 
    using Huebscher's formula.
    """
    try:
        cfm = float(airflow_cfm)
        hf = float(target_friction_loss) # in wg / 100ft
        max_v = float(max_velocity_fpm)

        if cfm <= 0 or hf <= 0:
            return "Error: Airflow (CFM) and target friction loss must be positive."

        # ASHRAE standard air friction equation inverted for round duct diameter (inches):
        # hf = 0.109136 * (Q^1.9) / (D^5.02) -> D = (0.109136 * Q^1.9 / hf) ^ (1 / 5.02)
        d_inches = (0.109136 * (cfm ** 1.9) / hf) ** (1.0 / 5.02)
        d_rounded = round(d_inches)
        
        # Cross sectional area (sq ft)
        area_sqft = math.pi * ((d_inches / 12.0) ** 2) / 4.0
        velocity = cfm / area_sqft
        velocity_pressure = (velocity / 4005.0) ** 2

        # Check velocity limit
        velocity_warning = ""
        if velocity > max_v:
            velocity_warning = f"\n[!] WARNING: Calculated velocity ({velocity:.0f} FPM) exceeds maximum limit ({max_v:.0f} FPM). Consider increasing duct size or lowering friction rate to prevent acoustic noise."

        # Equivalent rectangular ducts using Huebscher's formula:
        # De = 1.30 * (a * b)^0.625 / (a + b)^0.25
        # We test practical heights (in 2-inch increments from 8" to 36")
        rectangular_options = []
        for height in range(8, 40, 2):
            for width in range(height, 72, 2):
                ratio = width / height
                if ratio > aspect_ratio_limit:
                    continue
                de = 1.30 * ((width * height) ** 0.625) / ((width + height) ** 0.25)
                if abs(de - d_inches) <= 0.6:
                    rect_area_sqft = (width * height) / 144.0
                    v_rect = cfm / rect_area_sqft
                    rectangular_options.append((width, height, ratio, v_rect))
                    break

        rect_str = "\n".join([f"  - {w}\" W x {h}\" H (Aspect Ratio: {r:.1f}:1, Velocity: {v:.0f} FPM)" for w, h, r, v in rectangular_options[:4]])

        return (
            f"=== DUCT SIZING (EQUAL FRICTION METHOD) ===\n"
            f"Airflow:              {cfm:,.0f} CFM\n"
            f"Target Friction Rate: {hf:.3f} in. w.g. / 100 ft\n"
            f"-----------------------------------------\n"
            f"ROUND DUCT:\n"
            f"  - Exact Diameter:   {d_inches:.2f} inches\n"
            f"  - Standard Nominal: {d_rounded}\" diameter round duct\n"
            f"  - Air Velocity:     {velocity:.0f} FPM\n"
            f"  - Velocity Pressure: {velocity_pressure:.3f} in. w.g.\n"
            f"-----------------------------------------\n"
            f"EQUIVALENT RECTANGULAR OPTIONS (Huebscher):\n"
            f"{rect_str if rect_str else '  - Use standard round duct or custom aspect ratio.'}"
            f"{velocity_warning}"
        )
    except Exception as e:
        return f"Duct sizing calculation error: {e}"


# ─────────────────────────────────────────────────────────────
# 4. HYDRAULIC PIPE FRICTION & PUMP HEAD (HAZEN-WILLIAMS / DARCY)
# ─────────────────────────────────────────────────────────────

def calc_pipe_friction(flow_gpm: float, 
                       diameter_inches: float, 
                       length_ft: float, 
                       pipe_material: str = "steel_sch40", 
                       fittings_count_elbows: int = 0, 
                       fittings_count_valves: int = 0) -> str:
    """
    Calculate fluid flow velocity, friction head loss, equivalent length of fittings, 
    and total pressure drop across hydronic pipe runs.
    """
    try:
        q = float(flow_gpm)
        d = float(diameter_inches)
        l = float(length_ft)

        if d <= 0 or q <= 0 or l <= 0:
            return "Error: Flow (GPM), diameter (inches), and length (ft) must be positive values."

        # Hazen-Williams Roughness Constant C
        material_c_map = {
            "steel_sch40": 120,
            "copper_type_l": 150,
            "copper_type_k": 150,
            "pvc_sch40": 150,
            "pvc_sch80": 150,
            "cast_iron": 100,
            "ductile_iron": 140
        }
        c = material_c_map.get(pipe_material.lower(), 120)

        # Velocity (FPS): V = (0.4085 * Q) / (d^2)
        velocity = (0.4085 * q) / (d ** 2)

        # Fittings equivalent length (standard approximation L/D ~ 30 for 90 deg elbow, 10 for gate valve)
        # 1 fitting equivalent length in feet ~ (L/D) * (d / 12)
        equiv_length_elbow = float(fittings_count_elbows) * (30.0 * (d / 12.0))
        equiv_length_valve = float(fittings_count_valves) * (15.0 * (d / 12.0))
        total_equiv_length = l + equiv_length_elbow + equiv_length_valve

        # Hazen-Williams head loss equation:
        # h_f (ft per 100 ft) = 0.2083 * (100 / C)^1.852 * (Q^1.852 / d^4.8655) * 100
        hf_per_100ft = 0.2083 * ((100.0 / c) ** 1.852) * ((q ** 1.852) / (d ** 4.8655)) * 100.0
        total_head_loss_ft = (hf_per_100ft / 100.0) * total_equiv_length
        total_pressure_drop_psi = total_head_loss_ft / 2.307 # 1 psi = 2.307 ft H2O

        # ASHRAE Hydronic velocity guidelines check
        velocity_status = "Optimal"
        if velocity < 2.0:
            velocity_status = "Low (Risk of air trapping or sediment accumulation, min 2.0 FPS recommended)"
        elif velocity > 10.0:
            velocity_status = "HIGH (Erosion and water hammer risk, max 8-10 FPS recommended)"

        return (
            f"=== HYDRONIC PIPE FRICTION & HEAD LOSS ===\n"
            f"Material:               {pipe_material.upper()} (Hazen-Williams C = {c})\n"
            f"Flow Rate:              {q:,.1f} GPM\n"
            f"Inside Diameter:        {d:.2f} inches\n"
            f"Fluid Velocity:         {velocity:.2f} ft/sec ({velocity_status})\n"
            f"-----------------------------------------\n"
            f"Physical Pipe Length:   {l:,.1f} ft\n"
            f"Fittings Allowance:     {equiv_length_elbow + equiv_length_valve:.1f} ft ({fittings_count_elbows} elbows, {fittings_count_valves} valves)\n"
            f"Total Equivalent Run:   {total_equiv_length:,.1f} ft\n"
            f"Friction Head Loss:     {hf_per_100ft:.2f} ft of H2O / 100 ft ({hf_per_100ft / 2.307:.2f} psi / 100 ft)\n"
            f"-----------------------------------------\n"
            f"TOTAL HEAD LOSS:        {total_head_loss_ft:.2f} ft of head\n"
            f"TOTAL PRESSURE DROP:    {total_pressure_drop_psi:.2f} psi"
        )
    except Exception as e:
        return f"Pipe friction calculation error: {e}"


# ─────────────────────────────────────────────────────────────
# 5. FAN SYSTEM POWER & MOTOR SIZING
# ─────────────────────────────────────────────────────────────

def calc_fan_system_power(airflow_cfm: float, 
                          external_static_pressure_in_wg: float, 
                          fan_efficiency: float = 0.65, 
                          motor_efficiency: float = 0.90) -> str:
    """
    Calculate fan Air Horsepower (AHP), Brake Horsepower (BHP), and electrical motor kW demand
    given airflow and total static pressure.
    """
    try:
        cfm = float(airflow_cfm)
        sp = float(external_static_pressure_in_wg)
        fan_eff = float(fan_efficiency)
        motor_eff = float(motor_efficiency)

        if cfm <= 0 or sp <= 0 or fan_eff <= 0 or motor_eff <= 0:
            return "Error: All inputs must be strictly positive."

        # Air Horsepower: AHP = (CFM * Total Pressure) / 6356
        ahp = (cfm * sp) / 6356.0

        # Brake Horsepower: BHP = AHP / fan_efficiency
        bhp = ahp / fan_eff

        # Electrical Motor kW: kW = (BHP * 0.7457) / motor_efficiency
        motor_kw = (bhp * 0.7457) / motor_eff

        # Standard NEMA motor size selection
        standard_hp_ratings = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 75.0, 100.0]
        selected_motor_hp = next((hp for hp in standard_hp_ratings if hp >= bhp * 1.15), round(bhp * 1.25))

        return (
            f"=== FAN POWER & MOTOR SELECTION ===\n"
            f"Design Airflow:         {cfm:,.0f} CFM\n"
            f"Static Pressure (TSP):  {sp:.2f} in. w.g.\n"
            f"Fan / Motor Efficiency: {fan_eff*100:.0f}% / {motor_eff*100:.0f}%\n"
            f"-----------------------------------------\n"
            f"Air Horsepower (AHP):   {ahp:.2f} HP\n"
            f"Brake Horsepower (BHP): {bhp:.2f} BHP\n"
            f"Recommended NEMA Motor: {selected_motor_hp:.1f} HP (includes 15% safety factor)\n"
            f"Electrical Power Draw:  {motor_kw:.2f} kW"
        )
    except Exception as e:
        return f"Fan calculation error: {e}"


# ─────────────────────────────────────────────────────────────
# 6. PLUMBING WSFU & DFU SIZING (HUNTER'S CURVE / IPC)
# ─────────────────────────────────────────────────────────────

def calc_plumbing_water_demand(flush_valves_wsfu: float = 0.0, flush_tanks_wsfu: float = 0.0) -> str:
    """
    Convert Water Supply Fixture Units (WSFU) into peak GPM water demand using Hunter's Curve 
    (per IPC Appendix E / ASPE standards).
    """
    try:
        valves = float(flush_valves_wsfu)
        tanks = float(flush_tanks_wsfu)
        total_wsfu = valves + tanks

        if total_wsfu <= 0:
            return "Error: Total WSFU must be greater than zero."

        # Hunter's curve piecewise power polynomial approximation
        if valves > 0:
            # Curve 1: Flush Valve predominate
            if total_wsfu <= 10:
                gpm = 3.0 * total_wsfu
            elif total_wsfu <= 50:
                gpm = 15.0 + 0.85 * (total_wsfu - 10)
            elif total_wsfu <= 100:
                gpm = 49.0 + 0.50 * (total_wsfu - 50)
            elif total_wsfu <= 500:
                gpm = 74.0 + 0.28 * (total_wsfu - 100)
            else:
                gpm = 186.0 + 0.18 * (total_wsfu - 500)
            system_type = "Flushometer Valve System"
        else:
            # Curve 2: Flush Tank predominate
            if total_wsfu <= 10:
                gpm = 1.5 * total_wsfu
            elif total_wsfu <= 50:
                gpm = 15.0 + 0.45 * (total_wsfu - 10)
            elif total_wsfu <= 100:
                gpm = 33.0 + 0.25 * (total_wsfu - 50)
            elif total_wsfu <= 500:
                gpm = 45.0 + 0.18 * (total_wsfu - 100)
            else:
                gpm = 117.0 + 0.12 * (total_wsfu - 500)
            system_type = "Flush Tank System"

        # Minimum service main size based on 8 FPS velocity limit
        # d = sqrt(0.4085 * Q / V)
        min_pipe_dia = math.sqrt(0.4085 * gpm / 8.0)
        standard_sizes = [0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0]
        rec_pipe = next((s for s in standard_sizes if s >= min_pipe_dia), min_pipe_dia)

        return (
            f"=== DOMESTIC WATER SUPPLY DEMAND (HUNTER'S CURVE) ===\n"
            f"System Classification:  {system_type}\n"
            f"Flush Valve WSFU:       {valves:.1f}\n"
            f"Flush Tank WSFU:        {tanks:.1f}\n"
            f"Total WSFU Load:        {total_wsfu:.1f}\n"
            f"-----------------------------------------\n"
            f"ESTIMATED PEAK DEMAND:  {gpm:.1f} GPM\n"
            f"Recommended Main Size:  {rec_pipe:.2f}\" (velocity capped at 8 ft/sec)"
        )
    except Exception as e:
        return f"Plumbing water demand error: {e}"


def calc_plumbing_drainage_size(drainage_fixture_units_dfu: float, pipe_slope_inch_per_foot: float = 0.25) -> str:
    """
    Size horizontal building sanitary drainage pipe based on Drainage Fixture Units (DFU) 
    and fall per foot (slope) per International Plumbing Code (IPC Table 710.1(1)).
    """
    try:
        dfu = float(drainage_fixture_units_dfu)
        slope = float(pipe_slope_inch_per_foot)

        # IPC Table 710.1(1) max DFUs for building drain (horizontal)
        # Mapping: diameter_inches -> {slope_fraction: max_dfu}
        capacities = [
            (1.5, 0.25, 3),
            (2.0, 0.25, 21),
            (2.5, 0.25, 24),
            (3.0, 0.25, 42),
            (4.0, 0.25, 216),
            (5.0, 0.25, 480),
            (6.0, 0.25, 840),
            (8.0, 0.25, 2500),
            (10.0, 0.25, 4500),
            (12.0, 0.25, 7000)
        ]

        # Adjust for 1/8" slope if slope < 0.25
        size_found = None
        for diam, std_slope, cap in capacities:
            effective_cap = cap * (0.75 if slope < 0.20 else 1.0)
            if dfu <= effective_cap:
                size_found = (diam, effective_cap)
                break

        if not size_found:
            return f"Error: DFU of {dfu} exceeds maximum standard sizing table (7,000 DFU)."

        diam, max_cap = size_found
        return (
            f"=== SANITARY DRAINAGE SIZING (IPC TABLE 710.1) ===\n"
            f"Connected Fixture Load: {dfu:,.0f} DFU\n"
            f"Pipe Slope / Fall:      {slope:.3f}\" per foot\n"
            f"-----------------------------------------\n"
            f"REQUIRED DRAIN SIZE:    {diam:.1f}\" Diameter\n"
            f"Maximum Allowable DFU:  {max_cap:,.0f} DFU at this slope\n"
            f"Capacity Utilization:   {(dfu / max_cap) * 100.0:.1f} %"
        )
    except Exception as e:
        return f"Plumbing drainage sizing error: {e}"


# ─────────────────────────────────────────────────────────────
# 7. ELECTRICAL FEEDER SIZING & VOLTAGE DROP (NEC)
# ─────────────────────────────────────────────────────────────

def calc_electrical_feeder(load_kva: float, 
                           voltage: float = 480.0, 
                           phases: int = 3, 
                           power_factor: float = 0.85, 
                           distance_ft: float = 150.0, 
                           conductor_material: str = "copper", 
                           max_allowed_drop_pct: float = 3.0) -> str:
    """
    Size electrical feeder conductors, conduit, and calculate percent voltage drop 
    per National Electrical Code (NEC Table 310.16 and Chapter 9).
    """
    try:
        kva = float(load_kva)
        v = float(voltage)
        p = int(phases)
        pf = float(power_factor)
        l = float(distance_ft)
        mat = conductor_material.lower()
        max_vd = float(max_allowed_drop_pct)

        if kva <= 0 or v <= 0 or l <= 0:
            return "Error: Load (kVA), voltage, and distance must be positive."

        # Calculate Full Load Amperage (FLA)
        if p == 3:
            fla = (kva * 1000.0) / (math.sqrt(3) * v)
        else:
            fla = (kva * 1000.0) / v

        # NEC 125% continuous load factor
        design_amps = fla * 1.25

        # NEC Table 310.16 75°C Copper Ampacity & Circular Mils
        wire_table_cu = [
            ("#14 AWG", 20, 4110),
            ("#12 AWG", 25, 6530),
            ("#10 AWG", 35, 10380),
            ("#8 AWG", 50, 16510),
            ("#6 AWG", 65, 26240),
            ("#4 AWG", 85, 41740),
            ("#3 AWG", 100, 52620),
            ("#2 AWG", 115, 66360),
            ("#1 AWG", 130, 83690),
            ("1/0 AWG", 150, 105600),
            ("2/0 AWG", 175, 133100),
            ("3/0 AWG", 200, 167800),
            ("4/0 AWG", 230, 211600),
            ("250 kcmil", 255, 250000),
            ("300 kcmil", 285, 300000),
            ("350 kcmil", 310, 350000),
            ("400 kcmil", 335, 400000),
            ("500 kcmil", 380, 500000),
            ("600 kcmil", 420, 600000),
            ("750 kcmil", 475, 750000)
        ]

        k_factor = 12.9 if "cop" in mat else 21.2 # Resistivity constant: 12.9 for Cu, 21.2 for Al

        # Find smallest wire meeting ampacity
        selected_wire = None
        for name, ampacity, cm in wire_table_cu:
            if ampacity >= design_amps:
                selected_wire = (name, ampacity, cm)
                break

        if not selected_wire:
            selected_wire = wire_table_cu[-1]

        wire_name, wire_amp, wire_cm = selected_wire

        # Voltage Drop calculation:
        # 3-Phase: VD = (sqrt(3) * K * I * L) / CM
        # 1-Phase: VD = (2 * K * I * L) / CM
        multiplier = math.sqrt(3) if p == 3 else 2.0
        vd_volts = (multiplier * k_factor * fla * l) / wire_cm
        vd_pct = (vd_volts / v) * 100.0

        # Upsize if voltage drop exceeds threshold
        upsized_note = ""
        if vd_pct > max_vd:
            for name, ampacity, cm in wire_table_cu:
                test_vd = ((multiplier * k_factor * fla * l) / cm / v) * 100.0
                if test_vd <= max_vd:
                    upsized_note = f"\n[!] NOTE: Upsized wire to {name} ({ampacity}A) to limit voltage drop to {test_vd:.2f}% (<= {max_vd}%)."
                    wire_name, wire_amp, wire_cm = name, ampacity, cm
                    vd_pct = test_vd
                    vd_volts = test_vd * v / 100.0
                    break

        return (
            f"=== ELECTRICAL FEEDER & VOLTAGE DROP SIZING ===\n"
            f"Load:                 {kva:,.1f} kVA ({fla:.1f} FLA @ {v:.0f}V, {p}-Phase)\n"
            f"Design Current:       {design_amps:.1f} Amps (125% continuous duty per NEC)\n"
            f"Circuit Distance:     {l:,.0f} ft (Conductor: {mat.upper()})\n"
            f"-----------------------------------------\n"
            f"RECOMMENDED WIRE:     {wire_name} (Rated {wire_amp}A @ 75°C THHN/THWN-2)\n"
            f"VOLTAGE DROP:         {vd_volts:.2f} Volts ({vd_pct:.2f} %)\n"
            f"Compliance Status:    {'PASS (Within ' + str(max_vd) + '% limit)' if vd_pct <= max_vd else 'EXCEEDS LIMIT'}"
            f"{upsized_note}"
        )
    except Exception as e:
        return f"Electrical feeder calculation error: {e}"


# ─────────────────────────────────────────────────────────────
# 8. FIRE PROTECTION HYDRAULIC DEMAND (NFPA 13)
# ─────────────────────────────────────────────────────────────

def calc_fire_sprinkler_demand(hazard_class: str = "Ordinary Hazard Group 1", 
                               area_sqft: float = 1500.0, 
                               hose_stream_allowance_gpm: float = 250.0) -> str:
    """
    Calculate commercial fire sprinkler water demand (GPM) and hydraulic requirements 
    per NFPA 13 density/area curve.
    Hazard classes: Light Hazard, Ordinary Hazard Group 1, Ordinary Hazard Group 2, Extra Hazard Group 1.
    """
    try:
        area = float(area_sqft)
        hose = float(hose_stream_allowance_gpm)

        hazard_density_map = {
            "light hazard": (0.10, 1500.0, 100.0, 30),
            "ordinary hazard group 1": (0.15, 1500.0, 250.0, 60),
            "ordinary hazard group 2": (0.20, 1500.0, 250.0, 60),
            "extra hazard group 1": (0.30, 2500.0, 500.0, 90),
            "extra hazard group 2": (0.40, 2500.0, 500.0, 120),
        }

        hz_key = hazard_class.lower().strip()
        data = hazard_density_map.get(hz_key, (0.15, 1500.0, 250.0, 60))
        density, min_design_area, default_hose, duration = data

        design_area = max(area, min_design_area)
        sprinkler_flow = density * design_area
        total_flow = sprinkler_flow + hose

        # Water supply storage duration calculation (gallons required for dedicated tank)
        tank_storage_gallons = total_flow * duration

        return (
            f"=== FIRE SPRINKLER HYDRAULIC DEMAND (NFPA 13) ===\n"
            f"Occupancy Hazard:       {hazard_class.upper()}\n"
            f"Design Density:         {density:.2f} GPM / sq.ft\n"
            f"Design Hydraulic Area:  {design_area:,.0f} sq.ft\n"
            f"Duration Requirement:   {duration} minutes\n"
            f"-----------------------------------------\n"
            f"SPRINKLER SYSTEM FLOW:  {sprinkler_flow:,.0f} GPM\n"
            f"Hose Stream Allowance:  {hose:,.0f} GPM\n"
            f"TOTAL COMBINED DEMAND:  {total_flow:,.0f} GPM\n"
            f"-----------------------------------------\n"
            f"Dedicated Tank Volume:  {tank_storage_gallons:,.0f} gallons minimum storage"
        )
    except Exception as e:
        return f"Fire sprinkler calculation error: {e}"


# ─────────────────────────────────────────────────────────────
# REGISTER ALL TOOLS ON THE MCP SERVER
# ─────────────────────────────────────────────────────────────

server.add_tool(
    "calc_psychrometrics", 
    "Calculate complete ASHRAE psychrometric moist air properties (dew point, wet bulb, enthalpy, humidity ratio, vapor pressure).",
    {
        "type": "object", 
        "properties": {
            "dry_bulb_f": {"type": "number", "description": "Dry bulb temperature in degrees Fahrenheit"},
            "relative_humidity_pct": {"type": "number", "description": "Relative humidity percentage (0 to 100)"},
            "wet_bulb_f": {"type": "number", "description": "Wet bulb temperature in degrees Fahrenheit"},
            "dew_point_f": {"type": "number", "description": "Dew point temperature in degrees Fahrenheit"},
            "pressure_psi": {"type": "number", "description": "Atmospheric pressure in psi (default 14.696 for sea level)"}
        }, 
        "required": ["dry_bulb_f"]
    }, 
    calc_psychrometrics
)

server.add_tool(
    "calc_hvac_loads", 
    "Calculate HVAC sensible/latent cooling loads, required supply airflow (CFM), capacity in Tons/kW, and ASHRAE 62.1 outdoor air ventilation rates.",
    {
        "type": "object", 
        "properties": {
            "area_sqft": {"type": "number", "description": "Conditioned floor area in square feet"},
            "sensible_heat_gain_btuh": {"type": "number", "description": "Sensible heat gain in Btu/hr (optional, defaults to 30 Btu/hr/sqft)"},
            "latent_heat_gain_btuh": {"type": "number", "description": "Latent heat gain in Btu/hr (defaults to 0)"},
            "space_temp_f": {"type": "number", "description": "Design space temperature in deg F (default 75.0)"},
            "supply_temp_f": {"type": "number", "description": "Design supply air temperature in deg F (default 55.0)"},
            "occupancy_people": {"type": "integer", "description": "Number of occupants for ASHRAE 62.1 ventilation calculation"},
            "outdoor_cfm_per_person": {"type": "number", "description": "Ventilation CFM per person (default 20.0)"},
            "outdoor_cfm_per_sqft": {"type": "number", "description": "Ventilation CFM per square foot (default 0.06)"}
        }, 
        "required": ["area_sqft"]
    }, 
    calc_hvac_loads
)

server.add_tool(
    "calc_duct_sizing", 
    "Size HVAC ductwork using Equal Friction method. Returns diameter, velocity, velocity pressure, and equivalent rectangular dimensions via Huebscher formula.",
    {
        "type": "object", 
        "properties": {
            "airflow_cfm": {"type": "number", "description": "Total airflow volume in CFM"},
            "target_friction_loss": {"type": "number", "description": "Friction rate in in. w.g. per 100 ft (default 0.08)"},
            "max_velocity_fpm": {"type": "number", "description": "Maximum allowed air velocity in FPM (default 1200)"},
            "aspect_ratio_limit": {"type": "number", "description": "Maximum rectangular aspect ratio width:height (default 3.0)"}
        }, 
        "required": ["airflow_cfm"]
    }, 
    calc_duct_sizing
)

server.add_tool(
    "calc_pipe_friction", 
    "Calculate hydronic pipe friction head loss, velocity, equivalent fitting runs, and total pressure drop using Hazen-Williams.",
    {
        "type": "object", 
        "properties": {
            "flow_gpm": {"type": "number", "description": "Water flow rate in GPM"},
            "diameter_inches": {"type": "number", "description": "Inside pipe diameter in inches"},
            "length_ft": {"type": "number", "description": "Total pipe physical run in feet"},
            "pipe_material": {"type": "string", "description": "Pipe material: 'steel_sch40', 'copper_type_l', 'pvc_sch40', 'cast_iron'"},
            "fittings_count_elbows": {"type": "integer", "description": "Number of 90 degree elbows in the run"},
            "fittings_count_valves": {"type": "integer", "description": "Number of valves in the run"}
        }, 
        "required": ["flow_gpm", "diameter_inches", "length_ft"]
    }, 
    calc_pipe_friction
)

server.add_tool(
    "calc_fan_system_power", 
    "Calculate fan Air Horsepower (AHP), Brake Horsepower (BHP), and electrical motor kW demand given airflow and static pressure.",
    {
        "type": "object", 
        "properties": {
            "airflow_cfm": {"type": "number", "description": "Airflow in CFM"},
            "external_static_pressure_in_wg": {"type": "number", "description": "Total static pressure in inches water gauge"},
            "fan_efficiency": {"type": "number", "description": "Fan mechanical efficiency (default 0.65)"},
            "motor_efficiency": {"type": "number", "description": "Motor electrical efficiency (default 0.90)"}
        }, 
        "required": ["airflow_cfm", "external_static_pressure_in_wg"]
    }, 
    calc_fan_system_power
)

server.add_tool(
    "calc_plumbing_water_demand", 
    "Convert Water Supply Fixture Units (WSFU) into peak GPM water demand using Hunter's Curve and recommend main pipe diameter.",
    {
        "type": "object", 
        "properties": {
            "flush_valves_wsfu": {"type": "number", "description": "Total WSFU for flushometer valve fixtures"},
            "flush_tanks_wsfu": {"type": "number", "description": "Total WSFU for tank type fixtures"}
        }
    }, 
    calc_plumbing_water_demand
)

server.add_tool(
    "calc_plumbing_drainage_size", 
    "Size horizontal building sanitary drainage pipe based on Drainage Fixture Units (DFU) and slope per IPC Table 710.1.",
    {
        "type": "object", 
        "properties": {
            "drainage_fixture_units_dfu": {"type": "number", "description": "Total connected Drainage Fixture Units"},
            "pipe_slope_inch_per_foot": {"type": "number", "description": "Fall in inches per foot, e.g. 0.25 (1/4 in/ft)"}
        }, 
        "required": ["drainage_fixture_units_dfu"]
    }, 
    calc_plumbing_drainage_size
)

server.add_tool(
    "calc_electrical_feeder", 
    "Size electrical feeder conductors, ampacity, and calculate percent voltage drop per National Electrical Code (NEC).",
    {
        "type": "object", 
        "properties": {
            "load_kva": {"type": "number", "description": "Electrical demand in kVA"},
            "voltage": {"type": "number", "description": "Line-to-line voltage (e.g. 480, 208, 120, 240)"},
            "phases": {"type": "integer", "description": "Number of phases (3 or 1)"},
            "power_factor": {"type": "number", "description": "Load power factor (default 0.85)"},
            "distance_ft": {"type": "number", "description": "One-way circuit run distance in feet"},
            "conductor_material": {"type": "string", "description": "'copper' or 'aluminum'"},
            "max_allowed_drop_pct": {"type": "number", "description": "Maximum allowed voltage drop % (default 3.0)"}
        }, 
        "required": ["load_kva"]
    }, 
    calc_electrical_feeder
)

server.add_tool(
    "calc_fire_sprinkler_demand", 
    "Calculate fire sprinkler system flow demand (GPM) and tank storage requirements per NFPA 13 density/area curves.",
    {
        "type": "object", 
        "properties": {
            "hazard_class": {"type": "string", "description": "'Light Hazard', 'Ordinary Hazard Group 1', 'Ordinary Hazard Group 2', 'Extra Hazard Group 1'"},
            "area_sqft": {"type": "number", "description": "Design hydraulic area in sq ft (default 1500)"},
            "hose_stream_allowance_gpm": {"type": "number", "description": "Hose stream allowance in GPM (default 250)"}
        }
    }, 
    calc_fire_sprinkler_demand
)

if __name__ == "__main__":
    server.run()
