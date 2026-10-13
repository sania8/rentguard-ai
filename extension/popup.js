
const analyseButton = document.getElementById("analyseButton");
const status = document.getElementById("status");
const results = document.getElementById("results");
const pageTitle = document.getElementById("pageTitle");
const pageText = document.getElementById("pageText");

function extractListingDetails(title, text, billIconState = null) {
  const safeTitle = title || "";
  const safeText = text || "";

  const details = {
    propertyTitle: safeTitle || "Not found",
    location: "Not found",
    propertyType: "Not identified",
    rent: "Not found",
    deposit: "Not found",
    billsIncluded: "Not confirmed — needs review",
    broadband: "Not confirmed — needs review",
    dssLhaIndicator: "Not stated",
    includedServices: [],
    availability: "Not found — needs review",
    minimumTenancy: "Not stated",
    epcStatus: "Not stated",
    tenantRequirements: [],
    propertyFeatures: []
  };

  // 1. Extract town and postcode from the title.
  const titlePostcode = safeTitle.match(
    /\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b/i
  );

  const partialPostcode = safeTitle.match(/\b(ME\d{1,2})\b/i);

  const townMatch = safeTitle.match(
    /\b(Maidstone|London|Canterbury|Medway)\b/i
  );

  if (townMatch && titlePostcode) {
    details.location =
      `${townMatch[1]}, ${titlePostcode[0].toUpperCase()}`;
  } else if (townMatch && partialPostcode) {
    details.location =
      `${townMatch[1]}, ${partialPostcode[1].toUpperCase()}`;
  } else if (townMatch) {
    details.location = townMatch[1];
  } else if (titlePostcode) {
    details.location = titlePostcode[0].toUpperCase();
  }

  // 2. Identify property type.
  const lowerTitle = safeTitle.toLowerCase();

  if (
    lowerTitle.includes("room in a shared house") ||
    lowerTitle.includes("room in shared house")
  ) {
    details.propertyType = "Room in a shared house";
  } else if (lowerTitle.includes("studio")) {
    details.propertyType = "Studio";
  } else if (/\bflat\b/i.test(lowerTitle)) {
    details.propertyType = "Flat";
  } else if (/\bhouse\b/i.test(lowerTitle)) {
    details.propertyType = "House";
  }

  // 3. Extract monthly rent.
  const rentMatch = safeText.match(
    /\bRent\s*PCM\s*£?\s*([\d,]+(?:\.\d{1,2})?)/i
  );

  const titleRent = safeTitle.match(
    /£\s*([\d,]+(?:\.\d{1,2})?)\s*(?:p\/m|pcm|per month)\b/i
  );

  if (rentMatch) {
    details.rent = `£${rentMatch[1]} per month`;
  } else if (titleRent) {
    details.rent = `£${titleRent[1]} per month`;
  }

  // 4. Extract deposit.
  const depositMatch = safeText.match(
    /\bDeposit\s*£?\s*([\d,]+(?:\.\d{1,2})?)/i
  );

  if (depositMatch) {
    details.deposit = `£${depositMatch[1]}`;
  }

  // 5. Determine whether bills are included.
  // Prefer the actual OpenRent icon when we can identify it.
  const positiveBillsPattern =
    /\ball bills included\b|\bbills included in (?:the )?rent\b|\b(?:rent|monthly rent) includes all utility bills\b|\ball utilities (?:are )?included\b|\butilities are included\b|\bbills are included\b|\butilities included in (?:the )?rent\b/i;

  const negativeBillsPattern =
    /\bbills\s*:\s*not included\b|\bbills excluded\b|\bbills not included\b|\bbills are not included\b|\butilities not included\b|\butilities are not included\b|\butilities excluded\b/i;

  const saysBillsIncluded = positiveBillsPattern.test(safeText);
  const saysBillsExcluded = negativeBillsPattern.test(safeText);

  if (billIconState === "included") {
    details.billsIncluded = "Yes — green tick shown on listing";
  } else if (billIconState === "excluded") {
    details.billsIncluded = "No — red cross shown on listing";
  } else if (saysBillsIncluded && saysBillsExcluded) {
    details.billsIncluded = "Conflicting text — needs review";
  } else if (saysBillsExcluded) {
    details.billsIncluded = "No — explicitly stated";
  } else if (saysBillsIncluded) {
    details.billsIncluded = "Yes — stated in listing";
  } else {
    details.billsIncluded = "Not confirmed — needs review";
  }

  // 6. Extract broadband information separately.
  const broadbandRowMatch = safeText.match(
    /\bBroadband\s+(View Offers|Included|Not Included|Excluded)\b/i
  );

  const broadbandDescriptionMatch = safeText.match(
    /[^.!?\n]*(?:rent includes all utility bills|monthly rent includes all utility bills|broadband is included|broadband included|fibre broadband)[^.!?\n]*/i
  );

  const broadbandDescription = broadbandDescriptionMatch
    ? broadbandDescriptionMatch[0]
    : "";

  const broadbandDescriptionSaysIncluded =
    /\b(?:rent includes all utility bills|monthly rent includes all utility bills|broadband is included|broadband included|fibre broadband)\b/i.test(
      broadbandDescription
    );

  if (broadbandRowMatch) {
    const rowValue = broadbandRowMatch[1].toLowerCase();

    if (rowValue === "included") {
      details.broadband = "Included — listing field";
    } else if (
      rowValue === "not included" ||
      rowValue === "excluded"
    ) {
      details.broadband = "Not included — listing field";
    } else if (
      rowValue === "view offers" &&
      broadbandDescriptionSaysIncluded
    ) {
      details.broadband =
        "Description says included; separate row says View Offers";
    } else if (rowValue === "view offers") {
      details.broadband =
        "View Offers shown — inclusion not confirmed by this field";
    }
  } else if (broadbandDescriptionSaysIncluded) {
    details.broadband = "Described as included";
  }

  // 7. Extract the DSS/LHA indicator.
  if (/\bDSS\s*\/\s*LHA\s+Covers\s+Rent\b/i.test(safeText)) {
    details.dssLhaIndicator =
      "DSS/LHA Covers Rent indicator shown — not a guarantee of full coverage";
  }

  // 8. Extract included services.
  const utilitySentenceMatch = safeText.match(
    /(?:monthly rent|rent)\s+includes all utility bills[^.!?\n]*/i
  );

  if (utilitySentenceMatch) {
    const utilitySentence = utilitySentenceMatch[0];

    const servicePatterns = [
      { pattern: /\bgas\b/i, service: "Gas" },
      { pattern: /\belectricity\b/i, service: "Electricity" },
      { pattern: /\bwater\b/i, service: "Water" },
      { pattern: /\bcouncil tax\b/i, service: "Council Tax" },
      { pattern: /\bbroadband\b/i, service: "Broadband" }
    ];

    details.includedServices = servicePatterns
      .filter(item => item.pattern.test(utilitySentence))
      .map(item => item.service);
  }

  if (
    /(?:cleaning service|cleaning)[^.!\n]*\bincluded\b/i.test(safeText)
  ) {
    details.includedServices.push("Communal-area cleaning");
  }

  details.includedServices = [
    ...new Set(details.includedServices)
  ];

  // 9. Extract availability.
  const datePattern =
    /\b(\d{1,2}\s+[A-Za-z]+\s*,?\s+\d{4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})\b/;

  let foundAvailability = null;

  // First check the explicit "Available From" field.
  const availableFromMatch = safeText.match(
    /\bAvailable\s+From\s*:?\s*(Today|Immediately|Now|\d{1,2}\s+[A-Za-z]+\s*,?\s+\d{4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})\b/i
  );

  if (availableFromMatch) {
    const value = availableFromMatch[1].trim();

    if (/^today$/i.test(value)) {
      foundAvailability = "Today";
    } else if (/^immediately$/i.test(value)) {
      foundAvailability = "Immediately";
    } else if (/^now$/i.test(value)) {
      foundAvailability = "Now";
    } else {
      foundAvailability = value.replace(/\s*,\s*/, " ");
    }
  }

  // Fallback: search around the Availability heading.
  if (!foundAvailability) {
    const lines = safeText
      .split(/\n/)
      .map(line => line.trim())
      .filter(Boolean);

    const availabilityIndex = lines.findIndex(line =>
      /\bavailability\b/i.test(line)
    );

    if (availabilityIndex !== -1) {
      const nearbyLines = lines.slice(
        availabilityIndex,
        availabilityIndex + 10
      );

      for (const line of nearbyLines) {
        const dateMatch = line.match(datePattern);

        if (dateMatch) {
          foundAvailability = dateMatch[1].replace(
            /\s*,\s*/,
            " "
          );
          break;
        }

        if (/\b(?:available\s+from\s+)?today\b/i.test(line)) {
          foundAvailability = "Today";
          break;
        }

        const otherMatch = line.match(
          /\b(?:available\s+from\s+)?(immediately|now)\b/i
        );

        if (otherMatch) {
          foundAvailability =
            otherMatch[1].toLowerCase() === "immediately"
              ? "Immediately"
              : "Now";
          break;
        }
      }
    }
  }

  if (foundAvailability) {
    details.availability = foundAvailability;
  }

  // 10. Extract minimum tenancy.
  const tenancyMatch = safeText.match(
    /(?:preferred\s+)?minimum tenancy\s*:?\s*(\d+\s*(?:months?|years?))/i
  );

  if (tenancyMatch) {
    details.minimumTenancy = tenancyMatch[1].trim();
  }
  // 9. Extract EPC status.
  const epcMatch = safeText.match(
    /\bEPC Rating\s+(Currently Being Obtained|[A-G])\b/i
  );

  if (epcMatch) {
    const epcValue = epcMatch[1];

    details.epcStatus =
      /^currently being obtained$/i.test(epcValue)
        ? "Currently being obtained — ask the landlord for an update"
        : `Rating ${epcValue.toUpperCase()}`;
  }

  // 10. Extract tenant requirements.
  if (/\bpay slips required\b|\bpayslips required\b/i.test(safeText)) {
    details.tenantRequirements.push("Payslips required");
  }

  if (/\bprevious landlord reference required\b/i.test(safeText)) {
    details.tenantRequirements.push(
      "Previous landlord reference required"
    );
  }

  if (/\b(?:one|1) months? deposit required\b/i.test(safeText)) {
    details.tenantRequirements.push(
      "One month's deposit required — confirm the advertised deposit amount"
    );
  }

  // 11. Extract selected property features.
  if (/\bunfurnished\b/i.test(safeText)) {
    details.propertyFeatures.push("Unfurnished");
  }

  if (/\bno car parking\b|\bno parking\b/i.test(safeText)) {
    details.propertyFeatures.push("No parking stated");
  }

  details.tenantRequirements = [
    ...new Set(details.tenantRequirements)
  ];

  details.propertyFeatures = [
    ...new Set(details.propertyFeatures)
  ];
  return details;
}

