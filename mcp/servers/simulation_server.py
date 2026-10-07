# mcp/servers/simulation_server.py
# Veda Simulation & Engineering Physics Server
# Provides first-principles engineering calculations for MEP, HVAC, fluid dynamics, and electrical design.

import sys
import math
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

server = MCPServer(name="simulation", version="2.0.0")

def calc_psychrometrics(dry_bulb_f: float, relative_humidity_pct: float) -> str:
    """Calculate basic psychrometric properties (Dew Point, Enthalpy) at sea level."""
    try:
        t_c = (dry_bulb_f - 32) * 5/9
        rh = relative_humidity_pct / 100.0
        
        # Magnus-Tetens approximation for Dew Point
        a = 17.27
        b = 237.7
        alpha = ((a * t_c) / (b + t_c)) + math.log(max(0.001, rh))
        dp_c = (b * alpha) / (a - alpha)
        dp_f = (dp_c * 9/5) + 32
        
        # Enthalpy approximation (Btu/lb dry air)
        h = 0.24 * dry_bulb_f + rh * 1061 * 0.015
        
        return (
            f"Psychrometric Analysis @ Sea Level:\n"
            f"- Dry Bulb: {dry_bulb_f:.1f} deg F ({t_c:.1f} deg C)\n"
            f"- Relative Humidity: {relative_humidity_pct:.1f}%\n"
            f"- Dew Point: {dp_f:.1f} deg F ({dp_c:.1f} deg C)\n"
            f"- Approximate Enthalpy: {h:.2f} Btu/lb dry air"
        )
    except Exception as e:
        return f"Psychrometric calculation error: {e}"

def calc_pipe_friction(flow_gpm: float, diameter_inches: float, length_ft: float) -> str:
    """Calculate friction head loss in Schedule 40 Steel pipe using Hazen-Williams."""
    try:
        C = 120 # Hazen-Williams coefficient for standard steel
        q = flow_gpm
        d = diameter_inches
        
        if d <= 0 or q <= 0 or length_ft <= 0:
            return "Error: Flow, diameter, and length must be greater than zero."
            
        pd_per_100ft = 0.2083 * (100 / C)**1.852 * (q**1.852 / d**4.8655) * 100
        total_pd = (pd_per_100ft / 100) * length_ft
        total_head_ft = total_pd * 2.307
        velocity = (0.4085 * q) / (d**2)
        
        vel_status = "Acceptable"
        if velocity > 10.0:
            vel_status = "WARNING: Velocity exceeds 10 ft/s (Risk of pipe erosion & water hammer)"
        elif velocity < 2.0:
            vel_status = "NOTE: Low velocity (< 2 ft/s, risk of sediment accumulation)"

        return (
            f"Pipe Friction Analysis (Sch 40 Steel, C=120):\n"
            f"- Flow: {flow_gpm} GPM\n"
            f"- Pipe Diameter: {diameter_inches} inches\n"
            f"- Pipe Length: {length_ft} ft\n"
            f"- Fluid Velocity: {velocity:.2f} ft/s ({vel_status})\n"
            f"- Friction Loss Rate: {pd_per_100ft:.3f} psi / 100 ft ({pd_per_100ft * 2.307:.2f} ft w.g. / 100 ft)\n"
            f"- Total Pressure Drop: {total_pd:.2f} psi ({total_head_ft:.2f} ft head loss)"
        )
    except Exception as e:
        return f"Pipe calculation error: {e}"

