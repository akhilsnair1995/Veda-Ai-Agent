# mcp/servers/simulation_server.py
import sys
import math
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

server = MCPServer(name="simulation", version="1.0.0")

def calc_psychrometrics(dry_bulb_f: float, relative_humidity_pct: float) -> str:
    """Calculate basic psychrometric properties (Dew Point, Enthalpy) at sea level."""
    try:
        # Simplified equations for demonstration
        # Not for life-safety engineering without verification
        t_c = (dry_bulb_f - 32) * 5/9
        rh = relative_humidity_pct / 100.0
        
        # Magnus-Tetens approximation for Dew Point
        a = 17.27
        b = 237.7
        alpha = ((a * t_c) / (b + t_c)) + math.log(rh)
        dp_c = (b * alpha) / (a - alpha)
        dp_f = (dp_c * 9/5) + 32
        
        # Very rough enthalpy approximation (Btu/lb)
        h = 0.24 * dry_bulb_f + rh * 1061 # Simplified
        
        return (
            f"Psychrometric Analysis @ Sea Level:\n"
            f"Dry Bulb: {dry_bulb_f:.1f} °F\n"
            f"Relative Humidity: {relative_humidity_pct:.1f}%\n"
            f"Dew Point: {dp_f:.1f} °F\n"
            f"Approx Enthalpy: {h:.1f} Btu/lb dry air"
        )
    except Exception as e:
        return f"Calculation error: {e}"

def calc_pipe_friction(flow_gpm: float, diameter_inches: float, length_ft: float) -> str:
    """Calculate friction head loss in Schedule 40 Steel pipe using Hazen-Williams."""
    try:
        C = 120 # Hazen-Williams coefficient for standard steel
        
        # P = 4.52 * Q^1.85 / (C^1.85 * d^4.87) - pressure drop per foot
        q = flow_gpm
        d = diameter_inches
        
        if d <= 0 or q <= 0:
            return "Error: Flow and diameter must be greater than zero."
            
        pd_per_100ft = 0.2083 * (100 / C)**1.852 * (q**1.852 / d**4.8655) * 100
        total_pd = (pd_per_100ft / 100) * length_ft
        
        velocity = (0.4085 * q) / (d**2)
        
        return (
            f"Pipe Friction Analysis (Sch 40 Steel, C=120):\n"
            f"Flow: {flow_gpm} GPM\n"
            f"Diameter: {diameter_inches} inches\n"
            f"Velocity: {velocity:.2f} ft/s\n"
            f"Friction Loss: {pd_per_100ft:.2f} psi / 100 ft\n"
            f"Total Pressure Drop: {total_pd:.2f} psi over {length_ft} ft"
        )
    except Exception as e:
        return f"Calculation error: {e}"

server.add_tool("calc_psychrometrics", "Calculate dew point and enthalpy from dry bulb and RH",
    {
        "type": "object", 
        "properties": {
            "dry_bulb_f": {"type": "number"},
            "relative_humidity_pct": {"type": "number"}
        }, 
        "required": ["dry_bulb_f", "relative_humidity_pct"]
    }, calc_psychrometrics)

server.add_tool("calc_pipe_friction", "Calculate pressure drop in steel pipes",
    {
        "type": "object", 
        "properties": {
            "flow_gpm": {"type": "number"},
            "diameter_inches": {"type": "number"},
            "length_ft": {"type": "number"}
        }, 
        "required": ["flow_gpm", "diameter_inches", "length_ft"]
    }, calc_pipe_friction)

if __name__ == "__main__":
    server.run()
