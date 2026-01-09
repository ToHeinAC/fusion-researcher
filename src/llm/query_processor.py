"""Natural language query processor."""

import re
from typing import Optional
from dataclasses import dataclass

from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


@dataclass
class QueryResult:
    """Result from a natural language query."""
    query: str
    sql: Optional[str]
    results: list[dict]
    answer: str
    error: Optional[str] = None


class NLQueryProcessor:
    """Process natural language queries against the fusion database."""
    
    # Dangerous SQL patterns to block
    DANGEROUS_PATTERNS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", ";--"]
    
    def __init__(self, llm: ChatOllama, db: SQLDatabase):
        self.llm = llm
        self.db = db
        self._sql_chain = None
        self._answer_chain = None
    
    @property
    def sql_chain(self):
        """Get or create SQL generation chain."""
        if self._sql_chain is None:
            self._sql_chain = SQLDatabaseChain.from_llm(self.llm, self.db, verbose=False, return_intermediate_steps=True)
        return self._sql_chain
    
    def _create_answer_chain(self):
        """Create chain for generating natural language answers."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant that answers questions about fusion companies and the fusion energy market.
Based on the SQL query results provided, generate a clear, informative answer.
Include specific data points and format with bullet points when appropriate.
If the results are empty, acknowledge that no matching data was found."""),
            ("human", """Question: {question}

SQL Query: {sql}

Query Results: {results}

Provide a clear, informative answer:"""),
        ])
        return prompt | self.llm | StrOutputParser()
    
    def validate_sql(self, sql: str) -> tuple[bool, Optional[str]]:
        """Validate generated SQL for safety."""
        sql_upper = sql.upper()
        
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in sql_upper:
                return False, f"Dangerous SQL pattern detected: {pattern}"
        
        # Ensure it's a SELECT query
        if not sql_upper.strip().startswith("SELECT"):
            return False, "Only SELECT queries are allowed"
        
        # Check for valid table names
        valid_tables = self.db.get_usable_table_names()
        
        return True, None
    
    def process_query(self, question: str) -> QueryResult:
        """Process a natural language query and return results."""
        try:
            # Use SQLDatabaseChain which handles SQL generation and execution
            result = self.sql_chain.invoke({"query": question})
            
            # Extract SQL from intermediate steps if available
            sql = None
            raw_results = []
            
            if isinstance(result, dict):
                answer = result.get("result", str(result))
                # Get intermediate steps for SQL
                steps = result.get("intermediate_steps", [])
                for step in steps:
                    if isinstance(step, dict) and "sql_cmd" in step:
                        sql = step["sql_cmd"]
                    elif isinstance(step, str) and step.strip().upper().startswith("SELECT"):
                        sql = step
            else:
                answer = str(result)
            
            return QueryResult(
                query=question,
                sql=sql,
                results=raw_results,
                answer=answer,
            )
            
        except Exception as e:
            return QueryResult(
                query=question,
                sql=None,
                results=[],
                answer=f"An error occurred: {str(e)}",
                error=str(e),
            )
    
    def _parse_results(self, raw_results: str) -> list[dict]:
        """Parse raw SQL results into list of dicts."""
        if not raw_results or raw_results == "[]":
            return []
        
        # Try to parse as list of tuples
        try:
            import ast
            parsed = ast.literal_eval(raw_results)
            if isinstance(parsed, list):
                return [{"row": i, "data": row} for i, row in enumerate(parsed)]
        except (ValueError, SyntaxError):
            pass
        
        # Return as single result
        return [{"result": raw_results}]
    
    def get_schema_info(self) -> str:
        """Get database schema information."""
        return self.db.get_table_info()
    
    def get_sample_queries(self) -> list[str]:
        """Get sample queries for the UI."""
        return [
            "Show me all German fusion startups with funding over EUR 100M",
            "What are the top 5 fusion companies by total funding?",
            "List companies using Stellarator technology",
            "Which companies have TRL 6 or higher?",
            "Show funding rounds from 2024",
            "Compare Tokamak and Stellarator companies",
            "What is the total funding in the fusion industry?",
            "List companies founded after 2020",
        ]
