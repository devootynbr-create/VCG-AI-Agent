import fitz  # PyMuPDF

# Define the contents for the synthetic documents
documents = [
    {
        "filename": "VCG_Automotive_Case_Study.pdf",
        "content": (
            "VCG CASE STUDY: AUTOMOTIVE SECTOR\n\n"
            "Client: Automotive Manufacturer A\n\n"
            "Challenge:\n"
            "Inventory costs increased by 18%.\n\n"
            "VCG Intervention:\n"
            "Supply-chain redesign, supplier segmentation, inventory analytics.\n\n"
            "Outcome:\n"
            "Inventory reduced by 12%."
        )
    },
    {
        "filename": "VCG_Retail_Digital_Transformation.pdf",
        "content": (
            "VCG CASE STUDY: RETAIL & E-COMMERCE\n\n"
            "Client: National Retail Chain B\n\n"
            "Challenge:\n"
            "Customer acquisition costs rose by 25% due to inefficient digital channels.\n\n"
            "VCG Intervention:\n"
            "Omnichannel integration, personalized marketing automation, and dynamic pricing models.\n\n"
            "Outcome:\n"
            "Conversion rates increased by 15% and acquisition costs dropped by 20%."
        )
    },
    {
        "filename": "VCG_Banking_Risk_Management.pdf",
        "content": (
            "VCG CASE STUDY: FINANCIAL SERVICES\n\n"
            "Client: Commercial Bank C\n\n"
            "Challenge:\n"
            "Manual credit assessment workflows led to slow loan processing times.\n\n"
            "VCG Intervention:\n"
            "Automated credit scoring algorithm deployment and core workflow streamlining.\n\n"
            "Outcome:\n"
            "Turnaround time reduced by 40% with zero compromise on compliance."
        )
    },
    {
        "filename": "VCG_Healthcare_Operational_Efficiency.pdf",
        "content": (
            "VCG CASE STUDY: HEALTHCARE\n\n"
            "Client: Regional Hospital Network D\n\n"
            "Challenge:\n"
            "High patient wait times and low bed utilization rates.\n\n"
            "VCG Intervention:\n"
            "Capacity planning modeling, resource scheduling optimization, and digital patient intake.\n\n"
            "Outcome:\n"
            "Patient throughput improved by 22% and bed utilization optimized."
        )
    },
    {
        "filename": "VCG_Energy_Sustainability_Framework.pdf",
        "content": (
            "VCG CASE STUDY: ENERGY & UTILITIES\n\n"
            "Client: Utility Provider E\n\n"
            "Challenge:\n"
            "Strict regulatory mandates for carbon emissions reduction.\n\n"
            "VCG Intervention:\n"
            "Decarbonization roadmap development, renewable energy sourcing strategy, and waste reduction.\n\n"
            "Outcome:\n"
            "Achieved a 30% reduction in carbon footprint across core assets."
        )
    }
]

# Generate each PDF
for doc_info in documents:
    doc = fitz.open()
    page = doc.new_page()
    
    # Write text onto page
    text = doc_info["content"]
    page.insert_text((50, 50), text, fontsize=12)
    
    # Save PDF
    doc.save(doc_info["filename"])
    doc.close()
    print(f"Created {doc_info['filename']}")

print("\nAll 5 PDFs created successfully!")