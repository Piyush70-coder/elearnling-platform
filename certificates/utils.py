import os
import uuid
from datetime import datetime
from django.conf import settings
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas

def generate_certificate_pdf(certificate):
    """Generate a PDF certificate for a completed course"""
    # Create directory if it doesn't exist
    certificates_dir = os.path.join(settings.MEDIA_ROOT, 'certificates')
    os.makedirs(certificates_dir, exist_ok=True)
    
    # Generate a unique filename
    filename = f"{certificate.user.username}_{certificate.course.id}_{uuid.uuid4().hex}.pdf"
    filepath = os.path.join(certificates_dir, filename)
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        filepath,
        pagesize=landscape(letter),
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CertificateTitle',
        fontName='Helvetica-Bold',
        fontSize=24,
        alignment=1,  # Center alignment
        spaceAfter=20
    ))
    styles.add(ParagraphStyle(
        name='CertificateSubtitle',
        fontName='Helvetica-Bold',
        fontSize=18,
        alignment=1,
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name='CertificateText',
        fontName='Helvetica',
        fontSize=14,
        alignment=1,
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name='CertificateFooter',
        fontName='Helvetica-Italic',
        fontSize=10,
        alignment=1,
        textColor=colors.gray
    ))
    
    # Build the certificate content
    elements = []
    
    # Add university logo if available
    logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'university_logo.png')
    if os.path.exists(logo_path):
        img = Image(logo_path, width=200, height=100)
        img.hAlign = 'CENTER'
        elements.append(img)
        elements.append(Spacer(1, 20))
    
    # Certificate title
    elements.append(Paragraph("Certificate of Completion", styles['CertificateTitle']))
    elements.append(Spacer(1, 30))
    
    # Certificate text
    elements.append(Paragraph("This is to certify that", styles['CertificateText']))
    elements.append(Spacer(1, 10))
    
    # Student name
    student_name = f"{certificate.user.first_name} {certificate.user.last_name}" if certificate.user.first_name else certificate.user.username
    elements.append(Paragraph(f"<b>{student_name}</b>", styles['CertificateSubtitle']))
    elements.append(Spacer(1, 20))
    
    # Course completion text
    elements.append(Paragraph("has successfully completed the course", styles['CertificateText']))
    elements.append(Spacer(1, 10))
    
    # Course name
    elements.append(Paragraph(f"<b>{certificate.course.title}</b>", styles['CertificateSubtitle']))
    elements.append(Spacer(1, 30))
    
    # Date and instructor
    issue_date = certificate.issue_date.strftime("%B %d, %Y")
    elements.append(Paragraph(f"Issued on {issue_date}", styles['CertificateText']))
    elements.append(Spacer(1, 10))
    
    instructor_name = f"{certificate.course.instructor.first_name} {certificate.course.instructor.last_name}" if certificate.course.instructor.first_name else certificate.course.instructor.username
    elements.append(Paragraph(f"Instructor: {instructor_name}", styles['CertificateText']))
    elements.append(Spacer(1, 40))
    
    # Verification info
    elements.append(Paragraph(f"Certificate ID: {certificate.id}", styles['CertificateFooter']))
    elements.append(Spacer(1, 5))
    verification_url = f"{settings.SITE_URL}/certificates/verify/{certificate.id}/"
    elements.append(Paragraph(f"Verify at: {verification_url}", styles['CertificateFooter']))
    
    # Build the PDF
    doc.build(elements)
    
    return filepath