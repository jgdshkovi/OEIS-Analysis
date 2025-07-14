# from bs4 import BeautifulSoup
# from py2neo import Graph, Node, Relationship

# # Web Scraping
# with open('A001000.html', 'r') as file:
#     html_content = file.read()

# soup = BeautifulSoup(html_content, 'html.parser')

# # Neo4j Connection
# graph = Graph('bolt://localhost:7687', auth=('neo4j', 'test1234'))

# # Extract and Store Data
# sequence_node = Node("Sequence", number="A001000", name="Squares of integers", description="a(n) = n^2; or 1, 4, 9, 16, 25, 36, 49, ...")
# graph.create(sequence_node)

# for link in soup.find_all('a'):
#     link_text = link.text.strip()
#     link_url = link.get('href')
#     link_node = Node("Link", text=link_text, url=link_url)
#     graph.create(link_node)
#     graph.create(Relationship(sequence_node, "HAS_LINK", link_node))
#     if link_url.startswith('/'):
#         target_sequence_node = Node("Sequence", number=link_url.split('/')[-1])
#         graph.create(target_sequence_node)
#         graph.create(Relationship(link_node, "LINKS_TO", target_sequence_node))
#     else:
#         external_resource_node = Node("ExternalResource", url=link_url)
#         graph.create(external_resource_node)
#         graph.create(Relationship(link_node, "LINKS_EXTERNAL", external_resource_node))

# for section in soup.find_all('div', class_='section'):
#     section_name = section.find('div', class_='sectname').text.strip()
#     section_content = ''.join(str(elem) for elem in section.find('div', class_='sectbody').contents)
#     text_content_node = Node("TextContent", name=section_name, content=section_content)
#     graph.create(text_content_node)
#     graph.create(Relationship(sequence_node, "HAS_TEXT_CONTENT", text_content_node))


from bs4 import BeautifulSoup

# # Load your HTML content (e.g., from a file or a response from requests.get(url))
# html_content = """
# <!-- Example HTML structure -->
# <div class="seqdatabox">
#     <span class="sectname">Field1</span>
#     <div class="data">Data1</div>
#     <span class="sectname">Field2</span>
#     <div class="data">Data2</div>
#     <!-- Add more as needed -->
# </div>
# """

file_path = 'A001000.html'  # Replace with the path to your HTML file

with open(file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()


# Initialize BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Find the main container first (seqdatabox)
seqdatabox = soup.find('div', class_='seqdatabox')
seqdata = soup.find('div', class_='seqdata')

# print(seqdata.text.strip().replace('\n', '').split(','))
print(seqdata.text.strip().split(','))

# fields = seqdatabox.find_all(class_='sectname')

sectname_elements = soup.find_all('div', class_='section')
# print(sectname_elements)

for i in range(len(sectname_elements)):
    # soup = BeautifulSoup(sectname_elements[0], 'html.parser')
    # print(type(sectname_elements[0]))
    print(i, sectname_elements[i].get_text())
    # sectlines_soup = BeautifulSoup(sectname_elements[i], 'html.parser')
    # sectlines = sectname_elements[i].find_all('div', class_='sectline')
    # print(sectlines[0])
    


# for sectname in sectname_elements:
#     field_name = sectname.get_text(strip=True)
#     print(1)
#     print(field_name)
    
#     next_element = sectname.find_next()
#     data_value = next_element.get_text(strip=True) if next_element else 'No data'
    
#     print(f"{field_name}: {data_value}")
