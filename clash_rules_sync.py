import re
import sys
import os
from collections import defaultdict
import requests
import time


def parse_markdown_tables(markdown_text):
    """解析Markdown文本中的所有表格"""
    # 匹配整个表格的正则表达式
    table_pattern = r'\|(.+?)\|\s*\n\|\s*-+\s*\|.+?\|\s*\n((?:\|.+?\|\s*\n)+)'
    tables = re.findall(table_pattern, markdown_text, re.DOTALL)

    result = []
    
    for table in tables:
        # 获取表头行
        header_row = table[0].strip()
        # 获取数据行
        data_rows = table[1].strip().split('\n')
        
        # 解析表头
        headers = [h.strip() for h in header_row.split('|') if h.strip()]
        if not headers:
            continue
        
        # 使用第一个表头作为分类
        category = headers[0]
        # 创建表格数据结构
        table_data = {
            'category': category,
            'links': []
        }
        # 解析每一行数据
        for row in data_rows:
            cells = [cell.strip() for cell in row.split('|') if cell.strip()]
            
            # 提取所有链接
            for cell in cells:
                # 使用正则表达式匹配链接
                links = re.findall(r'https?://[^\s]+', cell)
                for link in links:
                    table_data['links'].append(link)
        
        # 将表格数据添加到结果列表
        result.append(table_data)
    
    return result


def get_last_part(url):
    # 使用正则表达式匹配URL的最后一部分
    match = re.search(r'/([^/?]+)/?(?:\?.*)?$', url)
    if match:
        return match.group(1)
    return ""


def download_and_merge(category, links):
    print(f"开始下载 {category} 分类的规则...")
    output_file=category+'.ymal'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"payload:\n")
    for link in links:
        link=link.replace(')','')
        link=link+'/'+get_last_part(link)+'.list'
        try:
            # 添加延迟避免请求过快
            time.sleep(1)
            raw_link = link.replace('github.com', 'raw.githubusercontent.com').replace('tree', 'refs/heads')
            # 下载内容
            print(f"下载: {raw_link}")
            response = requests.get(raw_link, timeout=10)

            if response.status_code == 200:
                for line in response.text.splitlines():
                    if line.strip() and not line.startswith('#'): 
                        with open(output_file, 'a', encoding='utf-8') as f:
                            f.write('  - '+line + '\n')

                print(f"成功下载并添加内容: {link}")
            else:
                print(f"下载失败 ({response.status_code}): {link}")
                # 记录失败的链接
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(f"## 下载失败: {link} (状态码: {response.status_code})\n\n")
        
        except Exception as e:
            print(f"处理链接时出错: {link}")
            print(f"错误: {str(e)}")


def main():
    response = requests.get('https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/README.md')
    markdown_text = response.text
    markdown_blocks = markdown_text.split('\n\n')
    all_tables = []
    for block in markdown_blocks:
        if '|' in block:  # 只处理包含表格标记的块
            tables_in_block = parse_markdown_tables(block)
            all_tables.extend(tables_in_block)
    print(f"找到 {len(all_tables)} 个表格")
    
    # 显示表格信息
    for table in all_tables:  # 直接遍历all_tables中的每个表格数据
        print(f"\n分类: {table['category']}")
        download_and_merge(table['category'], table['links'])
    
    





if __name__ == "__main__":
    main()
