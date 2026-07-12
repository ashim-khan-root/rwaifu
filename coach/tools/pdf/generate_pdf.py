"""
PDF Generator — wraps pdfme CLI for agentic PDF generation.

Usage:
  py -3 coach/tools/pdf/generate_pdf.py <command> [args]

Commands:
  generate   Generate PDF from template + inputs
  validate   Validate a template JSON file
  doctor     Diagnose environment and input readiness
  list       List example templates from pdfme
  quote      Generate a quotation PDF with company info and line items

Examples:
  py -3 coach/tools/pdf/generate_pdf.py list
  py -3 coach/tools/pdf/generate_pdf.py validate template.json
  py -3 coach/tools/pdf/generate_pdf.py generate -t template.json -i inputs.json -o out.pdf
  py -3 coach/tools/pdf/generate_pdf.py quote -o quotation.pdf --grid
"""

import json
import subprocess
import sys
import os
from pathlib import Path

PDF_DIR = Path(__file__).parent.resolve()
WORK_DIR = Path.cwd()
PDFME_CLI = os.path.join(PDF_DIR, "node_modules", ".bin", "pdfme")
if sys.platform == "win32":
    PDFME_CLI = os.path.join(PDF_DIR, "node_modules", ".bin", "pdfme.cmd")


def resolve_output_path(args):
    """Resolve -o/--output to absolute path relative to WORK_DIR."""
    resolved = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-o", "--output") and i + 1 < len(args):
            resolved.append(arg)
            out_path = args[i + 1]
            if not os.path.isabs(out_path):
                out_path = os.path.join(WORK_DIR, out_path)
            resolved.append(out_path)
            i += 2
        else:
            resolved.append(arg)
            i += 1
    return resolved


