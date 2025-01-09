import customtkinter as ctk
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread
import time
from datetime import datetime
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
from matplotlib.animation import FuncAnimation
import matplotlib.dates as mdates
import os
import platform
import ctypes

# Add ThemeManager class to handle theme switching
class ThemeManager:
    def __init__(self):
        self.dark_theme = {
            "bg": "#0B2239",  # Slightly lighter blue background
            "surface": "#000",  # Adjusted surface color for contrast
            "accent": "#1A73E8",  # Slightly softer blue accent
            "accent_secondary": "#21A1FF",  # Brighter secondary accent
            "text": "#FFFFFF",
            "text_secondary": "#A0B3C8",
            "border": "#264D73",  # Adjusted border for better visibility
            "success": "#66BB6A",
            "warning": "#FFA726",
            "error": "#F44336",
            "gradient": ["#1A73E8", "#21A1FF"]  # Gradient colors
        }

        self.light_theme = {
            "bg": "#E7ECF3",  # Slightly darker light background
            "surface": "#FAFBFD",  # Soft surface color
            "accent": "#1565C0",  # Stronger blue for light theme
            "accent_secondary": "#42A5F5",  # Bright secondary accent
            "text": "#212121",
            "text_secondary": "#546E7A",
            "border": "#CFD8DC",  # Softer border
            "success": "#388E3C",
            "warning": "#F57C00",
            "error": "#C62828",
            "gradient": ["#1565C0", "#42A5F5"]
        }

        self.current_theme = self.dark_theme
        self.is_dark = True

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.current_theme = self.dark_theme if self.is_dark else self.light_theme
        return self.current_theme
# Define a MetricBox class to show individual metrics
class MetricBox(ctk.CTkFrame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, **kwargs)
        
        main_window = self.winfo_toplevel()
        colors = main_window.colors
        
        self.configure(
            fg_color=colors["surface"],
            corner_radius=15,
            border_width=1,
            border_color=colors["border"]
        )
        
        # Create gradient effect
        gradient_canvas = ctk.CTkCanvas(
            self,
            height=4,
            width=self.winfo_width(),
            highlightthickness=0
        )
        gradient_canvas.pack(fill="x", side="top")
        
        # Create gradient effect
        def create_gradient():
            width = gradient_canvas.winfo_width()
            height = 4
            gradient_canvas.delete("gradient")
            
            # Create gradient colors
            for i in range(width):
                x = i / width
                r1, g1, b1 = tuple(int(colors["gradient"][0].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                r2, g2, b2 = tuple(int(colors["gradient"][1].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                r = int(r1 + (r2-r1) * x)
                g = int(g1 + (g2-g1) * x)
                b = int(b1 + (b2-b1) * x)
                color = f'#{r:02x}{g:02x}{b:02x}'
                gradient_canvas.create_line(i, 0, i, height, fill=color, tags="gradient")
        
        gradient_canvas.bind('<Configure>', lambda e: create_gradient())
        
        # Icon mapping for different metrics
        icons = {
            "CPU": "⚡", "Memory": "💾", "Disk": "💿",
            "Virtual Memory": "📊", "Core Count": "🔢",
            "Thread Count": "🧵", "CPU Usage": "📈",
            "CPU Frequency": "⚙"
        }
        
        icon = icons.get(title, "📊")
        
        # Title with icon
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=(15,5))
        
        icon_label = ctk.CTkLabel(
            title_frame,
            text=icon,
            font=ctk.CTkFont(size=20)
        )
        icon_label.pack(side="left", padx=5)
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=colors["accent"]
        )
        self.title_label.pack(side="left", padx=5)
        
        # Value with shadow effect
        value_frame = ctk.CTkFrame(self, fg_color="transparent")
        value_frame.pack(pady=(5,15))
        
        self.value_label = ctk.CTkLabel(
            value_frame,
            text="--",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=colors["text"]
        )
        self.value_label.pack()

# Define a GraphFrame class for plotting graphs
class GraphFrame(ctk.CTkFrame):
    def __init__(self, master, title, ylabel, **kwargs):
        super().__init__(master, **kwargs)
        
        main_window = self.winfo_toplevel()
        colors = main_window.colors
        
        self.configure(
            fg_color=colors["surface"],
            corner_radius=15,
            border_width=1,
            border_color=colors["border"]
        )
        
        # Modern header with gradient
        header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        header.pack(fill="x", padx=15, pady=(15,5))
        
        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=colors["accent"]
        )
        title_label.pack(side="left")
        
        # Enhanced zoom controls
        zoom_frame = ctk.CTkFrame(header, fg_color="transparent")
        zoom_frame.pack(side="right")
        
        ranges = ["1m", "5m", "15m", "1h"]
        self.time_buttons = {}
        for r in ranges:
            btn = ctk.CTkButton(
                zoom_frame,
                text=r,
                width=45,
                height=28,
                corner_radius=8,
                fg_color=colors["surface"],
                hover_color=colors["accent"],
                text_color=colors["text"],
                font=ctk.CTkFont(size=12, weight="bold"),
                border_width=1,
                border_color=colors["border"]
            )
            btn.pack(side="left", padx=2)
            self.time_buttons[r] = btn
        
        # Enhanced graph styling
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)
        
        # Modern graph styling
        self.ax.set_facecolor(colors["surface"])
        self.fig.patch.set_facecolor(colors["surface"])
        
        # Add grid with custom styling
        self.ax.grid(True, linestyle='--', alpha=0.2, color=colors["border"])
        self.ax.tick_params(colors=colors["text"], labelsize=9)
        
        # Custom spine colors
        for spine in self.ax.spines.values():
            spine.set_color(colors["border"])
            spine.set_linewidth(0.5)