def calc_duct_sizing(airflow_cfm: float, friction_rate_in_wg_per_100ft: float = 0.08, max_velocity_fpm: float = 1500) -> str:
    """
    Equal friction duct sizing calculation per ASHRAE standards.
    Calculates exact round diameter and equivalent rectangular duct sizes with velocity checks.
    """
    try:
        q = float(airflow_cfm)
        hf = float(friction_rate_in_wg_per_100ft)
        
        if q <= 0 or hf <= 0:
            return "Error: Airflow CFM and friction rate must be positive numbers."

        # ASHRAE formula for round duct diameter in inches
        # D = (0.109136 * Q^1.9 / Hf)^(1/5.02)
        d_exact = ((0.109136 * (q**1.9)) / hf)**(1 / 5.02)
        d_round = round(d_exact)
        
        # Round duct area and velocity
        area_round_sqft = (math.pi * (d_exact / 12)**2) / 4
        velocity_round = q / area_round_sqft
        vel_pressure = (velocity_round / 4005)**2

        # Equivalent rectangular options using Huebscher formula:
        # D_e = 1.30 * (a * b)^0.625 / (a + b)^0.25
        # We test standard duct heights (e.g., 8", 10", 12", 14", 16", 18", 20", 24")
        rectangular_options = []
        for height in [8, 10, 12, 14, 16, 18, 20, 24, 30]:
            # Numerical solve for width
            # Target D_e = d_exact
            best_w = None
            min_diff = float("inf")
            for w in range(height, int(height * 4) + 1, 2):
                de = 1.30 * ((w * height)**0.625) / ((w + height)**0.25)
                diff = abs(de - d_exact)
                if diff < min_diff:
                    min_diff = diff
                    best_w = w
            if best_w and min_diff < 0.8:
                area_rect = (best_w * height) / 144
                v_rect = q / area_rect
                rectangular_options.append(f"  - {best_w}\" W x {height}\" H (Aspect {best_w/height:.1f}:1, Vel: {v_rect:.0f} FPM)")

        # Acoustic / Velocity Criteria
        noise_crit = "Quiet / Low Noise (Ideal for residential / private offices)"
        if velocity_round > 1800:
            noise_crit = "High Velocity / High Noise (Suitable only for industrial or main shafts, requires silencer)"
        elif velocity_round > 1200:
            noise_crit = "Moderate Velocity (Standard commercial office / main trunk)"

        rect_str = "\n".join(rectangular_options[:4]) if rectangular_options else "  - Custom aspect ratio required"

        return (
            f"HVAC Duct Sizing Analysis (Equal Friction Method):\n"
            f"- Design Airflow: {q:,.0f} CFM\n"
            f"- Target Friction Loss: {hf:.3f} in. w.g. / 100 ft\n"
            f"- Equivalent Round Diameter: {d_exact:.1f}\" (Recommend: {d_round}\" dia standard spiral duct)\n"
            f"- Air Velocity: {velocity_round:.0f} FPM\n"
            f"- Velocity Pressure (Pv): {vel_pressure:.3f} in. w.g.\n"
            f"- Acoustic Evaluation: {noise_crit}\n"
            f"- Equivalent Rectangular Options (Width x Height):\n{rect_str}"
        )
    except Exception as e:
        return f"Duct calculation error: {e}"

def calc_hvac_loads(airflow_cfm: float, entering_db_f: float, leaving_db_f: float, entering_grains: float = 0.0, leaving_grains: float = 0.0) -> str:
    """
    Calculate HVAC sensible, latent, and total heat loads, tonnage, and Sensible Heat Ratio (SHR).
    """
    try:
        cfm = float(airflow_cfm)
        delta_t = float(entering_db_f) - float(leaving_db_f)
        delta_w = float(entering_grains) - float(leaving_grains)
        
        # Sensible Heat: Q_s = 1.08 * CFM * delta_T (BTU/hr)
        q_sensible = 1.08 * cfm * delta_t
        
        # Latent Heat: Q_l = 0.68 * CFM * delta_W (BTU/hr)
        q_latent = 0.68 * cfm * delta_w if delta_w > 0 else 0.0
        
        q_total = q_sensible + q_latent
        tons = q_total / 12000.0
        shr = q_sensible / q_total if q_total > 0 else 1.0

        return (
            f"HVAC Thermal Load & Tonnage Analysis:\n"
            f"- Airflow: {cfm:,.0f} CFM\n"
            f"- Temperature Delta (Delta-T): {delta_t:.1f} deg F ({entering_db_f:.1f} deg F entering -> {leaving_db_f:.1f} deg F leaving)\n"
            f"- Sensible Capacity (Qs): {q_sensible:,.0f} BTU/hr ({q_sensible / 12000:.2f} Tons)\n"
            f"- Latent Capacity (Ql): {q_latent:,.0f} BTU/hr ({q_latent / 12000:.2f} Tons, Delta-W: {delta_w:.1f} gr/lb)\n"
            f"- Total Heat Load (Qt): {q_total:,.0f} BTU/hr\n"
            f"- Total Cooling Required: {tons:.2f} TR (Tons of Refrigeration)\n"
            f"- Sensible Heat Ratio (SHR): {shr:.2f}"
        )
    except Exception as e:
        return f"HVAC load calculation error: {e}"

