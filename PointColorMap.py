from __main__ import vtk, qt, ctk, slicer

#
# PointColorMap
#

class PointColorMap:
  def __init__(self, parent):
    parent.title = "Marked Point Color Data"
    parent.categories = ["Examples"]
    parent.dependencies = []
    parent.contributors = ["Isaiah Norton, Brigham & Women's Hospital"]
    parent.helpText = """
    This is a module to apply colors to a set of marked points based on a specified value.
    """
    parent.acknowledgementText = """
    This file was originally developed by Isaiah Norton, Brigham & Women's Hospital, and supported in part by grant 1DP2OD007383-01.
""" 
    self.parent = parent

#
# qPointColorMapWidget
#

class PointColorMapWidget:
  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

  def setup(self):
    # Instantiate and connect widgets ...

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "PointColorMap Reload"
    self.layout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)


    # MarkupsFiducial Node Selector
    self.aLS = slicer.qMRMLNodeComboBox()
    self.aLS.setMRMLScene(slicer.mrmlScene)
    self.aLS.nodeTypes = (["vtkMRMLMarkupsFiducialNode"])
    self.aLS.connect('currentNodeChanged(vtkMRMLNode*)', self.setMarkupListNode)
    self.layout.addWidget(self.aLS)

    # ColorMap selector
    self.cmS = slicer.qMRMLColorTableComboBox()
    self.cmS.setMRMLScene(slicer.mrmlScene)
    self.layout.addWidget(self.cmS) 

    # Discrete Checkbox
    self.dsctCB = qt.QCheckBox()
    self.dsctCB.setText("Discrete Colors")
    self.layout.addWidget(self.dsctCB)

    # Discrete Checkbox
    self.scale1CB = qt.QCheckBox()
    self.scale1CB.setText("Concentration colors")
    self.layout.addWidget(self.scale1CB)

    # Manual color scale
    self.manualCmapCB = qt.QCheckBox()
    self.manualCmapCB.setText("Fixed range")
    self.layout.addWidget(self.manualCmapCB)

    self.manualCmapRange1 = qt.QLineEdit()
    self.manualCmapRange1L = qt.QLabel() 
    self.manualCmapRange1L.setText("Low:")
    self.manualCmapRange2 = qt.QLineEdit()
    self.manualCmapRange2L = qt.QLabel()
    self.manualCmapRange2L.setText("High:")

    self.manualCmapRangeLayout = qt.QHBoxLayout()
    self.manualCmapRangeLayout.addWidget(self.manualCmapRange1L)
    self.manualCmapRangeLayout.addWidget(self.manualCmapRange1)
    self.manualCmapRangeLayout.addWidget(self.manualCmapRange2L)
    self.manualCmapRangeLayout.addWidget(self.manualCmapRange2)

    self.manualCmapRangeFrame = qt.QFrame()
    self.manualCmapRangeFrame.setLayout(self.manualCmapRangeLayout)
    self.layout.addWidget(self.manualCmapRangeFrame)
    
    # Data Table View
    self.plView = qt.QTableView()
    self.plViewModel = qt.QStandardItemModel()
    self.plView.sortingEnabled = True
    vHeader = self.plView.verticalHeader()
    vHeader.hide()
    hHeader = self.plView.horizontalHeader()
    self.layout.addWidget(self.plView)


		# Paste action for data table
    paste = qt.QAction(self.plView)
    paste.setText("")
    paste.setShortcut( qt.QKeySequence('Ctrl+V') )
    paste.connect('triggered()', self.pasteData)
    self.plView.addAction(paste)

    # Update Button
    self.updateButton = qt.QPushButton("Apply ColorMap")
    self.updateButton.connect('clicked()', self.updateColorMap)
    self.layout.addWidget(self.updateButton)    

    # Toggle text display checkbox
    self.tdCB = qt.QCheckBox()
    self.tdCB.setText("Toggle Label Display")
    self.tdCB.connect('stateChanged(int)', self.toggleTextDisplay)
    self.layout.addWidget(self.tdCB)


  def setMarkupListNode(self, newNode):
    self.listNode = newNode
    self.updateList()

  def pasteData(self):
    self.dataRows = []
    if self.listNode is None:
      return
    cb = slicer.app.clipboard()
    cb_text = cb.text().split('\n')
    for i,row in enumerate(cb_text):
      item = self.plViewModel.item(i,1)
      if item:
        item.setText(row)
        self.dataRows.append(row)

  def updateList(self):
    self.fiduNodes = {}
    self.plViewModel.clear() 
    self.plView.setModel(self.plViewModel)
    
    numNodes = self.listNode.GetNumberOfFiducials()
    actRow = 0
    for i in xrange(0,numNodes):
      #annoNode = self.listNode.GetNthChildNode(i)
      #fiduNode = annoNode.GetAssociatedNode()
      if (self.listNode.GetNthFiducialVisibility(i) == False):
        continue
      fiduNodeName = self.listNode.GetNthFiducialLabel(i)

      labelItem = qt.QStandardItem()
      labelItem.setText( str(fiduNodeName) )
      entryItem = qt.QStandardItem()
      colorItem = qt.QStandardItem()
      self.plViewModel.setItem(actRow, 0, labelItem)
      self.plViewModel.setItem(actRow, 1, entryItem)
      self.plViewModel.setItem(actRow, 2, colorItem)

      actRow += 1

      # need to keep items so they don't go out of scope...
      self.fiduNodes[fiduNodeName] = [self.listNode.GetNthMarkupID(), labelItem, entryItem, colorItem]
    self.plViewModel.setHeaderData(0, 1, "Sample")
    self.plViewModel.setHeaderData(1, 1, "Value")
    self.plViewModel.setHeaderData(2, 1, "Color")

 
  def updateColorMap(self):
    self.colorItems = []
    self.dataRows = filter(None, self.dataRows)
    
    # Find data range
    d_float = [float(_x) for _x in self.dataRows]
    d_range = [min(d_float), max(d_float)]

    cmapNode = self.cmS.currentNode()
    if not cmapNode:
      print "No color map selected!"
      return
    lut = cmapNode.GetLookupTable()
    self.orig_range = [0.0,0.0]
    self.orig_range = lut.GetRange()

    #print self.dataRows
    print "orig range: ", self.orig_range
    print "d_range: ", d_range
   
    # Set color range unless asked for discrete
    if (not self.dsctCB.checked):
      lut.SetRange(d_range[0], d_range[1])
      lut.Modified()
    # Set to fixed range for concentration colors
    if (self.scale1CB.checked):
      lut.SetRange(0.0, 3.0)
      lut.Modified()
    if (self.manualCmapCB.checked):
      rLo = float(self.manualCmapRange1.text)
      rHi = float(self.manualCmapRange2.text)
      lut.SetRange(rLo, rHi)
      lut.Modified()

    print "lut range: ", lut.GetRange()
    for i in xrange(0, self.plViewModel.rowCount()):
      nameItem = self.plViewModel.item(i,0)
      dataItem = self.plViewModel.item(i,1)
      colorItem = self.plViewModel.item(i,2)
      val = dataItem.text()
      #print "   value: ", val
      rgb = [0,0,0]
      lut.GetColor(float(val),rgb)
      print nameItem, rgb
      rgb255 = [ rgb[0]*255.0, rgb[1]*255.0, rgb[2]*255.0 ]
      colorItem.setBackground(qt.QBrush(qt.QColor.fromRgb(rgb255[0],rgb255[1],rgb255[2])))

      fiduNode = slicer.util.getNode(self.fiduNodes[nameItem.text()][0])
      fiduNode.GetDisplayNode().SetColor(rgb)
      fiduNode.GetAnnotationTextDisplayNode().SetColor(rgb)
      fiduNode.GetAnnotationPointDisplayNode().SetColor(rgb)
      fiduNode.Modified()

    print "\nDone"

#    if (not self.dsctCB.checked):
#      lut.SetRange(self.orig_range[0], self.orig_range[1])

  def toggleTextDisplay(self, state):
    for i in xrange(0,self.plViewModel.rowCount()):
      nameItem = self.plViewModel.item(i,0)
      fiduNode = slicer.util.getNode(self.fiduNodes[nameItem.text()][0])
      tdn = fiduNode.GetAnnotationTextDisplayNode()
      if (state):
        tdn.SetTextScale(3.375)
      else:
        tdn.SetTextScale(0)
      fiduNode.Modified()

  def onReload(self,moduleName="PointColorMap"):
    """Generic reload method for any scripted module."""
    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)
