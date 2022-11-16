class IncorrectChomikPasswordException(Exception):
    pass


class UnknownChomikErrorException(Exception):
    pass


class PasswordProtectedDirectoryException(Exception):
    pass


class IncorrectDirectoryPasswordException(Exception):
    pass


class FileInPasswordProtectedDirOrNotFoundException(Exception):
    pass


class FileIsADirectoryException(Exception):
    pass


class NotEnoughTransferException(Exception):
    pass


class ParentFolderDoesntExistException(Exception):
    pass


class CannotDeleteFileException(Exception):
    pass
