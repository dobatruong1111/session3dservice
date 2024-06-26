import requests, vtk

from tools.measurement.utils import buildArcAngleMeasurement, buildTextActorLengthMeasurement

class MyAuth(requests.auth.AuthBase):
    def __init__(self, auth):
        self._auth = auth
    def __call__(self, r):
        # Implement my authentication
        r.headers['Authorization'] = self._auth
        return r

class DefaultInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self) -> None:
        self.angle_measurement_pipelines = []
        self.length_measurement_pipelines = []
        self.AddObserver(vtk.vtkCommand.MouseMoveEvent, self.__mouseMoveEvent)

    def getAngleMeasurementPipelines(self) -> list:
        return self.angle_measurement_pipelines

    def addAngleMeasurementPipeline(self, pipeline) -> None:
        self.angle_measurement_pipelines.append(pipeline)

    def getLengthMeasurementPipelines(self) -> list:
        return self.length_measurement_pipelines

    def addLengthMeasurementPipeline(self, pipeline) -> None:
        self.length_measurement_pipelines.append(pipeline)

    """
        Description: a handle function used to update the position of text actor when having mouse move event.
    """
    def __mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        if len(self.angle_measurement_pipelines):
            for pipeline in self.angle_measurement_pipelines:
                points = pipeline.line.GetPoints()
                # Update the position of text actor
                buildArcAngleMeasurement(pipeline.arc, pipeline.textActor, renderer, points)
            self.GetInteractor().Render()
        
        if len(self.length_measurement_pipelines):
            for pipeline in self.length_measurement_pipelines:
                points = pipeline.line.GetPoints()
                # Method used to update the position of text actor
                buildTextActorLengthMeasurement(pipeline.textActor, renderer, points)
            self.GetInteractor().Render()
        self.OnMouseMove()