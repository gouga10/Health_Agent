#!/usr/bin/env python
from random import randint
from pydantic import BaseModel
from crewai.flow.flow import Flow, listen, start ,router ,or_
from dotenv import load_dotenv
from litellm import completion
from my_langchain import database_context
import json
with open('/home/gouga/Desktop/crew/test_flow/src/test_flow/booking.json') as f:
    scheduele = json.load(f)


class ExampleFlow(Flow):
    model = "gpt-4o-mini"

    @start()
    def first_query(self):
        user_question = input("Hello i am your medical records assistant , how can i help you ?")
        self.state["conv"]=[f'user:{user_question}']
        self.state['user_question']=user_question
        sql_context=database_context(user_question,None)
        return sql_context
    
    @listen("more")
    def followup_query(self):

        followup_query = completion(
            model=self.model,
            api_key='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',
            messages=[
                {
                    "role": "user",
                    "content": f""" You are working in a medical data institution ,you are doing a conversation with a medical professionl,the conversation history going as follows : {self.state['conv']},
                    You have to understand the cpnversation and try to reformulate the last question to include as much information as possible
                    
                    """,
                },
            ],
        )
        
        print('followup_query  : ',followup_query)
        user_question = followup_query
        self.state["conv"]=[f'user:{user_question}']
        self.state['user_question']=user_question
        sql_context=database_context(user_question,self.state['conv'])
        print(sql_context)
        return sql_context

    @listen(first_query)
    def generate_customer_response(self,sql_context):
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
        response = completion(
            model=self.model,
            api_key='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',
            messages=[
                {
                    "role": "user",
                    "content": f""" You are working in a medical data institution ,you are doing a conversation with a medical professionl,the conversation history going as follows : {self.state['conv']}
                    then the user said {user_followup}

                    Based on the last message you decide if he wants more information or not

                    You can only answer with "more info" or "end conversation"
                    """,
                },
            ],
        )

        agent_response = response["choices"][0]["message"]["content"]
        self.state['conv']+=(f' / user:{user_followup}')
        print('agent_response   : ' ,agent_response)
        if 'more' in agent_response.lower() :
            return "more"
        else:
            return "END FLOW"
    




flow = ExampleFlow()
result = flow.kickoff()




