#!/usr/bin/env python
from crewai.flow.flow import Flow, listen, start, router, or_
from dotenv import load_dotenv
from litellm import completion
import os
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool

# Load environment variables
load_dotenv()

# Initialize database connection
# Using SQLite as the database source
# The "EMR" table contains medical records with the following columns:
# NAME, AGE, GENDER, BLOOD TYPE, MEDICAL CONDITION, DATE OF ADMISSION, DOCTOR, HOSPITAL, INSURANCE PROVIDER, BILLING AMOUNT, ROOM NUMBER, ADMISSION TYPE, DISCHARGE DATE, MEDICATION, TEST RESULTS
db = SQLDatabase.from_uri("sqlite:///database.db")
execute_sql = QuerySQLDatabaseTool(db=db, return_direct=True)

def query_SQL_DB(reformulated_user_question, model):
    """
    Generates an SQL query based on a reformulated natural language question and executes it on the database.
    """
    def generate(reformulated_user_question, model):
        return completion(
            model=model,
            api_key=os.getenv("OPENAI_API_KEY"),
            messages=[
                {
                    "role": "user",
                    "content": f""" You are an SQL specialist working in a medical data institution.
                        You are working with a table called \"EMR\". Based on the user's question: {reformulated_user_question},
                        create a SQL query to retrieve relevant data.
                        Always use SELECT * and format queries in uppercase.
                        Respond only with the SQL query formatted as:
                        Query :###SELECT * FROM EMR WHERE NAME = 'EDWARD EDWARDS'###
                        """,
                },
            ],
        )["choices"][0]["message"]["content"]

    Query = generate(reformulated_user_question, model)
    print('Generated SQL Query:', Query)
    try:
        response = execute_sql.invoke(str(Query).split("###", 2)[1])
        return response
    except:
        # Retry once in case of an error
        Query = generate(reformulated_user_question, model)
        response = execute_sql.invoke(str(Query).split("###", 2)[1])
        return response

def reformulate_NL_question(conv, model):
    """
    Reformulates the last user question in a conversation to include relevant context.
    """
    reformulation = completion(
        model=model,
        api_key=os.getenv("OPENAI_API_KEY"),
        messages=[
            {
                "role": "user",
                "content": f""" You are a data specialist assisting a medical professional. 
                Reformulate the last question in the conversation history to make it more precise.
                Conversation history: {conv}
                Ensure clarity and accuracy while maintaining context.
                """,
            },
        ],
    )["choices"][0]["message"]["content"]
    return reformulation

def check_end(user_followup, model, conv):
    """
    Determines if the conversation should continue or end.
    """
    response = completion(
        model=model,
        api_key=os.getenv("OPENAI_API_KEY"),
        messages=[
            {
                "role": "user",
                "content": f""" You are assisting a medical professional. 
                Based on the conversation history: {conv} and the latest user message: {user_followup}, 
                determine if they need more information.
                Respond with either \"more info\" or \"end conversation\".
                """,
            },
        ],
    )
    return response["choices"][0]["message"]["content"]

class ExampleFlow(Flow):
    """
    CrewAI Flow for managing interactions with the medical records assistant.
    """
    model = "gpt-4o-mini"

    @start()
    def first_query(self):
        """
        Handles the first user query, reformulates it, executes an SQL query, and returns the response.
        """
        user_question = input("Hello, I am your medical records assistant. How can I help you?")
        self.state["conv"] = [f'user: {user_question}']
        reformulated_user_question = reformulate_NL_question(self.state["conv"], self.model)
        sql_response = query_SQL_DB(reformulated_user_question, self.model)
        return sql_response

    @listen("more")
    def followup_query(self):
        """
        Handles follow-up queries.
        """
        reformulated_user_question = reformulate_NL_question(self.state["conv"], self.model)
        sql_response = query_SQL_DB(reformulated_user_question, self.model)
        return sql_response

    @listen(first_query)
    def generate_customer_response(self, sql_response):
        """
        Generates a response based on the SQL query results.
        """
        response = completion(
            model=self.model,
            api_key=os.getenv("OPENAI_API_KEY"),
            messages=[
                {
                    "role": "user",
                    "content": f""" Using the conversation history: {self.state['conv']} 
                    and the database results: {sql_response}, provide an answer.
                    """,
                },
            ],
        )
        agent_response = response["choices"][0]["message"]["content"]
        print(agent_response)
        self.state['conv'].append(f'Agent: {agent_response}')
        return input("Can I help you with something else?")

    @router(or_(generate_customer_response, followup_query))
    def followup(self, user_followup):
        """
        Determines whether the conversation continues or ends.
        """
        agent_response = check_end(user_followup, self.model, self.state['conv'])
        if 'more' in agent_response.lower():
            return "more"
        else:
            return "END FLOW"

# Start the CrewAI Flow
flow = ExampleFlow()
result = flow.kickoff()
