import os, vtk, requests, time, threading, json, enum, logging, base64, psutil

from argparse import ArgumentParser

from wslink import server

from vtk.web import wslink as vtk_wslink

from vtk.web import protocols as vtk_protocols

from protocol.vtk_protocol import Dicom3D

from concurrent.futures import ThreadPoolExecutor

from utils.utils import MyAuth

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

def add_arguments(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--studyUID",
        type=str,
        default=None,
        help="studyUID"
    )
    parser.add_argument(
        "--seriesUID",
        type=str,
        default=None,
        help="seriesUID"
    )
    parser.add_argument(
        "--storeUrl",
        type=str,
        default=None,
        help="storeUrl"
    )
    parser.add_argument(
        "--storeAuth",
        type=str,
        default=None,
        help="storeAuth"
    )

def base64_encode(data: str) -> str:
    byte_data = data.encode("utf-8")
    encoded_data = base64.b64encode(byte_data)
    return encoded_data.decode()

def get_size_of_dir(path: str) -> int:
    size = 0
    for file in os.scandir(path):
        size += os.path.getsize(file)
    size_kb = size / 1024
    size_mb = size_kb / 1024
    return round(size_mb)

def add_dicom_dir_path_and_dicom_dir_status(statusFilePath: str, dicomDirStatus: str) -> None:
    with open(statusFilePath, mode='r+') as file:
        data = json.load(file)
        data["status"] = dicomDirStatus
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()

def get_dicom_dir_status(statusFilePath: str) -> str:
    with open(statusFilePath, mode='r') as file:
        data = json.load(file)
    return data["status"]

class Status(enum.Enum):
    NONE = "NONE"
    DOWNLOADING = "DOWNLOADING"
    DONE = "DONE"

# =============================================================================
# Server class
# =============================================================================

