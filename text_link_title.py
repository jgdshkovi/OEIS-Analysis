from bs4 import BeautifulSoup
import requests

# URL of the webpage you want to scrape
url = "https://oeis.org/A001000"

# Fetch the webpage
response = requests.get(url)

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

# Find all div elements with the class 'section'
sections = soup.find_all("div", class_="section")

# Process each section
for section in sections:
    # Extract the section name
    sectname = section.find("div", class_="sectname").get_text(strip=True)
    print(f"Section Name: {sectname}")
    
    # Extract the body of the section
    sectbody = section.find("div", class_="sectbody")
    
    # Find all links within the section body
    links = sectbody.find_all("a")  # Find all <a> tags inside sectbody
    
    for link in links:
        link_text = link.get_text(strip=True)  # Extract the visible text of the link
        href = link.get("href")  # Extract the URL
        title = link.get("title", "--------------------------------")
        print(f"  Link Text: {link_text}. URL: {href}, TITLE: {title}")
        # print(f"  URL: {href}")
