import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j connection details
uri = "neo4j://localhost:7687"
username = "neo4j"
password = os.getenv("NEO4J_PASSWORD")

class OEISLoader:

    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def create_sequence_node(self, seq_id, description):
        with self.driver.session() as session:
            session.run(
                "MERGE (s:Sequence {id: $seq_id, description: $description})",
                seq_id=seq_id, description=description
            )

    def create_author_node(self, author_name):
        with self.driver.session() as session:
            session.run(
                "MERGE (a:Author {name: $author_name})",
                author_name=author_name
            )

    def create_reference_node(self, ref):
        with self.driver.session() as session:
            session.run(
                "MERGE (r:Reference {citation: $ref})",
                ref=ref
            )

    def create_relationships(self, seq_id, author_name=None, ref=None):
        with self.driver.session() as session:
            if author_name and ref:
                session.run(
                    """
                    MATCH (s:Sequence {id: $seq_id}), (a:Author {name: $author_name}), (r:Reference {citation: $ref})
                    MERGE (s)-[:HAS_AUTHOR]->(a)
                    MERGE (s)-[:HAS_REFERENCE]->(r)
                    MERGE (r)-[:AUTHORED_BY]->(a)
                    """,
                    seq_id=seq_id, author_name=author_name, ref=ref
                )
            elif author_name:
                session.run(
                    """
                    MATCH (s:Sequence {id: $seq_id}), (a:Author {name: $author_name})
                    MERGE (s)-[:HAS_AUTHOR]->(a)
                    """,
                    seq_id=seq_id, author_name=author_name
                )
            elif ref:
                session.run(
                    """
                    MATCH (s:Sequence {id: $seq_id}), (r:Reference {citation: $ref})
                    MERGE (s)-[:HAS_REFERENCE]->(r)
                    """,
                    seq_id=seq_id, ref=ref
                )

# Parse the .seq file
def parse_seq_file(file_path):
    sequence_data = {"id": None, "description": None, "authors": [], "references": []}
    # print(file_path)
    with open(file_path, 'r', encoding='utf8') as file:
        for line in file:
            if line.startswith('%I'):
                sequence_data["id"] = line.split()[1].strip()
            elif line.startswith('%N'):
                sequence_data["description"] = line.strip()[3:]
            elif line.startswith('%A'):
                author = line.split(" ")[2:]
                sequence_data["authors"].append(author)
            elif line.startswith('%D'):
                sequence_data["references"].append(line.strip()[3:])
    
    return sequence_data

# Load a single sequence into Neo4j
def load_to_neo4j(seq_data):
    oeis_loader = OEISLoader(uri, username, password)
    
    oeis_loader.create_sequence_node(seq_data["id"], seq_data["description"])
    
    for author in seq_data["authors"]:
        oeis_loader.create_author_node(author)
        oeis_loader.create_relationships(seq_data["id"], author, None)

    for ref in seq_data["references"]:
        oeis_loader.create_reference_node(ref)
        oeis_loader.create_relationships(seq_data["id"], None, ref)
    
    oeis_loader.close()

# Process all .seq files in the folder
def process_all_seq_files(folder_path):
    oeis_loader = OEISLoader(uri, username, password)
    
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".seq"):
            file_path = os.path.join(folder_path, file_name)
            seq_data = parse_seq_file(file_path)
            load_to_neo4j(seq_data)

    oeis_loader.close()

# Specify the folder containing .seq files

# folder_path = "seq/A000/"
# process_all_seq_files(folder_path)

for i in range(0, 377):
    folder_name = 'seq/' + 'A' + '{num:03d}'.format(num=i) + '/'
    process_all_seq_files(folder_name)
    print(folder_name)


# sudo docker ps
# sudo docker run -p7474:7474 -p7687:7687 -d --env NEO4J_AUTH=neo4j/test1234 neo4j:latest