import akshare as ak
import logging
from datetime import datetime
import pandas as pd
import csv
import importlib
import sys
import os
import traceback
from typing import Optional
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, QTextEdit,
                            QVBoxLayout, QWidget, QSplitter, QComboBox,
                            QListWidget, QListWidgetItem, QHBoxLayout,
                            QToolTip, QLabel, QFrame, QLineEdit, QScrollArea,
                            QPushButton, QLayout, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QPoint, QUrl
from PyQt5.QtGui import QDesktopServices, QKeyEvent
from PyQt5.QtGui import QFontMetrics

class ToolTipWindow(QLabel):
    """自定义ToolTip窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip)
        self.setStyleSheet("""
            background-color: #ffffdc;
            border: 1px solid black;
            padding: 3px;
        """)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close)
        
    def showText(self, pos, text, timeout=15000):
        self.setText(text)
        self.adjustSize()
        self.move(pos)
        self.show()
        self.timer.start(timeout)

def setup_logging():
    """配置日志记录"""
    try:
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"akshare_{today}.log")
        
        # 检查日志文件是否可写
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*20} 新的会话 {'='*20}\n")
        except Exception as e:
            raise Exception(f"无法写入日志文件: {log_file}, 错误: {str(e)}")
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            filename=log_file,
            encoding='utf-8'
        )
        logging.info("日志系统初始化成功")
    except Exception as e:
        print(f"无法初始化日志系统: {str(e)}")
        raise

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        setup_logging()
        self.initUI()
    
    def initUI(self):
        """初始化主界面UI"""
        self.setWindowTitle('AKShare数据加载器')
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器并添加到主布局
        splitter = QSplitter()
        main_layout.addWidget(splitter)
        
        # 创建左右面板
        left_panel = self.create_left_panel()
        right_panel = self.create_right_panel()
        
        # 添加面板到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 600])  # 左右比例1:3
        
        # 加载数据和菜单
        self.load_excel_data()
        self.createMenuBar()
    
    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 分类下拉菜单
        self.category_combo = QComboBox()
        layout.addWidget(self.category_combo)
        
        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索方法...")
        self.search_box.textChanged.connect(self.filter_methods)
        layout.addWidget(self.search_box)
        
        # 方法选择器
        self.method_list = QListWidget()
        layout.addWidget(self.method_list)
        self.method_list.setMouseTracking(True)
        self.method_list.itemEntered.connect(self.show_tooltip)
        self.method_list.itemClicked.connect(self.show_method_details)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 创建子面板
        self.top_panel = self.create_top_panel()
        self.middle_panel = self.create_middle_panel()
        bottom_panel = self.create_bottom_panel()
        
        # 添加子面板
        layout.addWidget(self.top_panel)
        layout.addWidget(self.middle_panel)
        layout.addWidget(bottom_panel, stretch=1)
        
        return panel
    
    def create_top_panel(self) -> QWidget:
        """创建顶部面板(方法说明)"""
        panel = QWidget()
        panel.setFixedHeight(160)
        layout = QVBoxLayout(panel)
        
        # 解释文本编辑区
        self.explanation_edit = QTextEdit()
        self.explanation_edit.setReadOnly(True)
        layout.addWidget(self.explanation_edit)
        
        return panel
    
    def create_middle_panel(self) -> QWidget:
        """创建中部面板(参数输入)"""
        panel = QWidget()
        panel.setFixedHeight(140)
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignTop)
        
        # 请求按钮
        self.request_btn = QPushButton("请求")
        self.request_btn.setFixedWidth(80)
        self.request_btn.clicked.connect(self.execute_akshare_request)
        layout.addWidget(self.request_btn, alignment=Qt.AlignLeft|Qt.AlignBottom)
        
        return panel
    
    def create_bottom_panel(self) -> QWidget:
        """创建底部面板(结果显示)"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 文本显示区域
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)
        
        return panel
        
    def load_excel_data(self):
        """加载Excel数据并初始化UI控件"""
        try:
            # 确保config目录存在
            if not os.path.exists('config'):
                os.makedirs('config')
            
            # 读取Excel文件
            df = pd.read_excel('config/akshare_method_doc.xlsx')
            
            # 获取唯一分类并添加到下拉菜单
            categories = df['分类'].unique().tolist()
            self.category_combo.addItem("显示全部")  # 添加"显示全部"选项
            self.category_combo.addItems(categories)
            # 存储原始数据
            self.methods_data = df
            
            # 默认选中"显示全部"
            self.category_combo.setCurrentIndex(0)
            self.method_list.setMouseTracking(True)
            self.method_list.itemEntered.connect(self.show_tooltip)
            self.method_items = []
            for _, row in self.methods_data.iterrows():
                item = row['方法']
                self.method_list.addItem(item)
                self.method_items.append(row)
            
            # 连接信号槽
            self.category_combo.currentTextChanged.connect(self.filter_methods)
            
            # 默认显示全部方法
            self.filter_methods("显示全部")
            
        except Exception as e:
            error_msg = f"加载Excel文件失败: {str(e)}"
            self.text_edit.append(error_msg)
            logging.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            
    def filter_methods(self, text=None):
        """根据选择分类和搜索文本过滤方法列表"""
        if not hasattr(self, 'methods_data'):
            return
            
        # 获取当前分类和搜索文本
        category = self.category_combo.currentText()
        search_text = self.search_box.text().lower() if hasattr(self, 'search_box') else ""
        
        self.method_list.clear()
        self.method_items = []
        
        # 按分类过滤
        if category == "显示全部":
            filtered_data = self.methods_data
        else:
            filtered_data = self.methods_data[self.methods_data['分类'] == category]
            
        # 按搜索文本过滤
        if search_text:
            filtered_data = filtered_data[
                filtered_data['方法'].str.lower().str.contains(search_text) |
                (filtered_data['注释'].fillna('').str.lower().str.contains(search_text))
            ]
            
        for _, row in filtered_data.iterrows():
            item = row['方法']
            self.method_list.addItem(item)
            self.method_items.append(row)
    
    def __init__(self):
        super().__init__()
        self.tooltip = ToolTipWindow(self)
        self.initUI()

    def clear_layout(self, layout: QLayout, preserve_widgets: list = None) -> None:
        """清除布局中的所有子部件"""
        if preserve_widgets is None:
            preserve_widgets = []
            
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            
            if item.widget():
                if item.widget() not in preserve_widgets:
                    item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout(), preserve_widgets)
                layout.removeItem(item)
    
    def show_method_details(self, list_item: QListWidgetItem) -> None:
        """显示选中方法的详细信息"""
        if not list_item:
            return
            
        # 清除顶部面板内容(保留解释文本编辑区)
        self.clear_layout(self.top_panel.layout(), [self.explanation_edit])
        
        # 清除中部面板内容(保留请求按钮)
        middle_layout = self.middle_panel.layout()
        self.clear_layout(middle_layout, [self.request_btn])
        
        # 获取方法信息
        method_name = list_item.text()
        method_data = next((row for row in self.method_items if row['方法'] == method_name), None)
        if method_data is None or method_data.empty:
            return
            
        # 显示方法解释
        explanation_text = str(method_data['解释']) if pd.notna(method_data['解释']) else ""
        explanation_text = explanation_text.replace('\\n', '\n')
        self.explanation_edit.setPlainText(explanation_text)
        
        # 添加参数输入框
        if pd.notna(method_data['参数']):
            params = method_data['参数'].split(';')
            for param in params:
                param = param.strip()
                if not param:
                    continue
                    
                hbox = QHBoxLayout()
                hbox.setAlignment(Qt.AlignLeft)
                hbox.setSpacing(2)
                hbox.setContentsMargins(0, 0, 0, 0)
                
                label = QLabel(param)
                input_box = QLineEdit()
                input_box.setFixedWidth(40)
                
                hbox.addWidget(label, 0)
                hbox.addWidget(input_box, 1)
                
                middle_layout.addLayout(hbox)

    def show_tooltip(self, item):
        """显示工具提示"""
        if item:
            method_name = item.text()
            for row in self.method_items:
                if row['方法'] == method_name:
                    rect = self.method_list.visualItemRect(item)
                    pos = self.method_list.mapToGlobal(rect.topLeft()) + QPoint(0, rect.height())
                    comment = str(row['注释']) if pd.notna(row['注释']) else "无注释"
                    self.tooltip.showText(pos, comment)
                    break
    
    def load_menu_config(self):
        """从Excel加载菜单配置"""
        try:
            # 尝试读取修正后的文件
            df = pd.read_excel('config/operation_menu.xlsx')
            
            # 按Level2分组
            self.menu_config = {}
            for _, row in df.iterrows():
                try:
                    level2 = row['Level2']
                    if pd.isna(level2):
                        continue
                        
                    if level2 not in self.menu_config:
                        self.menu_config[level2] = []
                        
                    # 验证并处理file_path
                    file_path = str(row['file_path']).strip() if pd.notna(row['file_path']) else None
                    if not file_path:
                        logging.warning(f"跳过无效配置: {row['Level3']} - 缺少file_path")
                        continue
                        
                    self.menu_config[level2].append({
                        'Level3': row['Level3'],
                        'akmethod': row['akmethod'],
                        'file_path': file_path,
                        'save_column': eval(row['save_column']) if pd.notna(row['save_column']) else None
                    })
                    
                except Exception as e:
                    print(f"处理菜单项出错: {str(e)}")
                    continue
                    
            if not self.menu_config:
                QMessageBox.critical(self, "错误", "菜单配置为空，请检查Excel文件内容")
                return False
                
            return True
            
        except Exception as e:
            error_msg = f"加载菜单配置失败: {str(e)}"
            QMessageBox.critical(self, "错误", error_msg)
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return False

    def createMenuBar(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        # 打开动作
        open_action = QAction('打开', self)
        open_action.setShortcut('Ctrl+O')
        file_menu.addAction(open_action)
        
        # 保存动作
        save_action = QAction('保存', self)
        save_action.setShortcut('Ctrl+S')
        file_menu.addAction(save_action)
        
        # 退出动作
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 操作菜单
        operation_menu = menubar.addMenu('操作(&O)')
        
        # 从配置加载菜单项
        if not hasattr(self, 'menu_config'):
            if not self.load_menu_config():
                return

        for level2, items in self.menu_config.items():
            sub_menu = operation_menu.addMenu(level2)
            
            # 添加获取动作
            fetch_action = QAction('获取', self)
            fetch_action.triggered.connect(lambda _, l2=level2: self.handle_fetch_data(l2))
            sub_menu.addAction(fetch_action)
            
            # 添加打开动作
            open_action = QAction('打开', self)
            open_action.triggered.connect(lambda _, l2=level2: self.handle_open_file(l2))
            sub_menu.addAction(open_action)

        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        # AKShare在线文档
        docs_action = QAction('AKShare在线文档', self)
        docs_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://akshare.akfamily.xyz/")))
        help_menu.addAction(docs_action)

        # 关于菜单
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def handle_fetch_data(self, level2):
        """处理获取数据请求"""
        if level2 not in self.menu_config:
            return
            
        items = self.menu_config[level2]
        for item in items:
            if pd.isna(item['akmethod']):
                continue
                
            try:
                # 执行AKShare方法
                method_str = str(item['akmethod']).strip()
                if not method_str:
                    continue
                    
                try:
                    # 检查方法字符串格式
                    if not method_str.startswith('ak.') or not method_str.endswith('()'):
                        raise ValueError(f"方法格式不正确: {method_str}")
                        
                    method_name = method_str[3:-2]  # 去掉ak.和()
                    if not hasattr(ak, method_name):
                        raise ValueError(f"AKShare方法不存在: {method_name}")
                        
                    method = getattr(ak, method_name)
                    df = method()
                except Exception as e:
                    error_msg = f"执行AKShare方法失败: {method_str}\n错误详情: {str(e)}"
                    logging.error(f"{error_msg}\n{traceback.format_exc()}")
                    QMessageBox.critical(self, "方法执行错误",
                        f"执行方法时出错:\n{method_str}\n\n错误原因:\n{str(e)}")
                    continue
                
                # 筛选需要的列
                if item['save_column']:
                    df = df[item['save_column']]
                
                # 确保目录存在
                os.makedirs(os.path.dirname(item['file_path']), exist_ok=True)
                
                # 保存到Excel文件
                file_path = str(item['file_path']).strip()
                if not file_path.lower().endswith('.xlsx'):
                    file_path += '.xlsx'
                
                try:
                    # 使用pandas默认Excel写入方式
                    df.to_excel(file_path, index=False)
                except Exception as e:
                    raise Exception(f"保存Excel文件失败: {str(e)}")
                
            except Exception as e:
                error_msg = f"获取{level2}数据失败: {str(e)}"
                logging.error(f"{error_msg}\n{traceback.format_exc()}")
                raise Exception(error_msg)
                
        QMessageBox.information(self, "成功", f"{level2}数据已保存")

    def handle_open_file(self, level2):
        """处理打开文件请求"""
        if level2 not in self.menu_config:
            return
            
        items = self.menu_config[level2]
        for item in items:
            # 确保file_path有效
            if 'file_path' not in item or pd.isna(item['file_path']):
                raise ValueError(f"无效的file_path配置: {item}")
            file_path = str(item['file_path']).strip()
            
            if not file_path or not os.path.exists(file_path):
                reply = QMessageBox.question(
                    self, '文件不存在',
                    f'{level2}文件不存在，是否现在下载？',
                    QMessageBox.Yes | QMessageBox.No
                )
                
                try:
                    # 确保路径为字符串并处理空格
                    file_path = str(item['file_path']).strip()
                    if not file_path.lower().endswith('.xlsx'):
                        file_path += '.xlsx'
                    
                    # 转换为绝对路径并规范化
                    abs_path = os.path.normpath(os.path.abspath(file_path))
                    
                    # 调试日志
                    logging.info(f"检查文件路径: {abs_path}")
                    logging.info(f"文件存在: {os.path.exists(abs_path)}")
                    
                    # 如果文件不存在，先尝试获取数据
                    if not os.path.exists(abs_path):
                        logging.info("文件不存在，尝试下载...")
                        self.handle_fetch_data(level2)
                        if not os.path.exists(abs_path):
                            logging.error("文件下载失败")
                            raise FileNotFoundError(f"文件不存在且获取失败: {abs_path}")
                    
                    # 打开文件
                    logging.info(f"准备打开文件: {abs_path}")
                    QDesktopServices.openUrl(QUrl.fromLocalFile(abs_path))
                except Exception as e:
                    error_msg = f"处理{level2}数据失败: {str(e)}"
                    logging.error(f"{error_msg}\n{traceback.format_exc()}")
                    QMessageBox.critical(self, "错误", error_msg)
            
            try:
                # 处理文件路径
                file_path = file_path.strip()
                abs_path = os.path.abspath(file_path)
                logging.info(f"尝试打开文件: {abs_path}")
                
                if not os.path.exists(abs_path):
                    raise FileNotFoundError(f"文件不存在: {abs_path}")
                
                QDesktopServices.openUrl(QUrl.fromLocalFile(abs_path))
            except Exception as e:
                error_msg = f"打开文件失败: {abs_path}\n错误: {str(e)}"
                logging.error(f"{error_msg}\n{traceback.format_exc()}")
                QMessageBox.critical(self, "错误", error_msg)

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", "AKShare数据加载器 v1.0")

    def execute_akshare_request(self):
        """执行AKShare请求并显示结果"""
        current_item = self.method_list.currentItem()
        if not current_item:
            return
            
        # 获取当前方法名
        method_name = current_item.text()
        
        # 收集参数值
        params = {}
        for i in range(self.middle_panel.layout().count()):
            item = self.middle_panel.layout().itemAt(i)
            if isinstance(item, QHBoxLayout):
                # 获取参数名和值
                label = item.itemAt(0).widget()
                input_box = item.itemAt(1).widget()
                if isinstance(label, QLabel) and isinstance(input_box, QLineEdit):
                    param_name = label.text().split(':')[0].strip()
                    param_value = input_box.text().strip()
                    if param_value:
                        params[param_name] = param_value
        
        try:
            # 执行AKShare请求
            method = getattr(ak, method_name)
            result = method(**params)
            
            # 显示结果
            self.text_edit.clear()
            if isinstance(result, pd.DataFrame):
                self.text_edit.append(result.to_string())
            else:
                self.text_edit.append(str(result))
                
        except Exception as e:
            error_msg = f"请求失败: {str(e)}"
            self.text_edit.append(error_msg)
            logging.error(error_msg)

def main():
    import warnings
    warnings.filterwarnings("ignore", category=FutureWarning, module="akshare.*")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()