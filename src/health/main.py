#!/usr/bin/env python
from random import randint
from pydantic import BaseModel
from crewai.flow.flow import Flow, listen, start ,router ,or_
from dotenv import load_dotenv
from litellm import completion
from langchain_openai import ChatOpenAI
import json
import os
from langchain_community.tools.sql_database.tool import QuerySQLCheckerTool
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
load_dotenv()






db = SQLDatabase.from_uri("sqlite:///database.db")
# llm = ChatOpenAI(
# temperature=0, 
# model="gpt-4o-mini",  
# api_key=os.getenv("OPENAI_API_KEY")
# )
#check_SQL= QuerySQLCheckerTool(db=db, llm=llm)
execute_sql = QuerySQLDatabaseTool(db=db, return_direct=True)





def query_SQL_DB(reformulated_user_question,model):
    
    def generate(reformulated_user_question,model):
        return completion(
                model=model,
                api_key='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',
                messages=[
                    {
                        "role": "user",
                        "content": f""" You are an SQL specialist working in a medical data institution 
                        you are working with a table called "EMR" with the following schema :
                        Columns:NAME, AGE, GENDER, BLOOD TYPE, MEDICAL CONDITION, DATE OF ADMISSION, DOCTOR, HOSPITAL, INSURANCE PROVIDER, BILLING AMOUNT, ROOM NUMBER, ADMISSION TYPE, DISCHARGE DATE, MEDICATION, TEST RESULTS

                        you are doing a conversation with a medical professionl,and you got this question : {reformulated_user_question},
                        
                        create the necessary SQL query to answer the question
                        make sure to use upper case for all words in the query
                        always use SELECT *
                        Respond only with the SQL query in this format 
                        Query :###SELECT * FROM EMR WHERE NAME = 'EDWARD EDWARDS'###
                        
                        """,
                    },
                ],
            )["choices"][0]["message"]["content"]
            
    
    Query = generate(reformulated_user_question,model)
    print('Reformulated query',Query)
    #Query=check_SQL.invoke(Query)
    try :
        response=execute_sql.invoke(str(Query).split("###",2)[1])
        return response
    except:
        Query = generate(reformulated_user_question,model)
        #Query=check_SQL.invoke(Query)
        response=execute_sql.invoke(str(Query).split("###",2)[1])
        return response
        



def reformulate_NL_question(conv,model):
    
    reformulation=completion(
            model=model,
            api_key='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',
            messages=[
                {
                    "role": "user",
                    "content": f""" You are a Data specialist working in a medical data institution , you are doing a conversation with a medical professionl,the conversation history going as follows : {conv},
                    you have to reformulate the last question to include as much information as possible from the conversation in order to make it more clear and precise to query the database .
                    Be careful , the user might ask about different people sequentially 
                    
                    """,
                },
            ],
        )["choices"][0]["message"]["content"]
    return reformulation    



def check_end(user_followup,model,conv):
            response=completion(
            model=model,
            api_key='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',
            messages=[
                {
                    "role": "user",
                    "content": f""" You are working in a medical data institution ,you are doing a conversation with a medical professionl,the conversation history going as follows : {conv}
                    then the user said {user_followup}

                    Based on the last message you decide if he wants more information or not

                    You can only answer with "more info" or "end conversation"
                    """,
                },
            ],
        )
            return response["choices"][0]["message"]["content"]

class ExampleFlow(Flow):
    model = "gpt-4o-mini"

    @start()
    def first_query(self):
        user_question = input("Hello i am your medical records assistant , how can i help you ?")
        self.state["conv"]=[f'user:{user_question}']
        self.state['user_question']=user_question
        reformulated_user_question=reformulate_NL_question(self.state['conv'],self.model)
        sql_response=query_SQL_DB(reformulated_user_question,self.model)
        return sql_response
    
    @listen("more") 
    def followup_query(self):

        reformulated_user_question=reformulate_NL_question(self.state['conv'],self.model)
        sql_response=query_SQL_DB(reformulated_user_question,self.model)
        return sql_response

    @listen(first_query)
    def generate_customer_response(self,sql_response):
        response = completion(
            model=self.model,
            api_key='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',
            messages=[
                {
                    "role": "user",
                    "content": f""" You are working in a medical data institution ,you are doing a conversation with a medical professionl,the conversation history going as follows : {self.state['conv']}
                    you have to the answer the question using the following information {sql_response}

                    only answer the last question 
                    if you got more than one person as response for a question about 1 person mention that there is more than one person with the same name 
                    do not offer more help
                    """,
                },
            ],
        )

        agent_response = response["choices"][0]["message"]["content"]
        # Store the fun fact in our state
        print(agent_response)
        self.state['conv']+=(f' / Agent:{agent_response} , Can i help you with something else ?')
        user_followup= input("Can i help you with something else ?")
        self.state["user_followup"]=user_followup
        
        return user_followup
    
    @listen(followup_query)
    def generate_customer_response_followup(self,sql_context):
        response = completion(
            model=self.model,
            api_key='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',
            messages=[
                {
                    "role": "user",
                    "content": f""" You are working in a medical data institution ,you are doing a conversation with a medical professionl,the conversation history going as follows : {self.state['conv']}
                    you have to the answer the question using the following informatn {sql_context}

                    only answer the last question 
                    do not offer more help
                    """,
                },
            ],
        )

        agent_response = response["choices"][0]["message"]["content"]
        # Store the fun fact in our state
        print(agent_response)
        self.state['conv']+=(f' / Agent:{agent_response} , Can i help you with something else ?')
        user_followup= input("Can i help you with something else ?")
        self.state["user_followup"]=user_followup
        
        return user_followup
    
    @router(or_(generate_customer_response,generate_customer_response_followup))
    def followup(self,user_followup):
        
        

        agent_response = check_end(user_followup,self.model,self.state['conv'])

        self.state['conv']+=(f' / user:{user_followup}')
        print('agent_response   : ' ,agent_response)
        if 'more' in agent_response.lower() :
            return "more"
        else:
            check_followup=input("Can i help you with something else ?")
            if 'more' in check_end(check_followup,self.model,self.state['conv']).lower():
                self.state['conv']+=(f' / Agent:Can i help you with something else ?')
                self.state['conv']+=(f' / user:{check_followup}')
                return "more"
            else:
                return "END FLOW"
    




flow = ExampleFlow()
result = flow.kickoff()




