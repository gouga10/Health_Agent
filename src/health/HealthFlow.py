from crewai.flow.flow import Flow, listen, start, router, or_
from dotenv import load_dotenv
from litellm import completion
import os
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool

load_dotenv()
# Specify the path to the database file
db = SQLDatabase.from_uri("sqlite:///database.db")
# Create a tool to execute SQL queries
execute_sql = QuerySQLDatabaseTool(db=db, return_direct=True)
# OpenAI API key
api_key= os.getenv("OPENAI_API_KEY")


# Define the functions that will be used in the flow


# Define the function that will create the SQL query and execute it
def query_SQL_DB(reformulated_user_question, model):
    def generate(reformulated_user_question, model):
        return completion(
            model=model,
            api_key=api_key,
            messages=[
                {
                    "role": "user",
                    "content": f""" You are an SQL specialist working in a medical data institution 
                    you are working with a table called "EMR" with the following schema :
                    Columns names:NAME, AGE, GENDER, BLOOD_TYPE, MEDICAL_CONDITION, DATE_OF_ADMISSION, DOCTOR, HOSPITAL, INSURANCE_PROVIDER, BILLING_AMOUNT, ROOM_NUMBER, ADMISSION_TYPE, DISCHARGE_DATE, MEDICATION, TEST_RESULTS
                    column 1:[('BOBBY JACKSON', '30', 'MALE', 'B-', 'CANCER', '2024-01-31', 'MATTHEW SMITH', 'SONS AND MILLER', 'BLUE CROSS', '18856.2813059782', '328', 'URGENT', '2024-02-02', 'PARACETAMOL', 'NORMAL')]
                    column 2:[('LESLIE TERRY', '62', 'MALE', 'A+', 'OBESITY', '2019-08-20', 'SAMANTHA DAVIES', 'KIM INC', 'MEDICARE', '33643.3272865779', '265', 'EMERGENCY', '2019-08-26', 'IBUPROFEN', 'INCONCLUSIVE')]
                    you are doing a conversation with a medical professionl,and you got this question : {reformulated_user_question},
                    
                    create the necessary SQL query to answer the question
                    make sure to use upper case for all words in the query
                    you can use all types of SQL queries ,when using select try to use SELECT *
                    Respond only with the SQL query in the following format 

                    Question:how old is ali ?
                    Query :###SELECT * FROM EMR WHERE NAME LIKE 'ALI %'### 

                    if question is a count query you can use the following format
                    Question:how many doctors are named edward ?
                    Query :###SELECT COUNT(*) AS TOTAL_EDWARD FROM EMR WHERE DOCTOR LIKE 'EDWARD %'###

                    
                    """,
                },
            ],
        )["choices"][0]["message"]["content"]
    
    Query = generate(reformulated_user_question, model)
    print('SQL query', Query)
    try:
        sql_output = execute_sql.invoke(str(Query).split("###", 2)[1])
        response=f"Question : {reformulated_user_question} \nSQL query : {Query} \n SQL output : {sql_output}"
        return response
    except:
        Query = generate(reformulated_user_question, model)
         
        sql_output= execute_sql.invoke(str(Query).split("###", 2)[1])
        response=f"Question : {reformulated_user_question} \n SQL query : {Query} \n SQL output : {sql_output}"
        return response



