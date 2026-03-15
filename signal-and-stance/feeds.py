DEFAULT_FEEDS = [
    # Executive leadership and career strategy
    {
        "url": "https://www.mckinsey.com/Insights/rss.aspx",
        "name": "McKinsey Insights",
        "category": "leadership",
        "weight": 1.0,
        "enabled": True,
    },
    {
        "url": "https://www.fastcompany.com/section/work-life/rss",
        "name": "Fast Company — Work Life",
        "category": "careers",
        "weight": 0.9,
        "enabled": True,
    },
    # HR and recruiting
    {
        "url": "https://www.hrdive.com/feeds/news/",
        "name": "HR Dive",
        "category": "hr_recruiting",
        "weight": 0.9,
        "enabled": True,
    },
    {
        "url": "https://recruitingdaily.com/feed/",
        "name": "RecruitingDaily",
        "category": "hr_recruiting",
        "weight": 0.8,
        "enabled": True,
    },
    {
        "url": "https://theundercoverrecruiter.com/feed/",
        "name": "Undercover Recruiter",
        "category": "hr_recruiting",
        "weight": 0.7,
        "enabled": True,
    },
    # Job market data and economics
    {
        "url": "https://www.bls.gov/feed/bls_latest.rss",
        "name": "Bureau of Labor Statistics",
        "category": "labor_data",
        "weight": 1.0,
        "enabled": True,
    },
    {
        "url": "https://www.hiringlab.org/feed/",
        "name": "Indeed Hiring Lab",
        "category": "labor_data",
        "weight": 0.9,
        "enabled": True,
    },
    # Career advice and job search
    {
        "url": "https://www.askamanager.org/feed",
        "name": "Ask a Manager",
        "category": "careers",
        "weight": 0.8,
        "enabled": True,
    },
    {
        "url": "https://www.inc.com/rss",
        "name": "Inc.",
        "category": "executive_careers",
        "weight": 0.8,
        "enabled": True,
    },
    # Business news (for market context)
    {
        "url": "https://fortune.com/feed/",
        "name": "Fortune",
        "category": "business_news",
        "weight": 0.7,
        "enabled": True,
    },
    # HR technology and workplace
    {
        "url": "https://workology.com/feed/",
        "name": "Workology",
        "category": "hr_tech",
        "weight": 0.8,
        "enabled": True,
    },
    # Workplace trends
    {
        "url": "https://www.glassdoor.com/blog/feed/",
        "name": "Glassdoor Blog",
        "category": "workplace",
        "weight": 0.7,
        "enabled": True,
    },
]

from business_config import FEEDS_CONFIG

FEED_CATEGORIES = FEEDS_CONFIG["categories"]