def run_pdfme(args, verbose=False):
    args = resolve_output_path(args)
    cmd = [PDFME_CLI] + args
    if verbose:
        print(f"[pdfme] {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PDF_DIR)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(result.returncode)
    return result.stdout


def cmd_list(args):
    """List or export official pdfme example templates."""
    run_pdfme(["examples"] + args)


def cmd_validate(args):
    """Validate a template or unified job JSON file."""
    result = run_pdfme(["validate"] + args + ["--json"])
    data = json.loads(result)
    if data.get("valid"):
        print("Valid")
    else:
        print("Invalid")
    print(json.dumps(data, indent=2))


def cmd_doctor(args):
    """Diagnose environment and input readiness."""
    result = run_pdfme(["doctor"] + args + ["--json"])
    data = json.loads(result)
    status = "healthy" if data.get("healthy") else "issues found"
    print(f"Status: {status}")
    print(json.dumps(data, indent=2))


def cmd_generate(args):
    """Generate PDF from template + inputs."""
    result = run_pdfme(["generate"] + args)
    # parse output path from args
    try:
        o_idx = args.index("-o") if "-o" in args else args.index("--output")
        out_path = args[o_idx + 1]
        print(f"PDF generated: {os.path.abspath(out_path)}")
    except (ValueError, IndexError):
        print(result)


def cmd_quote(args):
    """Generate a quotation PDF."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate a quotation PDF")
    parser.add_argument("-o", "--output", default="quotation.pdf")
    parser.add_argument("--grid", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--title", default="Quotation")
    parser.add_argument("--company", default="Your Company Name")
    parser.add_argument("--client", default="Client Name")
    parser.add_argument("--date", default="2026-07-06")
    parser.add_argument("--items", nargs="*", default=[
        '{"description": "Item 1", "qty": "1", "unit": "pcs", "rate": "100", "amount": "100"}'
    ])
    parsed, extra = parser.parse_known_args(args)

    items = []
    for item_str in parsed.items:
        items.append(json.loads(item_str))

    total = sum(float(i["amount"]) for i in items)

    template = {
        "basePdf": {
            "width": 210,
            "height": 297,
            "padding": [15, 15, 15, 15]
        },
        "schemas": [
            [
                {
                    "name": "title",
                    "type": "text",
                    "position": {"x": 15, "y": 15},
                    "width": 180,
                    "height": 12,
                    "fontSize": 22,
                    "alignment": "center",
                    "bold": True
                },
                {
                    "name": "company",
                    "type": "text",
                    "position": {"x": 15, "y": 35},
                    "width": 90,
                    "height": 8,
                    "fontSize": 12,
                    "bold": True
                },
                {
                    "name": "client",
                    "type": "text",
                    "position": {"x": 15, "y": 48},
                    "width": 90,
                    "height": 6,
                    "fontSize": 10
                },
                {
                    "name": "date",
                    "type": "text",
                    "position": {"x": 130, "y": 35},
                    "width": 65,
                    "height": 6,
                    "fontSize": 10,
                    "alignment": "right"
                },
                {
                    "name": "quote_number",
                    "type": "text",
                    "position": {"x": 130, "y": 44},
                    "width": 65,
                    "height": 6,
                    "fontSize": 10,
                    "alignment": "right"
                },
                {
                    "name": "header_item",
                    "type": "text",
                    "position": {"x": 15, "y": 65},
                    "width": 70,
                    "height": 7,
                    "fontSize": 9,
                    "bold": True
                },
                {
                    "name": "header_qty",
                    "type": "text",
                    "position": {"x": 90, "y": 65},
                    "width": 20,
                    "height": 7,
                    "fontSize": 9,
                    "alignment": "center",
                    "bold": True
                },
                {
                    "name": "header_unit",
                    "type": "text",
                    "position": {"x": 112, "y": 65},
                    "width": 25,
                    "height": 7,
                    "fontSize": 9,
                    "alignment": "center",
                    "bold": True
                },
                {
                    "name": "header_rate",
                    "type": "text",
                    "position": {"x": 139, "y": 65},
                    "width": 30,
                    "height": 7,
                    "fontSize": 9,
                    "alignment": "right",
                    "bold": True
                },
                {
                    "name": "header_amount",
                    "type": "text",
                    "position": {"x": 171, "y": 65},
                    "width": 24,
                    "height": 7,
                    "fontSize": 9,
                    "alignment": "right",
                    "bold": True
                }
            ]
        ]
    }

    inputs = [{
        "title": parsed.title,
        "company": parsed.company,
        "client": f"Client: {parsed.client}",
        "date": f"Date: {parsed.date}",
        "quote_number": f"Quote #: Q-{parsed.date.replace('-', '')}",
        "header_item": "Description",
        "header_qty": "Qty",
        "header_unit": "Unit",
        "header_rate": "Rate",
        "header_amount": "Amount"
    }]

    # Add dynamic line items
    y_pos = 76
    for i, item in enumerate(items):
        row_y = y_pos + (i * 10)
        desc = item["description"]
        qty = item["qty"]
        unit = item["unit"]
        rate = item["rate"]
        amount = item["amount"]

        page_schemas = template["schemas"][0]
        page_schemas.append({
            "name": f"item_desc_{i}",
            "type": "text",
            "position": {"x": 15, "y": row_y},
            "width": 73,
            "height": 7,
            "fontSize": 9
        })
        page_schemas.append({
            "name": f"item_qty_{i}",
            "type": "text",
            "position": {"x": 90, "y": row_y},
            "width": 20,
            "height": 7,
            "fontSize": 9,
            "alignment": "center"
        })
        page_schemas.append({
            "name": f"item_unit_{i}",
            "type": "text",
            "position": {"x": 112, "y": row_y},
            "width": 25,
            "height": 7,
            "fontSize": 9,
            "alignment": "center"
        })
        page_schemas.append({
            "name": f"item_rate_{i}",
            "type": "text",
            "position": {"x": 139, "y": row_y},
            "width": 30,
            "height": 7,
            "fontSize": 9,
            "alignment": "right"
        })
        page_schemas.append({
            "name": f"item_amount_{i}",
            "type": "text",
            "position": {"x": 171, "y": row_y},
            "width": 24,
            "height": 7,
            "fontSize": 9,
            "alignment": "right"
        })

        inputs[0][f"item_desc_{i}"] = desc
        inputs[0][f"item_qty_{i}"] = qty
        inputs[0][f"item_unit_{i}"] = unit
        inputs[0][f"item_rate_{i}"] = rate
        inputs[0][f"item_amount_{i}"] = amount

    # Total row
    total_y = y_pos + (len(items) * 10) + 5
    page_schemas.append({
        "name": "total_label",
        "type": "text",
        "position": {"x": 139, "y": total_y},
        "width": 30,
        "height": 8,
        "fontSize": 10,
        "alignment": "right",
        "bold": True
    })
    page_schemas.append({
        "name": "total_value",
        "type": "text",
        "position": {"x": 171, "y": total_y},
        "width": 24,
        "height": 8,
        "fontSize": 10,
        "alignment": "right",
        "bold": True
    })
    inputs[0]["total_label"] = "Total:"
    inputs[0]["total_value"] = f"{total:.2f}"

    job = {
        "template": template,
        "inputs": inputs
    }

    job_file = WORK_DIR / "_pdfme_job.json"
    with open(job_file, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2)

    gen_args = [str(job_file), "-o", parsed.output]
    if parsed.grid:
        gen_args.append("--grid")
    if parsed.verbose:
        gen_args.append("-v")

    cmd_generate(gen_args)
    os.remove(job_file)


def cmd_strategy(args):
    """Generate a marketing strategy document PDF."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate a marketing strategy PDF")
    parser.add_argument("-o", "--output", default="CEO_Smart_Home_Marketing_Strategy.pdf")
    parser.add_argument("--company", default="Technology Solutions Co.")
    parser.add_argument("-v", "--verbose", action="store_true")
    parsed, _ = parser.parse_known_args(args)

    title = "Marketing Strategy"
    subtitle = "Smart Home & Technology Solutions \u2014 Qatar Market"
    prepared = f"Prepared by: Hamid Ashim Khan"
    today = __import__("datetime").datetime.today().strftime("%B %d, %Y")

    content = [
        ("SECTION", "I. Executive Summary"),
        ("BODY", "This document outlines a comprehensive marketing strategy for the launch and growth of the company\u2019s smart home and technology solutions division in Qatar. The strategy leverages Qatar\u2019s accelerating demand for premium smart home integration across luxury residential, commercial, and hospitality sectors."),
        ("BODY", "The Opportunity: Qatar\u2019s smart home market is projected to grow at 15-18% CAGR through 2030, driven by World Cup legacy infrastructure, expanding real estate development, and increasing consumer awareness of IoT and home automation. Despite this growth, the market remains fragmented with few providers offering end-to-end premium service."),
        ("BODY", "Core Thesis: Differentiate on speed of installation, quality of design, depth of app integration, and post-install support rather than price. The premium segment values time, aesthetics, reliability, and a single point of accountability."),
        ("BODY", "3-Phase Approach: Phase 1 (Days 1-30) establishes digital presence and seeds pipeline. Phase 2 (Days 31-90) scales social proof through completed projects and partnerships. Phase 3 (Days 91-180) activates performance marketing and recurring revenue channels."),

        ("SECTION", "II. Market Context \u2014 Qatar"),
        ("BODY", "Qatar presents a unique smart home market dynamic. High disposable income, a large expat population in premium housing, ambitious real estate developments (Lusail, The Pearl, West Bay Lagoon, Msheireb), and a growing hospitality sector create sustained demand."),
        ("SUB", "Key Market Drivers"),
        ("BULLET", "Real Estate Boom: Qatar\u2019s construction sector is valued at over $40 billion with ongoing villa compounds, apartment towers, and mixed-use developments."),
        ("BULLET", "Tourism & Hospitality Growth: Hotels and serviced apartments upgrade to smart room controls as a competitive differentiator."),
        ("BULLET", "Security Consciousness: Residential and commercial clients demand integrated security \u2014 CCTV, access control, and alarm systems."),
        ("BULLET", "Government Digitization Push: Qatar National Vision 2030 drives smart city initiatives."),
        ("SUB", "Competitive Landscape"),
        ("BODY", "Three categories of players: (1) International Brands (Control4, Crestron, Lutron) \u2014 premium but expensive, limited local support. (2) Local Integrators \u2014 lack design sophistication and digital presence. (3) DIY/Consumer Retail (Philips Hue, Nest, Ring) \u2014 no integration or installation."),
        ("BODY", "Our positioning fills the gap: Premium design and execution at a competitive price, with local responsiveness multinationals cannot match and polish local competitors do not deliver."),

        ("SECTION", "III. Target Segments"),
        ("SUB", "A: Luxury Villa Owners (Primary)"),
        ("BODY", "Qatari nationals and high-income expat homeowners in The Pearl, Lusail, West Bay Lagoon. Decision criteria: design quality, brand reputation, single-vendor accountability. Est. market: 3,500-5,000 premium villas. Avg. project: QAR 40,000-150,000."),
        ("SUB", "B: Apartment Owners & Tenants"),
        ("BODY", "Professionals in luxury apartments (Pearl, Msheireb, Fox Hills). Compact packages: smart lighting, thermostat, doorbell, security hub. Est. market: 8,000-12,000 units. Avg. project: QAR 15,000-40,000."),
        ("SUB", "C: Hotels & Hospitality (Strategic)"),
        ("BODY", "Boutique hotels, serviced apartments. Bulk standardized deployments. A flagship hotel installation becomes your best sales tool. Target: 5-10 properties. Avg. project: QAR 100,000-500,000."),
        ("SUB", "D: Offices & Commercial"),
        ("BODY", "SME offices, co-working spaces, corporate HQ. Access control, meeting room automation, energy management, integrated CCTV. Recurring maintenance contracts."),

        ("SECTION", "IV. Positioning & Differentiation"),
        ("BODY", "Five competitive advantages: (1) Faster Installation: 5-7 days vs. 2-4 weeks. (2) Better Design: Aesthetic-first, flush-mounted, concealed wiring. (3) App Integration: Single-app control, Google Home, HomeKit, Alexa. (4) Customer Support: WhatsApp-based, <2 hour response, quarterly health checks. (5) Warranty: 3 years comprehensive vs. industry standard 1 year."),
        ("BODY", "Brand Voice: Confident, premium, approachable. Intelligent living, flawlessly executed."),

        ("SECTION", "V. 3-Phase Marketing Strategy"),
        ("SUB", "Phase 1: Foundation & Pipeline (Days 1-30)"),
        ("BULLET", "Launch premium website (Astryx design system) with services, gallery, WhatsApp CTA."),
        ("BULLET", "Google Business Profile: Doha, Lusail, The Pearl service areas."),
        ("BULLET", "Instagram: 10 seed posts \u2014 moodboards, product shots, before/afters."),
        ("BULLET", "Outreach to 10-15 interior designers + 5 developers via WhatsApp/LinkedIn."),
        ("BULLET", "First 3 projects at strategic discount in exchange for photo/video + testimonial."),
        ("BULLET", "WhatsApp Business: catalog, quick replies, automated greeting."),
        ("SUB", "Phase 2: Social Proof & Partnerships (Days 31-90)"),
        ("BULLET", "3 detailed case studies on website and Instagram."),
        ("BULLET", "Instagram Ads: geofenced Lusail/Pearl/West Bay, QAR 50-100/day."),
        ("BULLET", "Partnership pitch deck for designers: commission, co-branded materials."),
        ("BULLET", "Pursue 1 anchor hotel or serviced apartment project."),
        ("BULLET", "Google Ads: smart home Qatar, villa automation, CCTV Doha."),
        ("BULLET", "5+ Google reviews from completed projects."),
        ("SUB", "Phase 3: Scale & Recurring Revenue (Days 91-180)"),
        ("BULLET", "Scale Google Ads to QAR 200-400/day based on Phase 2 data."),
        ("BULLET", "Maintenance contracts: QAR 300-500/month per installation."),
        ("BULLET", "Exhibit at Project Qatar or similar industry event."),
        ("BULLET", "Partner with major developer for pre-installed packages in new compounds."),
        ("BULLET", "Referral program: QAR 1,000-2,000 per successful referral."),
        ("BULLET", "Content marketing: smart home tips, security best practices."),

        ("SECTION", "VI. Channel Strategy"),
        ("SUB", "Website (Astryx)"),
        ("BODY", "Central credibility hub. <2s load, WhatsApp prominent, project gallery, service packages. SEO-optimized for Qatar keywords."),
        ("SUB", "Instagram"),
        ("BODY", "Three pillars: project spotlights, educational carousels, lifestyle reels. Stories for daily engagement, Reels for reach."),
        ("SUB", "Google Business Profile"),
        ("BODY", "Local SEO anchor. Complete every field, weekly posts, active reviews. Service areas across greater Doha."),
        ("SUB", "WhatsApp Business"),
        ("BODY", "Primary conversion channel. Catalog with packages. Quick replies. Automated greeting. Qatar transacts here."),
        ("SUB", "LinkedIn"),
        ("BODY", "B2B for hotel/developer partnerships. Case studies. Direct outreach to facility managers."),
        ("SUB", "Google Ads"),
        ("BODY", "Phase 2 launch. QAR 100-200/day, scaling to 300-400. Keywords: smart home Qatar, villa automation, CCTV Doha."),
        ("SUB", "Referral Program"),
        ("BODY", "Highest-converting long-term. Each client generates 2-3 referrals in Qatar\u2019s luxury market."),
        ("SUB", "Partnerships (Designers)"),
        ("BODY", "Highest-leverage channel. A designer specifying your system brings the client pre-sold."),

        ("SECTION", "VII. 90-Day Milestones"),
        ("BULLET", "Week 1: Website live. GBP active. Instagram seeded."),
        ("BULLET", "Week 2: First 5 designer meetings. WhatsApp Business configured."),
        ("BULLET", "Week 3: First installation in progress. Photography arranged."),
        ("BULLET", "Week 4: Case study #1 published. 3 Google reviews."),
        ("BULLET", "Week 6: Instagram Ads launched. Partnership collateral ready."),
        ("BULLET", "Week 8: Case studies #2-3 published. 2 partner agreements signed."),
        ("BULLET", "Week 10: Google Ads launched. Maintenance contract template ready."),
        ("BULLET", "Week 12: Anchor hotel project secured. 10+ Google reviews."),

        ("SECTION", "VIII. Key Performance Indicators"),
        ("BODY", "Four dimensions: (1) Digital Presence: traffic, GBP clicks, Instagram reach, SERP ranking. (2) Engagement: WhatsApp inquiry rate, saves/shares, time-on-page. (3) Pipeline: qualified leads/mo, close rate, avg. project value. (4) Revenue: monthly revenue, CAC, LTV, maintenance attach rate."),
        ("BODY", "Phase 3 Targets: 3-5 projects/month, QAR 200K+/mo revenue, <30 day install cycle, 4.8+ stars, 3+ partner agreements."),

        ("SECTION", "IX. Immediate Next Steps"),
        ("BULLET", "Confirm company name, logo, brand colors, and tagline."),
        ("BULLET", "Provide 5-10 product/brand photos for website and Instagram."),
        ("BULLET", "Identify first 3 pilot project clients (discounted in exchange for materials)."),
        ("BULLET", "Compile list of 15 target interior designers and 5 developers."),
        ("BULLET", "Check social handle availability across platforms."),
    ]

    # Build pdfme template with positioned text fields
    PAGE_W = 210
    PAGE_H = 297
    LM = 15
    COL_W = 180

    schemas = []
    inputs_data = {}
    y = 10

    def add_text(name, text, y_pos, size=10, bold=False, color=None, align="left", w=180, h=8):
        s = {
            "name": name,
            "type": "text",
            "position": {"x": LM, "y": y_pos},
            "width": w,
            "height": h,
            "fontSize": size,
            "alignment": align,
        }
        if bold:
            s["bold"] = True
        if color:
            s["fontColor"] = color
        return s

    # Cover page
    cover_schemas = []
    cover_schemas.append(add_text("cover_company", parsed.company, 100, size=14, bold=False, color="#dfe6e9", align="center"))
    cover_schemas.append(add_text("cover_title", "MARKETING STRATEGY", 120, size=28, bold=True, color="#ffffff", align="center", h=14))
    cover_schemas.append(add_text("cover_subtitle", subtitle, 140, size=12, color="#dfe6e9", align="center"))
    cover_schemas.append(add_text("cover_prepared", prepared, 180, size=9, color="#b2bec3", align="center"))
    cover_schemas.append(add_text("cover_date", today, 190, size=9, color="#b2bec3", align="center"))
    cover_schemas.append(add_text("cover_class", "Confidential", 200, size=9, color="#b2bec3", align="center"))
    schemas.append(cover_schemas)
    inputs_data["cover_company"] = parsed.company
    inputs_data["cover_title"] = "MARKETING STRATEGY"
    inputs_data["cover_subtitle"] = subtitle
    inputs_data["cover_prepared"] = prepared
    inputs_data["cover_date"] = today
    inputs_data["cover_class"] = "Confidential"

    # Content pages
    page_schemas = []
    y = 15
    for i, item in enumerate(content):
        typ = item[0]
        text = item[1]
        name = f"item_{i}"

        if typ == "SECTION":
            y += 5
            page_schemas.append(add_text(name, text, y, size=16, bold=True, color="#1a1a2e", h=10))
            inputs_data[name] = text
            y += 14
        elif typ == "SUB":
            y += 3
            page_schemas.append(add_text(name, text, y, size=12, bold=True, color="#1a1a2e", h=8))
            inputs_data[name] = text
            y += 10
        elif typ == "BODY":
            page_schemas.append(add_text(name, text, y, size=9, h=22))
            inputs_data[name] = text
            y += 24
        elif typ == "BULLET":
            page_schemas.append(add_text(name, f"\u2022 {text}", y, size=9, h=10))
            inputs_data[name] = f"\u2022 {text}"
            y += 11

        if y > 270:
            schemas.append(page_schemas)
            page_schemas = []
            y = 15

    if page_schemas:
        schemas.append(page_schemas)

    # Build cover page with dark background
    cover_template = {
        "basePdf": {
            "width": PAGE_W,
            "height": PAGE_H,
            "padding": [0, 0, 0, 0],
            "backgroundColor": "#1a1a2e"
        },
        "schemas": [cover_schemas]
    }

    # Build content pages
    content_template = {
        "basePdf": {
            "width": PAGE_W,
            "height": PAGE_H,
            "padding": [15, 15, 15, 15],
            "backgroundColor": "#ffffff"
        },
        "schemas": schemas if len(schemas) > 1 else [page_schemas]
    }

    # Use content template (cover is first page already)
    template = content_template

    job = {
        "template": template,
        "inputs": [inputs_data]
    }

    job_file = WORK_DIR / "_pdfme_strategy_job.json"
    with open(job_file, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2)

    gen_args = [str(job_file), "-o", parsed.output]
    if parsed.verbose:
        gen_args.append("-v")

    cmd_generate(gen_args)
    os.remove(job_file)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "list": cmd_list,
        "validate": cmd_validate,
        "doctor": cmd_doctor,
        "generate": cmd_generate,
        "quote": cmd_quote,
        "strategy": cmd_strategy,
    }

    if command in commands:
        commands[command](args)
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
