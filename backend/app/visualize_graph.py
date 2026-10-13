from pathlib import Path
from rdflib import Graph, RDF, RDFS, URIRef, Literal
from pyvis.network import Network

# Paths are based on this file, so the script works from the backend folder
# or when launched directly from VS Code.
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
GRAPH_FILE = BACKEND_DIR / "rentguard_knowledge_graph.ttl"
OUTPUT_FILE = BACKEND_DIR / "rentguard_graph.html"

if not GRAPH_FILE.exists():
    raise FileNotFoundError(
        f"Could not find {GRAPH_FILE}. "
        "Run `python -m app.knowledge_graph` first to create the graph."
    )

kg = Graph()
kg.parse(GRAPH_FILE, format="turtle")

# Create an interactive network. Physics makes connected nodes settle naturally.
net = Network(
    height="780px",
    width="100%",
    directed=True,
    bgcolor="#0b1220",
    font_color="#e5edf8",
    notebook=False,
    cdn_resources="in_line",
)

net.set_options("""
{
  "nodes": {
    "shape": "dot",
    "size": 20,
    "borderWidth": 2,
    "borderWidthSelected": 4,
    "font": {
      "face": "Arial",
      "size": 15,
      "color": "#e5edf8",
      "strokeWidth": 3,
      "strokeColor": "#0b1220"
    },
    "shadow": {
      "enabled": true,
      "size": 10,
      "x": 0,
      "y": 3
    }
  },
  "edges": {
    "arrows": {
      "to": {
        "enabled": true,
        "scaleFactor": 0.7
      }
    },
    "smooth": {
      "type": "dynamic"
    },
    "color": {
      "color": "#64748b",
      "highlight": "#f8fafc",
      "hover": "#cbd5e1"
    },
    "font": {
      "size": 11,
      "color": "#cbd5e1",
      "strokeWidth": 3,
      "strokeColor": "#0b1220",
      "align": "middle"
    },
    "width": 1.5
  },
  "interaction": {
    "hover": true,
    "tooltipDelay": 150,
    "navigationButtons": true,
    "keyboard": true
  },
  "physics": {
    "enabled": true,
    "solver": "forceAtlas2Based",
    "forceAtlas2Based": {
      "gravitationalConstant": -55,
      "centralGravity": 0.015,
      "springLength": 150,
      "springConstant": 0.08,
      "avoidOverlap": 0.8
    },
    "stabilization": {
      "enabled": true,
      "iterations": 250,
      "updateInterval": 25
    }
  }
}
""")

# Use local names for display, while preserving full URIs in node details.
def local_name(uri):
    value = str(uri)
    if "#" in value:
        value = value.rsplit("#", 1)[-1]
    elif "/" in value:
        value = value.rstrip("/").rsplit("/", 1)[-1]
    return value or str(uri)


def first_literal(subject, predicate):
    values = list(kg.objects(subject, predicate))
    for value in values:
        if isinstance(value, Literal):
            return str(value)
    return ""


