from bs4 import BeautifulSoup
import requests
from neo4j import GraphDatabase
import re
import time
import json
import os
from openai import OpenAI
from typing import Dict, List
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
password = os.getenv("NEO4J_PASSWORD")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EntityExtractor:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        prompt = f"""Please analyze the following text from the OEIS (Online Encyclopedia of Integer Sequences) 
        and extract relevant entities. Pay special attention to:
        
        1. Sequence IDs, which are important. Ignore IDs without any context (e.g., A000045, A001000)
        2. Mathematical concepts and terms
        3. Authors and contributors.
        4. Cross-references to other sequences. You can igonre the 'Sequence in context' part, but consider the 'Cf.' and the 'Adjacent sequences' part. 
        5. Keywords in the KEYWORDS section.
        
        Text to analyze:
        {text}

        Please provide only the JSON output with the following structure:
        {{
            "sequence_ids": [],
            "mathematical_concepts": [],
            "authors": [],
            "cross_references": [],
            "keywords":[]
        }}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing OEIS content and extracting relevant mathematical and technical entities. Respond only with structured JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
                
        except Exception as e:
            logging.error(f"API call failed: {str(e)}")
            return {"error": f"API call failed: {str(e)}"}

class OEISGraphBuilder:
    def __init__(self, uri: str, username: str, password: str, api_key: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.extractor = EntityExtractor(api_key)

    def close(self):
        self.driver.close()

    def create_nodes_and_relationships(self, sequence_id: str, entities: Dict):
        with self.driver.session() as session:
            session.execute_write(self._create_graph_data, sequence_id, entities)

    def _create_graph_data(self, tx, sequence_id: str, entities: Dict):
        # Create sequence node
        query_sequence = """
        MERGE (s:Sequence {id: $sequence_id})
        SET s.url = $url
        """
        url = f"https://oeis.org/{sequence_id}"
        tx.run(query_sequence, sequence_id=sequence_id, url=url)

        # Create nodes and relationships for each category
        categories = {
            'mathematical_concepts': ('MathematicalConcept', 'USES_CONCEPT'),
            'authors': ('Author', 'AUTHORED_BY'),
            'keywords': ('Keyword', 'HAS_KEYWORD')
        }

        for category, (node_label, relationship) in categories.items():
            if category in entities and entities[category]:
                query = f"""
                MATCH (s:Sequence {{id: $sequence_id}})
                UNWIND $items as item
                MERGE (n:{node_label} {{name: item}})
                MERGE (s)-[r:{relationship}]->(n)
                """
                tx.run(query, sequence_id=sequence_id, items=entities[category])

        # Handle cross-references
        if 'cross_references' in entities and entities['cross_references']:
            query_refs = """
            MATCH (s1:Sequence {id: $sequence_id})
            UNWIND $refs as ref
            MERGE (s2:Sequence {id: ref})
            MERGE (s1)-[r:REFERENCES]->(s2)
            """
            tx.run(query_refs, sequence_id=sequence_id, refs=entities['cross_references'])

def process_sequences(start: int, end: int):
    # Neo4j connection details
    URI = "neo4j://localhost:7687"
    USERNAME = "neo4j"
    PASSWORD = os.getenv("NEO4J_PASSWORD")
    
    # OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set your OPENAI_API_KEY environment variable")

    # Initialize graph builder
    graph_builder = OEISGraphBuilder(URI, USERNAME, PASSWORD, api_key)

    try:
        init_time = time.time()
        
        for i in range(start, end + 1):
            sequence_number = f"A{i:06d}"
            logging.info(f"Processing {sequence_number}")

            try:
                # Fetch sequence data
                url = f"https://oeis.org/{sequence_number}"
                response = requests.get(url)
                response.raise_for_status()  # Raise exception for bad status codes
                
                soup = BeautifulSoup(response.content, "html.parser")
                sequence = soup.find(class_='sequence')
                
                if sequence:
                    web_text = sequence.get_text(strip=True)
                    # Extract entities
                    entities = graph_builder.extractor.extract_entities(web_text)
                    
                    if "error" not in entities:
                        # Create graph data
                        graph_builder.create_nodes_and_relationships(sequence_number, entities)
                        logging.info(f"Successfully processed {sequence_number}")
                    else:
                        logging.error(f"Entity extraction failed for {sequence_number}: {entities['error']}")
                
                # Add a small delay to avoid overwhelming the server
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to fetch {sequence_number}: {str(e)}")
                continue
            except Exception as e:
                logging.error(f"Error processing {sequence_number}: {str(e)}")
                continue

        total_time = time.time() - init_time
        logging.info(f"Total processing time: {total_time:.2f} seconds")

    finally:
        graph_builder.close()

# Example usage in Jupyter notebook:
if __name__ == "__main__":
    '''
    Can experiment small initially
    '''
    # process_sequences(1, 3)  # Process sequences A000001 to A000003
    # process_sequences(3, 50)
    process_sequences(50, 100)
