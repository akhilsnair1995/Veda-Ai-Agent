# mcp/servers/cad_server.py
# CAD / BIM Engineering Drafting & Analysis Server for Veda
# Supports DXF generation, parsing, layer extraction, and high-fidelity rendering using ezdxf & matplotlib

import os
import sys
import json
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

import ezdxf
from ezdxf import colors
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

server = MCPServer(name="cad", version="1.0.0")
WORKSPACE_FILE = BASE_DIR / "config" / "current_workspace.txt"

def _get_workspace() -> Path:
    if WORKSPACE_FILE.exists():
        try:
            ws_path = WORKSPACE_FILE.read_text(encoding="utf-8").strip()
            if ws_path and Path(ws_path).is_dir():
                return Path(ws_path).resolve()
        except Exception:
            pass
    ws = (BASE_DIR / "workspace").resolve()
    ws.mkdir(parents=True, exist_ok=True)
    return ws

def _resolve_path(filepath: str) -> Path:
    p = Path(filepath).expanduser()
    if not p.is_absolute():
        p = (_get_workspace() / p).resolve()
    return p

# ─────────────────────────────────────────────────────────────
# 1. GENERATE HVAC DUCTWORK CAD DXF LAYOUT
# ─────────────────────────────────────────────────────────────

def generate_dxf_hvac_layout(output_filename: str = "hvac_duct_layout.dxf", 
                             main_duct_cfm: float = 3000.0, 
                             length_feet: float = 40.0,
                             branch_count: int = 4) -> str:
    """
    Generate an industry-standard 2D HVAC CAD layout in DXF format.
    Includes main supply duct, branch takeoffs, diffusers, equipment AHU block, and annotation callouts
    following AIA CAD Layer Guidelines (M-DUCT-SUPP, M-DIFF, M-EQUP, M-TEXT).
    """
    try:
        out_path = _resolve_path(output_filename)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        # Setup standard AIA MEP layers
        doc.layers.add('M-DUCT-SUPP', color=colors.CYAN)
        doc.layers.add('M-DIFF', color=colors.GREEN)
        doc.layers.add('M-EQUP', color=colors.RED)
        doc.layers.add('M-TEXT', color=colors.WHITE)

        # Draw Air Handling Unit (AHU) Block
        # AHU at origin (0, -3) to (8, 3) in feet (1 unit = 1 foot)
        msp.add_lwpolyline([(0, -3), (8, -3), (8, 3), (0, 3), (0, -3)], dxfattribs={'layer': 'M-EQUP'})
        msp.add_text("AHU-01", height=0.8, dxfattribs={'layer': 'M-TEXT'}).set_placement((1.5, -0.4))
        msp.add_text(f"{main_duct_cfm:,.0f} CFM", height=0.5, dxfattribs={'layer': 'M-TEXT'}).set_placement((1.5, -1.2))

        # Size main duct (width in inches ~ sqrt(CFM), converted to feet)
        duct_w_ft = max(1.5, min(3.5, (main_duct_cfm / 1000.0) * 0.8))
        half_w = duct_w_ft / 2.0

        # Main Supply Duct Run
        start_x = 8.0
        end_x = start_x + float(length_feet)
        msp.add_line((start_x, half_w), (end_x, half_w), dxfattribs={'layer': 'M-DUCT-SUPP'})
        msp.add_line((start_x, -half_w), (end_x, -half_w), dxfattribs={'layer': 'M-DUCT-SUPP'})
        msp.add_line((end_x, half_w), (end_x, -half_w), dxfattribs={'layer': 'M-DUCT-SUPP'}) # Cap

        # Main duct label
        msp.add_text(f"SUPPLY AIR MAIN: {round(duct_w_ft*12)}\"x16\" @ {main_duct_cfm:,.0f} CFM", 
                     height=0.6, dxfattribs={'layer': 'M-TEXT'}).set_placement((start_x + 2.0, half_w + 0.6))

        # Branch takeoffs and diffusers
        branches = max(1, int(branch_count))
        spacing = float(length_feet) / (branches + 1)
        branch_cfm = main_duct_cfm / (branches * 2)

        for i in range(1, branches + 1):
            bx = start_x + (i * spacing)
            # North branch (+y)
            msp.add_line((bx, half_w), (bx, half_w + 6.0), dxfattribs={'layer': 'M-DUCT-SUPP'})
            # North diffuser (2x2 ft box)
            d_x, d_y = bx - 1.0, half_w + 6.0
            msp.add_lwpolyline([(d_x, d_y), (d_x + 2.0, d_y), (d_x + 2.0, d_y + 2.0), (d_x, d_y + 2.0), (d_x, d_y)], dxfattribs={'layer': 'M-DIFF'})
            msp.add_line((d_x, d_y), (d_x + 2.0, d_y + 2.0), dxfattribs={'layer': 'M-DIFF'})
            msp.add_line((d_x + 2.0, d_y), (d_x, d_y + 2.0), dxfattribs={'layer': 'M-DIFF'})
            msp.add_text(f"{branch_cfm:.0f} CFM", height=0.4, dxfattribs={'layer': 'M-TEXT'}).set_placement((d_x, d_y + 2.3))

            # South branch (-y)
            msp.add_line((bx, -half_w), (bx, -half_w - 6.0), dxfattribs={'layer': 'M-DUCT-SUPP'})
            # South diffuser
            sd_x, sd_y = bx - 1.0, -half_w - 8.0
            msp.add_lwpolyline([(sd_x, sd_y), (sd_x + 2.0, sd_y), (sd_x + 2.0, sd_y + 2.0), (sd_x, sd_y), (sd_x, sd_y)], dxfattribs={'layer': 'M-DIFF'})
            msp.add_line((sd_x, sd_y), (sd_x + 2.0, sd_y + 2.0), dxfattribs={'layer': 'M-DIFF'})
            msp.add_line((sd_x + 2.0, sd_y), (sd_x, sd_y + 2.0), dxfattribs={'layer': 'M-DIFF'})
            msp.add_text(f"{branch_cfm:.0f} CFM", height=0.4, dxfattribs={'layer': 'M-TEXT'}).set_placement((sd_x, sd_y - 0.7))

        doc.saveas(str(out_path))

        # Also render a PNG preview automatically
        png_path = out_path.with_suffix('.png')
        _render_dxf_geometry(doc, png_path, title=f"HVAC Ductwork Layout ({main_duct_cfm:,.0f} CFM)")

        return (
            f"SUCCESS: Generated HVAC CAD DXF layout!\n"
            f"File Path:    {out_path}\n"
            f"Preview Image: {png_path}\n"
            f"AIA Layers:   M-DUCT-SUPP, M-DIFF, M-EQUP, M-TEXT\n"
            f"Components:   AHU-01, {main_duct_cfm:,.0f} CFM main, {branches * 2} ceiling diffusers."
        )
    except Exception as e:
        return f"Error generating HVAC DXF layout: {e}"

