#!/usr/bin/env python3
"""
Send Test Email - Quick test of the email system with quality scoring

This script:
1. Selects top 3 deals using quality scoring
2. Builds beautiful HTML emails
3. Sends them to you for testing

Usage:
    # Using environment variables (from .env file)
    python send_test_email.py
    
    # Or specify credentials directly
    python send_test_email.py --to your@email.com --smtp-user your@gmail.com --smtp-pass "your_app_password"
    
    # Dry run (don't send, just show what would be sent)
    python send_test_email.py --dry-run
"""
import sys
import os
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use environment variables or command line args

from deal_selector import DealSelector
from email_builder import EmailBuilder
from send_daily_deals import EmailSender
from database.config import get_connection_string


def send_test_email(
    recipient_email: str,
    smtp_host: str = 'smtp.gmail.com',
    smtp_port: int = 587,
    smtp_user: str = None,
    smtp_pass: str = None,
    num_deals: int = 3,
    min_quality_score: int = 70,
    dry_run: bool = False
):
    """
    Send a test email with top quality deals.
    
    Args:
        recipient_email: Email address to send to
        smtp_host: SMTP server
        smtp_port: SMTP port
        smtp_user: SMTP username
        smtp_pass: SMTP password
        num_deals: Number of deals to send (default: 3)
        min_quality_score: Minimum quality score (default: 70)
        dry_run: If True, don't actually send email
    """
    print("\n" + "="*80)
    print("FLIGHT DEAL TEST EMAIL")
    print("="*80)
    
    # Step 1: Select top deals using simple price thresholds
    print("\n[1/3] Selecting deals using regional price thresholds...")
    print("  ℹ️  Using simple selection (no historical data required)")
    print("  ℹ️  Thresholds: Caribbean<$350, Europe<$600, Asia<$850, Pacific<$950")
    
    selector = DealSelector(get_connection_string())
    
    # Get origins from most recent scrape (last 48 hours)
    import psycopg2
    conn = psycopg2.connect(get_connection_string())
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT origin 
        FROM expanded_deals 
        WHERE found_at > NOW() - INTERVAL '48 hours'
        ORDER BY origin
    """)
    recent_origins = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    if recent_origins:
        print(f"  ℹ️  Using recently scraped origins: {len(recent_origins)} airports")
        deals = selector.select_deals_simple(
            origins=recent_origins,
            cooldown_days=7,
            limit=num_deals * 10  # Get more than needed
        )
    else:
        print(f"  ⚠️  No recent scrapes found, using all origins")
        deals = selector.select_deals_simple(
            cooldown_days=7,
            limit=num_deals * 10
        )
    
    if not deals:
        print(f"  ❌ No deals found meeting price thresholds")
        print(f"  Tip: Run more scrapes or adjust thresholds")
        selector.close()
        return
    
    print(f"  ✅ Found {len(deals)} deals meeting price thresholds")
    
    # Take top N deals
    top_deals = deals[:num_deals]
    print(f"  ✅ Selecting top {len(top_deals)} deals")
    
    # Show deal details
    print("\n  Top Deals:")
    for i, deal in enumerate(top_deals, 1):
        region = deal.get('search_region', 'unknown')
        threshold = selector.REGION_THRESHOLDS.get(region, 600)
        print(f"    {i}. {deal['origin']} → {deal['destination']}: ${deal['price']}")
        print(f"       Region: {region.title()} | Threshold: ${threshold}")
    
    # Step 2: Build digest email (all deals in one email)
    print("\n[2/3] Building digest email with all deals...")
    builder = EmailBuilder()
    
    email = builder.build_digest_email(top_deals, title="Today's Top Flight Deals")
    print(f"  ✅ Built digest email: {email['subject']}")
    
    # Step 3: Send or show preview
    if dry_run:
        print("\n[3/3] Email Preview (DRY RUN - not sending)")
        print(f"  Would send 1 digest email to: {recipient_email}")
        print(f"  From: {smtp_user or 'not specified'}")
        print(f"\n  Email subject: {email['subject']}")
        
        # Save email as HTML for preview
        preview_file = Path(__file__).parent / 'test_email_preview.html'
        with open(preview_file, 'w') as f:
            f.write(email['html'])
        print(f"\n  ✅ Preview saved to: {preview_file}")
        print(f"  Open in browser to see how it looks!")
        
    else:
        if not smtp_user or not smtp_pass:
            print("\n  ❌ SMTP credentials required for sending")
            print("  Use --smtp-user and --smtp-pass, or use --dry-run for preview")
            selector.close()
            return
        
        print(f"\n[3/3] Sending digest email to {recipient_email}...")
        sender = EmailSender(smtp_host, smtp_port, smtp_user, smtp_pass)
        
        try:
            sender.send_email(
                to=recipient_email,
                subject=email['subject'],
                html=email['html'],
                text=email['text'],
                from_email=smtp_user
            )
            print(f"  ✅ Email sent: {email['subject']}")
        except Exception as e:
            print(f"  ❌ Failed to send email: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n  ✅ Done!")
    
    selector.close()
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80)
    if not dry_run:
        print(f"Check your inbox: {recipient_email}")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Send test email with top quality flight deals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using .env file (easiest)
  python send_test_email.py
  
  # Dry run (preview only, no email sent)
  python send_test_email.py --dry-run
  
  # Override .env with command line
  python send_test_email.py --to luke@example.com --smtp-user luke@gmail.com --smtp-pass "app_password"
  
  # Send 5 deals with lower quality threshold
  python send_test_email.py --num-deals 5 --min-quality 60

Gmail App Password Setup:
  1. Go to: https://myaccount.google.com/apppasswords
  2. Create app password for "Mail"
  3. Use that password (not your regular Gmail password)
  
Setup .env file:
  1. Copy env.example to .env
  2. Fill in your email credentials
  3. Run: python send_test_email.py
        """
    )
    
    # Get defaults from environment variables
    default_to = os.getenv('RECIPIENT_EMAIL')
    default_smtp_user = os.getenv('SMTP_USER')
    default_smtp_pass = os.getenv('SMTP_PASS')
    default_smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    default_smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    parser.add_argument('--to', default=default_to, help='Recipient email address (default: from .env)')
    parser.add_argument('--smtp-host', default=default_smtp_host, help='SMTP server (default: smtp.gmail.com)')
    parser.add_argument('--smtp-port', type=int, default=default_smtp_port, help='SMTP port (default: 587)')
    parser.add_argument('--smtp-user', default=default_smtp_user, help='SMTP username (default: from .env)')
    parser.add_argument('--smtp-pass', default=default_smtp_pass, help='SMTP password (default: from .env)')
    parser.add_argument('--num-deals', type=int, default=3, help='Number of deals to send (default: 3)')
    parser.add_argument('--min-quality', type=int, default=70, help='Minimum quality score (default: 70)')
    parser.add_argument('--dry-run', action='store_true', help='Preview only, don\'t send email')
    
    args = parser.parse_args()
    
    # Validate required fields
    if not args.to:
        parser.error("--to is required (or set RECIPIENT_EMAIL in .env)")
    if not args.dry_run and (not args.smtp_user or not args.smtp_pass):
        parser.error("--smtp-user and --smtp-pass are required for sending (or set in .env), or use --dry-run")
    
    send_test_email(
        recipient_email=args.to,
        smtp_host=args.smtp_host,
        smtp_port=args.smtp_port,
        smtp_user=args.smtp_user,
        smtp_pass=args.smtp_pass,
        num_deals=args.num_deals,
        min_quality_score=args.min_quality,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()

