"""
Browser stealth configuration to evade bot detection.

This module provides comprehensive anti-detection measures including:
- Realistic user agents
- Fingerprint randomization
- Human-like behavior simulation
- Removal of automation markers
"""

import random
from typing import Dict, Any, Tuple
from faker import Faker

fake = Faker()

# Real Chrome user agents (recent versions)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
]

# Realistic viewport sizes (common desktop resolutions)
VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1600, "height": 900},
    {"width": 2560, "height": 1440},
]

# US timezones
TIMEZONES = [
    "America/New_York",
    "America/Chicago", 
    "America/Denver",
    "America/Los_Angeles",
    "America/Phoenix",
]

# Locales
LOCALES = [
    "en-US",
    "en-GB",
]


def get_random_user_agent() -> str:
    """Get a random realistic user agent."""
    return random.choice(USER_AGENTS)


def get_random_viewport() -> Dict[str, int]:
    """Get a random realistic viewport size."""
    return random.choice(VIEWPORTS)


def get_random_timezone() -> str:
    """Get a random US timezone."""
    return random.choice(TIMEZONES)


def get_random_locale() -> str:
    """Get a random locale."""
    return random.choice(LOCALES)


def get_stealth_context_options() -> Dict[str, Any]:
    """
    Get browser context options with anti-detection measures.
    
    Returns:
        Dictionary of context options for browser.new_context()
    """
    user_agent = get_random_user_agent()
    viewport = get_random_viewport()
    timezone = get_random_timezone()
    locale = get_random_locale()
    
    # Extract Chrome version from user agent
    chrome_version = "131"
    if "Chrome/" in user_agent:
        chrome_version = user_agent.split("Chrome/")[1].split(".")[0]
    
    return {
        "user_agent": user_agent,
        "viewport": viewport,
        "locale": locale,
        "timezone_id": timezone,
        "permissions": ["geolocation", "notifications"],
        "geolocation": {"latitude": 40.7128, "longitude": -74.0060},  # NYC
        "color_scheme": "light",
        "extra_http_headers": {
            "Accept-Language": f"{locale},en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "sec-ch-ua": f'"Google Chrome";v="{chrome_version}", "Chromium";v="{chrome_version}", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
    }


def get_stealth_launch_args() -> list:
    """
    Get Chrome launch arguments for stealth mode.
    
    Returns:
        List of Chrome arguments
    """
    return [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-site-isolation-trials",
        "--disable-features=ImprovedCookieControls,LazyFrameLoading,GlobalMediaControls,DestroyProfileOnBrowserClose,MediaRouter,DialMediaRouteProvider,AcceptCHFrame,AutoExpandDetailsElement,CertificateTransparencyComponentUpdater,AvoidUnnecessaryBeforeUnloadCheckSync",
        "--disable-blink-features=AutomationControlled",
        # Disable automation indicators
        "--excludeSwitches=enable-automation",
        "--disable-infobars",
        # Performance
        "--disable-gpu",
        "--disable-software-rasterizer",
        # Reduce memory footprint
        "--disable-extensions",
        "--disable-default-apps",
        "--disable-sync",
        # Disable logging
        "--log-level=3",
        "--silent",
    ]


# JavaScript to inject that removes automation markers
STEALTH_JS = """
// Remove webdriver property
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// Add chrome property
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
    app: {}
};

// Override permissions
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// Mock plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        {
            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
            description: "Portable Document Format",
            filename: "internal-pdf-viewer",
            length: 1,
            name: "Chrome PDF Plugin"
        },
        {
            0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
            description: "Portable Document Format", 
            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
            length: 1,
            name: "Chrome PDF Viewer"
        },
        {
            0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
            1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"},
            description: "",
            filename: "internal-nacl-plugin",
            length: 2,
            name: "Native Client"
        }
    ]
});

// Mock languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
});

// Override toString to hide proxy
const originalToString = Function.prototype.toString;
Function.prototype.toString = function() {
    if (this === navigator.permissions.query) {
        return 'function query() { [native code] }';
    }
    return originalToString.call(this);
};

// Add realistic screen properties
Object.defineProperty(screen, 'availTop', {get: () => 0});
Object.defineProperty(screen, 'availLeft', {get: () => 0});

// Mock battery API
navigator.getBattery = () => Promise.resolve({
    charging: true,
    chargingTime: 0,
    dischargingTime: Infinity,
    level: 1,
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => true
});

// Add connection info
Object.defineProperty(navigator, 'connection', {
    get: () => ({
        effectiveType: '4g',
        rtt: 50,
        downlink: 10,
        saveData: false
    })
});

// Mock WebGL vendor
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) {
        return 'Intel Inc.';
    }
    if (parameter === 37446) {
        return 'Intel Iris OpenGL Engine';
    }
    return getParameter.call(this, parameter);
};

// Add realistic hardware concurrency
Object.defineProperty(navigator, 'hardwareConcurrency', {
    get: () => 8
});

// Add realistic device memory
Object.defineProperty(navigator, 'deviceMemory', {
    get: () => 8
});

console.log('[Stealth] Anti-detection measures applied');
"""


async def apply_stealth_to_page(page):
    """
    Apply stealth JavaScript to a page.
    
    Args:
        page: Playwright page object
    """
    await page.add_init_script(STEALTH_JS)


async def add_human_behavior(page, verbose=False):
    """
    Add human-like behavior to page interactions.
    
    Args:
        page: Playwright page object
        verbose: Print debug info
    """
    # Random scroll
    scroll_amount = random.randint(200, 500)
    await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
    await page.wait_for_timeout(random.randint(500, 1500))
    
    # Scroll back a bit
    await page.evaluate(f"window.scrollBy(0, -{scroll_amount // 3})")
    await page.wait_for_timeout(random.randint(300, 800))
    
    # Random mouse movement (via evaluate to simulate)
    await page.evaluate("""
        () => {
            const event = new MouseEvent('mousemove', {
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: Math.random() * window.innerWidth,
                clientY: Math.random() * window.innerHeight
            });
            document.dispatchEvent(event);
        }
    """)
    
    if verbose:
        print("[Stealth] Added human-like behavior (scroll, mouse movement)")


def get_random_delay() -> Tuple[float, float]:
    """
    Get random delays for human-like timing.
    
    Returns:
        Tuple of (short_delay, long_delay) in seconds
    """
    short = random.uniform(0.5, 2.0)
    long = random.uniform(2.0, 5.0)
    return short, long