# ─────────────────────────────────────────────────────────────
# 2. GENERATE HYDRONIC PIPING CAD DXF LAYOUT
# ─────────────────────────────────────────────────────────────

def generate_dxf_piping_layout(output_filename: str = "chilled_water_piping.dxf", 
                               chiller_tons: float = 100.0, 
                               flow_gpm: float = 240.0) -> str:
    """
    Generate an industry-standard Chilled Water (CHW) hydronic piping CAD layout in DXF format.
    Includes Chiller package, Primary/Secondary pumps, Supply/Return headers, and air handler coils.
    """
    try:
        out_path = _resolve_path(output_filename)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        doc.layers.add('M-PIPE-CHWS', color=colors.CYAN) # Supply (44°F)
        doc.layers.add('M-PIPE-CHWR', color=colors.BLUE) # Return (54°F)
        doc.layers.add('M-EQUP', color=colors.MAGENTA)
        doc.layers.add('M-VALV', color=colors.YELLOW)
        doc.layers.add('M-TEXT', color=colors.WHITE)

        # Chiller block (CH-1)
        msp.add_lwpolyline([(0, 0), (12, 0), (12, 6), (0, 6), (0, 0)], dxfattribs={'layer': 'M-EQUP'})
        msp.add_text("CHILLER CH-01", height=0.7, dxfattribs={'layer': 'M-TEXT'}).set_placement((2.0, 3.5))
        msp.add_text(f"{chiller_tons:.0f} TONS / {flow_gpm:.0f} GPM", height=0.5, dxfattribs={'layer': 'M-TEXT'}).set_placement((2.0, 2.0))

        # Primary Chilled Water Pump (P-1) Circle
        msp.add_circle((16, 3), radius=1.5, dxfattribs={'layer': 'M-EQUP'})
        msp.add_text("P-1", height=0.6, dxfattribs={'layer': 'M-TEXT'}).set_placement((15.3, 2.7))

        # CHW Supply (CHWS) Line - Leaves Chiller at (12, 5) -> through pump -> to header
        msp.add_line((12, 5), (14.5, 5), dxfattribs={'layer': 'M-PIPE-CHWS'})
        msp.add_line((14.5, 5), (14.5, 3), dxfattribs={'layer': 'M-PIPE-CHWS'})
        msp.add_line((17.5, 3), (24.0, 3), dxfattribs={'layer': 'M-PIPE-CHWS'})
        msp.add_line((24.0, 3), (24.0, 10), dxfattribs={'layer': 'M-PIPE-CHWS'})
        msp.add_line((24.0, 10), (45.0, 10), dxfattribs={'layer': 'M-PIPE-CHWS'}) # Supply Header

        # CHW Return (CHWR) Line - Returns to Chiller at (12, 1)
        msp.add_line((45.0, 14), (20.0, 14), dxfattribs={'layer': 'M-PIPE-CHWR'})
        msp.add_line((20.0, 14), (20.0, 1), dxfattribs={'layer': 'M-PIPE-CHWR'})
        msp.add_line((20.0, 1), (12.0, 1), dxfattribs={'layer': 'M-PIPE-CHWR'})

        # AHU Coils connected across headers
        for cx in [28.0, 36.0, 42.0]:
            # Supply takeoff down to coil
            msp.add_line((cx, 10), (cx, 11), dxfattribs={'layer': 'M-PIPE-CHWS'})
            # Coil representation
            msp.add_lwpolyline([(cx - 1, 11), (cx + 1, 11), (cx + 1, 13), (cx - 1, 13), (cx - 1, 11)], dxfattribs={'layer': 'M-EQUP'})
            msp.add_text("COIL", height=0.3, dxfattribs={'layer': 'M-TEXT'}).set_placement((cx - 0.7, 11.8))
            # Return takeoff up to return header
            msp.add_line((cx, 13), (cx, 14), dxfattribs={'layer': 'M-PIPE-CHWR'})

        # Text labels
        msp.add_text("CHW SUPPLY HEADER (44°F)", height=0.5, dxfattribs={'layer': 'M-TEXT'}).set_placement((25.0, 9.2))
        msp.add_text("CHW RETURN HEADER (54°F)", height=0.5, dxfattribs={'layer': 'M-TEXT'}).set_placement((25.0, 14.5))

        doc.saveas(str(out_path))

        png_path = out_path.with_suffix('.png')
        _render_dxf_geometry(doc, png_path, title=f"Chilled Water Piping Schematic ({chiller_tons:.0f} Tons)")

        return (
            f"SUCCESS: Generated Chilled Water Piping CAD DXF layout!\n"
            f"File Path:    {out_path}\n"
            f"Preview Image: {png_path}\n"
            f"AIA Layers:   M-PIPE-CHWS, M-PIPE-CHWR, M-EQUP, M-VALV, M-TEXT"
        )
    except Exception as e:
        return f"Error generating piping DXF layout: {e}"

