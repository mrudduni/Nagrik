"""
create_mock_extraction.py
--------------------------
Creates a small mock extracted.jsonl (10 records) for testing
load_graph.py and embed.py WITHOUT needing the Gemini API.

Run this instead of extract.py when you want to test the Neo4j
ingestion and embedding pipeline with sample data.
"""
import json
import pathlib

MOCK_RECORDS = [
    {
        "_scheme_id": "pm-kisan",
        "_slug": "pm-kisan",
        "scheme_name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "department": "Department of Agriculture & Farmers Welfare",
        "summary": "Direct income support of Rs. 6000 per year to small and marginal farmers with landholding up to 2 hectares, paid in three equal installments.",
        "eligibility_rules": [
            {"field": "occupation", "operator": "eq", "value": "farmer"},
            {"field": "income_annual", "operator": "lte", "value": "200000"},
        ],
        "required_documents": ["Aadhaar Card", "Land Records", "Bank Account Passbook"],
        "beneficiary_categories": ["Farmers", "Small Farmers", "Marginal Farmers"],
        "applicable_states": ["All India"],
        "source_url": "https://www.myscheme.gov.in/schemes/pm-kisan",
    },
    {
        "_scheme_id": "sc-scholarship",
        "_slug": "sc-scholarship",
        "scheme_name": "Post Matric Scholarship for SC Students",
        "ministry": "Ministry of Social Justice and Empowerment",
        "department": "Department of Social Justice and Empowerment",
        "summary": "Financial assistance to SC students pursuing post-matriculation courses including professional and technical education.",
        "eligibility_rules": [
            {"field": "category", "operator": "eq", "value": "SC"},
            {"field": "income_annual", "operator": "lte", "value": "250000"},
            {"field": "occupation", "operator": "eq", "value": "student"},
        ],
        "required_documents": ["Caste Certificate", "Income Certificate", "Marksheet", "Aadhaar Card"],
        "beneficiary_categories": ["SC", "Students"],
        "applicable_states": ["All India"],
        "source_url": "https://www.myscheme.gov.in/schemes/sc-scholarship",
    },
    {
        "_scheme_id": "mudra-loan",
        "_slug": "mudra-loan",
        "scheme_name": "Pradhan Mantri MUDRA Yojana",
        "ministry": "Ministry of Finance",
        "department": "Department of Financial Services",
        "summary": "Provides loans up to Rs. 10 lakh to non-corporate, non-farm small/micro enterprises through three categories: Shishu, Kishor, and Tarun.",
        "eligibility_rules": [
            {"field": "occupation", "operator": "in", "value": "entrepreneur|business owner|self-employed"},
            {"field": "income_annual", "operator": "lte", "value": "1000000"},
        ],
        "required_documents": ["Business Plan", "Aadhaar Card", "Bank Statement", "Identity Proof"],
        "beneficiary_categories": ["Entrepreneurs", "Small Business Owners", "Women Entrepreneurs"],
        "applicable_states": ["All India"],
        "source_url": "https://www.myscheme.gov.in/schemes/mudra-loan",
    },
    {
        "_scheme_id": "widow-pension",
        "_slug": "widow-pension",
        "scheme_name": "National Family Benefit Scheme - Widow Pension",
        "ministry": "Ministry of Rural Development",
        "department": "Department of Rural Development",
        "summary": "Monthly pension support for widows aged 18-59 from BPL families, providing financial security to bereaved women.",
        "eligibility_rules": [
            {"field": "gender", "operator": "eq", "value": "female"},
            {"field": "marital_status", "operator": "eq", "value": "widowed"},
            {"field": "age", "operator": "gte", "value": "18"},
            {"field": "age", "operator": "lte", "value": "59"},
            {"field": "income_annual", "operator": "lte", "value": "100000"},
        ],
        "required_documents": ["Husband Death Certificate", "Aadhaar Card", "BPL Card", "Bank Passbook"],
        "beneficiary_categories": ["Women", "Widows", "BPL Families"],
        "applicable_states": ["All India"],
        "source_url": "https://www.myscheme.gov.in/schemes/widow-pension",
    },
    {
        "_scheme_id": "esic-health",
        "_slug": "esic-health",
        "scheme_name": "Employees State Insurance Scheme (ESIC)",
        "ministry": "Ministry of Labour and Employment",
        "department": "Employees State Insurance Corporation",
        "summary": "Comprehensive social security for workers in organised sector, covering medical care, sickness, maternity, and employment injury benefits.",
        "eligibility_rules": [
            {"field": "occupation", "operator": "in", "value": "labourer|worker|employee"},
            {"field": "income_annual", "operator": "lte", "value": "252000"},
        ],
        "required_documents": ["ESI Card", "Employment Certificate", "Aadhaar Card"],
        "beneficiary_categories": ["Workers", "Labourers", "Factory Employees"],
        "applicable_states": ["All India"],
        "source_url": "https://www.myscheme.gov.in/schemes/esic-health",
    },
    {
        "_scheme_id": "st-tribal-dev",
        "_slug": "st-tribal-dev",
        "scheme_name": "Eklavya Model Residential Schools for ST Students",
        "ministry": "Ministry of Tribal Affairs",
        "department": "Department of Tribal Affairs",
        "summary": "High quality education to tribal students in remote areas through residential schools with facilities at par with Navodaya Vidyalayas.",
        "eligibility_rules": [
            {"field": "category", "operator": "eq", "value": "ST"},
            {"field": "age", "operator": "lte", "value": "18"},
            {"field": "occupation", "operator": "eq", "value": "student"},
        ],
        "required_documents": ["Caste Certificate", "Birth Certificate", "Transfer Certificate"],
        "beneficiary_categories": ["ST", "Students", "Tribal Children"],
        "applicable_states": ["All India"],
        "source_url": "https://www.myscheme.gov.in/schemes/st-tribal-dev",
    },
    {
        "_scheme_id": "disability-pension",
        "_slug": "disability-pension",
        "scheme_name": "Indira Gandhi National Disability Pension Scheme",
        "ministry": "Ministry of Rural Development",
        "department": "Department of Rural Development",
        "summary": "Monthly pension of Rs. 300-500 for persons with severe/multiple disabilities aged 18-79 from BPL households.",
        "eligibility_rules": [
            {"field": "disability", "operator": "eq", "value": "True"},
            {"field": "age", "operator": "gte", "value": "18"},
            {"field": "age", "operator": "lte", "value": "79"},
            {"field": "income_annual", "operator": "lte", "value": "80000"},
        ],
        "required_documents": ["Disability Certificate", "BPL Card", "Aadhaar Card", "Bank Passbook"],
        "beneficiary_categories": ["Disabled Persons", "BPL Families"],
        "applicable_states": ["All India"],
        "source_url": "https://www.myscheme.gov.in/schemes/disability-pension",
    },
    {
        "_scheme_id": "rajasthan-farmer-loan",
        "_slug": "rajasthan-farmer-loan",
        "scheme_name": "Rajasthan Kisan Karj Mafi Yojana",
        "ministry": "Unknown Ministry",
        "department": "Rajasthan Agriculture Department",
        "summary": "Loan waiver scheme for small and marginal farmers in Rajasthan who have outstanding agricultural loans up to Rs. 2 lakh.",
        "eligibility_rules": [
            {"field": "residence_state", "operator": "eq", "value": "Rajasthan"},
            {"field": "occupation", "operator": "eq", "value": "farmer"},
            {"field": "income_annual", "operator": "lte", "value": "150000"},
        ],
        "required_documents": ["Land Records", "Loan Certificate", "Aadhaar Card", "Bank Passbook"],
        "beneficiary_categories": ["Farmers", "Small Farmers"],
        "applicable_states": ["Rajasthan"],
        "source_url": "https://www.myscheme.gov.in/schemes/rajasthan-farmer-loan",
    },
    {
        "_scheme_id": "obc-scholarship",
        "_slug": "obc-scholarship",
        "scheme_name": "Post Matric Scholarship for OBC Students",
        "ministry": "Ministry of Social Justice and Empowerment",
        "department": "Department of Social Justice and Empowerment",
        "summary": "Scholarship for OBC students pursuing post-matriculation education to support academic advancement of backward classes.",
        "eligibility_rules": [
            {"field": "category", "operator": "eq", "value": "OBC"},
            {"field": "income_annual", "operator": "lte", "value": "100000"},
            {"field": "occupation", "operator": "eq", "value": "student"},
        ],
        "required_documents": ["OBC Certificate", "Income Certificate", "Marksheet", "Aadhaar Card"],
        "beneficiary_categories": ["OBC", "Students"],
        "applicable_states": ["All India"],
        "source_url": "https://www.myscheme.gov.in/schemes/obc-scholarship",
    },
    {
        "_scheme_id": "construction-worker-health",
        "_slug": "construction-worker-health",
        "scheme_name": "Construction Workers Health Insurance Scheme",
        "ministry": "Ministry of Labour and Employment",
        "department": "Building and Other Construction Workers Welfare Board",
        "summary": "Health insurance coverage for registered building and construction workers and their families, covering hospitalization and accident benefits.",
        "eligibility_rules": [
            {"field": "occupation", "operator": "in", "value": "labourer|construction worker|building worker"},
            {"field": "age", "operator": "gte", "value": "18"},
            {"field": "age", "operator": "lte", "value": "60"},
        ],
        "required_documents": ["Labour Card", "Aadhaar Card", "Bank Account Details", "Passport Photo"],
        "beneficiary_categories": ["Construction Workers", "Labourers", "Building Workers"],
        "applicable_states": ["All India"],
        "source_url": "https://www.myscheme.gov.in/schemes/construction-worker-health",
    },
]

out = pathlib.Path("ingestion/data/extracted.jsonl")
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    for rec in MOCK_RECORDS:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"Created mock extraction with {len(MOCK_RECORDS)} records -> {out}")
print("These 10 schemes cover: SC/ST/OBC scholars, farmers, widows, disabled persons,")
print("construction workers, entrepreneurs — matching all 5 test profiles in test_search.py")
