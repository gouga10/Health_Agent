from langchain.agents import tool
from langchain_openai import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
    QuerySQLDataBaseTool,
)
from langchain_core.agents import AgentAction, AgentFinish

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
from typing import List, Optional, Tuple
load_dotenv()

db = SQLDatabase.from_uri("sqlite:///database.db")
llm = ChatOpenAI(
    temperature=0, 
    model="gpt-4o-mini",  
    api_key=os.getenv("OPENAI_API_KEY")
)




#Get the schema and sample rows for the specified tables
@tool("tables_schema")
def tables_schema(tables: str) -> str:
    """
    Input is a comma-separated list of tables, output is the schema and sample rows
    for those tables. 
    Example Input: table1, table2, table3
    """
    db = SQLDatabase.from_uri("sqlite:///database.db")

    return InfoSQLDatabaseTool(db=db).invoke("EMR")

#Execute a SQL query against the database
@tool("execute_sql")
def execute_sql(sql_query: str) -> str:
    """Execute a SQL query against the database. Returns the result"""
    db = SQLDatabase.from_uri("sqlite:///database.db")
    result = QuerySQLDataBaseTool(db=db, return_direct=True).invoke(sql_query)

    return result

#Check the correctness of a SQL query
@tool("check_sql")
def check_sql(sql_query: str) -> str:
    """
    Use this tool to double check if your query is correct before executing it.
    Always use this tool before executing a query with `execute_sql`.

    """
    db = SQLDatabase.from_uri("sqlite:///database.db")
    llm = ChatOpenAI(
    temperature=0, 
    model="gpt-4o-mini",  
    api_key=os.getenv("OPENAI_API_KEY")
)
    return QuerySQLCheckerTool(db=db, llm=llm).invoke({"query": sql_query})


class DirectSQLAgentExecutor(AgentExecutor):
    def _get_tool_return(
        self, next_step_output: Tuple[AgentAction, str]
    ) -> Optional[AgentFinish]:
        """Override to force return after successful SQL execution but continue on errors"""
        agent_action, observation = next_step_output
        
        if agent_action.tool == "execute_sql":
            if "Error: (sqlite3.OperationalError)" in observation:
                return None
            else:
                return AgentFinish(
                    return_values={"output": observation},
                    log=""
                )
        return None



def query_medical_database(query: str, context: str):
    result = agent_executor._call({"query": query, "context": context})
    return result

def database_context(user_query: str, context: str) -> str:
    result = query_medical_database(user_query, context)
    sql_context = result['output']
    return sql_context






tools = [ tables_schema, execute_sql, check_sql]
llm_with_tools = llm.bind_tools(tools)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
             """
You are a SQL Database Developer tasked with retrieving and returning information from the database  using the provided tools based on user query , return the same output as the execute_sql tool, incorporating contextual understanding from past user queries: {context}.
The database colums are as follows:Name,Age,Gender,Blood Type,Medical Condition,Date of Admission,Doctor,Hospital,Insurance Provider,Billing Amount,Room Number,Admission Type,Discharge Date,Medication,Test Results

- **Context Awareness**:
    - Compare the new query with the most recent past query in the context.
    - If the new query aligns with the most recent past query, leverage the existing context for continuity.
    - If the new query differs significantly, prioritize the new query, resetting the context to ensure accurate and focused results.

### Tools:
- `list_tables`: To view all available tables in the database.
- `tables_schema`: To understand the structure of specific tables.
- `execute_sql`: To run SQL queries and retrieve data.
- `check_sql`: To verify the correctness of SQL queries before executing them.

### Guidelines:
1. **Focus**: 
   - Use the tools to fetch the required information based on the user query.
   - Directly return the exact output of the `execute_sql` tool.

2. **Output Requirements**:
   - Provide the raw result as it is returned by the `execute_sql` tool.
   - Do not include any additional formatting, context, or commentary.

3. **Behavior**:
   - If a query is invalid or cannot be executed, return only the error message or result from the tools.
   - Do not attempt to explain the issue or rephrase the output.

4. **Expected Output Example**:
   ```plaintext
   
the following is the previous conversation context:

the table name is "EMR" so your query should be like "SELECT * FROM EMR WHERE ...." , 
make sure that in your queries all the words and names must be lowercase

""",
        ),
        ("user", "{query}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
agent = (
    {
        "query": lambda x: x["query"],
        "context": lambda x: x["context"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

agent_executor = DirectSQLAgentExecutor(agent=agent, tools=tools, verbose=True,return_intermediate_steps=True,early_stopping_method="force")

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a professional Medical   Assistant. Your role is to help professionals explore and understand the available data in the medical database provided to you. The database context contains information about various patients, . Your task is to present the full context in a clear, engaging, and visually appealing way.
Database context information below :
----------------------------------------------------------------
context : 
{sql_context}
----------------------------------------------------------------
### Instructions for Generating Responses:
1. **Understand the Context:**
   - The context provided contains the relevant rows from the database based on the user's query.
   - Each row represents a patient and some key details about him.

2. **Present the Information:**
   - Format your response to ensure it's easy to read and visually appealing:

   - Make the response friendly, professional, and helpful.
   

3. **Error Handling:**
    - If the context contains no relevant rows, respond with a polite and helpful message:

Your goal is to act as an expert assistant and deliver responses that make the professionals medical records finding experience easier .
            """,
        ),
        ("user", "{query}"),
        
    ]
)

output_parser = StrOutputParser()

chain = prompt | llm | StrOutputParser()






