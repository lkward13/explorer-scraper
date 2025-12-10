#!/usr/bin/env python3
"""
Daily Deal Email Sender

Complete pipeline:
1. Select deals (individual + regional)
2. Build emails
3. Send emails
4. Mark as posted
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
import argparse

from deal_selector import DealSelector
from email_builder import EmailBuilder
from database.config import get_connection_string


class EmailSender:
    """Send emails via SMTP."""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        """
        Initialize email sender.
        
        Args:
            smtp_host: SMTP server (e.g., 'smtp.gmail.com')
            smtp_port: SMTP port (e.g., 587 for TLS)
            username: SMTP username
            password: SMTP password or app password
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def send_email(self, to: str, subject: str, html: str, text: str, from_email: str = None):
        """
        Send a single email.
        
        Args:
            to: Recipient email
            subject: Email subject
            html: HTML body
            text: Plain text body
            from_email: Sender email (defaults to username)
        """
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email or self.username
        msg['To'] = to
        
        # Attach both plain text and HTML
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send via SMTP
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
    
    def send_batch(self, emails: List[Dict], to: str, from_email: str = None):
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
            print(f"  ✓ Sent: {email['subject']}")


def send_daily_deals(
    recipient_email: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_pass: str,
    origins: List[str] = None,
    max_price: int = 600,
    min_regional_destinations: int = 3,
    limit_per_origin: int = 5,
    dry_run: bool = False
):
    """
    Complete daily deal pipeline.
    
    Args:
        recipient_email: Email address to send deals to
        smtp_host: SMTP server
        smtp_port: SMTP port
        smtp_user: SMTP username
        smtp_pass: SMTP password
        origins: List of origin airports (None = all)
        max_price: Maximum price threshold
        min_regional_destinations: Min destinations for regional sale
        limit_per_origin: Max destinations per origin
        dry_run: If True, don't send emails or mark as posted
    """
    print("\n" + "="*80)
    print("DAILY DEAL EMAIL PIPELINE")
    print("="*80)
    
    # Step 1: Select deals
    print("\n[1/4] Selecting deals...")
    selector = DealSelector(get_connection_string())
    
    deals = selector.select_daily_deals(
        origins=origins,
        max_price=max_price,
        min_destinations_for_regional=min_regional_destinations,
        limit_per_origin=limit_per_origin
    )
    
    individual_count = len(deals['individual'])
    regional_count = len(deals['regional'])
    total_emails = individual_count + regional_count
    
    print(f"  ✓ Found {individual_count} individual deals")
    print(f"  ✓ Found {regional_count} regional sales")
    print(f"  ✓ Total emails to send: {total_emails}")
    
    if total_emails == 0:
        print("\n⚠️  No deals found. Exiting.")
        selector.close()
        return
    
    # Step 2: Build emails
    print("\n[2/4] Building emails...")
    builder = EmailBuilder()
    emails = []
    
    for deal in deals['individual']:
        email = builder.build_individual_email(deal)
        emails.append(email)
        print(f"  ✓ Individual: {deal['origin']} → {deal['destination']} (${deal['price']})")
    
    for regional in deals['regional']:
        email = builder.build_regional_email(regional)
        emails.append(email)
        print(f"  ✓ Regional: {regional['origin']} → {regional['region_display']} "
              f"({regional['destination_count']} destinations, ${regional['min_price']}-${regional['max_price']})")
    
    # Step 3: Send emails
    if dry_run:
        print("\n[3/4] Sending emails... (DRY RUN - skipped)")
        print(f"  Would send {len(emails)} emails to {recipient_email}")
    else:
        print(f"\n[3/4] Sending emails to {recipient_email}...")
        sender = EmailSender(smtp_host, smtp_port, smtp_user, smtp_pass)
        sender.send_batch(emails, to=recipient_email, from_email=smtp_user)
        print(f"  ✓ Sent {len(emails)} emails")
    
    # Step 4: Mark as posted
    if dry_run:
        print("\n[4/4] Marking deals as posted... (DRY RUN - skipped)")
    else:
        print("\n[4/4] Marking deals as posted...")
        deal_ids = selector.get_deal_ids_from_selection(deals)
        marked = selector.mark_as_posted(deal_ids)
        print(f"  ✓ Marked {marked} deals as posted")
    
    selector.close()
    
    print("\n" + "="*80)
    print("✅ PIPELINE COMPLETE")
    print("="*80)
    print(f"Emails sent: {len(emails)}")
    print(f"Individual deals: {individual_count}")
    print(f"Regional sales: {regional_count}")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Send daily flight deal emails",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run with 5 origins
  python3 send_daily_deals.py --origins DFW,ATL,LAX,ORD,JFK --dry-run
  
  # Send to yourself (test)
  python3 send_daily_deals.py --to your@email.com --origins DFW,ATL --smtp-user your@gmail.com --smtp-pass "app_password"
  
  # Production: All origins
  python3 send_daily_deals.py --to your@email.com --smtp-user your@gmail.com --smtp-pass "app_password"
        """
    )
    
    parser.add_argument('--to', required=True, help='Recipient email address')
    parser.add_argument('--smtp-host', default='smtp.gmail.com', help='SMTP server (default: smtp.gmail.com)')
    parser.add_argument('--smtp-port', type=int, default=587, help='SMTP port (default: 587)')
    parser.add_argument('--smtp-user', required=True, help='SMTP username')
    parser.add_argument('--smtp-pass', required=True, help='SMTP password or app password')
    parser.add_argument('--origins', help='Comma-separated list of origin airports (e.g., DFW,ATL,LAX)')
    parser.add_argument('--max-price', type=int, default=600, help='Maximum price threshold (default: 600)')
    parser.add_argument('--min-regional', type=int, default=3, help='Min destinations for regional sale (default: 3)')
    parser.add_argument('--limit-per-origin', type=int, default=5, help='Max destinations per origin (default: 5)')
    parser.add_argument('--dry-run', action='store_true', help='Test mode: select deals but don\'t send emails')
    
    args = parser.parse_args()
    
    origins = args.origins.split(',') if args.origins else None
    
    send_daily_deals(
        recipient_email=args.to,
        smtp_host=args.smtp_host,
        smtp_port=args.smtp_port,
        smtp_user=args.smtp_user,
        smtp_pass=args.smtp_pass,
        origins=origins,
        max_price=args.max_price,
        min_regional_destinations=args.min_regional,
        limit_per_origin=args.limit_per_origin,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()