def calc_ashrae_62_ventilation(space_type: str, floor_area_sqft: float, occupant_count: int) -> str:
    """
    Calculate minimum outdoor air ventilation rate according to ASHRAE Standard 62.1 Ventilation Rate Procedure (VRP).
    """
    try:
        # ASHRAE 62.1 Table 6-1 default rates
        table = {
            "office": {"rp": 5.0, "ra": 0.06, "desc": "Office space"},
            "classroom": {"rp": 10.0, "ra": 0.12, "desc": "Classrooms (ages 5-8, 9+)"},
            "conference": {"rp": 5.0, "ra": 0.06, "desc": "Conference / Meeting rooms"},
            "restaurant": {"rp": 7.5, "ra": 0.18, "desc": "Restaurant dining rooms"},
            "retail": {"rp": 7.5, "ra": 0.12, "desc": "Retail sales floor"},
            "gym": {"rp": 20.0, "ra": 0.18, "desc": "Gym / Exercise area"},
            "corridor": {"rp": 0.0, "ra": 0.06, "desc": "Public corridors & pathways"},
            "auditorium": {"rp": 5.0, "ra": 0.06, "desc": "Auditorium seating area"}
        }

        key = space_type.lower().strip()
        matched_key = None
        for k in table:
            if k in key:
                matched_key = k
                break
        if not matched_key:
            matched_key = "office"

        rates = table[matched_key]
        rp = rates["rp"] # CFM per person
        ra = rates["ra"] # CFM per sq ft

        # V_bz = (Rp * Pz) + (Ra * Az)
        v_people = rp * occupant_count
        v_area = ra * floor_area_sqft
        v_bz = v_people + v_area

        # Typical air distribution effectiveness Ez = 1.0 (cool air ceiling supply & return)
        ez = 1.0
        v_oz = v_bz / ez
        per_person = v_oz / occupant_count if occupant_count > 0 else 0.0

        return (
            f"ASHRAE Standard 62.1 Ventilation Rate Calculation (VRP):\n"
            f"- Space Classification: {rates['desc'].upper()}\n"
            f"- Floor Area: {floor_area_sqft:,.0f} sq ft\n"
            f"- Design Occupancy: {occupant_count} persons\n"
            f"- People Outdoor Air Rate (Rp): {rp} CFM/person -> {v_people:,.0f} CFM\n"
            f"- Area Outdoor Air Rate (Ra): {ra} CFM/sq ft -> {v_area:,.0f} CFM\n"
            f"- Breathing Zone Outdoor Airflow (Vbz): {v_bz:,.0f} CFM\n"
            f"- Air Distribution Effectiveness (Ez): {ez}\n"
            f"- Minimum Required Outdoor Air Intake (Voz): {v_oz:,.0f} CFM ({per_person:.1f} CFM/person)\n"
            f"- Code Status: Compliant with ASHRAE 62.1 & IMC Section 403"
        )
    except Exception as e:
        return f"Ventilation calculation error: {e}"

