"""One-off generator for the northwind-fabrication synthetic contract PDF fixtures.

Run once: python generate_contracts.py

Deliberately different risk profile than acme-distribution's two contracts: this data room
exercises the contract-reviewer's "other" clause_type (an exclusivity restriction) alongside the
three categories acme-distribution already covers, instead of just auto-renewal/pricing-escalator/
termination - proves the pipeline isn't hand-tuned to only ever produce three of the four
clause_type values.
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


maintenance_sections = [
    (
        "1. Parties",
        'This Equipment Maintenance Agreement ("Agreement") is entered into between '
        'Northwind Fabrication Ltd. ("Customer") and Precision Machine Services Inc. '
        '("Provider"), effective as of February 1, 2025.',
    ),
    (
        "2. Services",
        "Provider shall perform scheduled and emergency maintenance on the CNC and stamping "
        "equipment listed in Schedule A at Customer's Hamilton, Ontario facility.",
    ),
    (
        "3. Term",
        "This Agreement shall commence on the Effective Date and continue for an initial term "
        'of twenty-four (24) months (the "Initial Term").',
    ),
    (
        "4. Exclusivity",
        "During the Initial Term and any Renewal Term, Customer shall not engage any other "
        "provider to perform maintenance, repair, or calibration services on the equipment "
        "listed in Schedule A, and shall refer all such service needs to Provider in the first "
        "instance, regardless of Provider's response time or pricing on any given call.",
    ),
    (
        "5. Response Time",
        "Provider shall use commercially reasonable efforts to respond to emergency service "
        "requests within forty-eight (48) hours, but response time is not guaranteed and no "
        "service-level credit is payable for a missed response window.",
    ),
    (
        "6. Termination for Convenience",
        "Neither Party may terminate this Agreement for convenience during the Initial Term. "
        "Following the Initial Term, either Party may terminate on ninety (90) days' written "
        "notice.",
    ),
    (
        "7. Confidentiality",
        "Each Party shall maintain the confidentiality of the other Party's proprietary "
        "information disclosed in connection with this Agreement.",
    ),
    (
        "8. Governing Law",
        "This Agreement shall be governed by the laws of the Province of Ontario and the "
        "federal laws of Canada applicable therein.",
    ),
]

component_supply_sections = [
    (
        "1. Parties",
        'This Component Supply Agreement ("Agreement") is entered into between Aldergate Metals '
        'Ltd. ("Supplier") and Northwind Fabrication Ltd. ("Customer"), effective as of '
        "March 1, 2025.",
    ),
    (
        "2. Products and Pricing",
        "Supplier shall supply the raw steel and aluminum stock listed in Schedule A "
        '("Products") at the unit prices set out therein ("Base Prices").',
    ),
    (
        "3. Annual Price Adjustment",
        "Commencing on the first anniversary of the Effective Date and on each anniversary "
        "thereafter, Base Prices shall automatically increase by six percent (6%), applied "
        "without further notice to or consent from Customer, unless Customer terminates this "
        "Agreement in accordance with Section 6 at least forty-five (45) days prior to the "
        "applicable anniversary date.",
    ),
    (
        "4. Delivery",
        "Supplier shall deliver Products to Customer's designated facility in accordance with "
        "the delivery schedule set out in Schedule B, subject to standard lead times of "
        "fifteen (15) business days.",
    ),
    (
        "5. Renewal",
        "This Agreement has an initial term of two (2) years from the Effective Date and shall "
        "renew automatically for successive one (1) year terms unless either Party gives at "
        "least forty-five (45) days' written notice of non-renewal prior to the end of the "
        "then-current term.",
    ),
    (
        "6. Warranty",
        "Supplier warrants that all Products will conform to the specifications set out in "
        "Schedule A and will be free from material defects for a period of six (6) months from "
        "delivery.",
    ),
    (
        "7. Governing Law",
        "This Agreement shall be governed by the laws of the Province of Ontario and the "
        "federal laws of Canada applicable therein.",
    ),
]

build_pdf(
    "equipment_maintenance_agreement.pdf",
    "Equipment Maintenance Agreement — Precision Machine Services Inc.",
    maintenance_sections,
)
build_pdf(
    "component_supply_agreement.pdf",
    "Component Supply Agreement — Aldergate Metals Ltd.",
    component_supply_sections,
)