# Define a PieChartFrame for Pie Chart visualization
class PieChartFrame(ctk.CTkFrame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, **kwargs)
        self.title_label = ctk.CTkLabel(
            self, 
            text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.title_label.pack(pady=10)
        
        self.fig, self.ax = plt.subplots(figsize=(4, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ax.axis('equal')  # Equal aspect ratio ensures the pie is drawn as a circle.

    def update_chart(self, labels, sizes, colors):
        self.ax.clear()
        self.ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
        self.ax.set_title("Usage Distribution")
        self.canvas.draw()

# Main SystemMonitor application class
class SystemMonitor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("System Monitor Pro")
        self.geometry("1400x900")
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        self.colors = self.theme_manager.current_theme
        
        self.configure(fg_color=self.colors["bg"])
        
        # Initialize dictionaries for storing widgets
        self.overview_boxes = {}
        
        # Configure gselrid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create UI components
        self.create_sidebar()
        self.create_main_area()
        self.create_status_bar()
        
        # Initialize data storage
        self.history = {
            'time': [],
            'cpu': [],
            'memory': [],
            'virtual': [],
            'disk': [],
            'network_sent': [],
            'network_recv': [],
        }
        
        # Start monitoring thread
        self.running = True
        self.monitor_thread = Thread(target=self.update_metrics, daemon=True)
        self.monitor_thread.start()

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, 
            width=250,
            fg_color=self.colors["surface"],
            corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Logo/header area
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20,10), sticky="ew")
        
        logo_label = ctk.CTkLabel(
            header_frame,
            text="SYSTEM\nMONITOR",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["accent"]
        )
        logo_label.pack()
        
        # Add theme switch
        theme_switch = ctk.CTkSwitch(
            header_frame,
            text="Dark Mode",
            command=self.toggle_theme,
            progress_color=self.colors["accent"],
            button_color=self.colors["accent"],
            button_hover_color=self.colors["accent"],
            text_color=self.colors["text"]
        )
        theme_switch.pack(pady=10)
        theme_switch.select() if self.theme_manager.is_dark else theme_switch.deselect()
        
        # Separator
        separator = ctk.CTkFrame(
            self.sidebar,
            height=2,
            fg_color=self.colors["accent"]
        )
        separator.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        # Navigation buttons with icons
        sections = {
            "Overview": "🏠",
            "CPU": "⚡",
            "Memory": "💾",
            "Virtual Memory": "📊",
            "Disk": "💿",
            "Network":"🛜"
        }
        
        # Create a frame for navigation buttons
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        for i, (section, icon) in enumerate(sections.items()):
            btn = ctk.CTkButton(
                nav_frame,
                text=f" {icon} {section}",
                command=lambda s=section: self.show_section(s),
                fg_color="transparent",
                hover_color=self.colors["accent"],
                height=45,
                anchor="w",
                font=ctk.CTkFont(size=14),
                corner_radius=8,
                text_color=self.colors["text"],
                border_width=1,
                border_color=self.colors["border"]
            )
            btn.pack(fill="x", pady=2)

    def create_main_area(self):
        # Create a canvas with scrollbar
        self.canvas = ctk.CTkCanvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.main_frame = ctk.CTkFrame(self.canvas)
        
        # Configure scrolling
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Grid layout for canvas and scrollbar
        self.canvas.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.scrollbar.grid(row=0, column=2, sticky="ns")
        
        # Create window in canvas for main_frame
        self.canvas_window = self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        
        # Configure grid weights for layout stretching
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create sections (overview, cpu, memory, etc.)
        self.sections = {}
        self.create_overview_section()  # Dashboard/Overview
        self.create_cpu_section()  # CPU section
        self.create_memory_section()  # Memory section
        self.create_virtual_memory_section()  # Virtual Memory section
        self.create_disk_section()  # Disk section
        self.create_network_section()
        
        # Bind events for scrolling
        self.main_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Show the initial section (Overview by default)
        self.show_section("Overview")
        
        # Configure canvas scrolling area to match content size
        self.main_frame.update_idletasks()  # Update idletasks to ensure content size
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """When canvas is resized, resize the inner frame to match"""
        min_width = self.main_frame.winfo_reqwidth()
        if event.width > min_width:
            self.canvas.itemconfig(self.canvas_window, width=event.width)

    def create_virtual_memory_section(self):
        section = ctk.CTkFrame(self.main_frame)
        section.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Virtual Memory metrics boxes
        self.vm_boxes = {}
        metrics = [
            "Total Virtual Memory",
            "Available Virtual Memory",
            "Used Virtual Memory",
            "Page File Usage",
            "Commit Charge",
            "Commit Limit",
            "Peak Commit",
            "Page Faults"
        ]
        
        for i, metric in enumerate(metrics):
            box = MetricBox(section, metric)
            box.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="ew")
            self.vm_boxes[metric] = box
        
        # Create a frame to split the pie chart and graph
        vm_graph_frame = ctk.CTkFrame(section)
        vm_graph_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        vm_graph_frame.grid_columnconfigure(0, weight=1)  # Left column (pie chart)
        vm_graph_frame.grid_columnconfigure(1, weight=1)  # Right column (line graph)
        
        # Virtual memory pie chart (left side)
        self.vm_pie = PieChartFrame(vm_graph_frame, "Virtual Memory Usage")
        self.vm_pie.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Virtual memory line graph (right side)
        self.vm_graph = GraphFrame(vm_graph_frame, "Virtual Memory Usage", "Percentage (%)")
        self.vm_graph.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.sections["Virtual Memory"] = section

    def create_cpu_section(self):
        section = ctk.CTkFrame(self.main_frame)
        section.grid_columnconfigure((0, 1, 2), weight=1)
        
        # CPU metrics boxes
        self.cpu_boxes = {}
        metrics = [
            "CPU Usage",
            "CPU Frequency",
            "Core Count",
            "Thread Count"
        ]
        
        for i, metric in enumerate(metrics):
            box = MetricBox(section, metric)
            box.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="ew")
            self.cpu_boxes[metric] = box
            
        # Create a frame to split the pie chart and graph
        cpu_graph_frame = ctk.CTkFrame(section)
        cpu_graph_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        cpu_graph_frame.grid_columnconfigure(0, weight=1)  # Left column (pie chart)
        cpu_graph_frame.grid_columnconfigure(1, weight=1)  # Right column (line graph)
        
        # CPU usage pie chart (left side)
        self.cpu_pie = PieChartFrame(cpu_graph_frame, "CPU Usage")
        self.cpu_pie.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # CPU usage line graph (right side)
        self.cpu_graph = GraphFrame(cpu_graph_frame, "CPU Usage", "Percentage (%)")
        self.cpu_graph.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.sections["CPU"] = section

    def create_network_section(self):
        # Create the Network section frame
        section = ctk.CTkFrame(self.main_frame)
        section.grid_columnconfigure((0, 1), weight=1)  # Configure columns to be flexible
        
        # Network metrics boxes
        self.net_boxes = {}
        metrics = [
            "Bytes Sent",
            "Bytes Received"
        ]
        
        for i, metric in enumerate(metrics):
            box = MetricBox(section, metric)  # Default value for Bytes
            box.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew")
            self.net_boxes[metric] = box
        
        # Create a frame to split the pie chart and graph
        net_graph_frame = ctk.CTkFrame(section)
        net_graph_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        net_graph_frame.grid_columnconfigure(0, weight=1)  # Left column (pie chart)
        net_graph_frame.grid_columnconfigure(1, weight=1)  # Right column (line graph)
        
        # Network usage line graph (right side)
        self.net_graph = GraphFrame(net_graph_frame, "Network Usage", "MB")
        self.net_graph.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.sections["Network"] = section


    def create_memory_section(self):
        section = ctk.CTkFrame(self.main_frame)
        section.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Memory metrics boxes
        self.mem_boxes = {}
        metrics = [
            "Total Memory",
            "Available Memory",
            "Used Memory",
            "Memory Percentage"
        ]
        
        for i, metric in enumerate(metrics):
            box = MetricBox(section, metric)
            box.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="ew")
            self.mem_boxes[metric] = box
        
        # Create a frame to split the pie chart and graph
        mem_graph_frame = ctk.CTkFrame(section)
        mem_graph_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        mem_graph_frame.grid_columnconfigure(0, weight=1)  # Left column (pie chart)
        mem_graph_frame.grid_columnconfigure(1, weight=1)  # Right column (line graph)
        
        # Memory usage pie chart (left side)
        self.mem_pie = PieChartFrame(mem_graph_frame, "Memory Usage")
        self.mem_pie.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Memory usage line graph (right side)
        self.mem_graph = GraphFrame(mem_graph_frame, "Memory Usage", "Percentage (%)")
        self.mem_graph.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.sections["Memory"] = section


    def create_disk_section(self):
        section = ctk.CTkFrame(self.main_frame)
        section.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Disk metrics boxes
        self.disk_boxes = {}
        metrics = [
            "Total Disk Space",
            "Used Disk Space",
            "Free Disk Space",
            "Disk Usage Percentage"
        ]
        
        for i, metric in enumerate(metrics):
            box = MetricBox(section, metric)
            box.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="ew")
            self.disk_boxes[metric] = box
        
        # Create a frame to split the pie chart and graph
        disk_graph_frame = ctk.CTkFrame(section)
        disk_graph_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        disk_graph_frame.grid_columnconfigure(0, weight=1)  # Left column (pie chart)
        disk_graph_frame.grid_columnconfigure(1, weight=1)  # Right column (line graph)
        
        # Disk usage pie chart (left side)
        self.disk_pie = PieChartFrame(disk_graph_frame, "Disk Usage")
        self.disk_pie.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Disk usage line graph (right side)
        self.disk_graph = GraphFrame(disk_graph_frame, "Disk Usage Over Time", "Percentage (%)")
        self.disk_graph.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.sections["Disk"] = section

    def create_overview_section(self):
        section = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        section.grid_columnconfigure((0, 1), weight=1)

    # System Overview Header
        sys_frame = ctk.CTkFrame(section, fg_color=self.colors["surface"])
        sys_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    # System Info with more details
        sys_info = (
            f"Operating System: {platform.system()} {platform.release()}\n"
            f"CPU: {platform.processor()}\n"
            f"Total Cores: {psutil.cpu_count()} ({psutil.cpu_count(logical=False)} Physical)\n"
            f"Architecture: {platform.machine()}"
        )
    
        sys_title = ctk.CTkLabel(
            sys_frame,
            text=sys_info,
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text"]
        )
        sys_title.pack(pady=15)

    # Initialize overview boxes dictionary if not exists
        if not hasattr(self, 'overview_boxes'):
            self.overview_boxes = {}

    # Create metric boxes with proper initialization
        metrics = [
            ("CPU", "CPU Usage", 1, 0),
            ("Memory", "Memory Usage", 1, 1),
            ("Disk", "Disk Usage", 2, 0),
            ("Virtual Memory", "Virtual Memory", 2, 1)
        ]

        for key, title, row, col in metrics:
            box = MetricBox(section, title)
            box.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            self.overview_boxes[key] = box

    # Create a frame to split graph and details
        details_graph_frame = ctk.CTkFrame(section, fg_color="transparent")
        details_graph_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        details_graph_frame.grid_columnconfigure((0, 1), weight=1)

    # Performance Graph on the right
        perf_graph = GraphFrame(details_graph_frame, "System Performance Overview", "Usage (%)")
        perf_graph.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.overview_boxes["Performance"] = perf_graph

    # Additional System Details on the left
        details_frame = ctk.CTkFrame(details_graph_frame, fg_color=self.colors["surface"])
        details_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        details_frame.grid_columnconfigure(0, weight=1)

    # Add system details
        details = {
            "Boot Time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
            "Python Version": platform.python_version(),
            "Platform": platform.platform(),
            "Machine": platform.machine()
        }

        for i, (key, value) in enumerate(details.items()):
            label = ctk.CTkLabel(
                 details_frame,
                text=f"{key}:",
                font=ctk.CTkFont(size=12, weight="bold"),
                 text_color=self.colors["accent"]
            )
            label.grid(row=i, column=0, padx=10, pady=5, sticky="w")

            value_label = ctk.CTkLabel(
                details_frame,
                text=str(value),
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text"]
            )
            value_label.grid(row=i, column=1, padx=10, pady=5, sticky="e")

        self.sections["Overview"] = section


    def show_section(self, section_name):
        for section in self.sections.values():
            section.grid_remove()
        self.sections[section_name].grid(row=0, column=0, sticky="nsew")
        
        # Reset scroll to top when switching sections
        self.canvas.yview_moveto(0)

    def update_metrics(self):
        while self.running:
            try:
                # Get system metrics using psutil
                cpu_percent = psutil.cpu_percent()
                cpu_freq = psutil.cpu_freq().current
                core_count = psutil.cpu_count(logical=False)
                thread_count = psutil.cpu_count(logical=True)
                virtual = psutil.virtual_memory()
                swap = psutil.swap_memory()
                current_time = datetime.now()
                disk = psutil.disk_usage('/')
                process = psutil.Process()
                net_io = psutil.net_io_counters()
                bytes_sent = net_io.bytes_sent / (1024**2)  # Convert to MB
                bytes_recv = net_io.bytes_recv / (1024**2) 
                # Update history with current data
                self.history['time'].append(current_time)
                self.history['cpu'].append(cpu_percent)
                self.history['memory'].append(virtual.percent)
                self.history['virtual'].append(virtual.percent)
                self.history['disk'].append(psutil.disk_usage('/').percent)
                self.history['network_sent'].append(bytes_sent)
                self.history['network_recv'].append(bytes_recv)

