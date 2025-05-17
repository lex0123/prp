from pymongo import MongoClient
import networkx as nx
import numpy as np
import faiss
from openai import OpenAI
import json

# 连接到 MongoDB 数据库
client1 = MongoClient("mongodb://localhost:27017/")
db = client1["knowledge_database"]
collection = db["entities"]
# collection.delete_many({})  # 清空集合
# data = [
#     {"人物1": "李教授", "关联关系": "共同出席了a会议", "人物2": "王教授"},
#     {"人物1": "李教授", "关联关系": "师生", "人物2": "小王"},
#     {"人物1": "小王", "关联关系": "同学", "人物2": "小李"},
#     {"人物1": "王教授", "关联关系": "师生", "人物2": "小李"},
# ]
# collection.insert_many(data)
        
# print("数据已插入知识库！")

rows = list(collection.find({}, {"_id": 0, "人物1": 1, "关联关系": 1, "人物2": 1}))
documents = [f"{row['人物1']} {row['关联关系']} {row['人物2']}" for row in rows]
print("文档数据:", documents)

def generate_embeddings(texts):
    client = OpenAI(api_key="sk-57985661b21e4faf8eb0510447972368", base_url="https://api.deepseek.com")  # 替换为您的 DeepSeek API 密钥
    embeddings = []
    target_dimension = 10  # 假设目标维度为 10
    for text in texts:
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

# # 生成嵌入向量
# document_vectors = generate_embeddings(documents)

# # 创建 FAISS 索引
# dimension = len(document_vectors[0])
# index = faiss.IndexFlatL2(dimension)
# index.add(np.array(document_vectors).astype('float32'))

# # 保存索引
# faiss.write_index(index, "vector_index.faiss")
# print("FAISS 索引已创建！")

#加载 FAISS 索引
index = faiss.read_index("vector_index.faiss")

# 用户查询

query = input("请输入查询内容:")
query1="回答举例:如果接受到上下文为A 师生 B ,B 同学 C ,那么如果提问A和C的关系,你应该回答A和C所有关联的关系,即A和B是师生,B和C是同学,回答格式为A（师生）→ B(同学）→ C注意中间可以通过多个关联人进行关联，不需要直接的关系"
# 生成查询向量
query_vector = generate_embeddings([query])[0]
query=query1+query
# 检索最相似的文档
k = 100
distances, indices = index.search(np.array([query_vector]).astype('float32'), k)

# 获取检索到的文档并去重
retrieved_data = list(set(documents[i] for i in indices[0]))
print("检索到的文档:", retrieved_data)

# 将检索到的文档作为上下文,结合查询生成答案
context = ",".join(retrieved_data)  # 将检索到的文档拼接为上下文
print("上下文:", context)

# 使用生成模型生成答案
client = OpenAI(api_key="sk-57985661b21e4faf8eb0510447972368", base_url="https://api.deepseek.com")
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个知识问答助手,基于提供的上下文回答问题。"},
        {"role": "user", "content": f"上下文: {context}\n问题: {query}"}
    ],
    stream=False
)

# 输出生成的答案
answer = response.choices[0].message.content
print("生成的答案:", answer)

# # 创建图分析模块
# G = nx.Graph()
# for row in rows:
#     G.add_edge(row["人物1"], row["人物2"], 关联关系=row["关联关系"])

# # 查询最短路径
# source = "阿尔伯特·爱因斯坦"
# target = "玛丽·居里"
# try:
#     shortest_path = nx.shortest_path(G, source=source, target=target)
#     print("最短路径:", shortest_path)
#     print("路径详情:")
#     for i in range(len(shortest_path) - 1):
#         人物1 = shortest_path[i]
#         人物2 = shortest_path[i + 1]
#         关联关系 = G[人物1][人物2]["关联关系"]
#         print(f"{人物1} {关联关系} {人物2}")
# except nx.NetworkXNoPath:
#     print(f"No path found between {source} and {target}.")

# 打印所有索引及其对应的内容
# print("所有索引及其对应的内容:")
# for i in range(index.ntotal):  # 遍历所有索引
#     try:
#         # 获取向量
#         vector = index.reconstruct(i)
#         # 获取对应的文档
#         document = documents[i]
#         print(f"索引: {i}")
#         print(f"文档: {document}")
#         print(f"向量: {vector}")
#         print("-" * 50)
#     except Exception as e:
#         print(f"无法获取索引 {i} 的内容，错误: {e}")