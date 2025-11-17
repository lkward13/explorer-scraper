#!/usr/bin/env python3
"""
Generate HTML email newsletter from flight deals JSON.

Usage:
    python scripts/generate_newsletter.py --deals deals.json --origin PHX --out newsletter.html
"""

import json
import argparse
from datetime import datetime
from pathlib import Path


NEWSLETTER_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flight Deals from {origin} - {date}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            color: #1e40af;
            font-size: 28px;
        }}
        .header p {{
            margin: 10px 0 0 0;
            color: #6b7280;
            font-size: 14px;
        }}
        .deal-card {{
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            transition: border-color 0.2s;
        }}
        .deal-card:hover {{
            border-color: #2563eb;
        }}
        .deal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .destination {{
            font-size: 22px;
            font-weight: bold;
            color: #1e40af;
            margin: 0;
        }}
        .price {{
            font-size: 32px;
            font-weight: bold;
            color: #059669;
            margin: 0;
        }}
        .price-label {{
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
        }}
        .deal-quality {{
            background-color: #fef3c7;
            color: #92400e;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 10px;
        }}
        .flight-details {{
            background-color: #f9fafb;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
        }}
        .flight-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 14px;
        }}
        .flight-row:last-child {{
            margin-bottom: 0;
        }}
        .flight-label {{
            color: #6b7280;
            font-weight: 500;
        }}
        .flight-value {{
            color: #111827;
            font-weight: 600;
        }}
        .flexibility {{
            background-color: #dbeafe;
            padding: 12px;
            border-radius: 6px;
            margin-top: 15px;
            font-size: 14px;
        }}
        .flexibility strong {{
            color: #1e40af;
        }}
        .cta-button {{
            display: block;
            width: 100%;
            padding: 12px;
            background-color: #2563eb;
            color: white;
            text-align: center;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            margin-top: 15px;
            transition: background-color 0.2s;
        }}
        .cta-button:hover {{
            background-color: #1e40af;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280;
            font-size: 12px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            margin-left: 8px;
        }}
        .badge-nonstop {{
            background-color: #d1fae5;
            color: #065f46;
        }}
        .badge-stops {{
            background-color: #fef3c7;
            color: #92400e;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✈️ This Week's Best Flight Deals</h1>
            <p>From {origin_name} ({origin}) • {date}</p>
        </div>

        {deals_html}

        <div class="footer">
            <p><strong>How we find these deals:</strong></p>
            <p>We scan thousands of flight combinations daily and only show you deals with:<br>
            ✓ 5+ flexible date options within ±10% of the advertised price<br>
            ✓ Real-time pricing from Google Flights<br>
            ✓ Complete flight details (airline, times, stops)</p>
            <p style="margin-top: 20px;">
                <a href="#" style="color: #2563eb;">Unsubscribe</a> • 
                <a href="#" style="color: #2563eb;">Manage Preferences</a>
            </p>
        </div>
    </div>
</body>
</html>
"""

DEAL_CARD_TEMPLATE = """
        <div class="deal-card">
            <div class="deal-header">
                <div>
                    <h2 class="destination">{flag} {destination}</h2>
                </div>
                <div style="text-align: right;">
                    <div class="price-label">Round-trip from</div>
                    <div class="price">${price}</div>
                </div>
            </div>

            {deal_quality_html}

            <div class="flight-details">
                <div class="flight-row">
                    <span class="flight-label">✈️ Airline:</span>
                    <span class="flight-value">{airline} {stops_badge}</span>
                </div>
                <div class="flight-row">
                    <span class="flight-label">⏱️ Flight Time:</span>
                    <span class="flight-value">{duration}</span>
                </div>
                <div class="flight-row">
                    <span class="flight-label">🛫 Departure:</span>
                    <span class="flight-value">{departure_time}</span>
                </div>
                <div class="flight-row">
                    <span class="flight-label">🛬 Arrival:</span>
                    <span class="flight-value">{arrival_time}</span>
                </div>
            </div>

            <div class="flexibility">
                <strong>📅 Flexible Dates:</strong> {similar_count} similar-priced date combinations available within ±10% (${min_price}-${max_price})
            </div>

            <a href="{flights_url}" class="cta-button">
                View Flights on Google →
            </a>
        </div>
"""


def get_country_flag(destination: str) -> str:
    """Get country flag emoji based on destination."""
    # Simple mapping - could be expanded
    flags = {
        'Honduras': '🇭🇳',
        'Costa Rica': '🇨🇷',
        'Panama': '🇵🇦',
        'Nicaragua': '🇳🇮',
        'Guatemala': '🇬🇹',
        'Belize': '🇧🇿',
        'El Salvador': '🇸🇻',
        'Ireland': '🇮🇪',
        'United Kingdom': '🇬🇧',
        'France': '🇫🇷',
        'Spain': '🇪🇸',
        'Italy': '🇮🇹',
        'Germany': '🇩🇪',
        'Mexico': '🇲🇽',
        'Canada': '🇨🇦',
        'United States': '🇺🇸',
    }
    
    for country, flag in flags.items():
        if country.lower() in destination.lower():
            return flag
    
    return '🌍'  # Default globe


def build_flights_url(origin: str, destination: str, start_date: str, end_date: str) -> str:
    """Build Google Flights URL for the deal."""
    # This would use the same protobuf logic from expand_dates.py
    # For now, return a placeholder
    return f"https://www.google.com/travel/flights?q=Flights%20from%20{origin}%20to%20{destination}%20on%20{start_date}%20through%20{end_date}"


def generate_deal_html(deal: dict, origin: str) -> str:
    """Generate HTML for a single deal card."""
    explore = deal['explore_deal']
    expansion = deal['expansion']
    flight_details = expansion.get('flight_details', {})
    
    # Get deal quality HTML
    deal_quality_html = ""
    if expansion.get('deal_quality'):
        deal_quality_html = f"""
            <div class="deal-quality">
                💰 {expansion['deal_quality']}
            </div>
"""
    
    # Get stops badge
    stops = flight_details.get('stops', '?')
    if stops == 0:
        stops_badge = '<span class="badge badge-nonstop">Nonstop</span>'
    elif stops == '?':
        stops_badge = ''
    else:
        stops_badge = f'<span class="badge badge-stops">{stops} Stop{"s" if stops > 1 else ""}</span>'
    
    # Calculate price range
    price_range = expansion.get('price_range', {})
    min_price = price_range.get('min', explore['min_price'])
    max_price = price_range.get('max', explore['min_price'])
    
    # Build flights URL
    flights_url = build_flights_url(
        origin,
        expansion.get('actual_destination') or expansion['destination'],
        expansion['reference_start'],
        expansion['reference_end']
    )
    
    return DEAL_CARD_TEMPLATE.format(
        flag=get_country_flag(explore['destination']),
        destination=explore['destination'],
        price=explore['min_price'],
        deal_quality_html=deal_quality_html,
        airline=flight_details.get('airline', 'Unknown'),
        stops_badge=stops_badge,
        duration=flight_details.get('duration', '?'),
        departure_time=flight_details.get('departure_time', '?'),
        arrival_time=flight_details.get('arrival_time', '?'),
        similar_count=deal['similar_deals_count'],
        min_price=min_price,
        max_price=max_price,
        flights_url=flights_url
    )


def generate_newsletter(deals_data: dict, origin: str, origin_name: str = None) -> str:
    """Generate complete newsletter HTML from deals data."""
    
    # Get flexible deals
    flexible_deals = deals_data.get('flexible_deals', [])
    
    if not flexible_deals:
        return "<p>No flexible deals found this week.</p>"
    
    # Generate HTML for each deal
    deals_html = "\n".join([
        generate_deal_html(deal, origin)
        for deal in flexible_deals
    ])
    
    # Get origin name (could be from a lookup table)
    if not origin_name:
        origin_name = origin
    
    # Format date
    date_str = datetime.now().strftime("%B %d, %Y")
    
    return NEWSLETTER_TEMPLATE.format(
        origin=origin,
        origin_name=origin_name,
        date=date_str,
        deals_html=deals_html
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML email newsletter from flight deals JSON"
    )
    parser.add_argument("--deals", required=True, help="Input JSON file with deals")
    parser.add_argument("--origin", required=True, help="Origin airport code (e.g., PHX)")
    parser.add_argument("--origin-name", help="Origin city name (e.g., 'Phoenix')")
    parser.add_argument("--out", required=True, help="Output HTML file")
    
    args = parser.parse_args()
    
    # Load deals data
    with open(args.deals, 'r') as f:
        deals_data = json.load(f)
    
    # Generate newsletter
    html = generate_newsletter(deals_data, args.origin, args.origin_name)
    
    # Write output
    with open(args.out, 'w') as f:
        f.write(html)
    
    print(f"✅ Newsletter generated: {args.out}")
    print(f"   Deals included: {len(deals_data.get('flexible_deals', []))}")


if __name__ == "__main__":
    main()

