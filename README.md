# RentGuard AI 🏠

**An AI-assisted rental listing analysis tool combining a Chrome extension, a FastAPI backend, and a knowledge graph.**

RentGuard AI is an ongoing project designed to help users review rental listings by extracting key property details, highlighting items that may need attention, and linking rental guidance to supporting sources.

## Current Features

- **Chrome Extension:** Extracts relevant information from rental listings, including rent, deposit, property type, bills, tenancy length, and other available details.
- **FastAPI Backend:** Receives extracted listing information and generates structured analysis findings using an initial rule-based approach.
- **Rental Knowledge Graph:** Uses RDFLib to represent rental concepts, guidance rules, and supporting official sources as an RDF graph.
- **SPARQL Queries:** Supports querying the knowledge graph to retrieve rental concepts and explore their relationships.
- **Interactive Graph Visualisation:** Uses PyVis to generate an HTML visualisation of the knowledge graph.

## Tech Stack

- **Frontend:** HTML, CSS, JavaScript, Chrome Extension Manifest V3
- **Backend:** Python, FastAPI
- **Knowledge Graph:** RDFLib, RDF, SPARQL, Turtle (TTL)
- **Visualisation:** PyVis, HTML, JavaScript

## Project Structure

```text
rentguard-ai/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── knowledge_graph.py
│   │   ├── visualize_graph.py
│   │   └── __init__.py
│   ├── requirements.txt
│   ├── rentguard_knowledge_graph.ttl
│   └── rentguard_graph.html
├── extension/
│   ├── manifest.json
│   ├── content.js
│   ├── popup.html
│   ├── popup.css
│   └── popup.js
└── .gitignore
```

## Current Status

The initial prototype includes rental listing extraction, backend analysis, a starter knowledge graph, and an interactive graph visualisation. The knowledge graph currently contains example rental concepts, guidance rules, and source relationships.

**Next development goal:** Connect the knowledge graph to the backend analysis so findings can be supported by relevant rules and their associated sources.

## Disclaimer

RentGuard AI is an experimental project under development. Its findings are intended to support rental listing reviews, not to establish that a listing is fraudulent or provide definitive legal advice. Users should verify relevant details with landlords and consult current official guidance.

## License

No licence has been specified yet.
