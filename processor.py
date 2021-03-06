import sys
import numpy as np
import cv2
import util
import logging

from shapely.geometry import Point, LineString, Polygon
from element import *

class ElementDetector:

  def __init__(self):
    self.ocr = None
    # self.gui = None
    self.step = None

  def destroy_all_children(self, root):
    for i in range(len(root.children)):
      self.destroy_all_children(root.children[i])
      root.children[i] = None
    root.children = []

  def traverse_as_json(self, root):
    json = root.as_json()
    for i in range(len(root.children)):
      json += ","
      json += self.traverse_as_json(root.children[i])
    return json

  def destroy_all_children_of_triangle(self, root):
    if root.is_a(Description.Triangle):
      for i in range(len(root.children)):
        logging.info("Destroyed because its parent ('" + root.name + "') is Triangle: " + root.children[i].name)
      self.destroy_all_children(root)

    for c in root.children:
      self.destroy_all_children_of_triangle(c)

  def detect_image_placeholder(self, root):
    if len(root.children) == 4 and (root.is_a(Description.Quadrilateral)) and util.all_are(root.children, Description.Triangle):
      root.description = Description.ImagePlaceholder
      logging.info("Found ImagePlaceholder Rect: %s" % (root.name))
      root.name = root.description
      self.destroy_all_children(root)

    for c in root.children:
      self.detect_image_placeholder(c)

  def detect_video_player(self, root):
    if len(root.children) == 1 and root.is_a(Description.HorizontalRectangle) and root.children[0].is_a(Description.Triangle):
      root.description = Description.VideoPlayer
      logging.info("Found VideoPlayer Rect: %s and Tri: %s" % (root.name, root.children[0].name))
      root.name = root.description
      self.destroy_all_children(root)

    for c in root.children:
      self.detect_video_player(c)

  def detect_panel(self, root):
    if len(root.children) >= 1 and root.is_a(Description.HorizontalRectangle):
      root.description = Description.Panel
      root.name = root.description

    for c in root.children:
      self.detect_panel(c)

  def interpret_leaf_rectangle(self, root):
    if root.is_leaf():
      if root.is_a(Description.HorizontalRectangle):
        if (root.ratio > 4):
          root.description = Description.TextField
        else:
          root.description = Description.TextArea
        root.name = root.description
    
    for c in root.children:
      self.interpret_leaf_rectangle(c)

  def append_text_elements(self, filename, root, last_id):
    if self.ocr:
      response = self.ocr.detect_text(filename)
      if not bool(response):
        logging.info("No texts found.")
        return
      logging.info(response)

      texts = response[0]["description"].split("\n")
      texts = texts[:len(texts)-1]

      for i in range(len(texts)):
        text = texts[i]
        # vertice = response[0]["boundingPoly"]["vertices"][i]
       
        # TODO: Generate Unique ID
        last_id += 1
        e_id = last_id

        # TODO: Find proper position and size
        x = 100
        y = 60 * (i + 1)
        width = 200
        height = 50

        vertices = [Point(x, y), Point(x, y + height), Point(x + width, y + height), Point(x + width, y)]
        element = TextElement(e_id, vertices, text, text)
        root.add_child(element)

  def detect(self, filename):
    img = cv2.imread(filename, cv2.IMREAD_COLOR)
    if img is None:
      return '{"error_message": "Can\'t open file\'' + filename + '\'"}'

    self.step.log(img)
    prefer_height = 1000.0
    raw_height = img.shape[0]
    raw_width = img.shape[1]
    size_factor = prefer_height / raw_height
    img = cv2.resize(img, (int(raw_width * size_factor), int(prefer_height)))
    self.step.log(img)

    after_img = img.copy()
    original_img = img.copy()
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    self.step.log(img)

    img = cv2.GaussianBlur(img, (11, 11), 0)
    self.step.log(img)
    
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 51, 5)
    self.step.log(img)
    # src, result_intensity, method, type, block, area, weight_sum                   
    # cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    # cv2.THRESH_OTSU cv2.THRESH_BINARY
            
    img = cv2.bitwise_not(img)

    # if self.gui:
      # self.gui.show_image(0, img, 900)
    
    height, width = img.shape
    before_img = None
    final_img = np.zeros((height, width, 3), np.uint8)
    
    img = cv2.Canny(img, 128, 200) # min max
    self.step.log(img)
    # after_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    
    # if self.gui:
      # self.gui.show_image(1, img, 900)

    # cv2.cv.CV_RETR_EXTERNAL cv2.cv.CV_RETR_LIST
    contours, hierarchy = cv2.findContours(img, cv2.cv.CV_RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    elements = []
    root_element = Element(0, [Point(0, 0), Point(0, height), Point(width, height), Point(width, 0)], "Root")
    root_element.description = Description.Root
    root_area = root_element.polygon.area
    root_width = root_element.width
    # print root_width

    size_threshold = (0.05 / 100 * root_area)

    ### SHOW_WITHOUT_PREPROCESSING
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if self.step.active:
      last_number = 0
      for number, cnt in enumerate(contours):
        last_number = number
        if hierarchy[0, number, 3] == -1:
          approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
          vertices = util.get_vertices(approx)
          self.step.draw_vertices(img, vertices, (0, 0, 255), str(number))
          self.step.draw_vertices(original_img, vertices, (0, 0, 255), str(number))
      self.step.log(img)
      self.step.log(original_img)
    ###


    last_number = 0
    for number, cnt in enumerate(contours):
      last_number = number
      if hierarchy[0, number, 3] == -1:
        approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)

        vertices = util.get_vertices(approx)
        vertex_count = len(vertices)

        # if self.gui:
          # self.gui.raw_draw(before_img, vertices, util.rand_color(), str(number))
        before_img = after_img.copy()
        self.step.draw_vertices(before_img, util.get_bounding_vertices(vertices), (0, 255, 255), "")
        self.step.log_vertices(before_img, vertices, (0, 0, 255), str(number))

        vertices = util.reduce_vertex_by_length(vertices, 0.01 * root_width)
        vertices = util.reduce_vertex_by_angle(vertices, 160)
        vertices = util.reduce_vertex_by_average_length(vertices, 0.2)
        vertices = util.reduce_vertex_by_angle(vertices, 145)
        vertices = util.reduce_vertex_by_average_length(vertices, 0.25)
        vertices = util.reduce_vertex_by_angle(vertices, 130)
        vertices = util.reduce_vertex_by_average_length(vertices, 0.1)

        before_img = after_img.copy()
        self.step.draw_vertices(before_img, util.get_bounding_vertices(vertices), (0, 255, 255), "")
        self.step.log_vertices(before_img, vertices, (0, 0, 255), str(number))

        # vertices = util.reduce_vertex_by_average_length(vertices, 0.3)
        vertex_count = len(vertices)

        # if self.gui:
        #   self.gui.raw_draw(after_img, vertices, util.rand_color(), str(number))
        self.step.log_vertices(after_img, vertices, (255, 0, 0), str(number))
        self.step.draw_vertices(final_img, vertices, (0, 255, 0), str(number))

        if (vertex_count == 3):
          e = TriangleElement(number, vertices, "Tri#" + str(number))
          if e.polygon.area > size_threshold:
            elements.append(e)
          continue
        elif (vertex_count == 4):
          e = QuadrilateralElement(number, vertices, "Quad#" + str(number))
          if e.polygon.area > size_threshold:
            elements.append(e)
          continue
        else:
          pass

    self.step.log(final_img)
    # if self.gui:
    #   self.gui.show_image(2, before_img, 900)
    # if self.gui:
    #   self.gui.show_image(3, after_img, 900)

    elements = util.remove_resembling_element(elements, 0.5)
    elements.append(root_element)
    
    # START HANDLING ELEMENTS AS TREE
    util.construct_tree_by_within(elements) # use root_element from now on
    self.append_text_elements(filename, root_element, last_number)
    self.destroy_all_children_of_triangle(root_element)
    self.detect_video_player(root_element)
    self.detect_image_placeholder(root_element)
    self.detect_panel(root_element)
    self.interpret_leaf_rectangle(root_element)

    # if self.gui:
    #   self.gui.draw_tree(newimg, root_element)

    util.print_tree(root_element)
    
    # self.step.tree_log(root_element)
    # if self.gui:
    #   self.gui.show_image(4, newimg, 900)

    util.assign_depth(root_element)
    json_result = "{"
    json_result += '"error_message": null,'
    json_result += '"json_elements": {'
    json_result += '"width":' + str(width) + ','
    json_result += '"height":' + str(height) + ','
    json_result += '"elements":['
    json_result += self.traverse_as_json(root_element)
    json_result += "]"
    json_result += "}"
    json_result += "}"

    return json_result