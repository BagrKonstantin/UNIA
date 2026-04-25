import requests

# 1. Initialize a session
session = requests.Session()

# 2. Manually add your cookies from the browser
# You need to add EVERY cookie you found
cookies = {
    '.AspNet.Cookies': '',
    '.AspNet.CookiesC1': '',
    '.AspNet.CookiesC2': '',
    '__RequestVerificationToken_L0luc2NyaXB0aW9ucw2': '',
    'ASP.NET_SessionId': '',
    'LBServer': ''
}

# Apply them to the session
session.cookies.update(cookies)

# 3. Add the User-Agent (Crucial!)
# If you don't use a real browser's User-Agent, the Load Balancer (TS cookies) might block you.
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36'
})

# 4. Try to fetch the data
response = session.get("https://inscription.uni.lu/Inscriptions/student/guichetetudiant")
print(response.text)