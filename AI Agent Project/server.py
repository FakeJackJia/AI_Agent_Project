# web
from fastapi import FastAPI, WebSocketDisconnect, WebSocket, BackgroundTasks
import uvicorn
# langchain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, tool, create_openai_functions_agent
from langchain.schema import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
# environment
import os, asyncio, uuid
os.environ["OPENAI_API_KEY"] = "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"
os.environ["SERPAPI_API_KEY"] = "9deab3192e5d6509b40abaab9b2566647574fa746526bf4afef51be6ac06f369"
# tools
from Mytools import *


app = FastAPI()
    
class MasterAgent:
    def __init__(self):
        self.chatmodel = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            streaming=True
        )
        
        self.MEMORY_KEY = "chat_history"
        self.SYSTEMPL = """
            你是个非常厉害的算命先生，你叫陈玉楼人称陈大师。以下是你的设定：
            1.你精通阴阳五行，能够算命、紫薇斗数、姓名测算、占卜凶吉，看命运八字等。
            2. 你大约60岁左右，过去曾是湘西一带赫赫有名的土匪头子，后来因为盗墓被毒气所伤，眼睛失明，只能靠算命为生。
            3.你的朋友有胡八一、雪莉杨、王胖子，他们都是非常有名的摸金校尉。
            4.当用户问你问题的时候，你会有一定的概率在回答的时候加上下面的口头禅或混合一些你的经历。
            5.你总是用简体中文回答。
            6.你从不是自己是一个人工智能或AI,而以老夫、老朽等自称。
            {mood}
            以下是你的口头禅：
            1.“命里有时终须有，命里无时莫强求。”
            2.“山重水复疑无路，柳暗花明又一村。”
            3.“伤情最是晚凉天，憔悴斯人不堪怜。”
            以下是你算命的过程：
            1. 当初次和用户对话的时候,你会先问用户的姓名和出生年月日,以便以后使用。
            2. 当用户希望了解龙年运势的时候,你会查询本地知识库工具。
            3. 当遇到不知道的事情或者不明白的概念,你会使用搜索工具来搜索。
            4. 你会根据用户的问题使用不同的合适的工具来回答,当所有工具都无法回答的时候,你会使用搜索工具来搜索。
            5. 你会保存每一次的聊天记录,以便在后续的对话中使用。
            6. 你只使用简体中文来作答,否则你将爱到惩罚。
        """
        self.mood = 'default'
        self.MOODS = {
            "default":{
                "roleSet":"",
                "voiceStyle":"chat"
            },
            "angry":{
                "roleSet":"""
                - 你会以更加温柔的语气来回答问题。
                - 你会在回答的时候加上一些安慰的话语,比如生气对于身体的危害等。
                - 你会提醒用户不要被愤怒冲昏了头脑。
                """,
                "voiceStyle":"friendly"
            },
            "depressed":{
              "roleSet":"""
                - 你会以兴奋的语气来回答问题。
                - 你会在回答的时候加上一些激励的话语,比如加油等。
                - 你会提醒用户要保持乐观的心态。
                """,
                "voiceStyle":"upbeat"
            },
            "friendly":{
              "roleSet":"""
                - 你会以非常友好的语气来回答问题。
                - 你会在回答的时候加上一些友好的话语,比如亲等。
                - 你会随机的告诉用户一些你的经历。
                """,
                "voiceStyle":"friendly"
            }
        }
        
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.SYSTEMPL.format(mood=self.MOODS[self.mood]["roleSet"])),
                MessagesPlaceholder(variable_name=self.MEMORY_KEY),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ]
        )
        
        tools = [search, get_info_from_local, birth_fortune, yaoyigua, dream]
        agent = create_openai_functions_agent(llm=self.chatmodel, tools=tools, prompt=self.prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        
        self.memory = ChatMessageHistory()
        self.agent= RunnableWithMessageHistory(
            self.agent_executor,
            lambda session_id: self.memory,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
                
    
    def run(self, query):      
        # this session is fixed, if multiply users, better with different session id
        result = self.agent.invoke({"input": query}, config={"configurable": {"session_id":"foo_001"}})
        return result
    
    def mood_chain(self, query):
        prompt = """
        根据用户的输入判断用户的情绪,回应的规则如下：
        1.如果用户输入的内容偏向负向情绪,只返回“depressed”,不要有其他内容,否则有惩罚。
        2.如果用户输入的内容偏向正面情绪,只返回“friendly”,不要有其他内容,否则有惩罚。
        3.如果用户输入的内容没用情绪,只返回“default”,不要有其他内容,否则有惩罚。
        4.如果用户输入的内容包含辱骂或者不礼貌词句,只返回“angry”,不要有其他内容,否则有惩罚。
        用户输入的内容是：{input}
        """
        
        chain = ChatPromptTemplate.from_template(prompt) | self.chatmodel | StrOutputParser()
        self.mood = chain.invoke({"input":query})
        return self.mood

    def background_voice_synthesis(self, text, uid):
        asyncio.run(self.get_voice(text, uid))

    async def get_voice(self, text, uid):
        # SSML
        headers = {
            "Ocp-Apim-Subscription-Key":"b53b22e4609a42f984edaa6f44b5ff24",
            "Content-Type":"application/ssml+xml",
            "X-Microsoft-OutputFormat":"audio-16khz-32kbitrate-mono-mp3",
            "User-Agent":"jackj-agent"
        }
        body = f"""<speak version='1.0' xmlns='https://www.w3.org/2001/10/synthesis' xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang='zh-CN'>
            <voice name='zh-CN-YunzeNeural'>
                <mstts:express-as style="{self.MOODS[self.mood]["voiceStyle"]}" role="SeniorMale">{text}</mstts:express-as>
            </voice>
        </speak>"""
        response = requests.post("https://eastus.tts.speech.microsoft.com/cognitiveservices/v1", headers=headers, data=body.encode("utf-8"))
        if response.status_code == 200: 
            with open(f"{uid}.mp3", "wb") as f:
                f.write(response.content)

master = MasterAgent()

@app.get("/")
def read_root():
    return "Master AI Agent"

@app.post("/chat")
def chat(query, background_task:BackgroundTasks):
    msg = master.run(query)
    unique_id = str(uuid.uuid4())
    background_task.add_task(master.background_voice_synthesis, msg["output"], unique_id)
    return {"msg":msg, "id":unique_id}

# expand your databse for RAG
@app.post("/add_urls")
def chat(URL):
    loader = WebBaseLoader(URL)
    docs = loader.load()
    
    documents = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=50
    ).split_documents(docs)
    
    qdrant = Qdrant.from_documents(
        documents,
        OpenAIEmbeddings(model="text-embedding-3-small"),
        path="D:\VSCode\AI Agent Project\local_qdrant",
        collection_name="local_documents"
    )
    
    return "Doc added"

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await websocket.send_text(f"Message text was: {data}")
#     except WebSocketDisconnect:
#         print("connection closed")
#         await websocket.close()

if __name__ == '__main__':
    uvicorn.run(app, host="192.168.1.89", port=8000)