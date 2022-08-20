'''Является классом, описывающим настройки проекта'''
class ProjectClass():

    def __init__(self, name: str, path: str, activPath: bool) -> None:
        self.name = name
        self.path = path
        self.activePath = activPath


    def CreateJson(self):
        return {'name': self.name, 'folder': self.path, 'activePath': self.activePath }
