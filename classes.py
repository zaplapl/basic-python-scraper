class WebResource:
    def __init__(self, type: str, uri: str, tag: str) -> None:
        self.uri = uri
        self.type = type
        self.tag = tag


class FileResource:
    def __init__(self, type: str, path: str) -> None:
        self.path = path
        self.type = type
        self.tag = tag


class PageResources:
    def __init__(self, url: str) -> None:
        self.url = url
        self.file_resources = []
        self.web_resources = []

    def add_web_resource(self, resource: WebResource):
        self.web_resources.append(resource)

    def add_file_resource(self, resource: FileResource):
        self.web_resources.append(resource)
