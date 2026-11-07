import fitz
from pathlib import Path

sample_dir = Path("../sample_test_documents")
sample_dir.mkdir(exist_ok=True)

# 1. Blank Template Form
doc_tpl = fitz.open()
page = doc_tpl.new_page(width=595, height=842)
page.insert_text(fitz.Point(50, 60), "EMPLOYEE ONBOARDING & VERIFICATION FORM", fontsize=16, fontname="helv", color=(0.1, 0.2, 0.5))
page.insert_text(fitz.Point(50, 90), "Please fill in all mandatory information marked with (*).", fontsize=10, fontname="helv")

labels = [
    "Full Legal Name: ____________________________________",
    "Date of Birth: _______________________________________",
    "Gender: [  ] Male    [  ] Female    [  ] Other",
    "Email Address: _______________________________________",
    "Phone Number: ________________________________________",
    "Residential Address: _________________________________",
    "Postal Code: _________________________________________",
    "Permanent Account Number (PAN): ______________________",
    "Annual Gross Compensation: ___________________________",
    "Bank Account Number: _________________________________",
    "Bank IFSC Code: ______________________________________",
]

y = 140
for l in labels:
    page.insert_text(fitz.Point(50, y), l, fontsize=11, fontname="helv")
    y += 45

doc_tpl.save(str(sample_dir / "blank_onboarding_form.pdf"))
doc_tpl.close()

# 2. Supporting Document: Identity Proof
doc_id = fitz.open()
p_id = doc_id.new_page(width=595, height=842)
p_id.insert_text(fitz.Point(50, 70), "NATIONAL IDENTITY & TAX REGISTRY CARD", fontsize=14, fontname="helv", color=(0.2, 0.2, 0.2))
p_id.insert_text(fitz.Point(50, 110), "Full Name: David Miller", fontsize=12, fontname="helv")
p_id.insert_text(fitz.Point(50, 140), "Date of Birth: 1993-06-18", fontsize=12, fontname="helv")
p_id.insert_text(fitz.Point(50, 170), "Gender: Male", fontsize=12, fontname="helv")
p_id.insert_text(fitz.Point(50, 200), "PAN Number: ABCDE5678K", fontsize=12, fontname="helv")
p_id.insert_text(fitz.Point(50, 230), "Permanent Address: 742 Evergreen Terrace, Springfield", fontsize=12, fontname="helv")
p_id.insert_text(fitz.Point(50, 260), "Postal Code: 560001", fontsize=12, fontname="helv")
doc_id.save(str(sample_dir / "david_identity_card.pdf"))
doc_id.close()

# 3. Supporting Document: Salary Slip
doc_sal = fitz.open()
p_sal = doc_sal.new_page(width=595, height=842)
p_sal.insert_text(fitz.Point(50, 70), "APEX TECHNOLOGIES - MONTHLY SALARY STATEMENT", fontsize=14, fontname="helv", color=(0.1, 0.4, 0.2))
p_sal.insert_text(fitz.Point(50, 110), "Employee Name: David Miller", fontsize=12, fontname="helv")
p_sal.insert_text(fitz.Point(50, 140), "Email: david.miller@apextech.com", fontsize=12, fontname="helv")
p_sal.insert_text(fitz.Point(50, 170), "Contact Phone: 9876543210", fontsize=12, fontname="helv")
p_sal.insert_text(fitz.Point(50, 200), "Gross Annual Compensation: INR 9,50,000", fontsize=12, fontname="helv")
p_sal.insert_text(fitz.Point(50, 230), "Salary Credit Bank Account No: 109284759281", fontsize=12, fontname="helv")
doc_sal.save(str(sample_dir / "david_salary_slip.pdf"))
doc_sal.close()

print("Sample documents created successfully in sample_test_documents/!")
