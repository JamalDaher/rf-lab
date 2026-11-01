"""Pure navigation and report-center metadata for RF Lab v4."""
from rf_lab.dashboard import WORKSPACES

WORKFLOWS = (
    {"name":"Design an antenna","description":"Start with dimensions, inspect geometry, then plan construction.",
     "steps":(("Design & optimize","Antenna Designer"),
              ("Design & optimize","Design Workbench"),
              ("Design & optimize","Construction Assistant"))},
    {"name":"Measure and tune","description":"Import a VNA sweep, compare measurements, then tune.",
     "steps":(("Measure & match","NanoVNA S1P"),
              ("Measure & match","Measurement & Tuning Workbench"),
              ("Measure & match","Antenna Tuning"))},
    {"name":"Analyze a signal","description":"Inspect a recording, compare captures, and experiment with filters.",
     "steps":(("Signal analysis","RF Signal Analysis Dashboard"),
              ("Signal analysis","RF Signal Recording Comparison"),
              ("Signal analysis","RF Filter Design Laboratory"))},
)

REPORT_TOOLS = (
    ("Projects","Project Library","Project library JSON/ZIP backup"),
    ("Design & optimize","Design Workbench","Antenna design exports"),
    ("Measure & match","Measurement & Tuning Workbench","Measurement PDF reports"),
    ("Signal analysis","RF Signal Analysis Dashboard","Signal analysis JSON"),
    ("Signal analysis","RF Signal Recording Comparison","Recording comparison JSON"),
    ("Signal analysis","RF Filter Design Laboratory","FIR filter JSON and processed IQ"),
)

def all_tools():
    return [(category,name) for category,names in WORKSPACES.items() for name in names]

def search_tools(term):
    query=term.strip().casefold()
    if not query:
        return all_tools()
    return [(category,name) for category,name in all_tools()
            if query in category.casefold() or query in name.casefold()]

def tool_exists(category,name):
    return name in WORKSPACES.get(category,())

def normalize_favorites(values):
    """Discard stale/invalid favorites, preserve order, cap session UI clutter."""
    result=[]
    for item in values:
        if isinstance(item,(list,tuple)) and len(item)==2:
            pair=tuple(item)
            if tool_exists(*pair) and pair not in result:
                result.append(pair)
        if len(result)==8:
            break
    return result

def workflow_steps(index):
    if type(index)!=int or not 0<=index<len(WORKFLOWS):
        raise ValueError("unknown workflow")
    return WORKFLOWS[index]["steps"]
