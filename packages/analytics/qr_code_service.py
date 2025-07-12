#!/usr/bin/env python3
"""
QR Code Service for Company Management
=====================================
Service to generate QR codes for companies and email them
"""

import qrcode
import io
import base64
import json
import logging
from datetime import datetime
from PIL import Image
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from database_connection import read_companies, execute_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QRCodeService:
    def __init__(self):
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.email_from = os.getenv('EMAIL_FROM')
        
        if not self.sendgrid_api_key:
            logger.warning("SENDGRID_API_KEY not found in environment variables")
        if not self.email_from:
            logger.warning("EMAIL_FROM not found in environment variables")

    def get_companies(self, search_term=None):
        """Get companies from database with optional search"""
        try:
            if search_term:
                query = """
                SELECT company_id, name as company_name, primary_contact_email as company_email, 
                       primary_contact_phone as company_phone, location as company_address 
                FROM company 
                WHERE LOWER(name) LIKE LOWER(%(search_term)s) 
                ORDER BY name
                """
                companies = execute_query(query, params={'search_term': f'%{search_term}%'})
            else:
                query = """
                SELECT company_id, name as company_name, primary_contact_email as company_email, 
                       primary_contact_phone as company_phone, location as company_address 
                FROM company 
                ORDER BY name
                """
                companies = execute_query(query)
            
            return companies.to_dict('records') if not companies.empty else []
        except Exception as e:
            logger.error(f"Error fetching companies: {e}")
            return []

    def generate_qr_code(self, company_data):
        """Generate QR code for company data"""
        try:
            # Create QR code data
            qr_data = {
                'company_id': str(company_data.get('company_id', '')),
                'company_name': company_data.get('company_name', ''),
                'company_email': company_data.get('company_email', ''),
                'company_phone': company_data.get('company_phone', ''),
                'company_address': company_data.get('company_address', ''),
                'generated_at': datetime.now().isoformat(),
                'type': 'LISWMC_COMPANY'
            }
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 for web display
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return {
                'success': True,
                'qr_code_base64': img_str,
                'qr_data': qr_data,
                'image': img
            }
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return {'success': False, 'error': str(e)}

    def send_qr_code_email(self, company_data, qr_result):
        """Send QR code to company via email"""
        try:
            if not self.sendgrid_api_key or not self.email_from:
                return {'success': False, 'error': 'Email configuration missing'}
            
            company_email = company_data.get('company_email', '').strip()
            if not company_email:
                return {'success': False, 'error': 'Company email not found'}
            
            # Create email content
            subject = f"QR Code for {company_data.get('company_name', 'Your Company')}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 20px;">
                <h2 style="color: #2c3e50;">LISWMC Company QR Code</h2>
                <p>Dear {company_data.get('company_name', 'Valued Customer')},</p>
                
                <p>Please find attached your company QR code. This code contains your company information and can be used for:</p>
                <ul>
                    <li>Quick identification at waste collection points</li>
                    <li>Streamlined billing processes</li>
                    <li>Digital record keeping</li>
                </ul>
                
                <div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
                    <h3 style="color: #495057;">Company Information:</h3>
                    <p><strong>Company Name:</strong> {company_data.get('company_name', 'N/A')}</p>
                    <p><strong>Company ID:</strong> {company_data.get('company_id', 'N/A')}</p>
                    <p><strong>Email:</strong> {company_data.get('company_email', 'N/A')}</p>
                    <p><strong>Phone:</strong> {company_data.get('company_phone', 'N/A')}</p>
                    <p><strong>Address:</strong> {company_data.get('company_address', 'N/A')}</p>
                </div>
                
                <p>Please save this QR code for your records. If you have any questions, please contact us.</p>
                
                <p>Best regards,<br>
                LISWMC Team</p>
                
                <hr style="margin-top: 30px; border: none; border-top: 1px solid #dee2e6;">
                <p style="font-size: 12px; color: #6c757d;">
                    This is an automated email from Lusaka Integrated Solid Waste Management Company.
                </p>
            </body>
            </html>
            """
            
            # Create attachment
            buffered = io.BytesIO()
            qr_result['image'].save(buffered, format="PNG")
            attachment_data = base64.b64encode(buffered.getvalue()).decode()
            
            attachment = Attachment(
                FileContent(attachment_data),
                FileName(f"{company_data.get('company_name', 'company').replace(' ', '_')}_QR_Code.png"),
                FileType("image/png"),
                Disposition("attachment")
            )
            
            # Create and send email
            message = Mail(
                from_email=self.email_from,
                to_emails=company_email,
                subject=subject,
                html_content=html_content
            )
            message.attachment = attachment
            
            sg = SendGridAPIClient(api_key=self.sendgrid_api_key)
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"QR code email sent successfully to {company_email}")
                return {
                    'success': True,
                    'message': f'QR code sent successfully to {company_email}',
                    'status_code': response.status_code
                }
            else:
                logger.error(f"Failed to send email. Status code: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Email sending failed with status code: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error sending QR code email: {e}")
            return {'success': False, 'error': str(e)}

    def get_company_by_id(self, company_id):
        """Get specific company by ID"""
        try:
            query = """
            SELECT company_id, name as company_name, primary_contact_email as company_email, 
                   primary_contact_phone as company_phone, location as company_address 
            FROM company 
            WHERE company_id = %(company_id)s
            """
            result = execute_query(query, params={'company_id': company_id})
            
            if not result.empty:
                return result.iloc[0].to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Error fetching company by ID {company_id}: {e}")
            return None

# Initialize service instance
qr_service = QRCodeService()