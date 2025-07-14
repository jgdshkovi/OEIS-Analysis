# OEIS Analysis - Neo4j

This project provides tools for analyzing and visualizing data from the Online Encyclopedia of Integer Sequences (OEIS) using Python and Neo4j graph database.

## Features

- Web scraping of OEIS sequence pages
- Entity extraction using OpenAI's API
- Graph database population using Neo4j
- Asynchronous data processing for improved performance
- Various analysis queries and visualizations
- Secure environment variable management

## Requirements

- Python 3.10+
- Neo4j Database
- OpenAI API key
- Required Python packages (see installation section)

## Installation

1. **Clone the repository and navigate to the project directory**

2. **Install required Python packages:**
```bash
pip install beautifulsoup4 neo4j aiohttp openai requests pandas python-dotenv
```

3. **Set up environment variables:**
   - Create a `.env` file in the project root
   - Add your credentials:
```bash
# Neo4j Database Configuration
NEO4J_PASSWORD=test1234

# OpenAI API Configuration
OPENAI_API_KEY=your-actual-openai-api-key-here
```

4. **Start Neo4j database:**
```bash
sudo docker run -p7474:7474 -p7687:7687 -d --env NEO4J_AUTH=neo4j/test1234 neo4j:latest
```

## Project Structure

### **Data Loading Scripts:**
- **`load_oeis_batch.py`** - Main script for batch processing multiple OEIS folders (A000-A376)
- **`load_oeis_single.py`** - Processes a single OEIS folder for testing
- **`load_oeis_recursive.py`** - Recursively processes all OEIS folders
- **`oeis_experiments.py`** - Experimental/draft code for OEIS processing

### **Entity Extraction:**
- **`oeis_entity_extractor.py`** - Extracts mathematical concepts, authors, and cross-references using OpenAI's GPT API
- **`oeis_entity_extraction.ipynb`** - Jupyter notebook for entity extraction analysis

### **Performance Optimization:**
- **`neo4j_performance_optimization.py`** - Asynchronous processing for better performance with batch operations

### **Analysis & Utilities:**
- **`queries.ipynb`** - Collection of useful Neo4j queries for data analysis
- **`text_link_title.py`** - Text processing utilities
- **`text_link_title_boilerplate.ipynb`** - Initial data exploration notebook
- **`links.py`** - Link processing utilities

## Usage

### 1. **Basic Batch Processing (Recommended):**
```bash
python load_oeis_batch.py
```

### 2. **Single Folder Testing:**
```bash
python load_oeis_single.py
```

### 3. **Process All Sequences:**
```bash
python load_oeis_recursive.py
```

### 4. **Entity Extraction:**
```bash
python oeis_entity_extractor.py
```

### 5. **High-Performance Processing:**
```bash
python neo4j_performance_optimization.py
```

## Neo4j Query Examples

### 1. Find highly connected sequences:
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

### 2. Find sequences with multiple authors:
```cypher
MATCH (n)-[r:AUTHOR]->(m)
WITH n, COUNT(DISTINCT m) AS aCount
WHERE aCount > 2
MATCH (n)-[r:AUTHOR]->(m)
RETURN n, r, m;
```

### 3. Find sequences commonly cited by highly connected sequences:
```cypher
MATCH (s1:Sequence)-[cr1:CROSSREFS]->(sm:Sequence)<-[cr2:CROSSREFS]-(s2:Sequence) 
WITH s1, COUNT(DISTINCT sm) AS seqCount
WHERE seqCount > 60
MATCH (s1:Sequence)-[cr1:CROSSREFS]->(s2:Sequence) 
RETURN s1, cr1, s2;
```

## Security Notes

- **Never commit your `.env` file** - it contains sensitive credentials
- **Regenerate your OpenAI API key** if it was ever exposed in code
- **Use environment variables** for all sensitive configuration

## Features by Script

### Entity Extraction (`oeis_entity_extractor.py`)
- Extracts mathematical concepts, authors, and cross-references from OEIS pages
- Uses OpenAI's GPT API for intelligent entity recognition
- Processes sequences in batches for efficiency

### Performance Optimization (`neo4j_performance_optimization.py`)
- Implements asynchronous processing for better performance
- Handles batch operations for Neo4j database updates
- Includes progress tracking and error handling

### Data Loading Scripts
- **Batch Processing**: Handles multiple specific folders efficiently
- **Single Folder**: Perfect for testing and development
- **Recursive Processing**: Processes all available OEIS data

## Contributing

Feel free to submit issues and enhancement requests.

## License

This project is for educational and research purposes.


