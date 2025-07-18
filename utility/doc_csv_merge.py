import pandas as pd

def merge_csv_files():
    # 读取两个CSV文件
    df_func = pd.read_csv('functions.csv')
    df_doc = pd.read_csv('method_doc.csv')
    
    # 以"方法"列为key进行合并
    merged_df = pd.merge(df_func, df_doc, on='方法', how='outer')
    
    # 保存合并后的结果
    merged_df.to_csv('akshare_method_doc.csv', index=False, encoding='utf-8-sig')
    print("CSV文件合并完成，结果已保存到akshare_method_doc.csv")

if __name__ == '__main__':
    merge_csv_files()