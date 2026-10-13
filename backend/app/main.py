
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any
import re

app = FastAPI(
    title="RentGuard AI API",
    description="Backend API for rental listing analysis",
    version="0.2.0",
)

# Local development only. Restrict this for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



class ListingDetails(BaseModel):
    propertyTitle: str = "Not provided"
    location: str = "Not found"
    propertyType: str = "Not identified"
    rent: str = "Not found"
    deposit: str = "Not found"
    billsIncluded: str = "Not confirmed"
    broadband: str = "Not confirmed"
    dssLhaIndicator: str = "Not stated"
    includedServices: list[str] = Field(default_factory=list)
    availability: str = "Not found"
    minimumTenancy: str = "Not stated"
    epcStatus: str = "Not stated"
    tenantRequirements: list[str] = Field(default_factory=list)
    propertyFeatures: list[str] = Field(default_factory=list)



def parse_money(value: str) -> float | None:
    """Extract the first pound amount from a string."""
    if not value:
        return None

    match = re.search(
        r"£\s*([\d,]+(?:\.\d{1,2})?)",
        value
    )

    if not match:
        return None

    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def add_finding(
    findings: list[dict[str, Any]],
    category: str,
    level: str,
    title: str,
    evidence: str,
    explanation: str,
    recommended_action: str,
):
    findings.append({
        "category": category,
        "level": level,
        "title": title,
        "evidence": evidence,
        "explanation": explanation,
        "recommendedAction": recommended_action,
    })


