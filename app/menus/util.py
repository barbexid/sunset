from html.parser import HTMLParser
import os
import re
import textwrap

def clear_screen():
    print("Clearing screen...")
    os.system('cls' if os.name == 'nt' else 'clear')
    
    app_ver = os.getenv("APP_VERSION", "8.9.0")

    ascii_art = rf"""
            _____                    _____          
           /\    \                  /\    \         
          /::\____\                /::\    \        
         /::::|   |               /::::\    \       
        /:::::|   |              /::::::\    \      
       /::::::|   |             /:::/\:::\    \     
      /:::/|::|   |            /:::/__\:::\    \    
     /:::/ |::|   |           /::::\   \:::\    \   
    /:::/  |::|___|______    /::::::\   \:::\    \  
   /:::/   |::::::::\    \  /:::/\:::\   \:::\    \ 
  /:::/    |:::::::::\____\/:::/__\:::\   \:::\____\
  \::/    / ~~~~~/:::/    /\:::\   \:::\   \::/    /
   \/____/      /:::/    /  \:::\   \:::\   \/____/ 
               /:::/    /    \:::\   \:::\    \     
              /:::/    /      \:::\   \:::\____\    
             /:::/    /        \:::\   \::/    /    
            /:::/    /          \:::\   \/____/     
           /:::/    /            \:::\    \         
          /:::/    /              \:::\____\        
          \::/    /                \::/    /  
           \/____/                  \/____/ v{app_ver}
"""
    print(ascii_art)


def pause():
    input("\nPress enter to continue...")


class HTMLToText(HTMLParser):
    def __init__(self, width=80):
        super().__init__()
        self.width = width
        self.result = []
        self.in_li = False

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.in_li = True
        elif tag == "br":
            self.result.append("\n")

    def handle_endtag(self, tag):
        if tag == "li":
            self.in_li = False
            self.result.append("\n")

    def handle_data(self, data):
        text = data.strip()
        if text:
            if self.in_li:
                self.result.append(f"- {text}")
            else:
                self.result.append(text)

    def get_text(self):
        text = "".join(self.result)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return "\n".join(textwrap.wrap(text, width=self.width, replace_whitespace=False))


def display_html(html_text, width=80):
    parser = HTMLToText(width=width)
    parser.feed(html_text)
    return parser.get_text()


def format_quota_byte(quota_byte: int) -> str:
    TB = 1024 ** 4
    GB = 1024 ** 3 
    MB = 1024 ** 2
    KB = 1024

    if quota_byte >= TB:
        val = quota_byte / TB
        unit = "TB"
    elif quota_byte >= GB:
        val = quota_byte / GB
        unit = "GB"
    elif quota_byte >= MB:
        val = quota_byte / MB
        unit = "MB"
    elif quota_byte >= KB:
        val = quota_byte / KB
        unit = "KB"
    else:
        return f"{quota_byte} B"

    val = round(val, 2)
    if val.is_integer():
        return f"{int(val)} {unit}"
    else:
        return f"{val:.2f}".rstrip('0').rstrip('.') + f" {unit}"


def format_tier(tier_id):
    TIER_OFFSET = 0
    TIER_NAMES = ["Blue", "Silver", "Gold", "Platinum", "Diamond"]
    idx = tier_id - TIER_OFFSET
    if 0 <= idx < len(TIER_NAMES):
        return TIER_NAMES[idx]
    return f"Level {tier_id}"


def mask_phone_number(number) -> str:
    num_str = str(number).strip()
    is_628 = num_str.startswith("628")
    
    if is_628:
        num_str = "0" + num_str[2:]
        
    if len(num_str) <= 8:
        return num_str

    start = num_str[:5]
    end = num_str[8:]
    masked = f"{start}***{end}"

    if is_628:
        masked = "628" + masked[2:]
        
    return masked


def normalize_msisdn(number) -> str:
    num = "".join(filter(str.isdigit, str(number)))
    
    if num.startswith("0"):
        num = "62" + num[1:]
    elif num.startswith("8"):
        num = "62" + num
    elif num.startswith("628"):
        pass
    elif num.startswith("62"):
        pass
        
    return num