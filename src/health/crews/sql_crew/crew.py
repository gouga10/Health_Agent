# from crewai import Agent, Crew, Process, Task
# from crewai.project import CrewBase, agent, crew, task
# from langchain.agents import tool
# from langchain_openai import ChatOpenAI
# from langchain_community.utilities.sql_database import SQLDatabase
# from langchain_community.tools.sql_database.tool import (
#     InfoSQLDatabaseTool,
#     ListSQLDatabaseTool,
#     QuerySQLCheckerTool,
#     QuerySQLDataBaseTool,
# )
# from langchain_core.agents import AgentAction, AgentFinish

# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
# from langchain.agents import AgentExecutor
# from langchain.agents.format_scratchpad.openai_tools import (
#     format_to_openai_tool_messages,
# )
# from langchain.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# import os
# from crewai_tools import CSVSearchTool

# from dotenv import load_dotenv
# load_dotenv()
# OPEN_AI_API_KEY = os.getenv("OPENAI_API_KEY")


# #Check the available tables in the database
# @tool("list_tables")
# def list_tables() -> str:
#     """List the available tables in the database"""
#     db = SQLDatabase.from_uri("sqlite:///database.db")

#     return ListSQLDatabaseTool(db=db).invoke("")



# #Get the schema and sample rows for the specified tables
# @tool("tables_schema")
# def tables_schema(tables: str) -> str:
#     """
#     Input is a comma-separated list of tables, output is the schema and sample rows
#     for those tables. 
#     Example Input: table1, table2, table3
#     """
#     db = SQLDatabase.from_uri("sqlite:///database.db")

#     return InfoSQLDatabaseTool(db=db).invoke(tables)



# #Execute a SQL query against the database
# @tool("execute_sql")
# def execute_sql(sql_query: str) -> str:
#     """Execute a SQL query against the database. Returns the result"""
#     db = SQLDatabase.from_uri("sqlite:///database.db")
#     result = QuerySQLDataBaseTool(db=db, return_direct=True).invoke(sql_query)

#     return result



# #Check the correctness of a SQL query
# @tool("check_sql")
# def check_sql(sql_query: str) -> str:
#     """
#     Use this tool to double check if your query is correct before executing it.
#     Always use this tool before executing a query with `execute_sql`.

#     """
#     db = SQLDatabase.from_uri("sqlite:///database.db")
#     llm = ChatOpenAI(
#     temperature=0, 
#     model="gpt-4o-mini",  
#     api_key=os.getenv("OPENAI_API_KEY")
# )
#     return QuerySQLCheckerTool(db=db, llm=llm).invoke({"query": sql_query})




# @CrewBase
# class HelathAgent():
# 	"""HelathAgent crew"""


# 	agents_config = 'config/agents.yaml'
# 	tasks_config = 'config/tasks.yaml'


# 	@agent
# 	def sql_developer(self) -> Agent:
# 		return Agent(
# 			config=self.agents_config['sql_developer'],
# 			verbose=True,
# 			tools=[list_tables, tables_schema, execute_sql, check_sql],
			

# 		)
    
# 	@agent
# 	def reporting_analyst(self) -> Agent:
# 		return Agent(
# 			config=self.agents_config['reporting_analyst'],
# 			verbose=True,)


# 	@task
# 	def extract_data(self) -> Task:
# 		return Task(
# 			config=self.tasks_config['extract_data'],
# 		)
# 	@task
# 	def analyze_data(self) -> Task:
# 		return Task(
# 			config=self.tasks_config['analyze_data'],
# 		)




# 	@crew
# 	def crew(self) -> Crew:
# 		"""Creates the HelathAgent crew"""

# 		return Crew(
# 			agents=self.agents, # Automatically created by the @agent decorator
# 			tasks=self.tasks, # Automatically created by the @task decorator
# 			process=Process.sequential,
# 			verbose=True,
# 			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
# 		)
	
# inputs={"query":"in which hospital is he staying"}

# if __name__ == "__main__":
# 	# Instantiate the CrewBase class
# 	crew_instance = HelathAgent()
# 	# Initialize the crew
# 	my_crew = crew_instance.crew()
# 	# Run the crew with the inputs
# 	output = my_crew.kickoff(inputs=inputs)
# 	# Print the final processed output
# 	print("Final Output:", output)