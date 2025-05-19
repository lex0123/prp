import requests
from bs4 import BeautifulSoup
import os
import time
import random
import re
import concurrent.futures
from urllib.parse import urljoin
# 添加数据库模块导入
import sqlite3
from datetime import datetime

class NewsCrawler:
    def __init__(self, base_url, save_dir="corpus", db_path=None):
        self.base_url = base_url
        self.save_dir = save_dir
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.all_news_links = []
        
        # 创建保存目录
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        # 初始化数据库
        if db_path is None:
            self.db_path = os.path.join(save_dir, "corpus.db")
        else:
            self.db_path = db_path
        
        self.init_database()
    
    def init_database(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建新闻表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT
        )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON news (title)')    
        conn.commit()
        conn.close()
        print(f"数据库已初始化：{self.db_path}")
    
    def get_news_links(self, page_url):
        try:
            response = requests.get(page_url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有的新闻项
            news_items = soup.select('li.item a.card')
            news_links = []
            
            # 正确获取基础域名
            base_domain = "https://news.sjtu.edu.cn"
            
            print(f"找到 {len(news_items)} 个新闻项")
            for item in news_items:
                link = item.get('href')
                if link:
                    # 提取相对链接，例如 /jdyw/20250515/210548.html
                    print(f"发现链接: {link}")
                    
                    # 处理相对链接
                    if not link.startswith('http'):
                        # 使用urljoin正确拼接URL
                        full_link = urljoin(base_domain, link)
                        news_links.append(full_link)
                    else:
                        news_links.append(link)
                
            return news_links
        
        except Exception as e:
            print(f"获取新闻列表出错: {e}")
            return []
    
    def get_news_content(self, news_url):
        try:
            response = requests.get(news_url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            title = soup.select_one('title').text.strip() if soup.select_one('title') else "无标题"
            # 提取内容
            content_elements = soup.select('div.Article_content p')
            content = '\n'.join([p.text.strip() for p in content_elements if p.text.strip()])
            
            return title, content
        
        except Exception as e:
            print(f"获取新闻内容出错 {news_url}: {e}")
            return "获取失败", "内容获取失败", "", ""
    
    def save_to_corpus(self, title, content, news_url, file_index):
        """保存新闻内容到语料库文件和数据库，确保标题唯一
        
        Args:
            title: 新闻标题
            content: 新闻正文
            news_url: 新闻URL
            file_index: 文件索引
        """
        file_path = os.path.join(self.save_dir, f"news_{file_index}.txt")

        # 始终保存到文本文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"标题: {title}\n")
            f.write(f"来源URL: {news_url}\n")
            f.write(f"正文内容:\n{content}\n")

        # 添加数据库插入代码
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查标题是否已存在
            cursor.execute("SELECT COUNT(*) FROM news WHERE title = ?", (title,))
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                # 标题不存在，插入新记录
                cursor.execute(
                    "INSERT INTO news (title, content) VALUES (?, ?)",
                    (title, content)
                )
                
                # 提交事务并关闭连接
                conn.commit()
                print(f"新闻 #{file_index} '{title[:20]}...' 已保存到数据库")
            else:
                print(f"跳过重复标题: '{title[:20]}...'")
            
            conn.close()
        except Exception as e:
            print(f"保存到数据库出错: {e}")
    def process_news(self, args):
        link, index = args
        try:
            print(f"正在爬取第 {index + 1} 条新闻: {link}")
            title, content= self.get_news_content(link)
            
            if content != "内容获取失败":
                self.save_to_corpus(title, content, link, index + 1)
                # 添加随机延时，防止被封IP
                sleep_time = random.uniform(0.5, 1.5)
                time.sleep(sleep_time)
                return True
        except Exception as e:
            print(f"处理新闻出错 {link}: {e}")
        
        return False
    
    def crawl(self, start_page=2, end_page=2, max_news=500, max_workers=10):
        # 先获取所有页面的新闻链接
        for page in range(start_page, end_page + 1):
            page_url = self.base_url.format(i=page)
            print(f"正在获取第 {page} 页的新闻列表: {page_url}")
            
            news_links = self.get_news_links(page_url)
            print(f"在第 {page} 页找到 {len(news_links)} 条新闻链接")
            self.all_news_links.extend(news_links)
        
        # 打印所有收集到的新闻链接
        print("\n====== 所有新闻网站链接 ======")
        for i, link in enumerate(self.all_news_links):
            print(f"{i+1}. {link}")
        print("============================\n")
        
        # 限制最大新闻数量
        if len(self.all_news_links) > max_news:
            self.all_news_links = self.all_news_links[:max_news]
            print(f"已限制新闻数量为 {max_news} 条")
        
        # 准备线程池参数
        args_list = [(link, i) for i, link in enumerate(self.all_news_links)]
        
        # 使用线程池处理新闻
        total_news = len(args_list)
        successful_news = 0
        
        print(f"\n开始使用线程池爬取新闻，总数: {total_news}，最大线程数: {max_workers}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(self.process_news, args_list))
            successful_news = results.count(True)
        
        print(f"\n爬取完成，成功获取 {successful_news} 条新闻，失败 {total_news - successful_news} 条")

def main():
    # 上海交通大学新闻网站基础URL
    base_url = "https://news.sjtu.edu.cn/jdyw/index_{i}.html"
    
    # 创建爬虫实例
    crawler = NewsCrawler(base_url, save_dir="corpus")
    
    # 爬取第2页到第5页的新闻，使用20个线程
    crawler.crawl(start_page=2, end_page=50, max_news=500, max_workers=20)
    
    print("爬取完成，新闻已保存到 corpus 目录")

if __name__ == "__main__":
    main()