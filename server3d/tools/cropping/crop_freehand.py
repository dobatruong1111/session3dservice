import vtk, logging

from vtkmodules.vtkCommonCore import vtkMath, vtkCommand

from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

from enum import Enum

from typing import Tuple

from tools.cropping.utils import calcClipRange, GetImageToWorldMatrix, GetImageToWorldMatrix, SetImageToWorldMatrix, modifyImage

from utils.utils import DefaultInteractorStyle

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class Operation(Enum): 
    INSIDE=1,
    OUTSIDE=2

# Description: Drawing a 2D contour on display coordinates
class Contour2DPipeline():
    __slots__ = ["isDragging", "polyData", "mapper", "actor", "polyDataThin", "mapperThin", "actorThin"]
    def __init__(self) -> None:
        # 2D contour pipeline
        self.isDragging = False
        self.polyData = vtk.vtkPolyData()
        self.mapper = vtk.vtkPolyDataMapper2D()
        self.mapper.SetInputData(self.polyData)
        self.actor = vtk.vtkActor2D()
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetColor(1, 1, 0)
        self.actor.GetProperty().SetLineWidth(2)
        self.actor.VisibilityOff()

        # Thin 
        self.polyDataThin = vtk.vtkPolyData()
        self.mapperThin = vtk.vtkPolyDataMapper2D()
        self.mapperThin.SetInputData(self.polyDataThin)
        self.actorThin = vtk.vtkActor2D()
        self.actorThin.SetMapper(self.mapperThin)
        outlinePropertyThin = self.actorThin.GetProperty()
        outlinePropertyThin.SetColor(0.7, 0.7, 0)
        outlinePropertyThin.SetLineStipplePattern(0xff00)
        outlinePropertyThin.SetLineWidth(1)
        self.actorThin.VisibilityOff()

