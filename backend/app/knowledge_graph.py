
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

# Create the graph and our own namespace.
kg = Graph()
RENT = Namespace("https://rentguard.ai/ontology#")

kg.bind("rent", RENT)
kg.bind("rdfs", RDFS)

# Define the types of things our graph can represent.
kg.add((RENT.RentalRule, RDF.type, RDFS.Class))
kg.add((RENT.RentalConcept, RDF.type, RDFS.Class))
kg.add((RENT.OfficialSource, RDF.type, RDFS.Class))

# Define relationships between graph entities.
kg.add((RENT.appliesTo, RDF.type, RDF.Property))
kg.add((RENT.supportedBy, RDF.type, RDF.Property))
kg.add((RENT.sourceURL, RDF.type, RDF.Property))
kg.add((RENT.ruleDescription, RDF.type, RDF.Property))

# Add two example concepts.
kg.add((
    RENT.TenancyDeposit,
    RDF.type,
    RENT.RentalConcept
))
kg.add((
    RENT.EPC,
    RDF.type,
    RENT.RentalConcept
))

kg.add((
    RENT.TenancyDeposit,
    RDFS.label,
    Literal("Tenancy deposit")
))
kg.add((
    RENT.EPC,
    RDFS.label,
    Literal("Energy Performance Certificate (EPC)")
))

# Add an example source record.
# This is metadata only; it does not yet verify a legal rule.
source = URIRef(
    "https://www.gov.uk/tenancy-deposit-protection"
)

kg.add((source, RDF.type, RENT.OfficialSource))
kg.add((
    source,
    RDFS.label,
    Literal("GOV.UK tenancy deposit protection guidance")
))
kg.add((source, RENT.sourceURL, Literal(str(source), datatype=XSD.anyURI)))

# Add predicates for source traceability and rule relationships.
kg.add((RENT.hasRule, RDF.type, RDF.Property))
kg.add((RENT.jurisdiction, RDF.type, RDF.Property))
kg.add((RENT.sourceNote, RDF.type, RDF.Property))

# Official source: current tenancy deposit guidance for tenants.
deposit_source = URIRef(
    "https://www.gov.uk/assured-periodic-tenancies-tenants/"
    "rent-in-advance-and-deposits"
)

kg.add((deposit_source, RDF.type, RENT.OfficialSource))
kg.add((
    deposit_source,
    RDFS.label,
    Literal("GOV.UK: Assured periodic tenancies — deposits")
))
kg.add((
    deposit_source,
    RENT.sourceURL,
    Literal(str(deposit_source), datatype=XSD.anyURI)
))
kg.add((
    deposit_source,
    RENT.jurisdiction,
    Literal("England")
))
kg.add((
    deposit_source,
    RENT.sourceNote,
    Literal("Official tenant guidance; check current tenancy type and rent band.")
))

# Official source: EPC guidance for residential properties.
epc_source = URIRef(
    "https://www.gov.uk/government/publications/"
    "energy-performance-certificates-for-the-construction-sale-and-let-of-dwellings/"
    "a-guide-to-energy-performance-certificates-for-the-marketing-sale-and-let-of-dwellings"
)

kg.add((epc_source, RDF.type, RENT.OfficialSource))
kg.add((
    epc_source,
    RDFS.label,
    Literal("GOV.UK: Energy Performance Certificates for dwellings")
))
kg.add((
    epc_source,
    RENT.sourceURL,
    Literal(str(epc_source), datatype=XSD.anyURI)
))
kg.add((
    epc_source,
    RENT.jurisdiction,
    Literal("England and Wales")
))
kg.add((
    epc_source,
    RENT.sourceNote,
    Literal("Guidance last updated 11 December 2017; verify current requirements.")
))

# Define a deposit rule record.
deposit_rule = RENT.DepositLimitGuidance
kg.add((deposit_rule, RDF.type, RENT.RentalRule))
kg.add((
    deposit_rule,
    RDFS.label,
    Literal("Tenancy deposit limit guidance")
))
kg.add((
    deposit_rule,
    RENT.ruleDescription,
    Literal(
        "Official guidance describes a maximum of five weeks' rent "
        "for annual rent below £50,000, and six weeks for the "
        "applicable higher rent band. Verify the current rules, "
        "tenancy type and exceptions before assessing a listing."
    )
))
kg.add((deposit_rule, RENT.supportedBy, deposit_source))
kg.add((deposit_source, RENT.hasRule, deposit_rule))
kg.add((deposit_rule, RENT.appliesTo, RENT.TenancyDeposit))

# Define an EPC guidance record.
epc_rule = RENT.EPCAvailabilityGuidance
kg.add((epc_rule, RDF.type, RENT.RentalRule))
kg.add((
    epc_rule,
    RDFS.label,
    Literal("Residential EPC availability guidance")
))
kg.add((
    epc_rule,
    RENT.ruleDescription,
    Literal(
        "Official residential EPC guidance describes requirements "
        "for making an EPC available when a property is marketed "
        "or rented, subject to applicable exceptions. Check the "
        "current rules and property circumstances."
    )
))
kg.add((epc_rule, RENT.supportedBy, epc_source))
kg.add((epc_source, RENT.hasRule, epc_rule))
kg.add((epc_rule, RENT.appliesTo, RENT.EPC))

# Print basic information about the graph.
print("RentGuard AI Knowledge Graph created.")
print(f"Number of RDF triples: {len(kg)}")

print("\nGraph contents:")
for subject, predicate, obj in kg:
    print(subject, "|", predicate, "|", obj)

# Save the graph locally in Turtle format.
kg.serialize(
    destination="rentguard_knowledge_graph.ttl",
    format="turtle"
)

print("\nGraph saved to rentguard_knowledge_graph.ttl")

# Query the graph for all rental concepts.
query = """
PREFIX rent: <https://rentguard.ai/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?concept ?label
WHERE {
    ?concept a rent:RentalConcept ;
             rdfs:label ?label .
}
ORDER BY ?label
"""

print("\nRental concepts found by SPARQL:")

for row in kg.query(query):
    print(f"- {row.label} ({row.concept})")
