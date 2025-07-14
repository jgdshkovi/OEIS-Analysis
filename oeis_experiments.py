# from neo4j import GraphDatabase, RoutingControl
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# URI = "neo4j://localhost:7687"
# AUTH = ("neo4j", "test1234")


# def add_friend(driver, name, friend_name):
#     driver.execute_query(
#         "MERGE (a:Person {name: $name}) "
#         "MERGE (friend:Person {name: $friend_name}) "
#         "MERGE (a)-[:KNOWS]->(friend)",
#         name=name, friend_name=friend_name, database_="neo4j",
#     )


# def print_friends(driver, name):
#     records, _, _ = driver.execute_query(
#         "MATCH (a:Person)-[:KNOWS]->(friend) WHERE a.name = $name "
#         "RETURN friend.name ORDER BY friend.name",
#         name=name, database_="neo4j", routing_=RoutingControl.READ,
#     )
#     for record in records:
#         print(record["friend.name"])


# with GraphDatabase.driver(URI, auth=AUTH) as driver:
#     driver.verify_connectivity()
#     add_friend(driver, "Arthur", "Guinevere")
#     add_friend(driver, "Arthur", "Lancelot")
#     add_friend(driver, "Arthur", "Merlin")
#     print_friends(driver, "Arthur")


# ----------------------------------------------------------------------------------


# from neo4j import GraphDatabase
# import os

# # Neo4j connection setup
# uri = "neo4j://localhost:7687"
# user = "neo4j"
# password = "test1234"

# driver = GraphDatabase.driver(uri, auth=(user, password))

# def create_sequence(tx, seq_id, description):
#     tx.run("MERGE (s:Sequence {id: $seq_id, description: $description})",
#            seq_id=seq_id, description=description)

# def create_author(tx, author_name):
#     tx.run("MERGE (a:Author {name: $author_name})", author_name=author_name)

# def create_authorship(tx, author_name, seq_id):
#     tx.run("""
#     MATCH (a:Author {name: $author_name}), (s:Sequence {id: $seq_id})
#     MERGE (a)-[:AUTHORED]->(s)
#     """, author_name=author_name, seq_id=seq_id)

# def create_citation(tx, seq_id, citation):
#     tx.run("""
#     MATCH (s:Sequence {id: $seq_id})
#     MERGE (c:Citation {ref: $citation})
#     MERGE (s)-[:CITES]->(c)
#     """, seq_id=seq_id, citation=citation)

# # Parse a single .seq file
# def parse_seq_file(file_path):
#     seq_id = description = author = None
#     citations = []

#     with open(file_path, 'r') as file:
#         for line in file:
#             if line.startswith('%I'):
#                 seq_id = line.split()[1]
#             elif line.startswith('%N'):
#                 description = line[3:].strip()
#             elif line.startswith('%A'):
#                 author = line[3:].strip().split(" (")[0]  # Extract author name
#             elif line.startswith('%D'):
#                 citations.append(line[3:].strip())

#     return seq_id, description, author, citations

# # Insert data into Neo4j
# def load_data_into_neo4j(folder_path):
#     with driver.session() as session:
#         for filename in os.listdir(folder_path):
#             if filename.endswith(".seq"):
#                 file_path = os.path.join(folder_path, filename)
#                 seq_id, description, author, citations = parse_seq_file(file_path)

#                 if seq_id and description:
#                     session.write_transaction(create_sequence, seq_id, description)
#                 if author:
#                     session.write_transaction(create_author, author)
#                     session.write_transaction(create_authorship, author, seq_id)
#                 for citation in citations:
#                     session.write_transaction(create_citation, seq_id, citation)

# # Path to the A000 seq files folder
# folder_path = 'seq/A000'
# load_data_into_neo4j(folder_path)

# driver.close()


# ------------------------------------------------------------------------------------------------

from neo4j import GraphDatabase

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

    def create_relationships(self, seq_id, author_name, ref):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Sequence {id: $seq_id}), (a:Author {name: $author_name}), (r:Reference {citation: $ref})
                MERGE (s)-[:HAS_AUTHOR]->(a)
                MERGE (s)-[:HAS_REFERENCE]->(r)
                MERGE (r)-[:AUTHORED_BY]->(a)
                """,
                seq_id=seq_id, author_name=author_name, ref=ref
            )

# Parse the .seq file
def parse_seq_file(file_path):
    sequence_data = {"id": None, "description": None, "authors": [], "references": []}
    
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('%I'):
                sequence_data["id"] = line.split()[1].strip()
            elif line.startswith('%N'):
                sequence_data["description"] = line.strip()[3:]
            elif line.startswith('%C'):
                author = line.split(" - ")[1].split(",")[0].strip()
                sequence_data["authors"].append(author)
            elif line.startswith('%D'):
                sequence_data["references"].append(line.strip()[3:])
    
    return sequence_data

# Load data into Neo4j
def load_to_neo4j(file_path):
    seq_data = parse_seq_file(file_path)

    oeis_loader = OEISLoader(uri, username, password)
    
    oeis_loader.create_sequence_node(seq_data["id"], seq_data["description"])
    
    for author in seq_data["authors"]:
        oeis_loader.create_author_node(author)
        oeis_loader.create_relationships(seq_data["id"], author, None)

    for ref in seq_data["references"]:
        oeis_loader.create_reference_node(ref)
        oeis_loader.create_relationships(seq_data["id"], None, ref)
    
    oeis_loader.close()

# Test the loader with a sample .seq file
file_path = "seq/A000/A000001.seq"
load_to_neo4j(file_path)