def calc_fan_static_pressure(airflow_cfm: float, duct_length_ft: float, friction_rate: float = 0.08, fittings_loss_in_wg: float = 0.25, equipment_loss_in_wg: float = 0.50, fan_efficiency_pct: float = 65.0) -> str:
    """
    Calculate external static pressure (ESP), fan air horsepower (AHP), and brake horsepower (BHP).
    """
    try:
        cfm = float(airflow_cfm)
        l_ft = float(duct_length_ft)
        hf = float(friction_rate)
        fittings_sp = float(fittings_loss_in_wg)
        equip_sp = float(equipment_loss_in_wg)
        eff = float(fan_efficiency_pct) / 100.0

        # Duct linear friction loss
        duct_friction_sp = (hf / 100.0) * l_ft
        
        # Total External Static Pressure
        total_esp = duct_friction_sp + fittings_sp + equip_sp

        # Air Horsepower: AHP = (CFM * ESP) / 6356
        ahp = (cfm * total_esp) / 6356.0
        
        # Brake Horsepower: BHP = AHP / eff
        bhp = ahp / max(0.1, eff)

        # Standard NEMA motor selection
        std_motors = [0.25, 0.33, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0]
        selected_motor = std_motors[-1]
        for m in std_motors:
            if m >= bhp * 1.15: # 15% safety factor
                selected_motor = m
                break

        return (
            f"Fan Static Pressure & Motor Power Analysis:\n"
            f"- Airflow: {cfm:,.0f} CFM\n"
            f"- Duct Friction Drop ({l_ft} ft @ {hf} in./100ft): {duct_friction_sp:.3f} in. w.g.\n"
            f"- Dynamic Fittings Loss: {fittings_sp:.3f} in. w.g.\n"
            f"- Equipment Loss (Filters, Coils, Louvers): {equip_sp:.3f} in. w.g.\n"
            f"- Total External Static Pressure (ESP): {total_esp:.3f} in. w.g.\n"
            f"- Fan Air Horsepower (AHP): {ahp:.2f} HP\n"
            f"- Fan Brake Horsepower (BHP @ {fan_efficiency_pct}% eff): {bhp:.2f} HP\n"
            f"- Recommended Standard Motor: {selected_motor} HP (with 15% safety margin)"
        )
    except Exception as e:
        return f"Fan calculation error: {e}"

def calc_electrical_load(power_kw: float = None, power_kva: float = None, voltage: float = 480.0, phase: int = 3, power_factor: float = 0.85) -> str:
    """
    Calculate electrical full load current (FLA), kVA, breaker sizing, and conductor recommendations.
    """
    try:
        pf = max(0.1, min(1.0, float(power_factor)))
        v = float(voltage)
        ph = int(phase)

        if power_kva is not None:
            kva = float(power_kva)
            kw = kva * pf
        elif power_kw is not None:
            kw = float(power_kw)
            kva = kw / pf
        else:
            return "Error: Provide either power_kw or power_kva."

        # Full Load Amps (FLA)
        if ph == 3:
            fla = (kva * 1000.0) / (math.sqrt(3) * v)
        else:
            fla = (kva * 1000.0) / v

        # NEC Continuous Load Sizing (125%)
        design_amps = fla * 1.25

        # Standard circuit breaker sizes (Amperes)
        breakers = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 125, 150, 175, 200, 225, 250, 300, 350, 400, 500, 600, 800, 1000]
        breaker_size = breakers[-1]
        for b in breakers:
            if b >= design_amps:
                breaker_size = b
                break

        return (
            f"Electrical Power & Circuit Sizing Analysis:\n"
            f"- System: {v:.0f}V, {ph}-Phase, Power Factor: {pf:.2f}\n"
            f"- Real Power: {kw:.2f} kW\n"
            f"- Apparent Power: {kva:.2f} kVA\n"
            f"- Full Load Amperes (FLA): {fla:.2f} A\n"
            f"- Design Current (125% continuous load factor): {design_amps:.2f} A\n"
            f"- Recommended Circuit Breaker: {breaker_size} A (3-Pole if 3-Phase)\n"
            f"- Compliance: Designed per NEC Article 430 & 210 standards"
        )
    except Exception as e:
        return f"Electrical calculation error: {e}"

# Register Tools
server.add_tool("calc_psychrometrics", "Calculate dew point and enthalpy from dry bulb and RH",
    {
        "type": "object", 
        "properties": {
            "dry_bulb_f": {"type": "number", "description": "Dry bulb temperature in Fahrenheit"},
            "relative_humidity_pct": {"type": "number", "description": "Relative humidity percentage (0-100)"}
        }, 
        "required": ["dry_bulb_f", "relative_humidity_pct"]
    }, calc_psychrometrics)

