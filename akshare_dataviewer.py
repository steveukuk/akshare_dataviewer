import akshare as ak
from datetime import datetime
import pandas as pd
import sys
import os
import traceback
# QtWidgets 导入
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QTextEdit,
    QVBoxLayout, QWidget, QSplitter, QComboBox,
    QListWidget, QListWidgetItem, QHBoxLayout,
    QLabel, QLineEdit,QPushButton, QLayout, QMessageBox, QFileDialog
)

# QtCore 导入
from PyQt5.QtCore import (
    Qt, QTimer, QPoint, QUrl
)

# QtGui 导入
from PyQt5.QtGui import (
    QDesktopServices, QKeyEvent
)

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
        self.timer.setSingleShot(True)
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
        self.tooltip = ToolTipWindow(self)
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
    
    class MethodListWidget(QListWidget):
        """自定义列表控件，处理键盘导航"""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.parent_window = parent
        
        def keyPressEvent(self, event: QKeyEvent) -> None:
            """处理键盘事件"""
            if event.key() in (Qt.Key_Up, Qt.Key_Down):
                # 先调用父类方法处理导航
                super().keyPressEvent(event)
                # 然后显示当前选中项的详情
                current_item = self.currentItem()
                if current_item and self.parent_window:
                    self.parent_window.show_method_details(current_item)
            else:
                super().keyPressEvent(event)

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
        self.method_list = self.MethodListWidget(self)
        layout.addWidget(self.method_list)
        self.method_list.setMouseTracking(True)
        self.method_list.itemEntered.connect(self.show_tooltip)
        self.method_list.itemClicked.connect(self.show_method_details)
        
        # 启用键盘导航
        self.method_list.setFocusPolicy(Qt.StrongFocus)
        
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
        
        # 创建参数容器布局
        self.param_container = QVBoxLayout()
        layout.addLayout(self.param_container)   
         
        return panel
    
    def create_bottom_panel(self) -> QWidget:
        """创建底部面板(结果显示)"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignLeft)
        
        # 请求按钮
        self.request_btn = QPushButton("请求")
        self.request_btn.setFixedWidth(80)
        self.request_btn.clicked.connect(self.execute_akshare_request)
        btn_layout.addWidget(self.request_btn)
        
        # 保存按钮
        self.save_btn = QPushButton("保存")
        self.save_btn.setFixedWidth(80)
        self.save_btn.clicked.connect(self.save_to_csv)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
        layout.setAlignment(btn_layout, Qt.AlignLeft|Qt.AlignBottom)
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
        
        # 清除中部面板内容(保留请求按钮、保存按钮和参数容器)
        middle_layout = self.middle_panel.layout()
        self.clear_layout(middle_layout, [self.request_btn, self.save_btn, self.param_container])
        
        # 重新添加参数容器到布局
        if not middle_layout.indexOf(self.param_container) >= 0:
            middle_layout.insertLayout(0, self.param_container)
        
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
                input_box.setFixedWidth(100)
                
                hbox.addWidget(label, 0)
                hbox.addWidget(input_box, 1)
                
                self.param_container.addLayout(hbox)

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
            df = pd.read_excel('config/operation_menu.xlsx', engine='openpyxl')
            
            # 按Level2分组
            self.menu_config = {}
            for _, row in df.iterrows():
                try:
                    level2 = row['Level2']
                    if pd.isna(level2):
                        continue
                        
                    if level2 not in self.menu_config:
                        self.menu_config[level2] = []
                        
                    # 验证必填字段
                    level3 = str(row['Level3']).strip() if pd.notna(row['Level3']) else None
                    file_path = str(row['file_path']).strip() if pd.notna(row['file_path']) else None
                    if not level3 or not file_path:
                        continue  # 静默跳过无效配置
                        
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
            return False

    def createMenuBar(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        # 退出动作
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 操作菜单
        operation_menu = menubar.addMenu('操作(&O)')

        # 配置菜单
        config_menu = menubar.addMenu('配置(&C)')
        
        # Akshare方法配置
        method_config_action = QAction('Akshare方法配置', self)
        method_config_action.triggered.connect(lambda: self.open_config_file('config/akshare_method_doc.xlsx'))
        config_menu.addAction(method_config_action)
        
        # 操作菜单配置
        menu_config_action = QAction('操作菜单配置', self)
        menu_config_action.triggered.connect(lambda: self.open_config_file('config/operation_menu.xlsx'))
        config_menu.addAction(menu_config_action)
        
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
                    
                    # 如果文件不存在，先尝试获取数据
                    if not os.path.exists(abs_path):
                        self.handle_fetch_data(level2)
                        if not os.path.exists(abs_path):
                            raise FileNotFoundError(f"文件不存在且获取失败: {abs_path}")
                    
                    # 打开文件
                    QDesktopServices.openUrl(QUrl.fromLocalFile(abs_path))
                except Exception as e:
                    error_msg = f"处理{level2}数据失败: {str(e)}"
                    QMessageBox.critical(self, "错误", error_msg)
            
            try:
                # 处理文件路径
                file_path = file_path.strip()
                abs_path = os.path.abspath(file_path)
                
                if not os.path.exists(abs_path):
                    raise FileNotFoundError(f"文件不存在: {abs_path}")
                
                QDesktopServices.openUrl(QUrl.fromLocalFile(abs_path))
            except Exception as e:
                error_msg = f"打开文件失败: {abs_path}\n错误: {str(e)}"
                QMessageBox.critical(self, "错误", error_msg)

    def open_config_file(self, file_path):
        """打开配置文件"""
        try:
            abs_path = os.path.abspath(file_path)
            if not os.path.exists(abs_path):
                QMessageBox.warning(self, "警告", f"配置文件不存在: {abs_path}")
                return
            QDesktopServices.openUrl(QUrl.fromLocalFile(abs_path))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开配置文件失败: {str(e)}")

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", "AKShare数据加载器 v2.0")

    def execute_akshare_request(self):
        """执行AKShare请求并显示结果"""
        current_item = self.method_list.currentItem()
        if not current_item:
            return
            
        # 获取当前方法名
        self.current_method_name = current_item.text()
        
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
            method = getattr(ak, self.current_method_name)
            self.current_result = method(**params)
            
            # 显示结果
            self.text_edit.clear()
            if isinstance(self.current_result, pd.DataFrame):
                self.text_edit.append(self.current_result.to_string())
            else:
                self.text_edit.append(str(self.current_result))
                
        except Exception as e:
            error_msg = f"请求失败: {str(e)}"
            self.text_edit.append(error_msg)
    
    def save_to_csv(self):
        """将当前结果保存为CSV文件"""
        if not hasattr(self, 'current_result') or self.current_result is None:
            QMessageBox.warning(self, "警告", "没有可保存的数据，请先执行请求")
            return
            
        # 设置默认文件名
        default_name = f"{self.current_method_name}.csv"
        
        # 弹出文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存CSV文件",
            default_name,
            "CSV文件 (*.csv);;所有文件 (*)"
        )
        
        if not file_path:
            return  # 用户取消
            
        try:
            # 确保文件以.csv结尾
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'
                
            # 保存数据
            if isinstance(self.current_result, pd.DataFrame):
                self.current_result.to_csv(file_path, index=False)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(self.current_result))
                    
            QMessageBox.information(self, "成功", f"数据已保存到: {file_path}")
            
        except Exception as e:
            error_msg = f"保存文件失败: {str(e)}"
            QMessageBox.critical(self, "错误", error_msg)

def main():
    import warnings
    warnings.filterwarnings("ignore", category=FutureWarning, module="akshare.*")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()