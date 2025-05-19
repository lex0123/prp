import requests
from bs4 import BeautifulSoup
import os
import time
import random
import re
import json
import concurrent.futures
from urllib.parse import urljoin, urlparse
import sqlite3
from datetime import datetime
import openai  # 用于调用DeepSeek API
import ssl
from urllib3.poolmanager import PoolManager
import requests.adapters
# 使用自定义会话发送请求
# 替换sites列表，更新为50所高校
sites = [
    {"name": "清华大学", "url": "https://www.ee.tsinghua.edu.cn/dzxw/tpxw/73.htm"},
    # {"name": "北京大学", "url": "https://ele.pku.edu.cn/xwdt/27.htm"},
    # {"name": "复旦大学", "url": "http://www.it.fudan.edu.cn/Data/List/xyxw?page=2"},
    # {"name": "上海交通大学", "url": "https://www.seiee.sjtu.edu.cn/index_news/p3.html"},
    # {"name": "浙江大学", "url": "http://www.isee.zju.edu.cn/21123/list5.htm"},
    # {"name": "南京大学", "url": "https://www.nju.edu.cn/xww/zhxw/1062.htm"},
    # {"name": "中国科学技术大学", "url": "https://cs.ustc.edu.cn/3058/list2.htm"},
    # {"name": "中国人民大学", "url": "http://info.ruc.edu.cn/xwgg/xyxw/index.htm"},
    # {"name": "武汉大学", "url": "https://news.whu.edu.cn/wdzx/wdyw.htm"},
    # {"name": "南开大学", "url": "https://ceo.nankai.edu.cn/syxxwlm/xyxw.htm"},
    # {"name": "北京航空航天大学", "url": "https://www.ee.buaa.edu.cn/index/xyyw1.htm"},
    # {"name": "同济大学", "url": "https://see.tongji.edu.cn/index/xyxw/190.htm"},
    # {"name": "华中科技大学", "url": "https://ei.hust.edu.cn/tpxw/6.htm"},
    # {"name": "西安交通大学", "url": "https://esteie.xjtu.edu.cn/xwyhd/xw/3.htm"},
    # {"name": "北京理工大学", "url": "https://www.bit.edu.cn/xww/zhxw/index1.htm"},
    # {"name": "天津大学", "url": "https://news.tju.edu.cn/xnxw1/qb.htm"},
    # {"name": "东南大学", "url": "https://news.seu.edu.cn/xsdt/list.htm"},
    # {"name": "哈尔滨工业大学", "url": "https://news.hit.edu.cn/xxyw/list2.htm"},
    # {"name": "四川大学", "url": "https://news.scu.edu.cn/ztxw/kxyj/38.htm"},
    # {"name": "厦门大学", "url": "https://news.xmu.edu.cn/xwzh/kxyj/11.htm"},
    # {"name": "华南理工大学", "url": "https://news.scut.edu.cn/41/list2.htm"},
    # {"name": "中山大学", "url": "https://research.sysu.edu.cn/news?page=1"},
    # {"name": "大连理工大学", "url": "https://news.dlut.edu.cn/xsky/59.htm"},
    # {"name": "山东大学", "url": "https://www.view.sdu.edu.cn/xszh/336.htm"},
    # {"name": "吉林大学", "url": "https://news.jlu.edu.cn/jdxw/xykx/175.htm"},
    # {"name": "西北工业大学", "url": "https://news.nwpu.edu.cn/xsky/4.htm"},
    # {"name": "兰州大学", "url": "https://news.lzu.edu.cn/xyudt/xsky/24.htm"},
    # {"name": "中南大学", "url": "https://news.csu.edu.cn/jxky/46.htm"},
    # {"name": "电子科技大学", "url": "https://news.uestc.edu.cn/"},
    # {"name": "湖南大学", "url": "https://news.hnu.edu.cn/zhyw.htm"},
    # {"name": "东北大学", "url": "https://neunews.neu.edu.cn/xsky/xsdt.htm"},
    # {"name": "重庆大学", "url": "https://news.cqu.edu.cn/archives/trnews/list/2.html"},
    # {"name": "北京师范大学", "url": "https://news.bnu.edu.cn/zx/xzdt/index2.htm"},
    # {"name": "华东师范大学", "url": "http://www.cee.ecnu.edu.cn/xyxw/list3.htm"},
    # {"name": "中国海洋大学", "url": "https://news.ouc.edu.cn/xshd/list3.htm"},
    # {"name": "西南大学", "url": "https://ceie.swu.edu.cn/xxgk/xyxw/25.htm"},
    # {"name": "西南交通大学", "url": "https://news.swjtu.edu.cn/zx/jdyw/396.htm"},
    # {"name": "中国农业大学", "url": "https://coe.cau.edu.cn/col/col27675/index.html?uid=61008&pageNum=2"},
    # {"name": "北京科技大学", "url": "https://mse.ustb.edu.cn/kexueyanjiu/keyandong/"},
    # {"name": "南京理工大学", "url": "https://zs.njust.edu.cn/3558/list2.htm"},
    # {"name": "哈尔滨工程大学", "url": "https://news.hrbeu.edu.cn/xs/xscg/5.htm"},
    # {"name": "北京交通大学", "url": "https://news.bjtu.edu.cn/xysx/jxky/72.htm"},
    # {"name": "华中师范大学", "url": "https://kjc.ccnu.edu.cn/xsdt/10.htm"},
    # {"name": "暨南大学", "url": "https://news.jnu.edu.cn/col3_2.html"},
    # {"name": "南京航空航天大学", "url": "https://newsweb.nuaa.edu.cn/kjzx1/list2.htm"},
    # {"name": "华南师范大学", "url": "http://jky.scnu.edu.cn/xyxw/xwdt/2.html"},
    # {"name": "北京工业大学", "url": "https://news.bjut.edu.cn/gdyw/123.htm"},
    # {"name": "电子科技大学", "url": "https://kjb.szu.edu.cn/kydongta/kydt/65.htm"},
    # {"name": "中央民族大学", "url": "https://law.muc.edu.cn/xyxw/56.htm"},
    # {"name": "北京邮电大学", "url": "https://kyy.bupt.edu.cn/kydt/14.htm"}
]
def FindCss_selector():
    for site in sites:
        api_key = os.getenv("deepseek-api-key")
        api_base = "https://api.deepseek.com/v1"
        headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
        site_url = site["url"]
        site_name = site["name"]
        html_content = requests.get(site_url, headers=headers).text
        def analyze_site_with_deepseek(html_content, site_url, site_name):
            """使用DeepSeek模型分析网站HTML，识别新闻链接模式
            
            Args:
                html_content: 网站HTML内容
                site_url: 网站URL
                site_name: 网站名称
                
            Returns:
                pattern_dict: 包含链接模式的字典
            """
            try:
                # 解析HTML
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 提取所有链接供模型分析
                all_links = soup.find_all('a', href=True)
                link_samples = [f"{a.get_text().strip()} - {a['href']}" for a in all_links[:20] if a.get_text().strip()]
                
                # 准备发送给大模型的提示
                prompt = f"""
                {html_content}
                分析下面这个大学新闻列表网站的内容，其中包含很多新闻，找出其中的新闻文章的链接。:
                要求并提供以下信息:
                1. 一个选择器css_selector，可以用来选择该页面所有新闻链接,其中html是我传给你的网页内容
                我可以直接调用python代码
                soup = BeautifulSoup(html, 'html.parser')
                news_items = soup.select(“css_selector”)
                2. 新闻链接的基础连接base_domain
                获得其中包含的所有新闻链接，并且采用base_domain+news_items来直接访问网站
                
            
                请以JSON格式返回你的分析结果，格式如下:
                {{
                    "css_selector": "最佳CSS选择器",
                    "base_domain": "基础域名",
                    "sample_links": ["3个你识别的示例新闻链接，他们的链接和标题拼接起来"],
                }}
                """
                
                # 调用DeepSeek API获取分析结果
                if not api_key:
                    print(f"未提供API密钥，使用默认模式分析 {site_name}")
                    # 返回默认模式
                    base_domain = "https://" + urlparse(site_url).netloc
                    return {
                        "css_selector": "li a, div.news-list a, .news-item a",
                        "base_domain": base_domain,
                        "sample_links": []
                    }
                
                # 调用DeepSeek API
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer { api_key}"
                }
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "你是一个专业的网页分析工具，擅长识别网站结构和链接模式。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1500
                }
                
                response = requests.post(
                    f"{api_base}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    print(f"API请求失败: {response.status_code} {response.text}")
                    raise Exception(f"API请求失败: {response.status_code}")
                    
                result = response.json()
                analysis_text = result["choices"][0]["message"]["content"]
                print(f"\nDeepSeek分析结果({site_name}):\n{analysis_text}")
                
                # 提取JSON部分
                json_match = re.search(r'```json\s*({.*?})\s*```', analysis_text, re.DOTALL)
                if json_match:
                    analysis_json = json.loads(json_match.group(1))
                else:
                    # 尝试直接解析整个文本为JSON
                    try:
                        analysis_json = json.loads(analysis_text)
                    except:
                        # 使用正则表达式匹配整个JSON部分
                        json_match = re.search(r'{.*}', analysis_text, re.DOTALL)
                        if json_match:
                            analysis_json = json.loads(json_match.group(0))
                        else:
                            print(f"无法解析返回的JSON数据，使用默认模式 - {site_name}")
                            base_domain = "https://" + urlparse(site_url).netloc
                            analysis_json = {
                                "css_selector": "li a, div.news-list a, .news-item a",
                                "base_domain": base_domain,
                                "sample_links": []
                            }
                return analysis_json["css_selector"], analysis_json["base_domain"]
                
            except Exception as e:
                print(f"分析网站 {site_name} 出错: {e}")
                # 返回默认模式
                base_domain = "https://" + urlparse(site_url).netloc
                return {
                    "css_selector": "li a, div.news-list a, .news-item a",
                    "base_domain": base_domain,
                    "sample_links": []
                }
        def analyze_site_content_with_deepseek(html_content):
            """使用DeepSeek模型分析网站HTML，识别新闻链接模式
            
            Args:
                html_content: 网站HTML内容
                site_url: 网站URL
                site_name: 网站名称
                
            Returns:
                pattern_dict: 包含链接模式的字典
            """
            try:
                # 解析HTML
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 提取所有链接供模型分析
                all_links = soup.find_all('a', href=True)
                link_samples = [f"{a.get_text().strip()} - {a['href']}" for a in all_links[:20] if a.get_text().strip()]
                
                # 准备发送给大模型的提示
                prompt = f"""
                {html_content}
                分析下面这个大学新闻网站的内容。:
                要求并提供以下信息:
                1. 两个选择器css_selector1，css_selector2，可以用来选择该页面新闻标题和内容,其中html是我传给你的网页内容
                我可以直接调用python代码
                soup = BeautifulSoup(html, 'html.parser')
                news_items = soup.select(“css_selector1”)
                获得新闻标题
                新闻的标题是中文
                news_items = soup.select(“css_selector2”)
                获得新闻内容
                新闻的内容是是很长的中文段落
                
            
                请以JSON格式返回你的分析结果，格式如下:
                {{
                    "css_selector1": "标题选择器",
                    "css_selector2": "内容选择器",
                }}
                """
                
                # 调用DeepSeek API获取分析结果
                if not api_key:
                    print(f"未提供API密钥，使用默认模式分析 {site_name}")
                    # 返回默认模式
                    base_domain = "https://" + urlparse(site_url).netloc
                    return {
                        "css_selector1": "li a, div.news-list a, .news-item a",
                        "css_selector2": "li a, div.news-list a, .news-item a",
                    }
                
                # 调用DeepSeek API
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer { api_key}"
                }
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "你是一个专业的网页分析工具，擅长识别网站结构和链接模式。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1500
                }
                
                response = requests.post(
                    f"{api_base}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    print(f"API请求失败: {response.status_code} {response.text}")
                    raise Exception(f"API请求失败: {response.status_code}")
                    
                result = response.json()
                analysis_text = result["choices"][0]["message"]["content"]
                print(f"\nDeepSeek分析结果({site_name}):\n{analysis_text}")
                
                # 提取JSON部分
                json_match = re.search(r'```json\s*({.*?})\s*```', analysis_text, re.DOTALL)
                if json_match:
                    analysis_json = json.loads(json_match.group(1))
                else:
                    # 尝试直接解析整个文本为JSON
                    try:
                        analysis_json = json.loads(analysis_text)
                    except:
                        # 使用正则表达式匹配整个JSON部分
                        json_match = re.search(r'{.*}', analysis_text, re.DOTALL)
                        if json_match:
                            analysis_json = json.loads(json_match.group(0))
                        else:
                            print(f"无法解析返回的JSON数据，使用默认模式 - {site_name}")
                            base_domain = "https://" + urlparse(site_url).netloc
                            analysis_json = {
                                "css_selector1": "li a, div.news-list a, .news-item a",
                                "css_selector2": "li a, div.news-list a, .news-item a",
                            }
                return analysis_json["css_selector1"], analysis_json["css_selector2"]
                
            except Exception as e:
                print(f"分析网站 {site_name} 出错: {e}")
                # 返回默认模式
                base_domain = "https://" + urlparse(site_url).netloc
                return {
                    "css_selector1": "li a, div.news-list a, .news-item a",
                    "css_selector2": "li a, div.news-list a, .news-item a",
                }
        css_selector,base_domain=analyze_site_with_deepseek(html_content, site_url, site_name)
        print(f"分析结果: CSS选择器: {css_selector}, 基础域名: {base_domain}")
        soup = BeautifulSoup(html_content, 'html.parser')
        news_items = soup.select(css_selector)
        news_links = []
        print(f"找到 {len(news_items)} 个新闻项")
        full_links = ""
        for item in news_items:
            link = item.get('href')
            if link:
                # 提取相对链接，例如 /jdyw/20250515/210548.html
                print(f"发现链接: {link}")
                # 处理相对链接
                if  link.startswith('/'):
                    # 使用urljoin正确拼接URL
                    full_link = urljoin(base_domain, link)
                    news_links.append(full_link)
                else:
                    news_links.append(link)
        response = requests.get(full_link, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        css_selector1,css_selector2=analyze_site_content_with_deepseek(response.text)
        # 在函数末尾添加选择器到site字典
        site["css_selector"] = css_selector
        site["base_domain"] = base_domain
        site["title_selector"] = css_selector1
        site["content_selector"] = css_selector2
    return sites
if __name__ == "__main__":
    print(FindCss_selector())