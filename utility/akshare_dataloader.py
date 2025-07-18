import akshare as ak
import pandas as pd
import csv
import importlib
import sys
import os
from typing import Optional
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, QTextEdit,
                            QVBoxLayout, QWidget, QSplitter, QComboBox,
                            QListWidget, QListWidgetItem, QHBoxLayout,
                            QToolTip, QLabel, QFrame, QLineEdit, QScrollArea,
                            QPushButton, QLayout, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QPoint, QUrl
from PyQt5.QtGui import QDesktopServices
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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
            self.text_edit.append(f"加载Excel文件失败: {str(e)}")
            
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
        
        # 空气质量城市列表子菜单
        air_menu = operation_menu.addMenu('空气质量城市列表')
        
        # 获取动作
        fetch_action = QAction('获取', self)
        fetch_action.triggered.connect(self.fetch_air_city_data)
        air_menu.addAction(fetch_action)
        
        # 打开动作
        open_action = QAction('打开', self)
        open_action.triggered.connect(self.open_air_city_file)
        air_menu.addAction(open_action)

        # 基金公司列表-东方财富子菜单
        fund_menu = operation_menu.addMenu('基金公司列表-东方财富')
        
        # 获取动作
        fetch_fund_action = QAction('获取', self)
        fetch_fund_action.triggered.connect(self.fetch_fund_amc_data)
        fund_menu.addAction(fetch_fund_action)
        
        # 打开动作
        open_fund_action = QAction('打开', self)
        open_fund_action.triggered.connect(self.open_fund_amc_file)
        fund_menu.addAction(open_fund_action)

        # 场内交易基金列表-东方财富子菜单
        etf_menu = operation_menu.addMenu('场内交易基金列表-东方财富')
        
        # 获取动作
        fetch_etf_action = QAction('获取', self)
        fetch_etf_action.triggered.connect(self.fetch_etf_fund_data)
        etf_menu.addAction(fetch_etf_action)
        
        # 打开动作
        open_etf_action = QAction('打开', self)
        open_etf_action.triggered.connect(self.open_etf_fund_file)
        etf_menu.addAction(open_etf_action)

        # 所有基金列表-东方财富子菜单
        all_fund_menu = operation_menu.addMenu('所有基金列表-东方财富')
        
        # 获取动作
        fetch_all_fund_action = QAction('获取', self)
        fetch_all_fund_action.triggered.connect(self.fetch_all_fund_data)
        all_fund_menu.addAction(fetch_all_fund_action)
        
        # 打开动作
        open_all_fund_action = QAction('打开', self)
        open_all_fund_action.triggered.connect(self.open_all_fund_file)
        all_fund_menu.addAction(open_all_fund_action)

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

    def fetch_fund_amc_data(self):
        """获取基金公司列表数据并保存"""
        try:
            # 调用AKShare接口获取数据
            df = ak.fund_aum_em()
            
            # 确保data目录存在
            if not os.path.exists('data'):
                os.makedirs('data')
            
            # 保存到Excel文件
            save_path = 'data/china_amc_list_EM.xlsx'
            df.to_excel(save_path, index=False)
            
            # 显示成功消息
            QMessageBox.information(self, "成功", f"数据已保存到 {save_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取数据失败: {str(e)}")

    def fetch_etf_fund_data(self):
        """获取场内交易基金列表数据并保存"""
        try:
            # 调用AKShare接口获取数据
            df = ak.fund_etf_fund_daily_em()
            
            # 只保留需要的列并重命名
            df = df[['基金代码', '基金简称', '类型']]
            
            # 确保基金代码为纯数字
            df['基金代码'] = df['基金代码'].str.extract(r'(\d+)')
            
            # 确保data目录存在
            if not os.path.exists('data'):
                os.makedirs('data')
            
            # 保存到Excel文件
            save_path = 'data/etf_code_list_EM.xlsx'
            df.to_excel(save_path, index=False)
            
            # 显示成功消息
            QMessageBox.information(self, "成功", f"数据已保存到 {save_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取数据失败: {str(e)}")

    def fetch_all_fund_data(self):
        """获取所有基金列表数据并保存"""
        try:
            # 调用AKShare接口获取数据
            df = ak.fund_name_em()
            
            # 确保data目录存在
            if not os.path.exists('data'):
                os.makedirs('data')
            
            # 保存到Excel文件
            save_path = 'data/all_fund_code_list_EM.xlsx'
            df.to_excel(save_path, index=False)
            
            # 显示成功消息
            QMessageBox.information(self, "成功", f"数据已保存到 {save_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取数据失败: {str(e)}")

    def open_all_fund_file(self):
        """打开所有基金列表Excel文件"""
        file_path = 'data/all_fund_code_list_EM.xlsx'
        
        if not os.path.exists(file_path):
            # 文件不存在，先获取数据
            reply = QMessageBox.question(
                self, '文件不存在',
                '所有基金列表文件不存在，是否现在下载？',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.fetch_all_fund_data()
            else:
                return
        
        # 使用系统默认程序打开文件
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(file_path)))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件失败: {str(e)}")

    def open_etf_fund_file(self):
        """打开场内交易基金列表Excel文件"""
        file_path = 'data/etf_code_list_EM.xlsx'
        
        if not os.path.exists(file_path):
            # 文件不存在，先获取数据
            reply = QMessageBox.question(
                self, '文件不存在',
                '场内交易基金列表文件不存在，是否现在下载？',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.fetch_etf_fund_data()
            else:
                return
        
        # 使用系统默认程序打开文件
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(file_path)))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件失败: {str(e)}")

    def open_fund_amc_file(self):
        """打开基金公司列表Excel文件"""
        file_path = 'data/china_amc_list_EM.xlsx'
        
        if not os.path.exists(file_path):
            # 文件不存在，先获取数据
            reply = QMessageBox.question(
                self, '文件不存在',
                '基金公司列表文件不存在，是否现在下载？',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.fetch_fund_amc_data()
            else:
                return
        
        # 使用系统默认程序打开文件
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(file_path)))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件失败: {str(e)}")

    def open_air_city_file(self):
        """打开空气质量城市列表Excel文件"""
        file_path = 'data/air_quality_city_list.xlsx'
        
        if not os.path.exists(file_path):
            # 文件不存在，先获取数据
            reply = QMessageBox.question(
                self, '文件不存在',
                '空气质量城市列表文件不存在，是否现在下载？',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.fetch_air_city_data()
            else:
                return
        
        # 使用系统默认程序打开文件
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(file_path)))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件失败: {str(e)}")

    def fetch_air_city_data(self):
        """获取空气质量城市列表数据并保存"""
        try:
            # 调用AKShare接口获取数据
            df = ak.air_city_table()
            
            # 选择需要的列
            result_df = df[['序号', '省份', '城市']]
            
            # 确保data目录存在
            if not os.path.exists('data'):
                os.makedirs('data')
            
            # 保存到Excel文件
            save_path = 'data/air_quality_city_list.xlsx'
            result_df.to_excel(save_path, index=False)
            
            # 显示成功消息
            QMessageBox.information(self, "成功", f"数据已保存到 {save_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取数据失败: {str(e)}")

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
            self.text_edit.append(f"请求失败: {str(e)}")

def main():
    import warnings
    warnings.filterwarnings("ignore", category=FutureWarning, module="akshare.*")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()