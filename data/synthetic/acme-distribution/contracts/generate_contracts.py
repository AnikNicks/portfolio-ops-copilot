"""One-off generator for the two synthetic contract PDF fixtures.

Run once: python generate_contracts.py
Each contract has one deliberately embedded risk clause, buried in boilerplate,
for the contract-reviewer subagent to find via retrieval rather than a full-text dump.
"""

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

OUT_DIR = Path(__file__).parent
styles = getSampleStyleSheet()


def build_pdf(filename: str, title: str, sections: list[tuple[str, str]]) -> None:
    doc = SimpleDocTemplate(str(OUT_DIR / filename), pagesize=LETTER, topMargin=1 * inch, bottomMargin=1 * inch)
    story = [Paragraph(title, styles["Title"]), Spacer(1, 0.3 * inch)]
    for heading, body in sections:
        story.append(Paragraph(heading, styles["Heading3"]))
        story.append(Paragraph(body, styles["BodyText"]))
        story.append(Spacer(1, 0.18 * inch))
    doc.build(story)
    print(f"wrote {OUT_DIR / filename}")


freight_sections = [
    (
        "1. Parties",
        'This Freight Services Agreement ("Agreement") is entered into between '
        'Acme Distribution Inc. ("Customer") and Dominion Freight Carriers Ltd. ("Carrier"), '
        "effective as of January 1, 2024.",
    ),
    (
        "2. Services",
        "Carrier shall provide truckload and less-than-truckload freight services "
        "for Customer's outbound shipments from its Mississauga, Ontario distribution centre, "
        "in accordance with the rates set out in Schedule A.",
    ),
    (
        "3. Term",
        "This Agreement shall commence on the Effective Date and continue for an "
        'initial term of thirty-six (36) months (the "Initial Term").',
    ),
    (
        "4. Renewal",
        "Unless either Party provides the other with written notice of "
        "non-renewal not less than one hundred twenty (120) days prior to the expiration of the "
        "Initial Term or any Renewal Term, this Agreement shall automatically renew for "
        'successive twenty-four (24) month terms (each, a "Renewal Term") on the same terms and '
        "conditions then in effect, and Customer shall have no right to renegotiate rates during "
        "any such Renewal Term.",
    ),
    (
        "5. Rates and Fuel Surcharge",
        "Base rates are set out in Schedule A and are subject to a "
        "monthly fuel surcharge adjustment published by Carrier. Rates in Schedule A shall "
        "otherwise remain fixed during the Initial Term.",
    ),
    (
        "6. Termination for Convenience",
        "Except as set out in Section 4, neither Party may "
        "terminate this Agreement for convenience during the Initial Term or any Renewal Term.",
    ),
    (
        "7. Confidentiality",
        "Each Party shall maintain the confidentiality of the other Party's "
        "proprietary information disclosed in connection with this Agreement, using at least the "
        "same degree of care it uses to protect its own confidential information.",
    ),
    (
        "8. Governing Law",
        "This Agreement shall be governed by the laws of the Province of "
        "Ontario and the federal laws of Canada applicable therein.",
    ),
]

materials_sections = [
    (
        "1. Parties",
        'This Raw Materials Supply Agreement ("Agreement") is entered into '
        'between Steelcore Materials Ltd. ("Supplier") and Acme Distribution Inc. '
        '("Customer"), effective as of April 1, 2025.',
    ),
    (
        "2. Products and Pricing",
        "Supplier shall supply the components listed in Schedule A "
        '("Products") at the unit prices set out therein ("Base Prices").',
    ),
    (
        "3. Annual Price Adjustment",
        "Commencing on the first anniversary of the Effective Date "
        "and on each anniversary thereafter, Base Prices shall automatically increase by the "
        "greater of (a) four percent (4%), or (b) the year-over-year percentage change in the "
        "Statistics Canada Industrial Product Price Index for the preceding twelve-month period, "
        "without further notice to or consent from Customer, unless Customer terminates this "
        "Agreement in accordance with Section 6 at least sixty (60) days prior to the applicable "
        "anniversary date.",
    ),
    (
        "4. Volume Commitment",
        "Customer agrees to purchase not less than eighty-five percent "
        "(85%) of its annual requirements for the Products from Supplier during each Contract "
        "Year.",
    ),
    (
        "5. Delivery",
        "Supplier shall deliver Products to Customer's designated facilities in "
        "accordance with the delivery schedule set out in Schedule B, subject to standard lead "
        "times of ten (10) business days.",
    ),
    (
        "6. Term and Termination",
        "This Agreement has an initial term of three (3) years from "
        "the Effective Date and shall renew automatically for successive one (1) year terms "
        "unless either Party gives at least sixty (60) days' written notice of non-renewal prior "
        "to the end of the then-current term.",
    ),
    (
        "7. Warranty",
        "Supplier warrants that all Products will conform to the specifications "
        "set out in Schedule A and will be free from material defects for a period of twelve "
        "(12) months from delivery.",
    ),
    (
        "8. Governing Law",
        "This Agreement shall be governed by the laws of the Province of "
        "Ontario and the federal laws of Canada applicable therein.",
    ),
]

build_pdf(
    "vendor_contract_freight.pdf",
    "Freight Services Agreement — Dominion Freight Carriers Ltd.",
    freight_sections,
)
build_pdf(
    "vendor_contract_raw_materials.pdf",
    "Raw Materials Supply Agreement — Steelcore Materials Ltd.",
    materials_sections,
)
