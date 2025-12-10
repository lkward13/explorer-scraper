#!/usr/bin/env python3
"""
Email Builder for Flight Deal Notifications

Generates HTML emails for:
1. Individual deals (single destination)
2. Regional sales (multiple destinations in same region)
"""
from typing import Dict, List
from datetime import datetime


class EmailBuilder:
    """Build HTML emails for flight deals."""
    
    def __init__(self, from_email: str = "deals@flightdeals.com"):
        """
        Initialize email builder.
        
        Args:
            from_email: Sender email address
        """
        self.from_email = from_email
    
    def build_individual_email(self, deal: Dict) -> Dict[str, str]:
        """
        Build email for a single destination deal.
        
        Args:
            deal: Deal dict with origin, destination, price, etc.
            
        Returns:
            {
                'subject': 'Email subject',
                'html': 'HTML body',
                'text': 'Plain text body'
            }
        """
        origin = deal['origin']
        destination = deal['destination']
        city = deal.get('destination_city') or destination
        price = deal['price']
        outbound = deal['outbound_date']
        return_date = deal['return_date']
        url = deal['google_flights_url']
        
        subject = f"✈️ {origin} to {city} - ${price} Round Trip"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .deal-box {{ background: #f8f9fa; padding: 25px; border-radius: 0 0 10px 10px; }}
                .price {{ font-size: 48px; font-weight: bold; color: #667eea; margin: 20px 0; }}
                .route {{ font-size: 24px; margin: 15px 0; }}
                .dates {{ font-size: 18px; color: #666; margin: 15px 0; }}
                .button {{ display: inline-block; background: #667eea; color: white; 
                          padding: 15px 40px; text-decoration: none; border-radius: 5px; 
                          font-size: 18px; font-weight: bold; margin: 20px 0; }}
                .button:hover {{ background: #5568d3; }}
                .footer {{ text-align: center; margin-top: 30px; color: #999; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Great Deal Alert!</h1>
                </div>
                <div class="deal-box">
                    <div class="route">{origin} → {city}</div>
                    <div class="price">${price}</div>
                    <div class="dates">
                        <strong>Outbound:</strong> {outbound}<br>
                        <strong>Return:</strong> {return_date}
                    </div>
                    <div style="text-align: center;">
                        <a href="{url}" class="button">Book Now on Google Flights</a>
                    </div>
                    <p style="margin-top: 20px; font-size: 14px; color: #666;">
                        💡 <strong>Tip:</strong> This deal has {deal.get('similar_date_count', 'multiple')} 
                        similar dates available. Check Google Flights for more options!
                    </p>
                </div>
                <div class="footer">
                    <p>You're receiving this because you subscribed to flight deal alerts.</p>
                    <p>Prices and availability subject to change.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text = f"""
        Great Deal Alert!
        
        Route: {origin} → {city}
        Price: ${price} Round Trip
        
        Dates:
        Outbound: {outbound}
        Return: {return_date}
        
        Book now: {url}
        
        This deal has {deal.get('similar_date_count', 'multiple')} similar dates available.
        
        ---
        You're receiving this because you subscribed to flight deal alerts.
        Prices and availability subject to change.
        """
        
        return {
            'subject': subject,
            'html': html.strip(),
            'text': text.strip()
        }
    
    def build_regional_email(self, regional_deal: Dict) -> Dict[str, str]:
        """
        Build email for a regional sale (multiple destinations).
        
        Args:
            regional_deal: Regional deal dict from DealSelector
            
        Returns:
            {
                'subject': 'Email subject',
                'html': 'HTML body',
                'text': 'Plain text body'
            }
        """
        origin = regional_deal['origin']
        region = regional_deal['region_display']
        min_price = regional_deal['min_price']
        max_price = regional_deal['max_price']
        dest_count = regional_deal['destination_count']
        destinations = regional_deal['destinations']
        
        subject = f"✈️ {region} on Sale from {origin} - Starting at ${min_price}"
        
        # Build destination list HTML
        dest_html = ""
        dest_text = ""
        for dest in destinations:
            city = dest.get('destination_city') or dest['destination']
            price = dest['price']
            url = dest['google_flights_url']
            
            dest_html += f"""
            <div style="margin: 15px 0; padding: 15px; background: white; border-radius: 5px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="font-size: 18px;">{city}</strong>
                        <span style="color: #666; margin-left: 10px;">({dest['destination']})</span>
                    </div>
                    <div>
                        <span style="font-size: 24px; font-weight: bold; color: #667eea;">${price}</span>
                    </div>
                </div>
                <div style="margin-top: 10px;">
                    <a href="{url}" style="color: #667eea; text-decoration: none;">View Dates →</a>
                </div>
            </div>
            """
            
            dest_text += f"  • {city} ({dest['destination']}): ${price}\n    {url}\n\n"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                           color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .header p {{ margin: 10px 0 0 0; font-size: 16px; opacity: 0.9; }}
                .deal-box {{ background: #f8f9fa; padding: 25px; border-radius: 0 0 10px 10px; }}
                .sale-banner {{ background: #ff6b6b; color: white; padding: 15px; 
                               text-align: center; font-size: 20px; font-weight: bold; 
                               border-radius: 5px; margin-bottom: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; color: #999; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔥 {region} Flash Sale!</h1>
                    <p>From {origin}</p>
                </div>
                <div class="deal-box">
                    <div class="sale-banner">
                        {dest_count} Destinations on Sale: ${min_price} - ${max_price}
                    </div>
                    {dest_html}
                    <p style="margin-top: 20px; font-size: 14px; color: #666;">
                        💡 <strong>Tip:</strong> Each destination has multiple date options. 
                        Click "View Dates" to see all available flights!
                    </p>
                </div>
                <div class="footer">
                    <p>You're receiving this because you subscribed to flight deal alerts.</p>
                    <p>Prices and availability subject to change.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text = f"""
        🔥 {region} Flash Sale from {origin}!
        
        {dest_count} destinations on sale: ${min_price} - ${max_price}
        
        Destinations:
        {dest_text}
        
        Each destination has multiple date options available.
        
        ---
        You're receiving this because you subscribed to flight deal alerts.
        Prices and availability subject to change.
        """
        
        return {
            'subject': subject,
            'html': html.strip(),
            'text': text.strip()
        }


# Example usage
if __name__ == "__main__":
    builder = EmailBuilder()
    
    # Test individual deal
    individual_deal = {
        'origin': 'DFW',
        'destination': 'BCN',
        'destination_city': 'Barcelona',
        'price': 347,
        'outbound_date': '2026-03-15',
        'return_date': '2026-03-22',
        'google_flights_url': 'https://google.com/travel/flights?...',
        'similar_date_count': 47
    }
    
    email = builder.build_individual_email(individual_deal)
    print("INDIVIDUAL DEAL EMAIL:")
    print(f"Subject: {email['subject']}")
    print(f"HTML length: {len(email['html'])} chars")
    print()
    
    # Test regional deal
    regional_deal = {
        'type': 'regional',
        'origin': 'DFW',
        'region': 'europe',
        'region_display': 'Europe',
        'destination_count': 3,
        'min_price': 347,
        'max_price': 425,
        'destinations': [
            {'destination': 'BCN', 'destination_city': 'Barcelona', 'price': 347, 
             'google_flights_url': 'https://google.com/travel/flights?...'},
            {'destination': 'LIS', 'destination_city': 'Lisbon', 'price': 389,
             'google_flights_url': 'https://google.com/travel/flights?...'},
            {'destination': 'MAD', 'destination_city': 'Madrid', 'price': 425,
             'google_flights_url': 'https://google.com/travel/flights?...'},
        ]
    }
    
    email = builder.build_regional_email(regional_deal)
    print("REGIONAL SALE EMAIL:")
    print(f"Subject: {email['subject']}")
    print(f"HTML length: {len(email['html'])} chars")
    
    # Save sample HTML to file for preview
    with open('sample_regional_email.html', 'w') as f:
        f.write(email['html'])
    print("\n✅ Sample email saved to: sample_regional_email.html")

