import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import time

# Mustafa_Probe_Tracker
class Mustafa_Probe_Tracker(ScriptedLoadableModule):

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Mustafa_Probe_Tracker" # TODO make this more human readable by adding spaces
    self.parent.categories = ["MEDLAB Probe Tracker"]
    self.parent.dependencies = []


# Mustafa_Probe_TrackerWidget
class Mustafa_Probe_TrackerWidget(ScriptedLoadableModuleWidget):
  """ This class is GUI buttons side of the extension. """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    
    # Adding new collapsible button to loading probe model and tranformation
    loadingCollapsibleButton = ctk.ctkCollapsibleButton()
    loadingCollapsibleButton.text = "Load Probe Model and Transformation"
    self.layout.addWidget(loadingCollapsibleButton)

    # Layout within the dummy collabsible button
    loadingFormLayout = qt.QFormLayout(loadingCollapsibleButton)

    # Create a Mustafa_Probe_TrackerLogic() class for "connect" functions for buttons
    self.logic = Mustafa_Probe_TrackerLogic()

    # "Load Probe" Button
    self.probeButton = qt.QPushButton("Load Probe")
    self.probeButton.toolTip = "Load the Probe Model."
    self.probeButton.enabled = True
    loadingFormLayout.addRow(self.probeButton)

    # "Load Transformation and Apply It" Button
    self.transformationButton = qt.QPushButton("Load Transformation and Apply It")
    self.transformationButton.toolTip = "Load the Transformation."
    self.transformationButton.enabled = True
    loadingFormLayout.addRow(self.transformationButton)

    # "Launch the Plus Server" Button
    self.launchPlusServerButton = qt.QPushButton("Launch the Plus Server")
    self.launchPlusServerButton.toolTip = "Starts the Plus Server"
    self.launchPlusServerButton.enabled = True
    loadingFormLayout.addRow(self.launchPlusServerButton)

    # "Stop the Plus Server" Button
    self.stopPlusServerButton = qt.QPushButton("Stop the Plus Server")
    self.stopPlusServerButton.toolTip = "Stops the Plus Server"
    self.stopPlusServerButton.enabled = True
    loadingFormLayout.addRow(self.stopPlusServerButton)

    # "Start the tracking" Button
    self.startTheTrackingButton = qt.QPushButton("Start the tracking")
    self.startTheTrackingButton.toolTip = "Starts the tracking"
    self.startTheTrackingButton.enabled = True
    loadingFormLayout.addRow(self.startTheTrackingButton)

    # "Load the 3D Model" Button
    self.load3DModelButton = qt.QPushButton("Load the 3D Model")
    self.load3DModelButton.toolTip = "Loads the 3D Model and Fudicial points"
    self.load3DModelButton.enabled = True
    loadingFormLayout.addRow(self.load3DModelButton)

    # Connections for Buttons
    self.probeButton.connect('clicked(bool)',self.logic.loadProbeModel)
    self.transformationButton.connect('clicked(bool)', self.logic.loadPivotTransform)
    self.launchPlusServerButton.connect('clicked(bool)', self.logic.launchPlusServer)
    self.stopPlusServerButton.connect('clicked(bool)',self.logic.stopPlusServer)
    self.startTheTrackingButton.connect('clicked(bool)', self.logic.startTracking)
    self.load3DModelButton.connect('clicked(bool)', self.logic.load3DModel)

    
    # Add vertical spacer
    self.layout.addStretch(1)


