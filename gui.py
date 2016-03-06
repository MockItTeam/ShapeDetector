import sys
from PyQt4 import QtCore, QtGui

class ImageDebuggerGUI(QtGui.QWidget):
  def __init__(self, parent = None):
    super(ImageDebuggerGUI, self).__init__(parent)

    group_box = QtGui.QGroupBox("Steps")
    grid_layout = QtGui.QGridLayout()
    grid_layout.setSpacing(10)
    group_box.setLayout(grid_layout)

    # self.l1 = QtGui.QLabel("Threshold")
    # self.l1.setAlignment(QtCore.Qt.AlignCenter)
    # layout.addWidget(self.l1)
    # self.sl = QtGui.QSlider(QtCore.Qt.Horizontal)
    # self.sl.setMinimum(40)
    # self.sl.setMaximum(100)
    # self.sl.setValue(3)
    # self.sl.setTickPosition(QtGui.QSlider.TicksBelow)
    # self.sl.setTickInterval(1)
    # layout.addWidget(self.sl, 0, 0)

    scroll_area = QtGui.QScrollArea()
    scroll_area.setWidget(group_box)
    scroll_area.setWidgetResizable(True)
    scroll_area.setFixedWidth(1200)
    scroll_area.setFixedHeight(800)
    
    layout = QtGui.QVBoxLayout(self)
    layout.addWidget(scroll_area)

    self.pic_labels = []

    for i in range(5):
      pic_label = QtGui.QLabel()
      pic_label.setGeometry(10, 10, 100, 100)
      grid_layout.addWidget(pic_label, 5 - i, 0)
      self.pic_labels.append(pic_label)

    # self.sl.valueChanged.connect(self.valuechange)
    self.setLayout(layout)
    self.setWindowTitle("Image Debugger")
    self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

  def mouseReleaseEvent(self, QMouseEvent):
    # cursor = QtGui.QCursor()
    sys.exit(0)

  def valuechange(self):
    val = self.sl.value()
    self.l1.setText(str(val))
    cv2.destroyAllWindows()

  def show_image(self, index, img, height):
    tmp = "out/ " + str(index) + ".jpg"
    cv2.imwrite(tmp, img)
    pixmap = QtGui.QPixmap(tmp)
    pixmap = pixmap.scaledToHeight(height)
    self.pic_labels[index].setPixmap(pixmap)

  def draw_tree(self, root):
    self.draw(self.newimg, root, util.rand_color())
    for c in root.children:
      self.draw_tree(c)

  def draw(self, img, component, color):
    vertices = component.vertices

    vertex_count = len(vertices)
    for i in range(vertex_count):
      cv2.circle(img, util.point_to_int_tuple(vertices[i]), 3, color, -1)
      cv2.line(img, util.point_to_int_tuple(vertices[i]), util.point_to_int_tuple(vertices[(i + 1) % vertex_count]), color, 1)

    # centroid = util.point_to_int_tuple(polygon.centroid)
    cv2.putText(img, component.description, util.point_to_int_tuple(vertices[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

  def raw_draw(self, img, vertices, color, tag):
    vertex_count = len(vertices)
    for i in range(vertex_count):
      cv2.circle(img, util.point_to_int_tuple(vertices[i]), 3, color, -1)
      cv2.line(img, util.point_to_int_tuple(vertices[i]), util.point_to_int_tuple(vertices[(i + 1) % vertex_count]), color, 1)
    cv2.putText(img, tag, util.point_to_int_tuple(vertices[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)