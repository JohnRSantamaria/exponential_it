from abc import ABC, abstractmethod


class FileUploader(ABC):
    @abstractmethod
    def upload(self, local_path: str, remote_path: str) -> None:
        pass