# Mustafa_Probe_TrackerLogic
class Mustafa_Probe_TrackerLogic(ScriptedLoadableModuleLogic):

  def __init__(self):
    self.trackerNode = None
    self.transformNode = None
    self.markerModel = None
    self.cameraState = False
    self.launcherNode = None

    # Creating tracker and camera client nodes
    logging.info("Creating default OpenIGTL client.")
    self.trackerNode = Mustafa_Probe_TrackerLogic.startNewClient(18944, 'trackerClientTest')
    self.cameraNodeTest = Mustafa_Probe_TrackerLogic.startNewClient(18945, 'cameraClientTest')

    self.createServerAndLauncherNodes()

  # This function loads the Needle Model that we created previously.
  def loadProbeModel(self):
    slicer.util.loadModel("C:\Users\Mustafa Ugur\Documents\NeedleModel.vtk")
    logging.info("Needle Model is loaded.")

  # This function loads the transformation from the pivot calibration that we
  # done previously sets the hierarcy between needle and transformation.
  def loadPivotTransform(self):
    slicer.util.loadTransform("C:\Users\Mustafa Ugur\Documents\NeedleTipToMarker.h5")
    needleModel = slicer.util.getNode('NeedleModel')
    self.transformNode = slicer.util.getNode('NeedleTipToMarker')
    needleModel.SetAndObserveTransformNodeID(self.transformNode.GetID())

  # This function launches the Plus Server
  def launchPlusServer(self):
    state = self.serverNode.GetState()
    if state != 0:
      stateTxt = self.serverNode.GetStateAsString(state)
      logging.error('Attempted to start server, but server state is %s.', stateTxt)
      return

    self.serverNode.StartServer()
    self.cameraState = True
    logging.info("Plus server started.")

  # This function stops the Plus Server.
  def stopPlusServer(self):
    state = self.serverNode.GetState()
    if state != 1:
      stateTxt = self.serverNode.GetStateAsString(state)
      logging.error('Attempted to start server, but server state is %s.', stateTxt)
      return

    self.serverNode.StopServer()
    self.cameraState = False
    logging.info("Plus Server stopped.")

  # This function starts tracking.
  def startTracking(self):
    if self.cameraState is False:
      self.serverNode.StartServer()

    try:
      self.setHierarcy()
    except:
      print("Marker4ToTracker Exepcion occured.")
    logging.info("Hierarchies done. You can start the tracking.")

  # This function loads the 3D file was created for surface tracking.
  def load3DModel(self):
    slicer.util.loadModel("C:\Users\Mustafa Ugur\Desktop\simple_box\simple_box.STL")
    slicer.util.loadMarkupsFiducialList("C:\Users\Mustafa Ugur\Documents\From.fcsv")
    logging.info("3D Model for tracking is loaded.")

  # This function sets the hierarchy.
  def setHierarcy(self):
    # Setting the hierarchy again
    self.transformNode = slicer.util.getNode('NeedleTipToMarker')
    self.markerModel = slicer.util.getNode('Marker4ToTracker')
    self.transformNode.SetAndObserveTransformNodeID(self.markerModel.GetID())

  @staticmethod
  def startNewClient(port, nodeName):
    clientNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLIGTLConnectorNode', nodeName)
    clientNode.SetServerPort(port)
    clientNode.Start()
    logging.info('Added IGTL client with node name %s.', nodeName)
    return clientNode

  def createServerAndLauncherNodes(self):
    # Reading the config file for Plus Server
    self.fn = "C:\Users\Mustafa Ugur\PlusApp-2.8.0.20190617-Win64\config\PlusDeviceSet_Server_OpticalMarkerTracker_Mmf.xml"
    with open(self.fn, 'r') as file:
      self.configText = file.read()

    # Creating server and launcher nodes
    logging.info("Creating server launcher nodes.")
    self.configTextNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTextNode', 'PlusConfigTextNode')
    self.configTextNode.SetText(self.configText)
    self.launcherNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlusServerLauncherNode", 'PlusLauncherNode')
    self.serverNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlusServerNode", 'PlusServerNode')

    self.launcherNode.AddAndObserveServerNode(self.serverNode)
    self.serverNode.SetAndObserveConfigNode(self.configTextNode)
    logging.info('DvtPlusServer created.')

  def startTheClient(self):
    logging.info("Currently empty.")