# Determine node categories from RDF types.
class_uris = {
    str(RDFS.Class),
    str(URIRef("http://www.w3.org/2002/07/owl#Class")),
}
property_uris = {
    str(URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#Property")),
    str(URIRef("http://www.w3.org/2002/07/owl#ObjectProperty")),
    str(URIRef("http://www.w3.org/2002/07/owl#DatatypeProperty")),
}

type_colors = {
    "RentalConcept": "#38bdf8",  # sky blue
    "RentalRule": "#f59e0b",     # amber
    "OfficialSource": "#34d399", # green
    "Class": "#a78bfa",          # violet
    "Property": "#94a3b8",       # slate
    "Other": "#f472b6",          # pink
}

node_uris = set()
for subject, predicate, obj in kg:
    if isinstance(subject, URIRef):
        node_uris.add(subject)
    if isinstance(obj, URIRef):
        node_uris.add(obj)

# Build each node with a readable label and useful inspection details.
for uri in sorted(node_uris, key=str):
    rdf_types = list(kg.objects(uri, RDF.type))
    type_names = [local_name(t) for t in rdf_types]
    label = first_literal(uri, RDFS.label) or local_name(uri)

    if "RentalConcept" in type_names:
        category = "RentalConcept"
    elif "RentalRule" in type_names:
        category = "RentalRule"
    elif "OfficialSource" in type_names:
        category = "OfficialSource"
    elif any(str(t) in class_uris for t in rdf_types):
        category = "Class"
    elif any(str(t) in property_uris for t in rdf_types):
        category = "Property"
    else:
        category = "Other"

    details = [
        f"Label: {label}",
        f"Type: {', '.join(type_names) if type_names else 'Resource'}",
        f"URI: {uri}",
    ]

    description = first_literal(uri, URIRef("https://rentguard.ai/ontology#ruleDescription"))
    source_url = first_literal(uri, URIRef("https://rentguard.ai/ontology#sourceURL"))
    source_note = first_literal(uri, URIRef("https://rentguard.ai/ontology#sourceNote"))
    jurisdiction = first_literal(uri, URIRef("https://rentguard.ai/ontology#jurisdiction"))

    if description:
        details.append(f"Description: {description}")
    if source_url:
        details.append(f"Source URL: {source_url}")
    if source_note:
        details.append(f"Source note: {source_note}")
    if jurisdiction:
        details.append(f"Jurisdiction: {jurisdiction}")

    # Keep source links and longer descriptions available on hover/click.
    net.add_node(
        str(uri),
        label=label,
        title="<br>".join(details),
        color={
            "background": type_colors[category],
            "border": "#e2e8f0",
            "highlight": {
                "background": "#ffffff",
                "border": type_colors[category],
            },
        },
        group=category,
        shape="dot",
        size=30 if category in {"RentalConcept", "RentalRule", "OfficialSource"} else 15,
    )

# Turn RDF triples into labelled arrows. Hide RDF type links from the main
# relationship view to reduce clutter; type information remains in node details.
for subject, predicate, obj in kg:
    if not isinstance(subject, URIRef) or not isinstance(obj, URIRef):
        continue
    if predicate == RDF.type:
        continue

    relation = local_name(predicate)
    net.add_edge(
        str(subject),
        str(obj),
        label=relation,
        title=f"{subject} — {relation} → {obj}",
    )

# Add a small self-contained dashboard header and legend to the generated HTML.
net.generate_html(notebook=False)
html = net.html
dashboard_header = """
<div style="font-family:Arial,sans-serif;background:#0b1220;color:#e5edf8;
padding:22px 26px 12px;border-bottom:1px solid #243247;">
  <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;">
    <div>
      <div style="font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#94a3b8;">
        RentGuard AI · Local Knowledge Graph
      </div>
      <h1 style="margin:8px 0;font-size:26px;">Rental guidance explorer</h1>
      <p style="margin:0;color:#cbd5e1;font-size:14px;">
        Explore how rental concepts, guidance rules and official sources connect.
        Drag nodes, zoom, and click a node to inspect its details.
      </p>
    </div>
    <input id="nodeSearch" type="search" placeholder="Search concepts, rules, sources…"
      style="box-sizing:border-box;width:280px;max-width:100%;padding:11px 13px;
      border:1px solid #475569;border-radius:10px;background:#111c2e;color:#f8fafc;
      outline:none;font-size:14px;">
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:9px;margin:18px 0 6px;font-size:12px;">
    <span style="background:#13283b;border:1px solid #38bdf8;padding:7px 10px;border-radius:20px;">● Concepts</span>
    <span style="background:#302719;border:1px solid #f59e0b;padding:7px 10px;border-radius:20px;">● Rules</span>
    <span style="background:#123126;border:1px solid #34d399;padding:7px 10px;border-radius:20px;">● Official sources</span>
    <span style="background:#251e3b;border:1px solid #a78bfa;padding:7px 10px;border-radius:20px;">● Schema classes</span>
    <span style="background:#202a38;border:1px solid #94a3b8;padding:7px 10px;border-radius:20px;">● Properties</span>
  </div>
  <div id="graphStatus" style="font-size:12px;color:#94a3b8;padding:7px 0;">
    Tip: select a node to highlight its connections. Search dims unrelated nodes.
  </div>
</div>
<style>
  body { margin:0 !important; background:#0b1220 !important; }
  #mynetwork { border:0 !important; }
</style>
<script>
window.addEventListener("load", function () {
  const search = document.getElementById("nodeSearch");
  const status = document.getElementById("graphStatus");
  if (!search || typeof network === "undefined" || typeof nodes === "undefined") return;

  const originalColors = {};
  nodes.get().forEach(function (node) {
    originalColors[node.id] = JSON.parse(JSON.stringify(node.color));
  });

  search.addEventListener("input", function () {
    const q = search.value.trim().toLowerCase();
    const allNodes = nodes.get();
    if (!q) {
      nodes.update(allNodes.map(n => ({
        id: n.id,
        color: originalColors[n.id],
        hidden: false,
        opacity: 1
      })));
      network.setOptions({ edges: { color: { opacity: 1 } } });
      status.textContent = "Showing all graph nodes. Click a node to inspect its details.";
      return;
    }

    const matches = allNodes.filter(n =>
      String(n.label || "").toLowerCase().includes(q) ||
      String(n.title || "").toLowerCase().includes(q) ||
      String(n.id || "").toLowerCase().includes(q)
    );
    const matchedIds = new Set(matches.map(n => n.id));
    nodes.update(allNodes.map(n => ({
      id: n.id,
      hidden: false,
      opacity: matchedIds.has(n.id) ? 1 : 0.16
    })));
    status.textContent = matches.length + " matching node(s). Matching nodes are highlighted; other nodes are dimmed.";
    if (matches.length > 0) network.fit({ nodes: matches.map(n => n.id), animation: true });
  });

  network.on("click", function (params) {
    if (params.nodes && params.nodes.length) {
      const selected = nodes.get(params.nodes[0]);
      status.textContent = "Selected: " + (selected.label || selected.id) +
        " · " + (selected.group || "Graph resource") +
        " · Hover over the node for its URI and available metadata.";
    } else if (!search.value) {
      status.textContent = "Tip: select a node to highlight its connections. Search dims unrelated nodes.";
    }
  });
});
</script>
"""

# Insert the dashboard controls before the network canvas.
if "<body>" in html:
    html = html.replace("<body>", "<body>\n" + dashboard_header, 1)
else:
    html = html.replace("<body ", "<body " + dashboard_header, 1)

OUTPUT_FILE.write_text(html, encoding="utf-8")

print("RentGuard AI graph visualisation created.")
print(f"Nodes: {len(net.nodes)}")
print(f"Relationships: {len(net.edges)}")
print(f"HTML file: {OUTPUT_FILE}")
print("Open rentguard_graph.html in Chrome to explore the graph.")
