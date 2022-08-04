# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 17:00:00 2022

@author: Jhonatan Martínez
"""

from datetime import datetime
import inspect
from pathlib import Path
from answer import Answer
from connection_ftp import CONNECTIONFTP
import main_functions as mf


class Req2022407:
    """
    Esta es la clase principal de la aplicación, trabaja en BackEnd, no posee FrontEnd.\n
    En el archivo de configuración **config.json** están las diferentes secciones
    para las configuraciones de conexiones.\n
    ¿Qué realiza la aplicación?:\n
    * Conectar a una Base de Datos y consultar el o los sectores
    que estén en estado mantenimiento a través de un procedimiento almacenado.\n
    * Si encuentra datos envía una petición a una URL por cada registro
    para que se le actualice el estado a modo normal.\n
    * Envía un email notificando la operación realizada o error en su defecto.\n
    * Guarda un log localmente.
    """

    def __init__(self):
        self.__this = self.__class__.__name__
        self.__data = self._read_setup()
        self._load()

    def _create_folder(self):
        """
        Llama la función 'create_folder()' desde 'main_functions' y le envía el nombre de la carpeta
        la cual será creada en la raíz del aplicativo.

        Returns:
            **answer (Class):** Devuelve un estado y mensaje de la función.

        """
        # get function name
        process = inspect.stack()[0][3]
        # Invoke class Answer.
        answer = Answer()
        try:
            # Folder names to create.
            folders = ["Log"]
            # Start loop on folders
            for folder in folders:
                # Create folder.
                mf.create_folder(folder_name=folder)
            # Fill answer object with status, message and data.
            answer.load(status=True,
                        message="Folders are Ok")
        except Exception as exc:
            # Fill answer object with status and error message.
            answer.load(status=False,
                        message=self._print_error(process=process, message=exc))
        # Return answer object.
        return answer

    def _delete_backup(self):
        """
        Borrar los archivos log después de ciertos días, estos son configurados en el config.json BACKUP_DAYS

        """
        # get function name
        process = inspect.stack()[0][3]
        # Write on the Log file.
        self._write_log_file(message="Start process " + process)
        try:
            # Validate if backup days is greater than zero
            if self.__data["BACKUP_DAYS"] > 0:
                # get the last day allowed
                last_day = datetime.strptime(mf.get_current_date(days=-self.__data["BACKUP_DAYS"]).get_data(), "%Y-%m-%d")
                # get the path where the log files are
                path = Path(mf.get_current_path().get_data() + "/Log")
                # validate if path is a directory
                if path.is_dir():
                    # loop in the files
                    for file in path.iterdir():
                        # get file date
                        file_date = datetime.strptime(file.name[4:14], "%Y-%m-%d")
                        # validate dates
                        if file_date <= last_day:
                            # delete file
                            file.unlink()
                            self._write_log_file(message="The file " + file.name + " was deleted")
                else:
                    self._write_log_file(message="The path " + path.as_posix() + " doesn't exists")
            else:
                self._write_log_file(message=" The BACKUP_DAYS in config.json should be greater than zero")
        except Exception as exc:
            # Write on the Log file.
            self._write_log_file(message=self._print_error(process=process, message=exc))
        finally:
            # Write on the Log file.
            self._write_log_file(message="End process " + process)

    def _load(self):
        """
        This method has all the logic of the program.
        """
        folder = self._create_folder()
        # Validate folder creation status
        if folder.get_status():
            # Write on the Log file.
            self._write_log_file(message="Application has been launched")
            self._write_log_file(message=folder.get_message())
            # Start function to read folders
            folders, end_paths = self._read_folders()
            # loop to start function to get files on every folder
            for index, folder in enumerate(folders):
                # Start function to send files to FTP/SFTP
                self._send_file_ftp(files=self._read_files(folder=folder),
                                    path=end_paths[index])
            # Start function to delete log files
            self._delete_backup()
            # Write on the Log file.
            self._write_log_file(message="Application has been finished")

    def _print_error(self, process, message):
        """
        Muestra por consola cuando existe un error en una función de la clase.

        Params:
            * **process (Str):** Nombre de la función actual. \n
            * **message (Str):** Mensaje de error a mostrar. \n

        Returns:
            **show (Str):** Mensaje completo clase, función y error.

                """
        # show variable
        show = self.__this + "-" + process + ': ' + str(message)
        # Show in console
        print(show)
        # return show
        return show

    def _read_files(self, folder):
        """
        Obtiene los archivos por carpetas para enviar al FTP/SFTP
        """
        # get function name
        process = inspect.stack()[0][3]
        # Write on the Log file.
        self._write_log_file(message="Start process " + process)
        # Write on the Log file.
        self._write_log_file(message="Reading path: " + folder.as_posix())
        # files variable
        files = []
        try:
            # loop files in folder
            for file in folder.iterdir():
                # validate if ti is a file
                if file.is_file() and not file.name.startswith("~$"):
                    # add file to list
                    files.append(file)
                    # Write on the Log file.
            self._write_log_file(message="There are " + str(len(files)) + " files to do backup")
        except Exception as exc:
            # Write on the Log file.
            self._write_log_file(message=self._print_error(process=process, message=exc))
        finally:
            # Write on the Log file.
            self._write_log_file(message="End process " + process)
        return files

    def _read_folders(self):
        """

        Returns:
            * **folders (List):** Devuelve una lista con las carpetas locales a realizar la copia
            * **end_paths (List):** Devuelve una lista con las rutas a las que se copiaran los archivos.
        """
        # get function name
        process = inspect.stack()[0][3]
        # Write on the Log file.
        self._write_log_file(message="Start process " + process)
        # variables to return
        folders = []
        end_paths = []
        try:
            # Write on the Log file.
            self._write_log_file(message="There are " + str(len(self.__data["FOLDERS"])) + " folders to do backup")
            # loop in FOLDERS data
            for folder in self.__data["FOLDERS"]:
                # get path
                path = Path(folder["LOCAL_PATH"])
                # validate if it is a directory and exists
                if path.is_dir():
                    # add local path to folders variable
                    folders.append(path)
                    # add end path to end_paths variable
                    end_paths.append(folder["END_PATH"])
                else:
                    # Write on the Log file.
                    self._write_log_file(message="Path " + folder["LOCAL_PATH"] + " doesn't exists")
        except Exception as exc:
            # Write on the Log file.
            self._write_log_file(message=self._print_error(process=process, message=exc))
        finally:
            # Write on the Log file.
            self._write_log_file(message="End process " + process)
        return folders, end_paths

    def _read_setup(self):
        """
        Llama al método 'read_setup()' desde 'main_functions', para leer y obtener los datos desde archivo JSON.

        Returns:
            **data (Dict):** Diccionario con los datos de configuración.

        """
        # process variable
        process = inspect.stack()[0][3]
        # data variable
        data = None
        try:
            # Read CONNECTION configuration from JSON file.
            config = mf.read_setup(item=self.__this.upper())
            if config.get_status():
                # Assign values
                data = config.get_data()
        except Exception as exc:
            # Show error message in console.
            self._print_error(process=process,
                              message=exc)
        # Return data.
        return data

    def _send_file_ftp(self, files, path):
        """
        Crear la conexión al FTP/SFTP y llama la función 'upload_file' de la clase 'CONNECTIONFTP' para enviar los
        archivos.

        """

        # Variable process
        process = inspect.stack()[0][3]
        # Write on the Log file.
        self._write_log_file(message="Start process " + process)
        # Invoke class ConnectionFTP.
        ftp = CONNECTIONFTP()
        try:
            # Open connection to FTP server
            cnx = ftp.get_connection()
            # Write on the Log file.
            self._write_log_file(message=cnx.get_message())
            # Validate connection status
            if cnx.get_status():
                # change path to work
                path = ftp.change_path(path=path)
                # Write on the Log file.
                self._write_log_file(message=path.get_message())
                if path.get_status():
                    # Loop on the files in the PATH folder
                    for file in files:
                        # Upload file to ftp
                        upload = ftp.upload_file(file, file.name)
                        # Write on the Log file.
                        self._write_log_file(message=upload.get_message())
                        # Validate if the file was sent and if it is enabled to delete
                        if upload.get_status() and bool(self.__data["DELETE_FILES"]):
                            # Delete local file
                            file.unlink()
                            # Write on the Log file.
                            self._write_log_file(message=file.name + " local file was delete")
                # Close connection
                ftp.close_connection()
        except Exception as exc:
            # Write on the Log file.
            self._write_log_file(message=self._print_error(process=process, message=exc))
        finally:
            # Write on the Log file.
            self._write_log_file(message="End process " + process)

    def _write_log_file(self, message):
        """
        Llama a 'write_file_text()' desde 'main_functions' y guarda el texto en el archivo plano.

        Params:
            **message (String):** Dato a copiar en el archivo plano.
        """

        # Variable final_message.
        final_message = '[' + mf.get_current_time().get_data() + ']: ' + message + '.'
        # Write on the Log file.
        mf.write_file_text(file_name='Log/Log-' + mf.get_current_date().get_data(),
                           message=final_message + '\n')
        # Show message in console.
        print(final_message)


if __name__ == '__main__':
    main = Req2022407()