# ─────────────────────────────────────────────────────────────
# 3. PARSE EXISTING DXF DRAWINGS
# ─────────────────────────────────────────────────────────────

def parse_dxf_drawing(dxf_path: str) -> str:
    """
    Parse an existing CAD DXF file, extracting layer structure, text annotations, 
    block inserts, entity totals, and overall drawing bounding box.
    """
    try:
        p = _resolve_path(dxf_path)
        if not p.exists() or not p.is_file():
            return f"Error: CAD DXF file not found at {dxf_path}"

        doc = ezdxf.readfile(str(p))
        msp = doc.modelspace()

        layers = [layer.dxf.name for layer in doc.layers]
        blocks = [block.name for block in doc.blocks if not block.name.startswith('*')]

        texts = []
        entity_counts = {}

        for e in msp:
            dxftype = e.dxftype()
            entity_counts[dxftype] = entity_counts.get(dxftype, 0) + 1

            if dxftype in ('TEXT', 'MTEXT'):
                try:
                    txt_content = e.dxf.text if dxftype == 'TEXT' else e.text
                    if txt_content and txt_content.strip():
                        texts.append(txt_content.strip())
                except Exception:
                    pass

        # Summary output
        text_samples = "\n".join([f"  - \"{t}\"" for t in texts[:15]])
        entity_summary = "\n".join([f"  - {k}: {v}" for k, v in entity_counts.items()])

        return (
            f"=== CAD DXF DRAWING ANALYSIS: {p.name} ===\n"
            f"DXF Version:   {doc.dxfversion}\n"
            f"Total Layers:  {len(layers)} ({', '.join(layers[:12])}{'...' if len(layers) > 12 else ''})\n"
            f"Custom Blocks: {len(blocks)} ({', '.join(blocks[:8]) if blocks else 'None'})\n"
            f"-----------------------------------------\n"
            f"ENTITY BREAKDOWN:\n{entity_summary}\n"
            f"-----------------------------------------\n"
            f"ANNOTATION TEXT DETECTED ({len(texts)} total):\n{text_samples if text_samples else '  None'}"
        )
    except Exception as e:
        return f"Error parsing DXF drawing: {e}"