class Server(vtk_wslink.ServerProtocol):
    # Defaults
    authKey = "wslink-secret"
    dicom3d = Dicom3D()
    view = None
    dicomDirPath = None

    @staticmethod
    def save_all_instances(
        store: dict,
        studyUID: str,
        seriesUID: str,
        dicomDirPath: str,
        statusFilePath: str,
        threadCount: int = 4
    ) -> None:
        store_url = store["store_url"]
        store_auth = store["store_auth"]
        url = f"{store_url}/studies/{studyUID}/series/{seriesUID}/metadata"
        try:
            response = requests.get(
                url,
                auth = MyAuth(store_auth)
            )
            if response.status_code == 200:
                if get_dicom_dir_status(statusFilePath) == Status.NONE.value:
                    add_dicom_dir_path_and_dicom_dir_status(statusFilePath, Status.DOWNLOADING.value)

                    metadatas = response.json()
                    futures = [0 for _ in range(threadCount)]
                    chunkSize = len(metadatas) // threadCount

                    with ThreadPoolExecutor(max_workers=threadCount) as executor:
                        for i in range(threadCount):
                            startIndex = i * chunkSize
                            endIndex = (i + 1) * chunkSize if i != threadCount - 1 else len(metadatas)
                            if startIndex < endIndex:
                                futures[i] = executor.submit(
                                    Server.save_instances,
                                    f"Dicom download threading {i}",
                                    (startIndex, endIndex),
                                    metadatas,
                                    store,
                                    studyUID,
                                    seriesUID,
                                    dicomDirPath
                                )
                        executor.shutdown(wait=True)

                    add_dicom_dir_path_and_dicom_dir_status(statusFilePath, Status.DONE.value)
                else:
                    while get_dicom_dir_status(statusFilePath) == Status.DOWNLOADING.value:
                        logging.info("Waiting 5 seconds...")
                        time.sleep(5)
                Server.dicomDirPath = dicomDirPath
            else:
                logging.error(f"Get metadata: status code = {response.status_code}")
        except Exception as e:
            logging.error(f"Get metadata: exception = {e}")
    
    @staticmethod
    def save_instances(
        name: str,
        indexs: tuple,
        metadatas: dict,
        store: dict,
        studyUID: str,
        seriesUID: str,
        dicomDirPath: str
    ) -> None:
        store_url = store["store_url"].split("-")[0]
        try:
            for i in range(indexs[0], indexs[1]):
                object_uid = metadatas[i]["00080018"]["Value"][0]
                response = requests.get(
                    store_url,
                    params={
                        "studyUID": studyUID,
                        "seriesUID": seriesUID,
                        "objectUID": object_uid,
                        "requestType": "WADO",
                        "contentType": "application/dicom"
                    },
                    auth = MyAuth(store["store_auth"])
                )
                if response.status_code == 200:
                    bytes = response.content
                    with open(f"{dicomDirPath}/{object_uid}.dcm", "wb") as file:
                        file.write(bytes)
                else:
                    logging.info(f"{name}: {response.url}, status code = {response.status_code}")
            logging.info(f"{name}: done")
        except Exception as e:
            logging.error(f"{name}: exception = {e}")

    @staticmethod
    def configure(authKey: str) -> None:
        Server.authKey = authKey

    def onConnect(self, request, client_id) -> None:
        while self.dicomDirPath is None: time.sleep(5)
        else: self.dicom3d.dicomDirPath = self.dicomDirPath

    def initialize(self) -> None:
        # Bring Used Components
        # A list of LinkProtocol provide rpc and publish functionality
        self.registerVtkWebProtocol(vtk_protocols.vtkWebMouseHandler())
        self.registerVtkWebProtocol(vtk_protocols.vtkWebViewPort())
        self.registerVtkWebProtocol(vtk_protocols.vtkWebPublishImageDelivery(decode=False))
        
        # Custom API
        self.registerVtkWebProtocol(self.dicom3d)

        # tell the C++ web app to use no encoding.
        # ParaViewWebPublishImageDelivery must be set to decode=False to match.
        self.getApplication().SetImageEncoding(0)

        # Update authentication key to use
        self.updateSecret(Server.authKey)

        if not Server.view:
            renderer = vtk.vtkRenderer()
            renderWindow = vtk.vtkRenderWindow()
            renderWindowInteractor = vtk.vtkRenderWindowInteractor()

            renderWindow.AddRenderer(renderer)
            renderWindow.OffScreenRenderingOn()

            renderWindowInteractor.SetRenderWindow(renderWindow)
            renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
            renderWindowInteractor.EnableRenderOff()

            renderWindow.SetInteractor(renderWindowInteractor)

            self.getApplication().GetObjectIdMap().SetActiveObject("VIEW", renderWindow)

# =============================================================================
# Main: Parse args and start server3d
# =============================================================================

if __name__ == "__main__":
    # Create argument parser
    parser = ArgumentParser(description="Server3D")

    # Add arguments
    server.add_arguments(parser)
    add_arguments(parser)

    # Get arguments
    args = parser.parse_args()
    # Server.configure(args.authKey)

    dir_path = f"./server3d/data/{args.studyUID}/{args.seriesUID}"
    dicom_dir_path = f"{dir_path}/data"
    status_file_path = f"{dir_path}/status.json"
    if not os.path.exists(dir_path):
        os.makedirs(dicom_dir_path)
        with open(status_file_path, mode='w') as file:
            json.dump({"status": Status.NONE.value}, file, indent=4)

    # Get store url
    store = {
        "store_url": args.storeUrl,
        "store_auth": args.storeAuth.replace(":", " ")
    }

    # Start dicom download process
    thread_download_data = threading.Thread(
        target=Server.save_all_instances,
        args=(store, args.studyUID, args.seriesUID, dicom_dir_path, status_file_path, 8,)
    )
    thread_download_data.start()

    # Start server3d
    server.start_webserver(
        options=args,
        protocol=Server,
        disableLogging=True,
    )
