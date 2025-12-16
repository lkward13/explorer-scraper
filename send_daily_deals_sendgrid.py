#!/usr/bin/env python3
"""
Daily Deal Email Sender - SendGrid Version

Uses SendGrid API instead of SMTP (works on DigitalOcean where SMTP is blocked)
"""
import os
from typing import List, Dict
import argparse

from deal_selector import DealSelector
from email_builder import EmailBuilder
from database.config import get_connection_string

# Try to import SendGrid
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("⚠️  SendGrid not installed. Install with: pip3 install sendgrid")


class SendGridEmailSender:
    """Send emails via SendGrid API."""
    
    def __init__(self, api_key: str):
        """
        Initialize SendGrid email sender.
        
        Args:
            api_key: SendGrid API key
        """
        if not SENDGRID_AVAILABLE:
            raise ImportError("SendGrid library not installed. Run: pip3 install sendgrid")
        
        self.api_key = api_key
        self.client = SendGridAPIClient(api_key)
    
    def send_email(self, to: str, subject: str, html: str, text: str, from_email: str):
        """
        Send a single email via SendGrid.
        
        Args:
            to: Recipient email
            subject: Email subject
            html: HTML body
            text: Plain text body
            from_email: Sender email (must be verified in SendGrid)
        """
        message = Mail(
            from_email=from_email,
            to_emails=to,
            subject=subject,
            plain_text_content=text,
            html_content=html
        )
        
        response = self.client.send(message)
        
        if response.status_code not in [200, 201, 202]:
            raise Exception(f"SendGrid error: {response.status_code} - {response.body}")
    
    def send_batch(self, emails: List[Dict], to: str, from_email: str):
        """
        Send multiple emails to the same recipient.
        
        Args:
            emails: List of email dicts with 'subject', 'html', 'text'
            to: Recipient email
            from_email: Sender email
        """
        for email in emails:
            self.send_email(
                to=to,
                subject=email['subject'],
                html=email['html'],
                text=email['text'],
                from_email=from_email
            )


def send_daily_deals(
    recipient_email: str,
    from_email: str,
    sendgrid_api_key: str,
    num_deals: int = 50,
    min_quality: int = 70
):
    """
    Complete pipeline: select deals, build email, send via SendGrid.
    
    Args:
        recipient_email: Where to send the email
        from_email: Sender email (must be verified in SendGrid)
        sendgrid_api_key: SendGrid API key
        num_deals: Number of deals to include
        min_quality: Minimum quality score (0-100)
    """
    print("=" * 80)
    print("DAILY FLIGHT DEALS EMAIL (SendGrid)")
    print("=" * 80)
    print()
    
    # 1. Select deals
    print("[1/3] Selecting deals...")
    selector = DealSelector(get_connection_string())
    
    deals = selector.select_deals_simple(
        origins=None,  # All origins
        cooldown_days=7,
        limit=num_deals
    )
    
    if not deals:
        print("  ⚠️  No deals found")
        return
    
    print(f"  ✅ Selected {len(deals)} deals")
    print()
    
    # 2. Build email
    print("[2/3] Building email...")
    builder = EmailBuilder()
    subject, html, text = builder.build_digest_email(deals)
    print(f"  ✅ Built email: {subject}")
    print()
    
    # 3. Send via SendGrid
    print(f"[3/3] Sending email to {recipient_email} via SendGrid...")
    try:
        sender = SendGridEmailSender(sendgrid_api_key)
        sender.send_email(
            to=recipient_email,
            subject=subject,
            html=html,
            text=text,
            from_email=from_email
        )
        print("  ✅ Email sent successfully!")
    except Exception as e:
        print(f"  ❌ Failed to send email: {e}")
        raise
    
    print()
    print("=" * 80)
    print("✅ COMPLETE")
    print("=" * 80)
    print(f"Check your inbox: {recipient_email}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send daily flight deals via SendGrid")
    parser.add_argument("--recipient", help="Recipient email (or set RECIPIENT_EMAIL env var)")
    parser.add_argument("--from-email", help="Sender email (or set FROM_EMAIL env var)")
    parser.add_argument("--api-key", help="SendGrid API key (or set SENDGRID_API_KEY env var)")
    parser.add_argument("--num-deals", type=int, default=50, help="Number of deals to send")
    parser.add_argument("--min-quality", type=int, default=70, help="Minimum quality score")
    
    args = parser.parse_args()
    
    # Get config from args or environment
    recipient = args.recipient or os.getenv("RECIPIENT_EMAIL")
    from_email = args.from_email or os.getenv("FROM_EMAIL") or os.getenv("SMTP_USER")
    api_key = args.api_key or os.getenv("SENDGRID_API_KEY")
    
    if not recipient:
        print("❌ Error: Recipient email required (--recipient or RECIPIENT_EMAIL env var)")
        exit(1)
    
    if not from_email:
        print("❌ Error: Sender email required (--from-email or FROM_EMAIL env var)")
        exit(1)
    
    if not api_key:
        print("❌ Error: SendGrid API key required (--api-key or SENDGRID_API_KEY env var)")
        exit(1)
    
    send_daily_deals(
        recipient_email=recipient,
        from_email=from_email,
        sendgrid_api_key=api_key,
        num_deals=args.num_deals,
        min_quality=args.min_quality
    )