'''
Description: Interaction for cropping freehand 
    Step 1: Drawing a 2D contour on the screen
    Step 2: Mapping display space points to world positions
    Step 3: Take 2D contour as polydata line, and extrude surfaces from the near clipping plane
            to the far clipping plane.
    Step 4: Take the rasterized polydata from step 3, and do a 3D stencil operation/filter, where
            you leave voxels on if it's in the rasterized volume, and vice-versa. This can be
            inplemented as a filter, at the cost of duplicating the volume memory.
    Step 5: Render the new volume
'''
class CropFreehandInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(
            self, 
            contour2Dpipeline: Contour2DPipeline, 
            imageData: vtk.vtkImageData, 
            mask: vtk.vtkImageData, 
            operation: Operation,
            fillValue: int,
            defaultInteractorStyle: DefaultInteractorStyle
        ) -> None:
        # Pipeline used to drawing a 2D contour on the screen
        self.contour2Dpipeline = contour2Dpipeline

        # Origin image data
        self.imageData = imageData
        
        # Image data extends some properties from origin image data such as: extent, origin, spacing, direction and scalar type
        self.mask = mask

        # operation: INSIDE or OUTSIDE
        self.operation = operation

        # Fill value
        self.fillValue = fillValue

        # Set when cropping finished
        self.defaultInteractorStyle = defaultInteractorStyle
        
        # Clipping range
        self.clippingRange = None
    
        # Events
        self.AddObserver(vtkCommand.LeftButtonPressEvent, self.__leftButtonPressEvent)
        self.AddObserver(vtkCommand.MouseMoveEvent, self.__mouseMoveEvent)
        self.AddObserver(vtkCommand.LeftButtonReleaseEvent, self.__leftButtonReleaseEvent)

    def setOperation(self, operation: Operation) -> None:
        self.operation = operation

    def setFillValue(self, fillValue: int) -> None:
        self.fillValue = fillValue

    def __createGlyph(self, eventPosition: Tuple) -> None:
        if self.contour2Dpipeline.isDragging:
            points = vtk.vtkPoints()
            lines = vtk.vtkCellArray()
            self.contour2Dpipeline.polyData.SetPoints(points)
            self.contour2Dpipeline.polyData.SetLines(lines)

            points.InsertNextPoint(eventPosition[0], eventPosition[1], 0)

            # Thin
            pointsThin = vtk.vtkPoints()
            linesThin = vtk.vtkCellArray()
            self.contour2Dpipeline.polyDataThin.SetPoints(pointsThin)
            self.contour2Dpipeline.polyDataThin.SetLines(linesThin)

            pointsThin.InsertNextPoint(eventPosition[0], eventPosition[1], 0)
            pointsThin.InsertNextPoint(eventPosition[0], eventPosition[1], 0)

            idList = vtk.vtkIdList()
            idList.InsertNextId(0)
            idList.InsertNextId(1)
            self.contour2Dpipeline.polyDataThin.InsertNextCell(vtk.VTK_LINE, idList)

            self.contour2Dpipeline.actorThin.VisibilityOn()
            self.contour2Dpipeline.actor.VisibilityOn()
        else:
            self.contour2Dpipeline.actor.VisibilityOff()
            self.contour2Dpipeline.actorThin.VisibilityOff()

    def __updateGlyphWithNewPosition(self, eventPosition: Tuple, finalize: bool) -> None:
        if self.contour2Dpipeline.isDragging:
            points = self.contour2Dpipeline.polyData.GetPoints()
            newPointIndex = points.InsertNextPoint(eventPosition[0], eventPosition[1], 0)
            points.Modified()

            idList = vtk.vtkIdList()
            if finalize:
                idList.InsertNextId(newPointIndex)
                idList.InsertNextId(0)
            else:
                idList.InsertNextId(newPointIndex - 1)
                idList.InsertNextId(newPointIndex)

            self.contour2Dpipeline.polyData.InsertNextCell(vtk.VTK_LINE, idList)

            self.contour2Dpipeline.polyDataThin.GetPoints().SetPoint(1, eventPosition[0], eventPosition[1], 0)
            self.contour2Dpipeline.polyDataThin.GetPoints().Modified()
        else:
            self.contour2Dpipeline.actor.VisibilityOff()
            self.contour2Dpipeline.actorThin.VisibilityOff()

    def __leftButtonPressEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        self.contour2Dpipeline.isDragging = True
        eventPosition = self.GetInteractor().GetEventPosition()
        self.__createGlyph(eventPosition)
        self.OnLeftButtonDown()

    def __mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        if self.contour2Dpipeline.isDragging:
            eventPosition = self.GetInteractor().GetEventPosition()
            self.__updateGlyphWithNewPosition(eventPosition, False)
            self.GetInteractor().Render()
            
    def __leftButtonReleaseEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        if self.contour2Dpipeline.isDragging:
            renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
            eventPosition = self.GetInteractor().GetEventPosition()
            self.contour2Dpipeline.isDragging = False

            self.__updateGlyphWithNewPosition(eventPosition, True)
            self.__paintApply()

            renderer.RemoveActor(self.contour2Dpipeline.actor)
            renderer.RemoveActor(self.contour2Dpipeline.actorThin)

            self.OnLeftButtonUp()
            self.GetInteractor().SetInteractorStyle(self.defaultInteractorStyle)

    '''
    Description: Extrude surfaces from the near clipping plane to the far clipping plane.
    '''
    def __updateBrushModel(self, brushPolyDataNormals: vtk.vtkPolyDataNormals) -> bool:
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        camera = renderer.GetActiveCamera()

        pointsXY = self.contour2Dpipeline.polyData.GetPoints() # vtkPoints
        numberOfPoints = pointsXY.GetNumberOfPoints()

        segmentationToWorldMatrix = vtk.vtkMatrix4x4()
        segmentationToWorldMatrix.Identity()

        closedSurfacePoints = vtk.vtkPoints()
        
        # Camera parameters
        # Camera position
        cameraPos = list(camera.GetPosition())
        cameraPos.append(1)
        # Focal point
        cameraFP = list(camera.GetFocalPoint())
        cameraFP.append(1)
        # Direction of projection
        cameraDOP = [0, 0, 0]
        for i in range(3):
            cameraDOP[i] = cameraFP[i] - cameraPos[i]
        vtkMath.Normalize(cameraDOP)
        # Camera view up
        cameraViewUp = list(camera.GetViewUp())
        vtkMath.Normalize(cameraViewUp)
        
        renderer.SetWorldPoint(cameraFP[0], cameraFP[1], cameraFP[2], cameraFP[3])
        renderer.WorldToDisplay()
        displayCoords = renderer.GetDisplayPoint()
        selectionZ = displayCoords[2]

        # Get modifier labelmap extent in camera coordinates to know how much we have to cut through
        cameraToWorldMatrix = vtk.vtkMatrix4x4()
        cameraViewRight = [1, 0, 0]
        vtkMath.Cross(cameraDOP, cameraViewUp, cameraViewRight) # Tich co huong
        for i in range(3):
            cameraToWorldMatrix.SetElement(i, 0, cameraViewUp[i])
            cameraToWorldMatrix.SetElement(i, 1, cameraViewRight[i])
            cameraToWorldMatrix.SetElement(i, 2, cameraDOP[i])
            cameraToWorldMatrix.SetElement(i, 3, cameraPos[i])
        # cameraToWorldMatrix = [cameraViewUp cameraViewRight cameraDOP cameraPos]
        # print(cameraToWorldMatrix)

        worldToCameraMatrix = vtk.vtkMatrix4x4()
        vtk.vtkMatrix4x4().Invert(cameraToWorldMatrix, worldToCameraMatrix)
        # print(worldToCameraMatrix)

        segmentationToCameraTransform = vtk.vtkTransform()
        segmentationToCameraTransform.Concatenate(worldToCameraMatrix)
        segmentationToCameraTransform.Concatenate(segmentationToWorldMatrix)
        # print(segmentationToCameraTransform)

        if self.clippingRange is None:
            self.clippingRange = calcClipRange(self.mask, segmentationToCameraTransform, camera)
        
        for pointIndex in range(numberOfPoints):
            # Convert the selection point into world coordinates
            pointXY = pointsXY.GetPoint(pointIndex)
            renderer.SetDisplayPoint(pointXY[0], pointXY[1], selectionZ)
            renderer.DisplayToWorld()
            worldCoords = renderer.GetWorldPoint()
            if worldCoords[3] == 0:
                logging.info("Bad homogeneous coordinates - __updateBrushModel() function - cropping freehand tool")
                return False
            
            # Convert from homo coordinates to world coordinates
            pickPosition = [0, 0, 0]
            for i in range(3):
                pickPosition[i] = worldCoords[i] / worldCoords[3]

            # Compute the ray endpoints. The ray is along the line running from
            # the camera position to the selection point, starting where this line
            # intersects the front clipping plane, and terminating where this line
            # intersects the back clipping plane.
            ray = [0, 0, 0]
            for i in range(3):
                ray[i] = pickPosition[i] - cameraPos[i] # vector
            rayLength = vtk.vtkMath().Dot(cameraDOP, ray)
            if rayLength == 0:
                # print("Cannot process points")
                logging.error("Cannot process points - __updateBrushModel() function - cropping freehand tool")
                return False

            # Finding a point on the near clipping plane and a point on the far clipping plane 
            # (two points in world coordinates)
            p1World = [0, 0, 0]
            p2World = [0, 0, 0]
            tF = 0
            tB = 0
            if camera.GetParallelProjection():
                tF = self.clippingRange[0] - rayLength
                tB = self.clippingRange[1] - rayLength
                for i in range(3):
                    p1World[i] = pickPosition[i] + tF * cameraDOP[i]
                    p2World[i] = pickPosition[i] + tB * cameraDOP[i]
            else:
                tF = self.clippingRange[0] / rayLength
                tB = self.clippingRange[1] / rayLength
                for i in range(3):
                    p1World[i] = cameraPos[i] + tF * ray[i]
                    p2World[i] = cameraPos[i] + tB * ray[i]
                closedSurfacePoints.InsertNextPoint(p1World)
                closedSurfacePoints.InsertNextPoint(p2World)

        # Skirt
        closedSurfaceStrips = vtk.vtkCellArray() # object to represent cell connectivity
        # Create cells by specifying a count of total points to be inserted,
        # and then adding points one at a time using method InsertCellPoint()
        closedSurfaceStrips.InsertNextCell(numberOfPoints * 2 + 2)
        for i in range(numberOfPoints * 2):
            closedSurfaceStrips.InsertCellPoint(i)
        closedSurfaceStrips.InsertCellPoint(0)
        closedSurfaceStrips.InsertCellPoint(1)

        # Front cap
        closedSurfacePolys = vtk.vtkCellArray() # object to represent cell connectivity
        closedSurfacePolys.InsertNextCell(numberOfPoints)
        for i in range(numberOfPoints):
            closedSurfacePolys.InsertCellPoint(i * 2)

        # Back cap
        closedSurfacePolys.InsertNextCell(numberOfPoints)
        for i in range(numberOfPoints):
            closedSurfacePolys.InsertCellPoint(i * 2 + 1)
        
        # Construct polydata
        closedSurfacePolyData = vtk.vtkPolyData()
        closedSurfacePolyData.SetPoints(closedSurfacePoints)
        closedSurfacePolyData.SetStrips(closedSurfaceStrips)
        closedSurfacePolyData.SetPolys(closedSurfacePolys)

        brushPolyDataNormals.SetInputData(closedSurfacePolyData)
        brushPolyDataNormals.Update()

        return True

    '''
    Description:
        Using a transform matrix to convert from world coordinates to model (image) coordinates.
        Set bounds for image stencil with two cases: INSIDE or OUTSIDE
    '''
    def __updateBrushStencil(
        self, 
        worldToModifierLabelmapIjkTransform: vtk.vtkTransform, 
        worldToModifierLabelmapIjkTransformer: vtk.vtkTransformPolyDataFilter, 
        brushPolyDataToStencil: vtk.vtkPolyDataToImageStencil
    ) -> None:
        worldToModifierLabelmapIjkTransform.Identity()

        segmentationToSegmentationIjkTransformMatrix = vtk.vtkMatrix4x4()
        GetImageToWorldMatrix(self.mask, segmentationToSegmentationIjkTransformMatrix)
        segmentationToSegmentationIjkTransformMatrix.Invert()

        worldToModifierLabelmapIjkTransform.Concatenate(segmentationToSegmentationIjkTransformMatrix)

        worldToSegmentationTransformMatrix = vtk.vtkMatrix4x4()
        worldToSegmentationTransformMatrix.Identity()

        worldToModifierLabelmapIjkTransform.Concatenate(worldToSegmentationTransformMatrix)

        worldToModifierLabelmapIjkTransformer.Update()

        brushPolyDataToStencil.SetOutputWholeExtent(self.mask.GetExtent())

    '''
    Description: 
        Convert from image stencil to image data, set cropped region equal 1.
        Set spacing, origin and direction.
    '''
    def __paintApply(self) -> None:
        brushPolyDataNormals = vtk.vtkPolyDataNormals()
        brushPolyDataNormals.AutoOrientNormalsOn()

        worldToModifierLabelmapIjkTransformer = vtk.vtkTransformPolyDataFilter()
        worldToModifierLabelmapIjkTransform = vtk.vtkTransform()
        worldToModifierLabelmapIjkTransformer.SetTransform(worldToModifierLabelmapIjkTransform)
        worldToModifierLabelmapIjkTransformer.SetInputConnection(brushPolyDataNormals.GetOutputPort())

        brushPolyDataToStencil = vtk.vtkPolyDataToImageStencil()
        brushPolyDataToStencil .SetOutputOrigin(0, 0, 0)
        brushPolyDataToStencil.SetOutputSpacing(1, 1, 1)
        brushPolyDataToStencil.SetInputConnection(worldToModifierLabelmapIjkTransformer.GetOutputPort())

        if not self.__updateBrushModel(brushPolyDataNormals): return
        
        self.__updateBrushStencil(worldToModifierLabelmapIjkTransform, worldToModifierLabelmapIjkTransformer, brushPolyDataToStencil)

        brushPolyDataToStencil.Update()
    
        # vtkImageStencilToImage will convert an image stencil into a binary image
        # The default output will be an 8-bit image with a value of 1 inside the stencil and 0 outside
        stencilToImage = vtk.vtkImageStencilToImage()
        stencilToImage.SetInputData(brushPolyDataToStencil.GetOutput())
        stencilToImage.SetInsideValue(self.operation == Operation.INSIDE)
        stencilToImage.SetOutsideValue(self.operation != Operation.INSIDE)
        stencilToImage.SetOutputScalarType(vtk.VTK_UNSIGNED_CHAR) # vtk.VTK_UNSIGNED_CHAR: [0 -> 255]
        stencilToImage.Update()

        orientedBrushPositionerOutput = stencilToImage.GetOutput()

        imageToWorld = vtk.vtkMatrix4x4()
        GetImageToWorldMatrix(self.mask, imageToWorld)
        SetImageToWorldMatrix(orientedBrushPositionerOutput, imageToWorld)

        modifyImage(self.mask, orientedBrushPositionerOutput)
        self.__maskVolume()

    '''
    Description: Apply the mask for volume and render the new volume
        Hard edge: CT-Bone, CT-Angio
        Soft edge: CT-Muscle, CT-Mip
    '''
    def __maskVolume(self) -> None:
        shape = tuple(reversed(self.imageData.GetDimensions())) # (z, y, x)
        imageDataArray = vtk_to_numpy(self.imageData.GetPointData().GetScalars()).reshape(shape)

        # Convert binary mask image and origin image data from vtkDataArray (supper class) to numpy
        maskArray = vtk_to_numpy(self.mask.GetPointData().GetScalars()).reshape(shape)

        imageDataArray[maskArray > 0] = self.fillValue

        self.imageData.GetPointData().SetScalars(numpy_to_vtk(imageDataArray.reshape(1, -1)[0]))