# Keep last 60 data points for network
                if len(self.history['network_sent']) > 60:
                    self.history['network_sent'].pop(0)
                    self.history['network_recv'].pop(0)
                # Keep last 60 data points
                if len(self.history['time']) > 60:
                    for key in self.history:
                        self.history[key].pop(0)

                # Update Overview section metrics
                if hasattr(self, 'overview_boxes'):
                    if "CPU" in self.overview_boxes:
                        self.overview_boxes["CPU"].value_label.configure(text=f"{cpu_percent:.1f}%")
                    if "Memory" in self.overview_boxes:
                        self.overview_boxes["Memory"].value_label.configure(text=f"{virtual.percent:.1f}%")
                    if "Disk" in self.overview_boxes:
                        self.overview_boxes["Disk"].value_label.configure(text=f"{psutil.disk_usage('/').percent:.1f}%")
                    if "Virtual Memory" in self.overview_boxes:
                        self.overview_boxes["Virtual Memory"].value_label.configure(text=f"{virtual.percent:.1f}%")
                    
                    # Update overview performance graph
                    if "Performance" in self.overview_boxes:
                        perf_graph = self.overview_boxes["Performance"]
                        perf_graph.ax.clear()
                        
                        # Set graph style
                        perf_graph.ax.set_facecolor("#1E2137")
                        perf_graph.ax.grid(True, linestyle='--', alpha=0.2, color="#4A5B7A")
                        perf_graph.ax.tick_params(colors="#B0B9D0", labelsize=9)
                        
                        # Plot data with better colors
                        perf_graph.ax.plot(self.history['time'], self.history['cpu'], 
                                         label="CPU", color="#00A9FF", linewidth=2)
                        perf_graph.ax.plot(self.history['time'], self.history['memory'], 
                                         label="Memory", color="#FF6B6B", linewidth=2)
                        perf_graph.ax.plot(self.history['time'], self.history['disk'], 
                                         label="Disk", color="#32CD32", linewidth=2)
                        
                        # Customize legend
                        perf_graph.ax.legend(loc='upper right', facecolor="#1E2137", 
                                           edgecolor="#4A5B7A", labelcolor="#B0B9D0")
                        
                        # Format time axis
                        perf_graph.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                        perf_graph.ax.set_xlabel("Time", color="#B0B9D0", labelpad=10)
                        perf_graph.ax.set_ylabel("Usage (%)", color="#B0B9D0", labelpad=10)
                        
                        # Update the graph
                        perf_graph.canvas.draw()

                # Update CPU metrics boxes
                self.cpu_boxes["CPU Usage"].value_label.configure(text=f"{cpu_percent:.1f}%")
                self.cpu_boxes["CPU Frequency"].value_label.configure(text=f"{cpu_freq} MHz")
                self.cpu_boxes["Core Count"].value_label.configure(text=f"{core_count} Cores")
                self.cpu_boxes["Thread Count"].value_label.configure(text=f"{thread_count} Threads")
                
                # Update Pie chart for CPU
                self.cpu_pie.update_chart(
                    ["Used", "Idle"], [cpu_percent, 100 - cpu_percent], ["#FF6347", "#32CD32"]
                )
                
                # Update Graph for CPU usage
                self.cpu_graph.ax.clear()
                self.cpu_graph.ax.plot(self.history['time'], self.history['cpu'], label="CPU Usage", color="tomato")
                self.cpu_graph.ax.legend()
                self.cpu_graph.ax.set_xlabel("Time (s)", labelpad=10, color='white')
                self.cpu_graph.ax.set_ylabel("CPU Usage (%)", labelpad=10, color='white')
                self.cpu_graph.canvas.draw()

                # Update Virtual Memory metrics
                self.vm_boxes["Total Virtual Memory"].value_label.configure(
                    text=f"{(virtual.total + swap.total) / (1024**3):.2f} GB"
                )
                self.vm_boxes["Used Virtual Memory"].value_label.configure(
                    text=f"{swap.used / (1024**3):.2f} GB"
                )
                self.vm_boxes["Available Virtual Memory"].value_label.configure(
                    text=f"{(virtual.available + swap.free) / (1024**3):.2f} GB"
                )
                self.vm_boxes["Page File Usage"].value_label.configure(
                    text=f"{swap.percent:.1f}%"
                )
                self.vm_boxes["Commit Charge"].value_label.configure(
                    text=f"{process.memory_info().private / (1024**3):.2f} GB"
                )
                self.vm_boxes["Commit Limit"].value_label.configure(
                    text=f"{(virtual.total + swap.total) / (1024**3):.2f} GB"
                )
                self.vm_boxes["Peak Commit"].value_label.configure(
                    text=f"{process.memory_info().peak_wset / (1024**3):.2f} GB"
                )
                self.vm_boxes["Page Faults"].value_label.configure(
                    text=f"{process.memory_info().num_page_faults:,}"
                )

                # Update Pie chart for Virtual Memory
                self.vm_pie.update_chart(
                    ["Used", "Free"], [virtual.percent, 100 - virtual.percent], ["#FF6347", "#32CD32"]
                )

                # Update Graph for Virtual Memory
                self.vm_graph.ax.clear()
                self.vm_graph.ax.plot(self.history['time'], self.history['virtual'], label="Virtual Memory Usage", color="yellowgreen")
                self.vm_graph.ax.legend()
                self.vm_graph.ax.set_xlabel("Time (s)", labelpad=10, color='white')
                self.vm_graph.ax.set_ylabel("Memory Usage (%)", labelpad=10, color='white')
                self.vm_graph.canvas.draw()

                # Update Memory metrics
                self.mem_boxes["Total Memory"].value_label.configure(
                    text=f"{virtual.total / (1024**3):.2f} GB"
                )
                self.mem_boxes["Used Memory"].value_label.configure(
                    text=f"{virtual.used / (1024**3):.2f} GB"
                )
                self.mem_boxes["Available Memory"].value_label.configure(
                    text=f"{virtual.available / (1024**3):.2f} GB"
                )
                self.mem_boxes["Memory Percentage"].value_label.configure(
                    text=f"{virtual.percent:.1f}%"
                )

                  # Update Memory Pie Chart
                self.mem_pie.update_chart(
                    ["Used", "Free"],
                    [virtual.percent, 100 - virtual.percent],
                    ["#FF6347", "#32CD32"]
                )
                # Dynamic y-axis limits for Memory Graph
                current_value = virtual.percent
                y_min = max(0, current_value - 5)
                y_max = min(100, current_value + 5)

                # Update Memory Graph
                self.mem_graph.ax.clear()
                self.mem_graph.ax.plot(self.history['time'], self.history['memory'], 
                                     label="Memory Usage", color="coral")
                self.mem_graph.ax.legend()
                self.mem_graph.ax.set_xlabel("Time", labelpad=10, color='white')
                self.mem_graph.ax.set_ylabel("Memory Usage (%)", labelpad=10, color='white')
                self.mem_graph.canvas.draw()

                # Update Disk metrics
                try:
                    self.disk_boxes["Total Disk Space"].value_label.configure(
                        text=f"{disk.total / (1024**3):.2f} GB"
                    )
                    self.disk_boxes["Used Disk Space"].value_label.configure(
                        text=f"{disk.used / (1024**3):.2f} GB"
                    )
                    self.disk_boxes["Free Disk Space"].value_label.configure(
                        text=f"{disk.free / (1024**3):.2f} GB"
                    )
                    self.disk_boxes["Disk Usage Percentage"].value_label.configure(
                        text=f"{disk.percent:.1f}%"
                    )
                except AttributeError as e:
                    print(f"Disk metrics error: {e}")

                # Update Pie chart for Disk Usage
                self.disk_pie.update_chart(
                    ["Used", "Free"], [disk.percent, 100 - disk.percent], ["#FF6347", "#32CD32"]
                )

                # Update Graph for Disk usage
                self.disk_graph.ax.clear()
                self.disk_graph.ax.plot(self.history['time'], self.history['disk'], label="Disk Usage", color="dodgerblue")
                self.disk_graph.ax.legend()
                self.disk_graph.ax.set_xlabel("Time (s)", labelpad=10, color='white')
                self.disk_graph.ax.set_ylabel("Disk Usage (%)", labelpad=10, color='white')
                self.disk_graph.canvas.draw()

                self.net_boxes["Bytes Sent"].value_label.configure(text=f"{bytes_sent:.2f} MB")
                self.net_boxes["Bytes Received"].value_label.configure(text=f"{bytes_recv:.2f} MB")