// Find the OpenRent icon associated with the "Bills Included" field.
// Returns "included", "excluded", or null if the field/icon is unclear.
function getBillsIncludedIconState() {
  const normalise = value =>
    (value || "").replace(/\s+/g, " ").trim().toLowerCase();

  // Find an element whose text is exactly "Bills Included".
  const labelElements = Array.from(
    document.querySelectorAll("body *")
  ).filter(element =>
    element.children.length === 0 &&
    normalise(element.textContent) === "bills included"
  );

  for (const label of labelElements) {
    // Check nearby ancestors for the label and its associated SVG.
    let container = label;

    for (let level = 0; level < 5 && container; level++) {
      const icons = Array.from(
        container.querySelectorAll("svg.or-icon")
      );

      if (icons.length > 0) {
        const hasSuccess = icons.some(icon =>
          icon.classList.contains("text-success")
        );

        const hasDanger = icons.some(icon =>
          icon.classList.contains("text-danger")
        );

        if (hasSuccess && !hasDanger) return "included";
        if (hasDanger && !hasSuccess) return "excluded";
      }

      container = container.parentElement;
    }
  }

  return null;
}

// Read the active webpage and analyse its visible text.

analyseButton.addEventListener("click", async () => {
  analyseButton.disabled = true;
  status.textContent = "Reading listing...";
  results.hidden = true;

  try {
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true
    });

    if (!tab?.id || !tab.url?.startsWith("http")) {
      throw new Error("Please open an OpenRent listing first.");
    }

    const [pageData] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const text = document.body?.innerText?.slice(0, 15000) || "";

        const normalise = value =>
          (value || "").replace(/\s+/g, " ").trim().toLowerCase();

        const labels = Array.from(
          document.querySelectorAll("body *")
        ).filter(element =>
          element.children.length === 0 &&
          normalise(element.textContent) === "bills included"
        );

        let billIconState = null;

        for (const label of labels) {
          let container = label;

          for (let level = 0; level < 5 && container; level++) {
            const icons = Array.from(
              container.querySelectorAll("svg.or-icon")
            );

            const success = icons.some(icon =>
              icon.classList.contains("text-success")
            );

            const danger = icons.some(icon =>
              icon.classList.contains("text-danger")
            );

            if (success && !danger) {
              billIconState = "included";
              break;
            }

            if (danger && !success) {
              billIconState = "excluded";
              break;
            }

            container = container.parentElement;
          }

          if (billIconState) break;
        }

        return {
          title: document.title,
          url: window.location.href,
          text,
          billIconState
        };
      }
    });

    const data = pageData?.result;

    if (!data || !data.text.trim()) {
      throw new Error("No visible listing text was found.");
    }

    const details = extractListingDetails(
      data.title,
      data.text,
      data.billIconState
    );

    pageTitle.textContent = data.title;
    status.textContent = "Sending listing to backend...";

    const response = await fetch(
      "http://127.0.0.1:8000/analyse",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(details)
      }
    );

    if (!response.ok) {
      throw new Error(`Backend error: HTTP ${response.status}`);
    }
    
    const backendResult = await response.json();

    const property = backendResult.property || {};
    const analysis = backendResult.analysis || {};
    const findings = analysis.findings || [];

    // Display the extracted property details.   
    pageText.textContent = [
      `Location: ${property.location || "Not found"}`,
      `Property type: ${property.propertyType || "Not identified"}`,
      `Rent: ${property.rent || "Not found"}`,
      `Deposit: ${property.deposit || "Not found"}`,
      `Bills: ${property.billsIncluded || "Not confirmed"}`,
      `Broadband: ${property.broadband || "Not confirmed"}`,
      `Availability: ${property.availability || "Not found"}`,
      `Minimum tenancy: ${property.minimumTenancy || "Not stated"}`,
      `EPC status: ${property.epcStatus || "Not stated"}`,
      `Tenant requirements: ${
        property.tenantRequirements?.length
          ? property.tenantRequirements.join(", ")
          : "Not identified"
      }`,
      `Property features: ${
        property.propertyFeatures?.length
          ? property.propertyFeatures.join(", ")
          : "Not identified"
      }`
    ].join("\n");


    pageTitle.textContent = property.propertyTitle || "Rental listing";


    // Build readable analysis cards.
    let report = document.getElementById("rentguard-report");

    if (!report) {
      report = document.createElement("div");
      report.id = "rentguard-report";
      pageText.insertAdjacentElement("afterend", report);
    }

    report.replaceChildren();

    const heading = document.createElement("h3");
    heading.textContent = "Analysis results";
    report.appendChild(heading);

    const summary = document.createElement("p");
    summary.textContent =
      analysis.summary || `${findings.length} findings generated.`;
    report.appendChild(summary);

    findings.forEach((finding) => {
      const card = document.createElement("section");
      card.className = `finding-card finding-${finding.level || "information"}`;

      const title = document.createElement("h4");
      title.textContent = finding.title || "Listing finding";
      card.appendChild(title);

      const level = document.createElement("p");
      const labels = {
        information: "Information",
        needs_review: "Needs review",
        potential_concern: "Potential concern"
      };

      level.textContent = labels[finding.level] || "Review";
      level.className = "finding-level";
      card.appendChild(level);

      if (finding.evidence) {
        const evidence = document.createElement("p");
        evidence.textContent = `Evidence: ${finding.evidence}`;
        card.appendChild(evidence);
      }

      if (finding.explanation) {
        const explanation = document.createElement("p");
        explanation.textContent = finding.explanation;
        card.appendChild(explanation);
      }

      if (finding.recommendedAction) {
        const action = document.createElement("p");
        action.textContent = `Suggested action: ${finding.recommendedAction}`;
        card.appendChild(action);
      }

      report.appendChild(card);
    });

    if (analysis.disclaimer) {
      const disclaimer = document.createElement("p");
      disclaimer.className = "report-disclaimer";
      disclaimer.textContent = analysis.disclaimer;
      report.appendChild(disclaimer);
    }

    results.hidden = false;
    status.textContent =
      "Success! Listing analysed by the RentGuard AI backend.";


    console.log("Extracted details:", details);
    console.log("Backend response:", backendResult);
    console.log("Listing URL:", data.url);

  } catch (error) {
    console.error("RentGuard AI:", error);

    status.textContent =
      error.message || "Could not analyse this listing.";

  } finally {
    analyseButton.disabled = false;
  }
});
