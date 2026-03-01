# mcp/servers/visualization_server.py
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
from mcp.server_base import MCPServer

server = MCPServer(name="visualization", version="1.0.0")

def generate_chart(data_json: str, chart_type: str, title: str, save_path: str) -> str:
    """
    Generate a chart (bar, line, pie) from JSON data and save as PNG.
    data_json must be a stringified dictionary: {"Label1": value1, "Label2": value2}
    """
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
        
        data = json.loads(data_json)
        if not data:
            return "Error: Empty data dictionary provided."
            
        labels = list(data.keys())
        values = list(data.values())
        
        plt.figure(figsize=(10, 6))
        
        if chart_type.lower() == 'bar':
            plt.bar(labels, values, color='#2ecc71')
            plt.ylabel('Values')
        elif chart_type.lower() == 'line':
            plt.plot(labels, values, marker='o', color='#3498db', linestyle='-', linewidth=2)
            plt.ylabel('Values')
            plt.grid(True, linestyle='--', alpha=0.7)
        elif chart_type.lower() == 'pie':
            plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        else:
            return f"Error: Unsupported chart_type '{chart_type}'. Use 'bar', 'line', or 'pie'."
            
        if chart_type.lower() != 'pie':
            plt.xticks(rotation=45, ha='right')
            
        plt.title(title)
        plt.tight_layout()
        
        p = Path(save_path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        
        plt.savefig(p, dpi=300)
        plt.close()
        
        return f"Successfully generated {chart_type} chart and saved to: {p}"
    except Exception as e:
        return f"Error generating chart: {e}"

server.add_tool("generate_chart", "Generate a bar, line, or pie chart from JSON data and save as PNG",
    {
        "type": "object", 
        "properties": {
            "data_json": {"type": "string", "description": "JSON string mapping labels to numeric values, e.g., '{\"Chiller A\": 100, \"Chiller B\": 120}'"},
            "chart_type": {"type": "string", "description": "'bar', 'line', or 'pie'"},
            "title": {"type": "string"},
            "save_path": {"type": "string", "description": "Absolute or relative path to save the .png file"}
        }, 
        "required": ["data_json", "chart_type", "title", "save_path"]
    }, generate_chart)

if __name__ == "__main__":
    server.run()
