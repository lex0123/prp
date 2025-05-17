from pymongo import MongoClient
import numpy as np
import faiss
from openai import OpenAI
import json
from bs4 import BeautifulSoup
import requests
import chardet

# 连接到 MongoDB 数据库
client1 = MongoClient("mongodb://localhost:27017/")
db = client1["knowledge_database"]
collection = db["entities"]
dimension = 10  # 嵌入向量的维度
index = faiss.IndexFlatL2(dimension)

# 定义嵌入向量生成函数
def generate_embeddings(texts):
    client = OpenAI(api_key="sk-57985661b21e4faf8eb0510447972368", base_url="https://api.deepseek.com")  # 替换为您的 DeepSeek API 密钥
    embeddings = []
    target_dimension = 10  # 假设目标维度为 10
    for text in texts:
        print(text)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "转化为10维嵌入向量,只需要输出单个向量,不需要打印任何其他信息"},
                {"role": "user", "content": f"转化为10维嵌入向量,只需要输出单个嵌入式向量,不需要打印任何其他信息: {text}"}
            ],
            stream=False
        )
        embedding = response.choices[0].message.content
        print("API 返回的嵌入内容:", embedding)
        try:
            # 使用 JSON 解析嵌入向量
            embedding_vector = np.array(json.loads(embedding))
            # 检查是否为有效的数值数组
            if not np.issubdtype(embedding_vector.dtype, np.number):
                raise ValueError("嵌入向量包含非法值")
            # 调整向量维度为目标维度
            if len(embedding_vector) > target_dimension:
                embedding_vector = embedding_vector[:target_dimension]  # 截断多余部分
            elif len(embedding_vector) < target_dimension:
                embedding_vector = np.pad(embedding_vector, (0, target_dimension - len(embedding_vector)), mode='constant')  # 填充0
            embeddings.append(embedding_vector)
        except Exception as e:
            print("解析嵌入向量失败:", e)
            print("原始嵌入内容:", embedding)
            continue
    return np.array(embeddings)


# 获取网页内容
print("请输入需要增加关系的网页地址:")
url = input()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
response = requests.get(url, headers=headers)
response.encoding = response.apparent_encoding  
context = response.text

# 提取人物关系并生成数据
query = "从提取中的网页内容中提取出人物关系,并将其转化为知识库中的数据格式。人物关系的格式为:人物1 关联关系 人物2,如参加大会X的名单有:A,B,C...,那么A,B,C之间都添加\
    关系,这个关系形式是A 共同参加大会X B,输出格式为[{\"人物1\": \"A\", \"关联关系\": \"X\", \"人物2\": \"B\"}...],只需要输出输出格式要求内容就可以,以纯文本形式输出,不需要以json格式输出,注意外面加上[],不需要输出其他的任何东西"
client = OpenAI(api_key="sk-57985661b21e4faf8eb0510447972368", base_url="https://api.deepseek.com")
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个知识问答助手,基于提供的上下文回答问题。"},
        {"role": "user", "content": f"上下文: {context}\n问题: {query}"}
    ],
    stream=False
)

try:
    # 解析返回的数据
    data = json.loads(response.choices[0].message.content)
    
    print("标准化后的数据:", data)
    # 插入到 MongoDB 数据库
    collection.insert_many(data)
    print("数据已成功插入知识库！")
    # 为每条数据生成嵌入向量并更新 FAISS 索引
    documents = [f"{row['人物1']} {row['关联关系']} {row['人物2']}" for row in data]
    print("文档数据:", documents)
    embeddings = generate_embeddings(data)
    print("嵌入向量:", embeddings)
    index.add(embeddings.astype('float32'))
    print("嵌入向量已成功添加到 FAISS 索引！")
    # 保存 FAISS 索引
    faiss.write_index(index, "vector_index.faiss")
    print("FAISS 索引已保存！")
except json.JSONDecodeError as e:
    print("解析 JSON 数据失败:", e)

