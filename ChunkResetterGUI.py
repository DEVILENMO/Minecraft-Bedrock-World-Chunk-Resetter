#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minecraft 区块重置器 GUI
基于tkinter的图形化界面，支持领地保护的区块重置功能

作者: DEVILENMO
依赖: amulet-core, tkinter (Python自带)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
from pathlib import Path

# 导入我们的核心模块
try:
    from ChunkAutoResetter import ChunkAutoResetter
    from land_data_reader import LandDataReader
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保 ChunkAutoResetter.py 和 land_data_reader.py 在同一目录下")
    sys.exit(1)


class ChunkResetterGUI:
    """区块重置器图形界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft 区块重置器 v2.0 (集成领地保护)")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 配置样式
        self.setup_styles()
        
        # 初始化变量
        self.world_path = tk.StringVar()
        self.db_path = tk.StringVar()
        self.search_range = tk.StringVar(value="750")
        self.extra_protection_distance = tk.StringVar(value="0")
        self.dimension = tk.StringVar(value="minecraft:overworld")
        
        # 核心对象
        self.resetter = None
        self.land_reader = None
        self.lands_data = []
        self.covered_chunks = set()
        
        # 操作状态
        self.is_processing = False
        
        # 创建界面
        self.create_widgets()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        
        # 配置颜色主题
        style.configure('Title.TLabel', font=('Microsoft YaHei', 14, 'bold'))
        style.configure('Section.TLabel', font=('Microsoft YaHei', 10, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="Minecraft 区块重置器", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 文件选择区域
        self.create_file_selection_area(main_frame, row=1)
        
        # 设置区域
        self.create_settings_area(main_frame, row=2)
        
        # 领地信息显示区域
        self.create_land_info_area(main_frame, row=3)
        
        # 控制按钮区域
        self.create_control_area(main_frame, row=4)
        
        # 日志输出区域
        self.create_log_area(main_frame, row=5)
        
        # 状态栏
        self.create_status_bar(main_frame, row=6)
    
    def create_file_selection_area(self, parent, row):
        """创建文件选择区域"""
        # 文件选择框架
        file_frame = ttk.LabelFrame(parent, text="路径配置", padding="10")
        file_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # 世界路径选择
        ttk.Label(file_frame, text="世界路径:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        world_entry = ttk.Entry(file_frame, textvariable=self.world_path, width=50)
        world_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(file_frame, text="浏览", command=self.select_world_path).grid(row=0, column=2)
        
        # 数据库路径选择
        ttk.Label(file_frame, text="领地数据库:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        db_entry = ttk.Entry(file_frame, textvariable=self.db_path, width=50)
        db_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(10, 0))
        ttk.Button(file_frame, text="浏览", command=self.select_db_path).grid(row=1, column=2, pady=(10, 0))
        
        # 加载按钮
        load_button = ttk.Button(file_frame, text="加载配置", command=self.load_configuration)
        load_button.grid(row=2, column=0, columnspan=3, pady=(15, 0))
    
    def create_settings_area(self, parent, row):
        """创建设置区域"""
        settings_frame = ttk.LabelFrame(parent, text="重置设置", padding="10")
        settings_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 搜索范围
        ttk.Label(settings_frame, text="搜索范围:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        range_entry = ttk.Entry(settings_frame, textvariable=self.search_range, width=10)
        range_entry.grid(row=0, column=1, sticky=tk.W)
        ttk.Label(settings_frame, text="(区块坐标，如50表示-50到50一百个区块，一个区块的尺寸为16x16格)").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        
        # 额外保护距离
        ttk.Label(settings_frame, text="额外保护距离:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        protection_entry = ttk.Entry(settings_frame, textvariable=self.extra_protection_distance, width=10)
        protection_entry.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        ttk.Label(settings_frame, text="(在领地边界外额外保护的区块数，0表示不保护)").grid(row=1, column=2, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        # 维度选择
        ttk.Label(settings_frame, text="维度:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        dimension_combo = ttk.Combobox(settings_frame, textvariable=self.dimension, width=25, state="readonly")
        dimension_combo['values'] = ("minecraft:overworld", "minecraft:the_nether", "minecraft:the_end")
        dimension_combo.grid(row=2, column=1, sticky=tk.W, pady=(10, 0))
    
    def create_land_info_area(self, parent, row):
        """创建领地信息显示区域"""
        info_frame = ttk.LabelFrame(parent, text="领地信息", padding="10")
        info_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(row, weight=1)
        
        # 创建Treeview显示领地信息
        columns = ("ID", "名称", "拥有者", "坐标范围", "覆盖区块", "面积")
        self.land_tree = ttk.Treeview(info_frame, columns=columns, show="headings", height=8)
        
        # 设置列标题和宽度
        self.land_tree.heading("ID", text="领地ID")
        self.land_tree.heading("名称", text="领地名称")
        self.land_tree.heading("拥有者", text="拥有者")
        self.land_tree.heading("坐标范围", text="坐标范围")
        self.land_tree.heading("覆盖区块", text="覆盖区块")
        self.land_tree.heading("面积", text="面积(方块)")
        
        self.land_tree.column("ID", width=60, anchor=tk.CENTER)
        self.land_tree.column("名称", width=120)
        self.land_tree.column("拥有者", width=100)
        self.land_tree.column("坐标范围", width=150)
        self.land_tree.column("覆盖区块", width=120)
        self.land_tree.column("面积", width=100, anchor=tk.CENTER)
        
        # 添加滚动条
        tree_scroll = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.land_tree.yview)
        self.land_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.land_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 统计信息标签
        self.stats_label = ttk.Label(info_frame, text="请先加载配置")
        self.stats_label.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)
    
    def create_control_area(self, parent, row):
        """创建控制按钮区域"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=row, column=0, columnspan=3, pady=(0, 10))
        
        # 预览按钮
        self.preview_button = ttk.Button(control_frame, text="预览重置操作", command=self.preview_reset)
        self.preview_button.grid(row=0, column=0, padx=(0, 10))
        
        # 执行按钮
        self.execute_button = ttk.Button(control_frame, text="执行重置", command=self.execute_reset, state=tk.DISABLED)
        self.execute_button.grid(row=0, column=1, padx=(0, 10))
        
        # 取消按钮
        self.cancel_button = ttk.Button(control_frame, text="取消操作", command=self.cancel_operation, state=tk.DISABLED)
        self.cancel_button.grid(row=0, column=2, padx=(0, 10))
        
        # 进度条
        self.progress = ttk.Progressbar(control_frame, mode='determinate', maximum=100)
        self.progress.grid(row=0, column=3, padx=(20, 0), sticky=(tk.W, tk.E))
        
        # 进度百分比标签
        self.progress_label = ttk.Label(control_frame, text="0%", width=5)
        self.progress_label.grid(row=0, column=4, padx=(5, 0))
        
        control_frame.columnconfigure(3, weight=1)
    
    def create_log_area(self, parent, row):
        """创建日志输出区域"""
        log_frame = ttk.LabelFrame(parent, text="操作日志", padding="10")
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(row, weight=1)
        
        # 日志文本区域
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 清空日志按钮
        clear_button = ttk.Button(log_frame, text="清空日志", command=self.clear_log)
        clear_button.grid(row=1, column=0, pady=(10, 0), sticky=tk.W)
    
    def create_status_bar(self, parent, row):
        """创建状态栏"""
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def select_world_path(self):
        """选择世界路径"""
        path = filedialog.askdirectory(title="选择Minecraft世界文件夹")
        if path:
            self.world_path.set(path)
    
    def select_db_path(self):
        """选择数据库路径"""
        path = filedialog.askopenfilename(
            title="选择领地数据库文件",
            filetypes=[("数据库文件", "*.db"), ("所有文件", "*.*")]
        )
        if path:
            self.db_path.set(path)
    
    def log_message(self, message, level="INFO"):
        """添加日志消息"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
        self.root.update()
    
    def load_configuration(self):
        """加载配置"""
        if not self.world_path.get():
            messagebox.showerror("错误", "请选择世界路径")
            return
        
        if not self.db_path.get():
            messagebox.showerror("错误", "请选择领地数据库路径")
            return
        
        if not os.path.exists(self.world_path.get()):
            messagebox.showerror("错误", "世界路径不存在")
            return
        
        if not os.path.exists(self.db_path.get()):
            messagebox.showerror("错误", "数据库文件不存在")
            return
        
        # 在后台线程中加载
        threading.Thread(target=self._load_configuration_thread, daemon=True).start()
    
    def _load_configuration_thread(self):
        """在后台线程中加载配置"""
        try:
            self.update_status("正在加载配置...")
            self.log_message("开始加载配置")
            
            # 创建重置器实例
            self.resetter = ChunkAutoResetter(self.world_path.get(), self.db_path.get())
            
            # 加载世界
            self.log_message("正在加载世界...")
            if not self.resetter.load_world():
                raise Exception("世界加载失败")
            
            # 检查领地数据库
            if not self.resetter.land_reader:
                raise Exception("领地数据库连接失败")
            
            # 获取领地信息
            self.log_message("正在获取领地信息...")
            self._load_lands_info()
            
            self.log_message("配置加载完成")
            self.update_status("配置加载完成")
            
            # 启用预览按钮
            self.preview_button.config(state=tk.NORMAL)
            
        except Exception as e:
            self.log_message(f"配置加载失败: {e}", "ERROR")
            self.update_status("配置加载失败")
            messagebox.showerror("错误", f"配置加载失败: {e}")
    
    def _load_lands_info(self):
        """加载领地信息"""
        # 清空现有数据
        for item in self.land_tree.get_children():
            self.land_tree.delete(item)
        
        # 获取维度对应的数据库维度名
        dimension_mapping = {
            'minecraft:overworld': 'Overworld',    # 首字母大写
            'minecraft:the_nether': 'Nether',     # 首字母大写  
            'minecraft:the_end': 'TheEnd'         # 驼峰命名
        }
        
        db_dimension = dimension_mapping.get(self.dimension.get(), 'Overworld')
        
        # 获取领地数据
        self.lands_data = self.resetter.land_reader.get_lands_by_dimension(db_dimension)
        self.covered_chunks = set()
        
        # 填充树形视图
        for land in self.lands_data:
            land_id = land['land_id']
            name = land['land_name']
            owner = land['owner_uuid'][:8] + "..."  # 显示UUID前8位
            
            # 坐标范围
            coord_range = f"({land['min_x']}, {land['min_z']}) - ({land['max_x']}, {land['max_z']})"
            
            # 计算覆盖的区块
            start_chunk_x = land['min_x'] // 16
            start_chunk_z = land['min_z'] // 16
            end_chunk_x = land['max_x'] // 16
            end_chunk_z = land['max_z'] // 16
            
            chunk_range = f"({start_chunk_x}, {start_chunk_z}) - ({end_chunk_x}, {end_chunk_z})"
            
            # 添加到覆盖区块集合
            for cx in range(start_chunk_x, end_chunk_x + 1):
                for cz in range(start_chunk_z, end_chunk_z + 1):
                    self.covered_chunks.add((cx, cz))
            
            # 面积
            area = land['area']
            
            # 插入到树形视图
            self.land_tree.insert("", tk.END, values=(land_id, name, owner, coord_range, chunk_range, area))
        
        # 更新统计信息
        stats_text = f"共找到 {len(self.lands_data)} 个领地，覆盖 {len(self.covered_chunks)} 个区块"
        self.stats_label.config(text=stats_text)
    
    def preview_reset(self):
        """预览重置操作"""
        if not self.resetter:
            messagebox.showerror("错误", "请先加载配置")
            return
        
        try:
            search_range = int(self.search_range.get())
        except ValueError:
            messagebox.showerror("错误", "搜索范围必须是数字")
            return
        
        try:
            extra_protection = int(self.extra_protection_distance.get())
        except ValueError:
            messagebox.showerror("错误", "额外保护距离必须是数字")
            return
        
        # 在后台线程中执行预览
        threading.Thread(target=self._preview_reset_thread, args=(search_range, extra_protection), daemon=True).start()
    
    def _preview_reset_thread(self, search_range, extra_protection):
        """在后台线程中执行预览"""
        try:
            self.is_processing = True
            self.progress['value'] = 0
            self.progress_label.config(text="0%")
            self.preview_button.config(state=tk.DISABLED)
            self.cancel_button.config(state=tk.NORMAL)
            
            self.update_status("正在预览重置操作...")
            self.log_message("开始预览重置操作")
            
            # 定义进度回调函数
            def progress_callback(current, total, message):
                if total > 0:
                    progress_percent = (current / total) * 100
                    self.progress['value'] = progress_percent
                    self.progress_label.config(text=f"{progress_percent:.1f}%")
                    self.update_status(message)
                    self.root.update()
            
            # 执行试运行
            stats = self.resetter.reset_chunks_except_lands(
                dimension=self.dimension.get(),
                search_range=search_range,
                extra_protection_distance=extra_protection,
                dry_run=True,
                progress_callback=progress_callback
            )
            
            if stats:
                self.log_message("预览完成")
                self.log_message(f"检查的坐标总数: {stats['total_checked']}")
                self.log_message(f"找到的区块数量: {stats['found_chunks']}")
                self.log_message(f"领地保护的区块数量: {stats['land_protected_chunks']}")
                self.log_message(f"将被保留的区块数量: {stats['preserved_chunks']}")
                self.log_message(f"将被重置的区块数量: {stats['reset_chunks']}")
                self.log_message(f"错误数量: {stats['errors']}")
                
                if stats['reset_chunks'] > 0:
                    self.execute_button.config(state=tk.NORMAL)
                    self.update_status(f"预览完成 - 将重置 {stats['reset_chunks']} 个区块")
                    
                    # 显示确认对话框
                    result = messagebox.askyesno(
                        "预览完成",
                        f"预览完成！\n\n"
                        f"找到区块: {stats['found_chunks']} 个\n"
                        f"领地保护: {stats['preserved_chunks']} 个\n"
                        f"将重置: {stats['reset_chunks']} 个\n"
                        f"错误: {stats['errors']} 个\n\n"
                        f"是否现在执行重置操作？"
                    )
                    
                    if result:
                        # 直接执行重置
                        self.execute_reset()
                else:
                    self.update_status("预览完成 - 没有需要重置的区块")
                    messagebox.showinfo("预览完成", "没有需要重置的区块")
            else:
                self.log_message("预览失败", "ERROR")
                self.update_status("预览失败")
                
        except Exception as e:
            self.log_message(f"预览操作失败: {e}", "ERROR")
            self.update_status("预览失败")
            messagebox.showerror("错误", f"预览操作失败: {e}")
        finally:
            self.is_processing = False
            self.progress['value'] = 0
            self.progress_label.config(text="0%")
            self.preview_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
    
    def execute_reset(self):
        """执行重置操作"""
        if not self.resetter:
            messagebox.showerror("错误", "请先加载配置")
            return
        
        # 最终确认
        result = messagebox.askyesno(
            "最终确认",
            "⚠️ 警告 ⚠️\n\n"
            "此操作将永久删除未被领地保护的区块！\n"
            "操作不可撤销，请确保已备份世界文件。\n\n"
            "确定要继续吗？",
            icon='warning'
        )
        
        if not result:
            return
        
        try:
            search_range = int(self.search_range.get())
        except ValueError:
            messagebox.showerror("错误", "搜索范围必须是数字")
            return
        
        try:
            extra_protection = int(self.extra_protection_distance.get())
        except ValueError:
            messagebox.showerror("错误", "额外保护距离必须是数字")
            return
        
        # 在后台线程中执行重置
        threading.Thread(target=self._execute_reset_thread, args=(search_range, extra_protection), daemon=True).start()
    
    def _execute_reset_thread(self, search_range, extra_protection):
        """在后台线程中执行重置"""
        try:
            self.is_processing = True
            self.progress['value'] = 0
            self.progress_label.config(text="0%")
            self.execute_button.config(state=tk.DISABLED)
            self.preview_button.config(state=tk.DISABLED)
            self.cancel_button.config(state=tk.NORMAL)
            
            self.update_status("正在执行重置操作...")
            self.log_message("开始执行重置操作")
            
            # 定义进度回调函数
            def progress_callback(current, total, message):
                if total > 0:
                    progress_percent = (current / total) * 100
                    self.progress['value'] = progress_percent
                    self.progress_label.config(text=f"{progress_percent:.1f}%")
                    self.update_status(message)
                    self.root.update()
            
            # 执行实际重置
            stats = self.resetter.reset_chunks_except_lands(
                dimension=self.dimension.get(),
                search_range=search_range,
                extra_protection_distance=extra_protection,
                dry_run=False,
                progress_callback=progress_callback
            )
            
            if stats:
                self.log_message("重置操作完成")
                self.log_message(f"成功重置了 {stats['reset_chunks']} 个区块")
                
                # 保存世界
                self.log_message("正在保存世界...")
                self.update_status("正在保存世界...")
                
                # 定义保存进度回调函数
                def save_progress_callback(chunk_index, chunk_count):
                    if chunk_count > 0:
                        progress = (chunk_index / chunk_count) * 100
                        self.log_message(f"保存进度: {chunk_index}/{chunk_count} ({progress:.1f}%)")
                        self.update_status(f"保存中... {progress:.1f}%")
                
                if self.resetter.save_world(progress_callback=save_progress_callback):
                    self.log_message("世界保存成功")
                    self.update_status("操作完成")
                    messagebox.showinfo(
                        "操作完成",
                        f"重置操作成功完成！\n\n"
                        f"重置区块: {stats['reset_chunks']} 个\n"
                        f"保留区块: {stats['preserved_chunks']} 个\n"
                        f"世界已保存"
                    )
                else:
                    self.log_message("世界保存失败", "ERROR")
                    self.update_status("保存失败")
                    messagebox.showerror("错误", "重置完成但世界保存失败")
            else:
                self.log_message("重置操作失败", "ERROR")
                self.update_status("重置失败")
                messagebox.showerror("错误", "重置操作失败")
                
        except Exception as e:
            self.log_message(f"重置操作失败: {e}", "ERROR")
            self.update_status("重置失败")
            messagebox.showerror("错误", f"重置操作失败: {e}")
        finally:
            self.is_processing = False
            self.progress['value'] = 0
            self.progress_label.config(text="0%")
            self.preview_button.config(state=tk.NORMAL)
            self.execute_button.config(state=tk.DISABLED)
            self.cancel_button.config(state=tk.DISABLED)
    
    def cancel_operation(self):
        """取消操作"""
        if self.is_processing:
            # 注意: 实际的取消功能需要在ChunkAutoResetter中实现中断机制
            # 这里只是停止进度条和恢复按钮状态
            self.log_message("用户取消操作", "WARNING")
            self.update_status("操作已取消")
            
            self.is_processing = False
            self.progress['value'] = 0
            self.progress_label.config(text="0%")
            self.preview_button.config(state=tk.NORMAL)
            self.execute_button.config(state=tk.DISABLED)
            self.cancel_button.config(state=tk.DISABLED)
    
    def on_closing(self):
        """程序关闭时的处理"""
        if self.is_processing:
            result = messagebox.askyesno("确认退出", "操作正在进行中，确定要退出吗？")
            if not result:
                return
        
        # 关闭世界连接
        if self.resetter:
            try:
                self.resetter.close_world()
                self.log_message("世界连接已关闭")
            except:
                pass
        
        self.root.destroy()


def main():
    """主函数"""
    # 检查依赖
    try:
        import amulet
    except ImportError:
        messagebox.showerror("依赖错误", "请先安装 amulet-core:\npip install amulet-core")
        return
    
    # 创建主窗口
    root = tk.Tk()
    app = ChunkResetterGUI(root)
    
    # 运行GUI
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
