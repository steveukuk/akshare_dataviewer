# akshare_dataviewer

AKShare数据加载器是一个基于PyQt5的桌面应用程序，提供用户友好的界面来访问和操作AKShare金融数据。

## 项目描述
该工具允许用户：
- 浏览AKShare提供的各种数据获取方法
- 执行数据请求并查看结果
- 将结果保存为CSV文件
- 通过菜单系统批量获取预定义数据集
- 管理AKShare方法配置和操作菜单配置

## 使用方法

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行程序
```bash
python akshare_dataviewer.py
```

### 3. 主要功能说明
1. **方法浏览**：
   - 左侧面板选择分类或搜索方法
   - 鼠标悬停查看方法注释
   - 点击方法查看详细说明

2. **执行请求**：
   - 在参数区域输入所需参数
   - 点击"请求"按钮执行
   - 结果将显示在底部区域

3. **保存结果**：
   - 执行成功后点击"保存"按钮
   - 选择保存路径和文件名
   - 数据将保存为CSV格式

4. **批量操作**：
   - 使用顶部菜单栏的"操作"菜单
   - 选择预定义的数据集获取任务
   - 支持"获取"和"打开"操作

### 4. 配置文件
- `config/akshare_method_doc.xlsx`: AKShare方法文档
- `config/operation_menu.xlsx`: 操作菜单配置

## 技术支持
- 详细文档：
  - [业务需求文档](doc/user_requirements.md)
  - [技术设计文档](doc/technical_requirements.md)
- AKShare官方文档：[https://akshare.akfamily.xyz/](https://akshare.akfamily.xyz/)