# ─────────────────────────────────────────────────────────────
# 4. RENDER DXF DRAWING TO HIGH-RES PNG PREVIEW
# ─────────────────────────────────────────────────────────────

def render_dxf_to_image(dxf_path: str, output_png_path: str = None) -> str:
    """
    Convert a 2D CAD DXF drawing into a high-resolution PNG image 
    so Veda and the user can visually inspect layouts, duct runs, and floor plans.
    """
    try:
        p = _resolve_path(dxf_path)
        if not p.exists():
            return f"Error: DXF file not found at {dxf_path}"

        if not output_png_path:
            png_path = p.with_suffix('.png')
        else:
            png_path = _resolve_path(output_png_path)

        doc = ezdxf.readfile(str(p))
        _render_dxf_geometry(doc, png_path, title=f"CAD Drawing Preview: {p.name}")

        return (
            f"SUCCESS: Rendered CAD DXF to PNG image!\n"
            f"Source CAD:   {p}\n"
            f"Rendered PNG: {png_path}\n"
            f"File Size:    {png_path.stat().st_size / 1024:.1f} KB"
        )
    except Exception as e:
        return f"Error rendering DXF to image: {e}"

def _render_dxf_geometry(doc, save_path: Path, title: str = "CAD Layout"):
    """Internal helper using matplotlib to draw DXF 2D vectors cleanly."""
    msp = doc.modelspace()
    fig, ax = plt.subplots(figsize=(14, 8), facecolor='#1e1e1e')
    ax.set_facecolor('#121212')

    layer_colors = {
        'M-DUCT-SUPP': '#00bcd4',
        'M-DUCT-RETN': '#2196f3',
        'M-DIFF': '#4caf50',
        'M-EQUP': '#e91e63',
        'M-PIPE-CHWS': '#00e5ff',
        'M-PIPE-CHWR': '#2979ff',
        'M-VALV': '#ffeb3b',
        'M-TEXT': '#ffffff'
    }

    for e in msp:
        dxftype = e.dxftype()
        layer = e.dxf.layer if hasattr(e.dxf, 'layer') else '0'
        c = layer_colors.get(layer, '#aaaaaa')

        if dxftype == 'LINE':
            start = e.dxf.start
            end = e.dxf.end
            ax.plot([start.x, end.x], [start.y, end.y], color=c, linewidth=1.5)
        elif dxftype == 'LWPOLYLINE':
            pts = list(e.get_points())
            if pts:
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                ax.plot(xs, ys, color=c, linewidth=1.5)
        elif dxftype == 'CIRCLE':
            center = e.dxf.center
            r = e.dxf.radius
            circle = plt.Circle((center.x, center.y), r, color=c, fill=False, linewidth=1.5)
            ax.add_patch(circle)
        elif dxftype in ('TEXT', 'MTEXT'):
            try:
                pos = e.dxf.insert
                txt = e.dxf.text if dxftype == 'TEXT' else e.text
                ax.text(pos.x, pos.y, txt, color='#ffffff', fontsize=8, family='sans-serif',
                        bbox=dict(boxstyle='square,pad=0.1', facecolor='#121212', edgecolor='none', alpha=0.6))
            except Exception:
                pass

    ax.set_title(title, color='#ffffff', fontsize=12, pad=15)
    ax.grid(True, linestyle='--', color='#2a2a2a', alpha=0.7)
    ax.tick_params(colors='#888888')
    for spine in ax.spines.values():
        spine.set_color('#444444')
    ax.axis('equal')
    plt.tight_layout()

    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(save_path), dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)

