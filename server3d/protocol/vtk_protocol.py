from vtk.web import protocols as vtk_protocols

from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

from wslink import register as exportRpc

import vtk, logging

from vtkmodules.vtkCommonCore import vtkCommand

from model.colormap import CUSTOM_COLORMAP

from model.presets import *

from utils.utils import DefaultInteractorStyle

from tools.measurement.length_measurement import LengthMeasurementPipeline, LengthMeasurementInteractorStyle

from tools.measurement.angle_measurement import AngleMeasurementPipeline, AngleMeasurementInteractorStyle

from tools.cropping.crop_freehand import Contour2DPipeline, CropFreehandInteractorStyle, Operation

from tools.cropping.utils import IPWCallback

from tools.panning.panning import PanningInteractorStyle

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# -------------------------------------------------------------------------
# View Manager
# -------------------------------------------------------------------------

class Volume(vtk_protocols.vtkWebProtocol):
    def __init__(self) -> None:
        # Dicom directory path
        # self.dicomDirPath = "./server3d/data/test"
        self.dicomDirPath = None
    
        # Pipeline
        self.colors = vtk.vtkNamedColors()
        self.reader = vtk.vtkDICOMImageReader()
        self.mask = None
        self.mapper = vtk.vtkSmartVolumeMapper()
        self.volProperty = vtk.vtkVolumeProperty()
        self.volume = vtk.vtkVolume()
        
        # Transfer function
        self.color = vtk.vtkColorTransferFunction()
        self.scalarOpacity = vtk.vtkPiecewiseFunction()

        # Cropping by box
        self.checkBox = False
        self.boxRep = None
        self.widget = None
        self.planes = None

        self.cellPicker = None
        self.defaultInteractorStyle = None

        # Panning
        self.checkPanning = False

        # Crop freehand
        self.contour2Dpipeline = None
        self.cropFreehandInteractorStyle = None

    def colorMappingWithStandardCT(self) -> None:
        self.color.RemoveAllPoints()
        rgbPoints = CUSTOM_COLORMAP.get("STANDARD_CT").get("rgbPoints")
        for point in rgbPoints:
            self.color.AddRGBPoint(point[0], point[1], point[2], point[3])
        self.volProperty.SetColor(self.color)
    
    def setDefaultPreset(self) -> None:
        # Bone preset
        self.colorMappingWithStandardCT()

        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = BONE_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

    def resetBox(self) -> None:
        renderWindowInteractor = self.getApplication().GetObjectIdMap().GetActiveObject("INTERACTOR")

        # Set clipping planes outside 3D object
        planes = vtk.vtkPlanes()
        self.mapper.SetClippingPlanes(planes)

        if self.boxRep is None:
            self.boxRep = vtk.vtkBoxRepresentation()
            self.boxRep.GetOutlineProperty().SetColor(1, 1, 1)
            self.boxRep.SetInsideOut(True)

        if self.widget is None:
            self.widget = vtk.vtkBoxWidget2()
            self.widget.SetRepresentation(self.boxRep)
            self.widget.SetInteractor(renderWindowInteractor)
            self.widget.GetRepresentation().SetPlaceFactor(1)
            self.widget.GetRepresentation().PlaceWidget(self.imageData.GetBounds())
            self.widget.SetEnabled(True)

        if self.planes is None:
            self.planes = vtk.vtkPlanes()
            ipwcallback = IPWCallback(self.planes, self.mapper)
            self.widget.AddObserver(vtk.vtkCommand.InteractionEvent, ipwcallback)
            self.widget.Off()

        # Set origin bounds of box
        self.widget.GetRepresentation().PlaceWidget(self.imageData.GetBounds())

        # Turn off box
        if self.checkBox:
            self.widget.Off()
            self.checkBox = False

    @exportRpc("volume.initialize")
    def createVisualization(self) -> None:
        renderWindow = self.getApplication().GetObjectIdMap().GetActiveObject("VIEW")
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        # Reader
        self.reader.SetDirectoryName(self.dicomDirPath)
        self.reader.Update()

        self.imageData = vtk.vtkImageData()
        self.imageData.DeepCopy(self.reader.GetOutput())

        # Mapper
        self.mapper.SetInputData(self.imageData)

        # Volume property
        self.volProperty.ShadeOn()
        self.volProperty.SetScalarOpacityUnitDistance(0.1)
        self.volProperty.SetInterpolationTypeToLinear() # default: Nearest Neighbor

        # Light
        self.volProperty.SetAmbient(0.1)
        self.volProperty.SetDiffuse(0.9)
        self.volProperty.SetSpecular(0.2)

        # Color mapping
        self.colorMappingWithStandardCT()

        # Bone CT: opacity mapping
        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = BONE_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

        self.volProperty.SetScalarOpacity(self.scalarOpacity)

        # Volume
        self.volume.SetMapper(self.mapper)
        self.volume.SetProperty(self.volProperty)

        # Render
        renderer.AddVolume(self.volume)
        renderer.ResetCamera()

        # Render window
        renderWindow.Render()
        
    @exportRpc("volume.bone.preset.ct")
    def applyBonePresetCT(self) -> None:
        renderWindow = self.getApplication().GetObjectIdMap().GetActiveObject("VIEW")
        self.colorMappingWithStandardCT()

        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = BONE_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

        renderWindow.Render()
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)
      
    @exportRpc("volume.angio.preset.ct")
    def applyAngioPresetCT(self) -> None:
        renderWindow = self.getApplication().GetObjectIdMap().GetActiveObject("VIEW")
        self.colorMappingWithStandardCT()

        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = ANGIO_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

        renderWindow.Render()
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    @exportRpc("volume.muscle.preset.ct")
    def applyMusclePresetCT(self) -> None:
        renderWindow = self.getApplication().GetObjectIdMap().GetActiveObject("VIEW")
        self.colorMappingWithStandardCT()

        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = MUSCLE_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

        renderWindow.Render()
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    @exportRpc("volume.mip.preset.ct")
    def applyMipPresetCT(self) -> None:
        renderWindow = self.getApplication().GetObjectIdMap().GetActiveObject("VIEW")

        self.color.RemoveAllPoints()
        rgbPoints = MIP.get("colorMap").get("rgbPoints")
        if len(rgbPoints):
            for point in rgbPoints:
                self.color.AddRGBPoint(point[0], point[1], point[2], point[3])

        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = MIP.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

        renderWindow.Render()
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    def initObjectsMeasurementTool(self, renderWindowInteractor: vtk.vtkRenderWindowInteractor) -> None:
        if self.defaultInteractorStyle is None:
            self.defaultInteractorStyle = DefaultInteractorStyle()

        if self.cellPicker is None:
            self.cellPicker = vtk.vtkCellPicker()
            self.cellPicker.AddPickList(self.volume)
            self.cellPicker.PickFromListOn()
            renderWindowInteractor.SetPicker(self.cellPicker)

    @exportRpc("volume.length")
    def activeLength(self) -> None:
        renderWindow = self.getApplication().GetObjectIdMap().GetActiveObject("VIEW")
        renderWindowInteractor = renderWindow.GetInteractor()
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        self.initObjectsMeasurementTool(renderWindowInteractor)

        pipeline = LengthMeasurementPipeline()
        renderer.AddActor(pipeline.lineActor)
        renderer.AddActor(pipeline.textActor)

        style = LengthMeasurementInteractorStyle(pipeline, self.defaultInteractorStyle)
        renderWindowInteractor.SetInteractorStyle(style)

        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    @exportRpc("volume.angle")
    def activeAngle(self) -> None:
        renderWindow = self.getApplication().GetObjectIdMap().GetActiveObject("VIEW")
        renderWindowInteractor = renderWindow.GetInteractor()
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        self.initObjectsMeasurementTool(renderWindowInteractor)

        pipeline = AngleMeasurementPipeline()
        renderer.AddActor(pipeline.firstLineActor)
        renderer.AddActor(pipeline.secondLineActor)
        renderer.AddActor(pipeline.arcActor)
        renderer.AddActor(pipeline.textActor)
        renderer.AddActor(pipeline.markText)

        style = AngleMeasurementInteractorStyle(pipeline, self.defaultInteractorStyle)
        renderWindowInteractor.SetInteractorStyle(style)

        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    @exportRpc("volume.cut")
    def activeCut(self) -> None:
        # self.getApplication() -> vtkWebApplication()
        renderWindow = self.getApplication().GetObjectIdMap().GetActiveObject("VIEW")
        renderWindowInteractor = renderWindow.GetInteractor()

        if self.boxRep is None:
            self.boxRep = vtk.vtkBoxRepresentation()
            self.boxRep.GetOutlineProperty().SetColor(1, 1, 1)
            self.boxRep.SetInsideOut(True)

        if self.widget is None:
            self.widget = vtk.vtkBoxWidget2()
            self.widget.SetRepresentation(self.boxRep)
            self.widget.SetInteractor(renderWindowInteractor)
            self.widget.GetRepresentation().SetPlaceFactor(1)
            self.widget.GetRepresentation().PlaceWidget(self.imageData.GetBounds())
            self.widget.SetEnabled(True)

        if self.planes is None:
            self.planes = vtk.vtkPlanes()
            ipwcallback = IPWCallback(self.planes, self.mapper)
            self.widget.AddObserver(vtk.vtkCommand.InteractionEvent, ipwcallback)
            self.widget.Off()

        if not self.checkBox:
            self.widget.On()
            self.checkBox = True
        else:
            self.widget.Off()
            self.checkBox = False

        renderWindow.Render()
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    @exportRpc("volume.cut.freehand")
    def activeCutFreehand(self, operation: Operation = Operation.INSIDE, fillValue: int = -1000) -> None:
        renderWindow = self.getApplication().GetObjectIdMap().GetActiveObject("VIEW")
        renderWindowInteractor = renderWindow.GetInteractor()
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        if self.contour2Dpipeline is None:
            self.contour2Dpipeline = Contour2DPipeline()

        if self.mask is None:
            self.mask = vtk.vtkImageData()
            self.mask.SetExtent(self.imageData.GetExtent())
            self.mask.SetOrigin(self.imageData.GetOrigin())
            self.mask.SetSpacing(self.imageData.GetSpacing())
            self.mask.SetDirectionMatrix(self.imageData.GetDirectionMatrix())
            self.mask.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)
            self.mask.GetPointData().GetScalars().Fill(0)

        if self.defaultInteractorStyle is None:
            self.defaultInteractorStyle = DefaultInteractorStyle()

        if self.cropFreehandInteractorStyle is None:
            self.cropFreehandInteractorStyle = CropFreehandInteractorStyle(
                contour2Dpipeline=self.contour2Dpipeline,
                imageData=self.imageData,
                mask=self.mask,
                operation=Operation.INSIDE,
                fillValue=-1000,
                defaultInteractorStyle=self.defaultInteractorStyle
            )

        renderer.AddActor(self.contour2Dpipeline.actor)
        renderer.AddActor(self.contour2Dpipeline.actorThin)

        self.cropFreehandInteractorStyle.setOperation(operation)
        self.cropFreehandInteractorStyle.setFillValue(fillValue)

        renderWindowInteractor.SetInteractorStyle(self.cropFreehandInteractorStyle)
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    @exportRpc("volume.reset")
    def activeReset(self) -> None:
        renderWindow = self.getApplication().GetObjectIdMap().GetActiveObject("VIEW")
        renderWindowInteractor = renderWindow.GetInteractor()
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        if not self.mask is None:
            shape = tuple(reversed(self.reader.GetOutput().GetDimensions())) # (z, y, x)
            oriImageDataArray = vtk_to_numpy(self.reader.GetOutput().GetPointData().GetScalars()).reshape(shape)
            maskArray = vtk_to_numpy(self.mask.GetPointData().GetScalars()).reshape(shape)
            imageDataArray = vtk_to_numpy(self.imageData.GetPointData().GetScalars()).reshape(shape)

            imageDataArray[maskArray > 0] = oriImageDataArray[maskArray > 0]

            self.imageData.GetPointData().SetScalars(numpy_to_vtk(imageDataArray.reshape(1, -1)[0]))
            self.mask.GetPointData().GetScalars().Fill(0)

        # Set origin 3D object
        # self.mapper.SetInputData(self.imageData)

        # Set origin box status
        self.resetBox()

        # Set default bone preset
        # self.setDefaultPreset()

        # Remove actors
        renderer.RemoveAllViewProps()
        renderer.AddVolume(self.volume)

        # Render window
        renderWindow.Render()

        # Turn off panning interactor
        self.checkPanning = False

        # Set default interactor style
        renderWindowInteractor.SetInteractorStyle(DefaultInteractorStyle())
        
        self.getApplication().InvalidateCache(renderWindow)
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)
    
    @exportRpc("volume.pan")
    def activePan(self) -> None:
        renderWindow = self.getApplication().GetObjectIdMap().GetActiveObject("VIEW")
        renderWindowInteractor = renderWindow.GetInteractor()

        if self.defaultInteractorStyle is None:
            self.defaultInteractorStyle = DefaultInteractorStyle()

        if not self.checkPanning:
            self.checkPanning = True
            style = PanningInteractorStyle(self.defaultInteractorStyle)
        else:
            self.checkPanning = False
            style = self.defaultInteractorStyle

        renderWindowInteractor.SetInteractorStyle(style)

        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)
        