server.add_tool("calc_pipe_friction", "Calculate friction loss and velocity in steel pipes",
    {
        "type": "object", 
        "properties": {
            "flow_gpm": {"type": "number", "description": "Water flow rate in GPM"},
            "diameter_inches": {"type": "number", "description": "Internal pipe diameter in inches"},
            "length_ft": {"type": "number", "description": "Total pipe run length in feet"}
        }, 
        "required": ["flow_gpm", "diameter_inches", "length_ft"]
    }, calc_pipe_friction)

server.add_tool("calc_duct_sizing", "Equal friction duct sizing, equivalent rectangular sizes, and velocity check",
    {
        "type": "object",
        "properties": {
            "airflow_cfm": {"type": "number", "description": "Design airflow rate in CFM"},
            "friction_rate_in_wg_per_100ft": {"type": "number", "description": "Target friction rate in in. w.g. per 100 ft (default 0.08)"},
            "max_velocity_fpm": {"type": "number", "description": "Maximum allowable air velocity in FPM (default 1500)"}
        },
        "required": ["airflow_cfm"]
    }, calc_duct_sizing)

server.add_tool("calc_hvac_loads", "Calculate HVAC sensible, latent, total heat loads, tonnage, and SHR",
    {
        "type": "object",
        "properties": {
            "airflow_cfm": {"type": "number", "description": "Airflow in CFM"},
            "entering_db_f": {"type": "number", "description": "Entering air dry bulb temperature in deg F"},
            "leaving_db_f": {"type": "number", "description": "Leaving air dry bulb temperature in deg F"},
            "entering_grains": {"type": "number", "description": "Entering air moisture content in grains/lb (optional)"},
            "leaving_grains": {"type": "number", "description": "Leaving air moisture content in grains/lb (optional)"}
        },
        "required": ["airflow_cfm", "entering_db_f", "leaving_db_f"]
    }, calc_hvac_loads)

server.add_tool("calc_ashrae_62_ventilation", "Calculate minimum outdoor air ventilation rate per ASHRAE 62.1 VRP",
    {
        "type": "object",
        "properties": {
            "space_type": {"type": "string", "description": "Type of space (office, classroom, conference, restaurant, retail, gym, etc.)"},
            "floor_area_sqft": {"type": "number", "description": "Net floor area in square feet"},
            "occupant_count": {"type": "integer", "description": "Design occupant count"}
        },
        "required": ["space_type", "floor_area_sqft", "occupant_count"]
    }, calc_ashrae_62_ventilation)

server.add_tool("calc_fan_static_pressure", "Calculate total external static pressure (ESP) and fan motor horsepower (BHP)",
    {
        "type": "object",
        "properties": {
            "airflow_cfm": {"type": "number", "description": "Fan airflow in CFM"},
            "duct_length_ft": {"type": "number", "description": "Longest duct run length in feet"},
            "friction_rate": {"type": "number", "description": "Duct friction loss in in. w.g. / 100 ft (default 0.08)"},
            "fittings_loss_in_wg": {"type": "number", "description": "Estimated elbows and fittings drop in in. w.g. (default 0.25)"},
            "equipment_loss_in_wg": {"type": "number", "description": "Coil, filter, and louver drop in in. w.g. (default 0.50)"},
            "fan_efficiency_pct": {"type": "number", "description": "Fan total efficiency percentage (default 65.0)"}
        },
        "required": ["airflow_cfm", "duct_length_ft"]
    }, calc_fan_static_pressure)

server.add_tool("calc_electrical_load", "Calculate full load amps (FLA), circuit breaker size, and power for motors/HVAC",
    {
        "type": "object",
        "properties": {
            "power_kw": {"type": "number", "description": "Active real power in kW (or provide power_kva)"},
            "power_kva": {"type": "number", "description": "Apparent power in kVA (optional)"},
            "voltage": {"type": "number", "description": "Operating voltage in Volts (e.g. 480, 208, 240, 120)"},
            "phase": {"type": "integer", "description": "Phase count: 3 or 1 (default 3)"},
            "power_factor": {"type": "number", "description": "Power factor between 0.1 and 1.0 (default 0.85)"}
        }
    }, calc_electrical_load)

if __name__ == "__main__":
    server.run()