# ─────────────────────────────────────────────────────────────
# REGISTER CAD TOOLS
# ─────────────────────────────────────────────────────────────

server.add_tool(
    "generate_dxf_hvac_layout", 
    "Generate an AutoCAD-compatible DXF layout of HVAC ductwork, AHU equipment, and diffusers with standard AIA layers.",
    {
        "type": "object", 
        "properties": {
            "output_filename": {"type": "string", "description": "Filename for output DXF, e.g. 'office_hvac_plan.dxf'"},
            "main_duct_cfm": {"type": "number", "description": "Airflow capacity of the main supply duct in CFM (default 3000)"},
            "length_feet": {"type": "number", "description": "Total length of the main duct run in feet (default 40)"},
            "branch_count": {"type": "integer", "description": "Number of branch takeoff pairs along the run (default 4)"}
        }
    }, 
    generate_dxf_hvac_layout
)

server.add_tool(
    "generate_dxf_piping_layout", 
    "Generate an AutoCAD-compatible DXF schematic of Chilled Water hydronic piping loops, pumps, chillers, and headers.",
    {
        "type": "object", 
        "properties": {
            "output_filename": {"type": "string", "description": "Filename for output DXF, e.g. 'chiller_plant_piping.dxf'"},
            "chiller_tons": {"type": "number", "description": "Cooling capacity of chiller in Tons (default 100)"},
            "flow_gpm": {"type": "number", "description": "Hydronic water flow rate in GPM (default 240)"}
        }
    }, 
    generate_dxf_piping_layout
)

server.add_tool(
    "parse_dxf_drawing", 
    "Analyze an existing CAD DXF file, extracting layer lists, text callouts, block symbols, and entity counts.",
    {
        "type": "object", 
        "properties": {
            "dxf_path": {"type": "string", "description": "Path to the DXF file to parse"}
        }, 
        "required": ["dxf_path"]
    }, 
    parse_dxf_drawing
)

server.add_tool(
    "render_dxf_to_image", 
    "Render any 2D CAD DXF drawing into a high-resolution PNG image so Veda and user can visually inspect plans.",
    {
        "type": "object", 
        "properties": {
            "dxf_path": {"type": "string", "description": "Path to source DXF file"},
            "output_png_path": {"type": "string", "description": "Optional destination path for the rendered PNG"}
        }, 
        "required": ["dxf_path"]
    }, 
    render_dxf_to_image
)

if __name__ == "__main__":
    server.run()
