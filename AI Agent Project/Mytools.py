from langchain_community.utilities import SerpAPIWrapper
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings, ChatOpenAI, OpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.agents import tool
from langchain_core.output_parsers import JsonOutputParser
import requests
import json

@tool
def search(query):
    """只有需要了解实时信息或不知道的事情的时候才会使用这个工具"""
    serp = SerpAPIWrapper()
    return serp.run(query)

@tool
def get_info_from_local(query):
    """只有回答与2024年运势或者龙年运势相关的问题的时候会使用这个工具"""
    client = Qdrant(
        QdrantClient(path="D:\VSCode\AI Agent Project\local_qdrant"),
        "local_documents",
        OpenAIEmbeddings()
    )
    retriever = client.as_retriever(search_type="mmr")
    results = retriever.get_relevant_documents(query)
    return results

@tool
def birth_fortune(query):
    """只有做八字排盘的时候才会使用这个工具,需要输入用户姓名和出生年月日,如果缺少用户姓名和出生年月日则不用"""
    url = "https://api.yuanfenju.com/index.php/v1/Bazi/cesuan"
    prompt = ChatPromptTemplate.from_template("""
                                              你是个参数查询助手，根据用户输入内容找出相关的参数并按json格式返回。
                                              JSON字段如下：-“api_key":"SvxFRRIZdhMU7eGX3qGaL2uaR", -"name":"姓名"，
                                              -"sex":"性别"，0表示男，1表示女，根据姓名判断", -"type":"日历类型，0农历，1公历，默认1"，
                                              -"year":"出生年份 例：1998"，-"month":"出生月份 例8"，-"day":"出生日期 例12"，
                                              -"hours":"出生小时 例9"，-"minute":“0”，如果没用找到相关参数，则需要提醒用户告诉你这些内容，
                                              只返回数据结构，不要有其他评论，用户输入：{input}
                                              """)
    parser = JsonOutputParser()
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())
    chain = prompt | ChatOpenAI(model="gpt-3.5-turbo", temperature=0) | parser
    data = chain.invoke({"input":query})
    result = requests.post(url, data=data)
    if result.status_code == 200:
        try:
            json = result.json()
            return "八字为: " + json["data"]["bazi_info"]["bazi"]
        except Exception as e:
            return "八字查询失败"
    else:
        return "技术错误，请稍后再试"

@tool
def yaoyigua():
    """只有用户想要占卜抽签的时候才会使用这个工具"""
    api_key = "SvxFRRIZdhMU7eGX3qGaL2uaR"
    url = "https://api.yuanfenju.com/index.php/v1/Zhanbu/yaogua"
    result = requests.post(url, data={"api_key":api_key})
    if result.status_code == 200:
        returnstring = json.loads(result.text)
        return returnstring
    else:
        return "技术错误，请稍后再试"
    
@tool
def dream(query):
    """只有用户想要解梦的时候才会使用这个工具，需要输入用户梦境的内容，如果缺少内容则不可用"""
    api_key = "SvxFRRIZdhMU7eGX3qGaL2uaR"
    url = "https://api.yuanfenju.com/index.php/v1/Gongju/zhougong"
    
    LLM = OpenAI(temperature=0)
    prompt = PromptTemplate.from_template("根据内容提取一个关键词，只返回关键词，内容为：{topic}")
    prompt_value = prompt.invoke({"topic":query})
    keyword = LLM.invoke(prompt_value)
    result = requests.post(url, data={"api_key":api_key, "title_zhougong":keyword})
    if result.status_code == 200:
        returnstring = json.loads(result.text)
        return returnstring
    else:
        return "技术错误，请稍后再试"