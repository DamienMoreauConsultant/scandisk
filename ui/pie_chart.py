"""
Pie chart widget for visualizing directory sizes.
"""

from typing import List, Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QColor, QFont, QPen, QBrush
from utils.constants import PIE_CHART_COLORS
from utils.file_utils import format_size


class PieChartWidget(QWidget):
    """Widget for displaying a pie chart of directory sizes."""
    
    def __init__(self):
        super().__init__()
        self._chart = QChart()
        self._chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self._chart.setTitle("Directory Distribution")
        self._chart.setTitleFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._chart.legend().setVisible(True)
        self._chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        self._chart_view = QChartView(self._chart)
        self._chart_view.setRenderHints(Qt.RenderHints.Antialiasing)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._chart_view)
        
        self._series = QPieSeries()
        self._series.setHoleSize(0.35)  # Donut chart
        self._chart.addSeries(self._series)
        
        self._data: List[tuple] = []
        self._parent_path: str = ""
        
    def set_data(self, labels: List[str], sizes: List[int], parent_path: str):
        """
        Set the data for the pie chart.
        
        Args:
            labels: List of category labels.
            sizes: List of sizes (in bytes) for each category.
            parent_path: The parent directory path.
        """
        self._data = list(zip(labels, sizes))
        self._parent_path = parent_path
        self._update_chart()
        
    def clear(self):
        """Clear the pie chart."""
        self._series.clear()
        self._data = []
        self._parent_path = ""
        self._chart.setTitle("Directory Distribution")
        
    def _update_chart(self):
        """Update the chart with current data."""
        self._series.clear()
        
        if not self._data:
            self._chart.setTitle("No data to display")
            return
            
        total_size = sum(size for _, size in self._data)
        
        # Sort by size (descending)
        sorted_data = sorted(self._data, key=lambda x: x[1], reverse=True)
        
        for i, (label, size) in enumerate(sorted_data):
            if size == 0:
                continue
                
            # Get color from palette (repeat if needed)
            color = QColor(PIE_CHART_COLORS[i % len(PIE_CHART_COLORS)])
            
            # Create slice
            slice = QPieSlice(label, size)
            slice.setColor(color)
            slice.setLabelVisible(True)
            slice.setLabel(f"{label}\n{format_size(size)} ({size/total_size*100:.1f}%)")
            slice.setLabelFont(QFont("Segoe UI", 8))
            slice.setLabelPosition(QPieSlice.LabelPosition.LabelInsideHorizontal)
            
            # Add tooltip
            slice.tooltip = f"{label}: {format_size(size)} ({size/total_size*100:.1f}%)"
            
            self._series.append(slice)
            
        # Set chart title
        if self._parent_path:
            self._chart.setTitle(f"Distribution in: {self._parent_path}")
        else:
            self._chart.setTitle("Directory Distribution")