def analyse_listing(listing: ListingDetails) -> dict[str, Any]:
    """Run transparent, preliminary checks on extracted listing details."""
    findings: list[dict[str, Any]] = []

    # 1. Check whether the rent was extracted.
    rent = parse_money(listing.rent)

    if rent is None:
        add_finding(
            findings,
            "rent",
            "needs_review",
            "Confirm the monthly rent",
            listing.rent,
            "A monthly rent amount could not be reliably extracted.",
            "Check the advertised rent and payment frequency with the landlord.",
        )

    # 2. Check whether the deposit was extracted.
    deposit = parse_money(listing.deposit)

    if deposit is None:
        add_finding(
            findings,
            "deposit",
            "needs_review",
            "Confirm the deposit amount",
            listing.deposit,
            "A deposit amount could not be reliably extracted.",
            "Ask the landlord for the exact deposit and applicable tenancy terms.",
        )

    # 3. Explain the bills status without treating excluded bills as misconduct.
    bills = listing.billsIncluded.lower()

    if "not confirmed" in bills or "needs review" in bills:
        add_finding(
            findings,
            "bills",
            "needs_review",
            "Check which bills are included",
            listing.billsIncluded,
            "The listing does not clearly establish whether bills are included.",
            "Ask which utilities and other household costs you must pay separately.",
        )

    elif bills.startswith("no"):
        add_finding(
            findings,
            "bills",
            "information",
            "Budget for bills separately",
            listing.billsIncluded,
            "The listing indicates that bills are not included in the rent. "
            "This is not, by itself, a warning sign.",
            "Ask for an estimate of utilities, council tax where applicable, "
            "and any other additional costs.",
        )

    # 4. Broadband is a separate field from utility bills.
    broadband = listing.broadband.lower()

    if (
        "view offers" in broadband
        or "not confirmed" in broadband
        or "needs review" in broadband
    ):
        add_finding(
            findings,
            "broadband",
            "needs_review",
            "Verify broadband availability and cost",
            listing.broadband,
            "The listing field does not confirm that broadband is included.",
            "Check availability, installation requirements, contract terms "
            "and monthly cost.",
        )

    elif "not included" in broadband or "excluded" in broadband:
        add_finding(
            findings,
            "broadband",
            "information",
            "Broadband may cost extra",
            listing.broadband,
            "The listing indicates broadband is not included.",
            "Check provider availability and budget for a separate service if needed.",
        )

    # 5. Compare the deposit with a five-week rent benchmark.
    # This is a screening check, not a legal determination.
    if rent is not None and deposit is not None and rent > 0:
        weekly_rent = rent * 12 / 52
        five_week_benchmark = weekly_rent * 5

        if deposit > five_week_benchmark + 0.01:
            add_finding(
                findings,
                "deposit",
                "potential_concern",
                "Deposit exceeds the five-week benchmark",
                (
                    f"Advertised monthly rent: £{rent:,.2f}; "
                    f"advertised deposit: £{deposit:,.2f}; "
                    f"five-week benchmark: £{five_week_benchmark:,.2f}."
                ),
                "The advertised deposit is higher than a common five-week "
                "rent benchmark used for many residential tenancies in England. "
                "Exceptions and the applicable tenancy rules must be checked.",
                "Ask the landlord to explain the calculation and verify the "
                "applicable deposit limit before paying.",
            )
        else:
            add_finding(
                findings,
                "deposit",
                "information",
                "Deposit compared with a five-week benchmark",
                (
                    f"Advertised monthly rent: £{rent:,.2f}; "
                    f"advertised deposit: £{deposit:,.2f}; "
                    f"five-week benchmark: £{five_week_benchmark:,.2f}."
                ),
                "The advertised deposit does not exceed this preliminary "
                "benchmark. This alone does not establish legal compliance.",
                "Confirm the tenancy type, applicable rules and how the deposit "
                "will be protected.",
            )

    # 6. Check the availability statement.
    availability = listing.availability.lower()

    if (
        "not found" in availability
        or "not confirmed" in availability
        or "needs review" in availability
    ):
        add_finding(
            findings,
            "availability",
            "needs_review",
            "Confirm the move-in date",
            listing.availability,
            "The available move-in date could not be clearly established.",
            "Ask the landlord to confirm the earliest move-in date.",
        )
    else:
        add_finding(
            findings,
            "availability",
            "information",
            "Availability extracted",
            listing.availability,
            "A move-in date or availability statement was found. "
            "It may not reflect the property's current status.",
            "Confirm that the property is still available for your intended date.",
        )

    # 7. Flag an unconfirmed minimum tenancy.
    tenancy = listing.minimumTenancy.lower()

    if tenancy == "not stated" or "not found" in tenancy:
        add_finding(
            findings,
            "tenancy",
            "needs_review",
            "Confirm tenancy length and terms",
            listing.minimumTenancy,
            "The minimum tenancy length was not stated in the extracted details.",
            "Ask about the tenancy duration, break clause and notice requirements.",
        )

    # 8. Clarify the meaning of the DSS/LHA listing indicator.
    if "covers rent" in listing.dssLhaIndicator.lower():
        add_finding(
            findings,
            "benefits",
            "information",
            "Verify benefit affordability",
            listing.dssLhaIndicator,
            "This listing indicator does not guarantee that benefit payments "
            "will cover the full rent or that a tenancy will be offered.",
            "Check your individual entitlement and discuss the landlord's "
            "requirements before relying on this indicator.",
        )
    
    # 9. Check EPC status.
    epc_status = listing.epcStatus.lower()

    if "currently being obtained" in epc_status:
        add_finding(
            findings,
            "epc",
            "needs_review",
            "Verify the property's EPC status",
            listing.epcStatus,
            "The listing states that the EPC is currently being obtained.",
            "Ask the landlord or agent for an update and the EPC details when available.",
        )

    # 10. Summarise stated tenant requirements.
    if listing.tenantRequirements:
        add_finding(
            findings,
            "tenant_requirements",
            "information",
            "Tenant requirements stated",
            "; ".join(listing.tenantRequirements),
            "The listing specifies requirements for prospective tenants. "
            "These are listing statements, not a judgement about the applicant.",
            "Confirm which documents are required and how they will be handled.",
        )
    # 9. Avoid presenting an empty report when no rules trigger.
    if not findings:
        add_finding(
            findings,
            "general",
            "information",
            "No checks were triggered",
            "The available extracted fields did not trigger the current rules.",
            "This is not proof that the listing is safe or that all details "
            "have been verified.",
            "Review the listing and confirm important terms before paying.",
        )

    review_count = sum(
        finding["level"] == "needs_review"
        for finding in findings
    )

    concern_count = sum(
        finding["level"] == "potential_concern"
        for finding in findings
    )

    return {
        "status": "completed",
        "summary": (
            f"{len(findings)} findings generated: "
            f"{concern_count} potential concerns and "
            f"{review_count} items needing review."
        ),
        "findings": findings,
        "disclaimer": (
            "Preliminary automated checks only. Findings are not proof of "
            "fraud, a safety assessment or legal advice. Verify details "
            "independently."
        ),
    }


@app.get("/")
def home():
    return {
        "message": "RentGuard AI backend is running",
        "status": "ready",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/analyse")
def analyse_endpoint(listing: ListingDetails):
    analysis = analyse_listing(listing)

    return {
        "property": listing.model_dump(),
        "analysis": analysis,
    }
