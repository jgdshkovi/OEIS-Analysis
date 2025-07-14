# OEIS Analysis - Neo4j

This project provides tools for analyzing and visualizing data from the Online Encyclopedia of Integer Sequences (OEIS) using Python and Neo4j graph database.

## Features

- Web scraping of OEIS sequence pages
- Entity extraction using OpenAI's API
- Graph database population using Neo4j
- Asynchronous data processing
- Various analysis queries and visualizations

## Requirements

- Python 3.10+
- Neo4j Database
- OpenAI API key
- Required Python packages:
  - beautifulsoup4
  - neo4j
  - aiohttp
  - openai
  - requests
  - pandas

## Setup

1. Start Neo4j:
```bash
sudo docker run -p7474:7474 -p7687:7687 -d --env NEO4J_AUTH=neo4j/test1234 neo4j:latest
```

2. Set your OpenAI API key:
```python
os.environ["OPENAI_API_KEY"] = "your-api-key-here"
```

3. Install required Python packages:
```bash
pip install -r requirements.txt
```

## Main Components

### 1. Entity Extraction (`ent_extractor__.py`)
- Extracts mathematical concepts, authors, and cross-references from OEIS pages
- Uses OpenAI's GPT API for intelligent entity recognition
- Processes sequences in batches for efficiency

### 2. Improved Neo4j Processing (`improve_n4j_time.py`)
- Implements asynchronous processing for better performance
- Handles batch operations for Neo4j database updates
- Includes progress tracking and error handling

### 3. Data Processing Scripts
- `main.py`, `main1.py`, `main2.py`: Various implementations for processing OEIS data
- `boilerPlate_TextLinkTitle.ipynb`: Notebook for initial data exploration
- `queries.ipynb`: Collection of useful Neo4j queries for data analysis

## Usage

1. For basic sequence processing:
```python
python main.py
```

2. For improved performance with async processing:
```python
python improve_n4j_time.py
```

3. For entity extraction:
```python
python ent_extractor__.py
```

## Neo4j Query Examples

1. Find highly connected sequences:
```cypher
MATCH (n:Sequence)
WITH n, COUNT { (n)--() } as connectionCount
WHERE connectionCount >= 250
WITH COLLECT(n) as highlyConnectedNodes
UNWIND highlyConnectedNodes as n
MATCH (n)-[r]-(connected:Sequence)
WHERE connected IN highlyConnectedNodes
RETURN n, r, connected LIMIT 20;
```

2. Find sequences with multiple authors:
```cypher
MATCH (n)-[r:AUTHOR]->(m)
WITH n, COUNT(DISTINCT m) AS aCount
WHERE aCount > 2
MATCH (n)-[r:AUTHOR]->(m)
RETURN n, r, m
```

3. A Sequence which is commonly cited by 2 famous sequences and both of them are connected to at least 60 other Sequences
```cypher
MATCH (s1:Sequence)-[cr1:CROSSREFS]->(sm:Sequence)<-[cr2:CROSSREFS]-(s2:Sequence) 
WITH s1, COUNT(DISTINCT sm) AS seqCount
WHERE seqCount > 60
MATCH (s1:Sequence)-[cr1:CROSSREFS]->(s2:Sequence) 
RETURN s1, cr1, s2
```

## Notes

- The project supports processing both individual sequence files and batch processing
- Error handling and logging are implemented for robust operation
- Asynchronous processing is recommended for large-scale data extraction

## Contributing

Feel free to submit issues and enhancement requests.


