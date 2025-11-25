import sys
import json
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QFileDialog, QSpinBox, QCheckBox, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer
from pathlib import Path
import picture_spawner
import tempfile
import keyboard
import os

class ConfigGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_file = "config.json"
        self.initUI()
        self.load_config()

    def initUI(self):
        self.setWindowTitle('AVG Text Spawner 配置')
        self.setGeometry(100, 100, 900, 1000)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QLabel {
                color: #333;
            }
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 配置区域
        config_group = QGroupBox("配置设置")
        config_layout = QVBoxLayout()

        # 头像路径
        avatar_layout = QHBoxLayout()
        self.avatar_path = QLineEdit()
        avatar_btn = QPushButton('选择头像')
        avatar_btn.clicked.connect(lambda: self.browse_file(self.avatar_path, "图片文件 (*.png *.jpg *.jpeg)"))
        avatar_layout.addWidget(QLabel('头像路径:'))
        avatar_layout.addWidget(self.avatar_path)
        avatar_layout.addWidget(avatar_btn)
        layout.addLayout(avatar_layout)

        # 背景路径
        bg_layout = QHBoxLayout()
        self.bg_path = QLineEdit()
        bg_btn = QPushButton('选择背景')
        bg_btn.clicked.connect(lambda: self.browse_file(self.bg_path, "图片文件 (*.png *.jpg *.jpeg)"))
        bg_layout.addWidget(QLabel('背景路径:'))
        bg_layout.addWidget(self.bg_path)
        bg_layout.addWidget(bg_btn)
        layout.addLayout(bg_layout)

        # 用户名
        username_layout = QHBoxLayout()
        self.username = QLineEdit()
        username_layout.addWidget(QLabel('用户名:'))
        username_layout.addWidget(self.username)
        layout.addLayout(username_layout)

        # 热键布局
        hotkey_layout = QHBoxLayout()
        self.hotkey = QLineEdit()
        detect_btn = QPushButton('检测热键')
        detect_btn.clicked.connect(self.detect_hotkey)
        hotkey_layout.addWidget(QLabel('热键:'))
        hotkey_layout.addWidget(self.hotkey)
        hotkey_layout.addWidget(detect_btn)
        layout.addLayout(hotkey_layout)


        # 字体索引
        font_layout = QHBoxLayout()
        self.font_index = QSpinBox()
        self.font_index.setRange(0, 10)
        font_layout.addWidget(QLabel('字体索引:'))
        font_layout.addWidget(self.font_index)
        layout.addLayout(font_layout)

        # 自动发送
        self.auto_send = QCheckBox('自动发送')
        layout.addWidget(self.auto_send)

        # 添加预览按钮
        preview_btn = QPushButton('预览效果')
        preview_btn.clicked.connect(self.preview_image)
        config_layout.addWidget(preview_btn)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # 预览区域
        preview_group = QGroupBox("预览区域")
        preview_layout = QVBoxLayout()
        
        # 预览图片显示区域
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet("border: 1px solid #ddd; border-radius: 4px;")
        preview_layout.addWidget(self.preview_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
    
        # 添加状态指示灯
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(16, 16)
        self.status_indicator.setStyleSheet("background-color: gray; border-radius: 8px;")
        
        save_btn = QPushButton('保存配置')
        save_btn.clicked.connect(self.save_config)
        self.run_btn = QPushButton('运行服务')
        self.run_btn.clicked.connect(self.run_service)
        
        btn_layout.addWidget(self.status_indicator)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(self.run_btn)
        layout.addLayout(btn_layout)

    def detect_hotkey(self):
        """检测用户输入的热键，按ESC退出"""
        # 检查是否为root用户
        if os.name == 'posix' and os.geteuid() != 0:
            QMessageBox.warning(self, '权限提示', '请使用root权限重新打开程序以设置热键')
            return
        # 创建覆盖窗口
        self.overlay = QWidget(self)
        self.overlay.setGeometry(self.rect())
        self.overlay.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 150);
            }
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        
        # 添加提示文本
        self.label = QLabel("热键检测中，请输入...")
        self.label.setAlignment(Qt.AlignCenter)
        self.layout = QVBoxLayout(self.overlay)
        self.layout.addWidget(self.label)
        
        # 显示覆盖窗口
        self.overlay.show()

        self.hotkey.setPlaceholderText("按下热键，按ESC退出...")
        self.hotkey.setEnabled(False)
        
        current_keys = set()  # 当前按下的键集合
    
        def on_key_press(event):
            if event.name == 'esc':
                self.hotkey.setPlaceholderText("")
                self.hotkey.setEnabled(True)
                keyboard.unhook_all()
                self.overlay.close()
                return
                
            current_keys.add(event.name)
            
            # 组合键处理
            hotkey_str = ''
            if keyboard.is_pressed('ctrl'):
                hotkey_str += 'ctrl+'
            if keyboard.is_pressed('alt'):
                hotkey_str += 'alt+'
            if keyboard.is_pressed('shift'):
                hotkey_str += 'shift+'
            
            # 添加非修饰键
            for key in current_keys:
                if key not in ['ctrl', 'alt', 'shift']:
                    hotkey_str += key
                    break
            
            self.hotkey.setText(hotkey_str)
        
        def on_key_release(event):
            # 如果松开的是非修饰键，保存热键
            if event.name not in ['ctrl', 'alt', 'shift'] and event.name in current_keys:
                new_hotkey = self.hotkey.text()
                if new_hotkey:
                    self.hotkey.setText(new_hotkey)
                    QMessageBox.information(self, '成功', f'热键已设置为: {new_hotkey}')
                self.hotkey.setPlaceholderText("")
                self.hotkey.setEnabled(True)
                keyboard.unhook_all()
                self.overlay.close()
                return
            
            current_keys.discard(event.name)
        
        keyboard.hook(on_key_press)
        keyboard.hook(on_key_release)


    def preview_image(self):
        try:
            # 获取当前配置
            avatar_path = self.avatar_path.text()
            background_path = self.bg_path.text()
            username = self.username.text()
            
            # 生成临时预览图片
            temp_path = tempfile.mktemp(suffix='.png')
            img = picture_spawner.generate_dialog_image(
                avatar_path=avatar_path,
                background_path=background_path,
                username=username,
                dialog_text="这是一段预览文本\n用于展示生成的对话框\n",
                font_index=self.font_index.value(),
                img_size=(1200, 300),
                output_path=temp_path
            )
            
            # 在预览标签中显示图片
            pixmap = QPixmap(temp_path)
            scaled_pixmap = pixmap.scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)
            
            # 清理临时文件
            QTimer.singleShot(1000, lambda: Path(temp_path).unlink(missing_ok=True))
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"预览失败: {str(e)}")

    def browse_file(self, line_edit, file_filter):
        file_name, _ = QFileDialog.getOpenFileName(self, '选择文件', '', file_filter)
        if file_name:
            line_edit.setText(file_name)

    def load_config(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.avatar_path.setText(config.get('avatar_image_path', ''))
                self.bg_path.setText(config.get('background_image_path', ''))
                self.username.setText(config.get('username', ''))
                self.hotkey.setText(config.get('hotkey', 'enter'))
                self.font_index.setValue(config.get('font_index', 0))
                self.auto_send.setChecked(config.get('want_auto_send', 0))
        except Exception as e:
            print(f"加载配置文件失败: {e}")

    def save_config(self):
        config = {
            'avatar_image_path': self.avatar_path.text(),
            'background_image_path': self.bg_path.text(),
            'username': self.username.text(),
            'hotkey': self.hotkey.text(),
            'font_index': self.font_index.value(),
            'want_auto_send': 1 if self.auto_send.isChecked() else 0
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print("配置已保存")
        except Exception as e:
            print(f"保存配置失败: {e}")

    def run_service(self):
        if self.run_btn.text() == '运行服务':
            self.save_config()  # 先保存当前配置
            try:
                # 启动main.py
                if sys.platform.startswith('win'):
                    #self.process = subprocess.Popen([sys.executable, 'main.py'])
                    self.process = subprocess.Popen(['main.exe'])
                else:
                    self.process = subprocess.Popen(['sudo', '-E', sys.executable, 'main.py'])
                self.status_indicator.setStyleSheet("background-color: green; border-radius: 8px;")
                self.run_btn.setText('停止服务')
                print("服务已启动")
            except Exception as e:
                self.status_indicator.setStyleSheet("background-color: red; border-radius: 8px;")
                QMessageBox.critical(self, "服务启动失败！", f"预览失败: {str(e)}")
                print(f"启动服务失败: {e}")
        else:
            try:
                self.process.terminate()
                self.status_indicator.setStyleSheet("background-color: gray; border-radius: 8px;")
                self.run_btn.setText('运行服务')
                print("服务已停止")
            except Exception as e:
                print(f"停止服务失败: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = ConfigGUI()
    gui.show()
    sys.exit(app.exec_())