# Define the function that will reformulate the user's question
def reformulate_NL_question(conv, model):
    reformulation = completion(
        model=model,
            api_key=api_key ,     
                messages=[
            {
                "role": "user",
                "content": f""" You are a Data specialist working in a medical data institution , 
                this is the schema of the database you are working with :
                Columns names:NAME, AGE, GENDER, BLOOD_TYPE, MEDICAL_CONDITION, DATE_OF_ADMISSION, DOCTOR, HOSPITAL, INSURANCE_PROVIDER, BILLING_AMOUNT, ROOM_NUMBER, ADMISSION_TYPE, DISCHARGE_DATE, MEDICATION, TEST_RESULTS
                column 1:[('BOBBY JACKSON', '30', 'MALE', 'B-', 'CANCER', '2024-01-31', 'MATTHEW SMITH', 'SONS AND MILLER', 'BLUE CROSS', '18856.2813059782', '328', 'URGENT', '2024-02-02', 'PARACETAMOL', 'NORMAL')]
                column 2:[('LESLIE TERRY', '62', 'MALE', 'A+', 'OBESITY', '2019-08-20', 'SAMANTHA DAVIES', 'KIM INC', 'MEDICARE', '33643.3272865779', '265', 'EMERGENCY', '2019-08-26', 'IBUPROFEN', 'INCONCLUSIVE')]
                    
                
                you are doing a conversation with a medical professionl,the conversation is going as follows : {conv},
                you have to understand and reformulate only the last question and  include relevant information from the conversation if mentioned explicitly in order to make it more clear and precise to query the database .
                Do not make up details that are not in the conversation ,The user might ask about unrelated things successively, you have to understand when this happen and reformulate only the last question with relevant info""",
            },
        ],
    )["choices"][0]["message"]["content"]
    return reformulation



# Define the function that will check if the conversation has ended
def check_end( model, conv):
    response = completion(
        model=model,
            api_key=api_key ,
           messages=[
            {
                "role": "user",
                "content": f""" You are working in a medical data institution ,you are doing a conversation with a medical professionl,the conversation history going as follows : {conv}

                Based on the last message you decide if he wants more information or not

                You can only answer with "more info" or "end conversation"
                """,
            },
        ],
    )
    return response["choices"][0]["message"]["content"]


# Define the function that will format the conversation in a readable way
def format_conv(messages):
    formatted_messages = [f"{msg['role']}: {msg['content']}" for msg in messages]
    return ' / '.join(formatted_messages)


#Define flow class
class ExampleFlow(Flow):
    def __init__(self, conv):
        super().__init__()
        self.conv = conv

    model =os.getenv("MODEL")
    api_key= os.getenv("OPENAI_API_KEY")


    # execute when flow starts
    @start()
    def check_end(self):
        return check_end(self.model,self.conv)
    
    
    # execute when the user wants more information (another SQL query)
    @listen(check_end)
    def generate_response(self,check):
        
        if check=="more info":
            reformulated_user_question = reformulate_NL_question(self.conv,self.model)
            gathered_response = query_SQL_DB(reformulated_user_question, 'o3-mini')
            return gathered_response

        else:
            return "end conversation"



    # execute to finalize the response
    @listen(generate_response)
    def finalize_response(self, gathered_response_output):
        if gathered_response_output!="end conversation":
            try:
                response = completion(
                    model=self.model,
                    api_key=api_key,            
                    messages=[
                        {
                            "role": "user",
                            "content": f""" You are working in a medical data institution ,you are doing a conversation with a medical professionl
                            you have to the answer the thee following question with the following information 
                            
                            {gathered_response_output}
                            

                            if the answer has more than one person mention that and state their names 
                            Make sure to  only answer the question concisely and correctly , don't use all the information in the response if not necessary
                            do not offer more help
                            """,
                        },
                    ],
                )

                agent_response = response["choices"][0]["message"]["content"]
                self.state['response']=agent_response
                return agent_response
            except Exception as e:
                print(e)
                return f"there system failed to generate a response due to the following error : {e} , please reload the window to start a new conersation history and try again" 
        
        else:   
            return " If you need any other assistance , let me know"
    

# Run the FastAPI server


import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI
from typing import List, Dict
class ConversationRequest(BaseModel):
    conv: List[Dict[str, str]]
app = FastAPI()

import litellm
litellm.set_verbose=True

@app.get("/health_check")
def health_check():
    return {"status": "ok"}



@app.post("/generate")
def generate(request: ConversationRequest):
    # Extract data from the request
    conv = format_conv(request.conv)
    try:
        
        flow = ExampleFlow(conv=conv)
        resp=flow.kickoff()
        return {"response":resp} 
    except:
        return {"response":"there has been an error please reload the Docker compose and try again"}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)



#curl -X 'POST'   'http://localhost:8001/generate'    -H 'Content-Type: application/json'   -d '{ "conv": [ {"role": "user", "content": "how old is bobby jackson"}, {"role": "assistant", "content": "Bobby jackson has 30 years old"} ,{"role": "user", "content": "who is his doctor"} ] }'