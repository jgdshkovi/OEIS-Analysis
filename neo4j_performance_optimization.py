from bs4 import BeautifulSoup
import aiohttp
import asyncio
from neo4j import GraphDatabase
import re
import time
from typing import List, Dict
from collections import deque
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OEISProcessor:
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.sequence_queue = asyncio.Queue()
        self.results_queue = deque()
        self.processed_count = 0
        self.batch_size = 50
        self.last_batch_time = time.time()
        self.sequences_processed = set()
        self.neo4j_batch_size = 1000  # Number of relationships to process in each Neo4j batch
        
    async def fetch_sequence(self, session: aiohttp.ClientSession, sequence_number: str) -> Dict:
        """Fetch and parse a single OEIS sequence page"""
        url = f"https://oeis.org/{sequence_number}"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, "html.parser")
                    sections = soup.find_all("div", class_="section")
                    
                    sequence_data = []
                    for section in sections:
                        sectname = section.find("div", class_="sectname").get_text(strip=True)
                        sectbody = section.find("div", class_="sectbody")
                        if sectbody:
                            links = sectbody.find_all("a")
                            for link in links:
                                sequence_data.append({
                                    'from_id': sequence_number,
                                    'to_id': link.get_text(strip=True),
                                    'relationship': sectname
                                })
                    return sequence_data
        except Exception as e:
            logging.error(f"Error fetching {sequence_number}: {str(e)}")
            return []
        return []

    async def scraper_worker(self, session: aiohttp.ClientSession):
        """Worker to process sequences from the queue"""
        while True:
            sequence_number = await self.sequence_queue.get()
            
            if sequence_number not in self.sequences_processed:
                results = await self.fetch_sequence(session, sequence_number)
                if results:
                    self.results_queue.extend(results)
                
                self.sequences_processed.add(sequence_number)
                self.processed_count += 1
                
                if self.processed_count % self.batch_size == 0:
                    current_time = time.time()
                    batch_duration = current_time - self.last_batch_time
                    total_duration = current_time - self.init_time
                    print(f"Processed {self.processed_count} sequences:")
                    # print(f"  Last {self.batch_size} sequences took: {batch_duration:.2f} seconds")
                    # print(f"  Average time per sequence: {batch_duration/self.batch_size:.2f} seconds")
                    print(f"  Total elapsed time: {total_duration:.2f} seconds")
                    print("----------------------------------------")
                    self.last_batch_time = current_time
            
            self.sequence_queue.task_done()

    def neo4j_worker(self):
        """Process results queue and write to Neo4j in batches"""
        with self.driver.session() as session:
            # Create indexes if they don't exist
            session.run("CREATE INDEX sequence_id IF NOT EXISTS FOR (n:Sequence) ON (n.id)")
            
            batch = []
            total_relationships = len(self.results_queue)
            relationships_processed = 0
            batch_count = 0
            
            while self.results_queue:
                batch.append(self.results_queue.popleft())
                
                if len(batch) >= self.neo4j_batch_size or not self.results_queue:
                    batch_start_time = time.time()
                    
                    # Process batch using UNWIND
                    query = """
                    UNWIND $batch as row
                    MERGE (from:Sequence {id: row.from_id})
                    MERGE (to:Sequence {id: row.to_id})
                    WITH from, to, row
                    CALL apoc.merge.relationship(from, row.relationship, {}, {}, to)
                    YIELD rel
                    RETURN count(*) as count
                    """
                    
                    try:
                        session.run(query, {"batch": batch})
                        relationships_processed += len(batch)
                        batch_count += 1
                        
                        batch_duration = time.time() - batch_start_time
                        print(f"Neo4j Batch {batch_count} processed:")
                        # print(f"  Relationships in batch: {len(batch)}")
                        # print(f"  Batch processing time: {batch_duration:.2f} seconds")
                        print(f"  Progress: {relationships_processed}/{total_relationships} ({(relationships_processed/total_relationships*100):.1f}%)")
                        print("----------------------------------------")
                        
                    except Exception as e:
                        logging.error(f"Neo4j batch error: {str(e)}")
                        # If APOC is not available, fall back to basic MERGE
                        fallback_query = """
                        UNWIND $batch as row
                        MERGE (from:Sequence {id: row.from_id})
                        MERGE (to:Sequence {id: row.to_id})
                        CALL {
                            WITH from, to, row
                            MERGE (from)-[r:`${row.relationship}`]->(to)
                        }
                        """
                        try:
                            session.run(fallback_query, {"batch": batch})
                        except Exception as e2:
                            logging.error(f"Neo4j fallback error: {str(e2)}")
                    
                    batch = []

    async def process_sequences(self, start: int, end: int, num_workers: int = 10):
        """Main processing function"""
        self.init_time = time.time()
        self.last_batch_time = self.init_time
        self.processed_count = 0
        self.sequences_processed.clear()
        
        print(f"Starting processing of sequences A{start:06d} to A{end:06d}")
        print(f"Using {num_workers} workers")
        print("----------------------------------------")
        
        # Queue up all sequences
        for i in range(start, end + 1):
            sequence_number = f"A{i:06d}"
            await self.sequence_queue.put(sequence_number)

        # Create worker tasks
        async with aiohttp.ClientSession() as session:
            workers = [
                asyncio.create_task(self.scraper_worker(session))
                for _ in range(num_workers)
            ]
            
            await self.sequence_queue.join()
            
            for worker in workers:
                worker.cancel()
            
            neo4j_start_time = time.time()
            self.neo4j_worker()
            neo4j_duration = time.time() - neo4j_start_time
            
            total_duration = time.time() - self.init_time
            print("\nFinal Statistics:")
            print(f"Total sequences processed: {self.processed_count}")
            print(f"Neo4j processing time: {neo4j_duration:.2f} seconds")
            print(f"Total processing time: {total_duration:.2f} seconds")
            print(f"Average time per sequence: {total_duration/self.processed_count:.2f} seconds")

# Usage example
async def main():
    processor = OEISProcessor(
        neo4j_uri="neo4j://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password=os.getenv("NEO4J_PASSWORD")
    )
    await processor.process_sequences(1, 1000)

if __name__ == "__main__":
    asyncio.run(main())