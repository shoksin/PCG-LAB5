import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import tkinter.messagebox as messagebox

INSIDE = 0
LEFT = 1
RIGHT = 2
BOTTOM = 4
TOP = 8

def compute_outcode(x, y, xmin, ymin, xmax, ymax):
    code = INSIDE
    if x < xmin:
        code |= LEFT
    elif x > xmax:
        code |= RIGHT
    if y < ymin:
        code |= BOTTOM
    elif y > ymax:
        code |= TOP
    return code

def cohen_sutherland_clip(x1, y1, x2, y2, xmin, ymin, xmax, ymax):
    outcode1 = compute_outcode(x1, y1, xmin, ymin, xmax, ymax)
    outcode2 = compute_outcode(x2, y2, xmin, ymin, xmax, ymax)
    accept = False
    visible_segment = None

    while True:
        if outcode1 == 0 and outcode2 == 0:
            accept = True
            visible_segment = (x1, y1, x2, y2)
            break
        elif outcode1 & outcode2 != 0:
            break
        else:
            outcode_out = outcode1 if outcode1 != 0 else outcode2
            if outcode_out & TOP:
                x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1)
                y = ymax
            elif outcode_out & BOTTOM:
                x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1)
                y = ymin
            elif outcode_out & RIGHT:
                y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
                x = xmax
            elif outcode_out & LEFT:
                y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
                x = xmin

            if outcode_out == outcode1:
                x1, y1 = x, y
                outcode1 = compute_outcode(x1, y1, xmin, ymin, xmax, ymax)
            else:
                x2, y2 = x, y
                outcode2 = compute_outcode(x2, y2, xmin, ymin, xmax, ymax)

    return visible_segment

def sutherland_hodgman_clip(polygon, clip_rect):
    xmin, ymin, xmax, ymax = clip_rect

    def clip_edge(polygon, edge_func):
        new_polygon = []
        for i in range(len(polygon)):
            cur_point = polygon[i]
            prev_point = polygon[i - 1]
            if edge_func(cur_point):
                if not edge_func(prev_point):
                    new_polygon.append(intersect(prev_point, cur_point, edge_func))
                new_polygon.append(cur_point)
            elif edge_func(prev_point):
                new_polygon.append(intersect(prev_point, cur_point, edge_func))
        return new_polygon

    def inside_left(p): return p[0] >= xmin
    def inside_right(p): return p[0] <= xmax
    def inside_bottom(p): return p[1] >= ymin
    def inside_top(p): return p[1] <= ymax

    def intersect(p1, p2, edge_func):
        x1, y1 = p1
        x2, y2 = p2
        if edge_func == inside_left:
            x, y = xmin, y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
        elif edge_func == inside_right:
            x, y = xmax, y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
        elif edge_func == inside_bottom:
            x, y = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1), ymin
        elif edge_func == inside_top:
            x, y = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1), ymax
        return (x, y)

    clipped_polygon = polygon
    for edge in [inside_left, inside_right, inside_bottom, inside_top]:
        clipped_polygon = clip_edge(clipped_polygon, edge)
    return clipped_polygon

class ClippingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Отсечение отрезков и многоугольников")
        self.root.geometry("1200x900")
        self.root.resizable(False, False)

        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.ax.set_xlim(-25, 25)
        self.ax.set_ylim(-25, 25)
        self.ax.axhline(0, color='black', linewidth=0.5)
        self.ax.axvline(0, color='black', linewidth=0.5)
        self.ax.set_xticks(range(-25, 26, 1))
        self.ax.set_yticks(range(-25, 26, 1))
        self.ax.grid(True)


        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Label(self.control_frame, text="Координаты отрезка(x1 y1 x2 y2)", font=("Comic Sans MS", 18)).grid(row=0, column=0, padx=1, pady=5)
        self.segment_entry = tk.Entry(self.control_frame, font=("Arial", 18), width=33)
        self.segment_entry.grid(row=0, column=1, padx=1, pady=5)

        tk.Label(self.control_frame, text="Координаты окна(Xmin Ymin Xmax Ymax)", font=("Comic Sans MS", 18)).grid(row=1, column=0, padx=2, pady=5)
        self.window_entry = tk.Entry(self.control_frame, font=("Arial", 18), width=33)
        self.window_entry.grid(row=1, column=1, padx=1, pady=5)

        self.add_button = tk.Button(self.control_frame, text="Добавить отрезок", font=("Comic Sans MS", 16), command=self.add_segment, fg="black", bg="white")
        self.add_button.grid(row=0, column=2, padx=1, pady=5)

        self.window_button = tk.Button(self.control_frame, text="Установить окно", font=("Comic Sans MS", 16), command=self.set_window, fg="black", bg="lightgreen")
        self.window_button.grid(row=1, column=2, padx=1, pady=5)
        
        self.clip_button = tk.Button(self.control_frame, text="Отсечь", font=("Comic Sans MS", 28), command=self.clip_segments, fg="black", bg="lightblue")
        self.clip_button.grid(row=2, column=0, padx=1, pady=5, rowspan=2)

        self.polygon_button = tk.Button(self.control_frame, text="Нарисовать многоугольник", font=("Comic Sans MS", 15), command=self.draw_polygon, fg="white", bg="#ff3000")
        self.polygon_button.grid(row=2, column=2, padx=1, pady=3)

        self.finish_polygon_button = tk.Button(self.control_frame, text="Закончить многоугольник", font=("Comic Sans MS", 15), command=self.finish_polygon, fg="white", bg="red")
        self.finish_polygon_button.grid(row=3, column=2, padx=1, pady=3)

        self.clear_button = tk.Button(self.control_frame, text="Стереть все", font=("Comic Sans MS", 28), command=self.clear_all, fg="white", bg="black")
        self.clear_button.grid(row=2, column=1, padx=5, pady=5, rowspan=2)

        self.segments = []
        self.polygon_points = []
        self.clip_window = None

    def clear_all(self):
        self.segments.clear()
        self.polygon_points.clear()
        self.clip_window = None
        self.ax.clear()
        
        self.ax.set_xlim(-25, 25)
        self.ax.set_ylim(-25, 25)
        self.ax.axhline(0, color='black', linewidth=0.5)
        self.ax.axvline(0, color='black', linewidth=0.5)
        self.ax.set_xticks(range(-25, 26, 1))
        self.ax.set_yticks(range(-25, 26, 1))
        self.ax.grid(True)
        
        self.canvas.draw()

    def add_segment(self):
        try:
            x1, y1, x2, y2 = map(float, self.segment_entry.get().split())
            self.segments.append((x1, y1, x2, y2))
            self.ax.plot([x1, x2], [y1, y2], 'k-')
            self.canvas.draw()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные координаты отрезка!")

    def set_window(self):
        try:
            xmin, ymin, xmax, ymax = map(float, self.window_entry.get().split())
            self.clip_window = (xmin, ymin, xmax, ymax)
            self.ax.plot([xmin, xmax, xmax, xmin, xmin], [ymin, ymin, ymax, ymax, ymin], 'g')
            self.canvas.draw()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные координаты окна отсечения!")


    def clip_segments(self):
        if self.clip_window:
            xmin, ymin, xmax, ymax = self.clip_window
            if self.polygon_points:
                clipped_polygon = sutherland_hodgman_clip(self.polygon_points, (xmin, ymin, xmax, ymax))
                if clipped_polygon:
                    self.ax.fill(*zip(*clipped_polygon), 'b', alpha=0.5)
            for x1, y1, x2, y2 in self.segments:
                visible_segment = cohen_sutherland_clip(x1, y1, x2, y2, xmin, ymin, xmax, ymax)
                if visible_segment:
                    x1_clip, y1_clip, x2_clip, y2_clip = visible_segment
                    self.ax.plot([x1_clip, x2_clip], [y1_clip, y2_clip], 'b-')
            self.canvas.draw()

    def draw_polygon(self):
        def on_click(event):
            if event.inaxes != self.ax:
                return
            x, y = event.xdata, event.ydata
            self.polygon_points.append((x, y))
            if len(self.polygon_points) > 1:
                self.ax.plot([self.polygon_points[-2][0], self.polygon_points[-1][0]], 
                             [self.polygon_points[-2][1], self.polygon_points[-1][1]], 'r-')
            self.canvas.draw()

        self.cid = self.fig.canvas.mpl_connect('button_press_event', on_click)

    def finish_polygon(self):
        if len(self.polygon_points) > 2:
            self.polygon_points.append(self.polygon_points[0])
            self.ax.plot(*zip(*self.polygon_points), 'r-')
            self.canvas.draw()
        self.fig.canvas.mpl_disconnect(self.cid)

if __name__ == "__main__":
    root = tk.Tk()
    app = ClippingApp(root)
    root.mainloop()