# Update Graph for Network Usage
                self.net_graph.ax.clear()
                self.net_graph.ax.plot(self.history['time'], self.history['network_sent'], label="Bytes Sent", color="orange")
                self.net_graph.ax.plot(self.history['time'], self.history['network_recv'], label="Bytes Received", color="blue")
                self.net_graph.ax.legend()
                self.net_graph.ax.set_xlabel("Time", labelpad=10, color='white')
                self.net_graph.ax.set_ylabel("Network (MB)", labelpad=10, color='white')
                self.net_graph.canvas.draw()

                time.sleep(1)

            except Exception as e:
                print(f"Error updating metrics: {e}")
                time.sleep(1)

    def on_closing(self):
        self.running = False
        self.destroy()

    def create_status_bar(self):
        self.status_bar = ctk.CTkFrame(
            self,
            height=30,
            fg_color=self.colors["surface"]
        )
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        # System info
        sys_info = ctk.CTkLabel(
            self.status_bar,
            text=f"OS: {os.name.upper()} | CPU: {psutil.cpu_count()} Cores",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        )
        sys_info.pack(side="left", padx=15)
        
        # Add live clock
        self.clock_label = ctk.CTkLabel(
            self.status_bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        )
        self.clock_label.pack(side="right", padx=15)
        self.update_clock()

    def update_clock(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.clock_label.configure(text=current_time)
        self.after(1000, self.update_clock)

    def toggle_theme(self):
        self.colors = self.theme_manager.toggle_theme()
        ctk.set_appearance_mode("dark" if self.theme_manager.is_dark else "light")
        
        try:
            # Update main window
            self.configure(fg_color=self.colors["bg"])
            
            # Update sidebar
            self.sidebar.configure(fg_color=self.colors["surface"])
            
            # Update navigation buttons
            for child in self.sidebar.winfo_children():
                if isinstance(child, ctk.CTkFrame):  # Nav frame
                    for button in child.winfo_children():
                        if isinstance(button, ctk.CTkButton):
                            button.configure(
                                text_color=self.colors["text"],
                                hover_color=self.colors["accent"],
                                border_color=self.colors["border"]
                            )
            
            # Update theme switch
            for child in self.sidebar.winfo_children():
                if isinstance(child, ctk.CTkSwitch):
                    child.configure(
                        text_color=self.colors["text"],
                        progress_color=self.colors["accent"],
                        button_color=self.colors["accent"]
                    )
            
            # Update all metric boxes
            for box in self.overview_boxes.values():
                if isinstance(box, MetricBox):
                    box.configure(
                        fg_color=self.colors["surface"],
                        border_color=self.colors["border"]
                    )
                    box.title_label.configure(text_color=self.colors["accent"])
                    box.value_label.configure(text_color=self.colors["text"])
            
            # Update all graphs
            for section in self.sections.values():
                for child in section.winfo_children():
                    if isinstance(child, GraphFrame):
                        child.configure(fg_color=self.colors["surface"])
                        if hasattr(child, 'ax') and hasattr(child, 'fig'):
                            child.ax.set_facecolor(self.colors["surface"])
                            child.fig.patch.set_facecolor(self.colors["surface"])
                            child.ax.tick_params(colors=self.colors["text"])
                            for spine in child.ax.spines.values():
                                spine.set_color(self.colors["text_secondary"])
                            child.canvas.draw()
            
            # Update status bar
            if hasattr(self, 'status_bar'):
                self.status_bar.configure(fg_color=self.colors["surface"])
                if hasattr(self, 'status_label'):
                    self.status_label.configure(text_color=self.colors["text_secondary"])
                if hasattr(self, 'time_label'):
                    self.time_label.configure(text_color=self.colors["text_secondary"])
        
        except Exception as e:
            print(f"Error updating theme: {e}")

# Run the application
if __name__ == "__main__":
    app = SystemMonitor()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
