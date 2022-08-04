# -*- coding: utf-8 -*-
"""
Created on Mon Jul 11 17:00:00 2022

@author: Jhonatan Martínez
"""

import inspect
from ftplib import FTP
import pysftp
from answer import Answer
import main_functions as mf


class CONNECTIONFTP:
    """
    Permite la conexión y envío de email por SMTP,
    los datos de configuración están en el archivo JSON llamado **config.json**.\n
    Para su funcionamiento importa los siguientes paquetes y clases:\n
    * **inspect:** Para obtener información de la función actual.\n
    * **ftplib:** Para conectar al servidor FTP.\n
    * **pysftp:** Para conectar al servidor SFTP.\n
    * **Answer:** Dónde se envían el estado, mensaje y datos desde una función.\n
    * **main_functions:** Funciones principales para el funcionamiento del aplicativo.

    """

    def __init__(self):
        """
        Los datos están en la sección FTP en el archivo JSON los cuales son:\n
        * **FTP_TYPE:** Tipo de servidor, se permiten (FTP, SFTP).\n
        * **FTP_SERVER:** Host del servidor.\n
        * **FTP_PORT:** Puerto al que nos vamos a conectar.\n
        * **FTP_USER:** Usuario para conectar al servidor.\n
        * **FTP_PASSWORD:**  Clave para conectar al servidor.\n
        * **FTP_PATH:** Directorio en el que se va a trabajar.\n
        """
        self.__this = self.__class__.__name__
        self.__connection = None
        self.__data = self._read_setup()

    def change_path(self, path):
        """
        Change path in FTP/SFTP server

        Returns:

        """
        # process variable
        process = inspect.stack()[0][3]
        # Invoke class Answer.
        answer = Answer()
        try:
            # Change path
            self.__connection.cwd(path)
            # Fill answer object with status, message and data list.
            answer.load(status=True,
                        message="Path was changed to " + path)
        except Exception as exc:
            # Fill answer object with status and error message.
            answer.load(status=False,
                        message=self._print_error(process=process,
                                                  message=exc))
        return answer

    def close_connection(self):
        """
        Cierra la conexión a al FTP.

        """

        # process variable
        process = inspect.stack()[0][3]
        # Invoke class Answer.
        answer = Answer()
        try:
            # Validate status of connection
            if self.__connection is not None:
                # Close connection.
                self.__connection.close()
                # Fill answer object with status, message and data list.
                answer.load(status=True,
                            message="connection was closed")
        except Exception as exc:
            # Fill answer object with status and error message.
            answer.load(status=False,
                        message=self._print_error(process=process,
                                                  message=exc))

    def get_connection(self):
        """
        Realiza y establece la conexión al servidor FTP/SFTP.\n
        Los datos son leídos desde la función '_read_setup()',
        Estos datos se obtienen y agregan en el constructor de la clase.

        Returns:
            **Answer (Class):** Devuelve un estado y mensaje de la función.

        """

        # process variable
        process = inspect.stack()[0][3]
        # Invoke class Answer.
        answer = Answer()
        try:
            # Choose the type of server.
            if str(self.__data["TYPE"]).upper() == "FTP":
                self.__connection = FTP(host=self.__data["SERVER"],
                                        user=mf.decrypt(text=self.__data["USER"],
                                                        key="REQ2022407").get_data(),
                                        passwd=mf.decrypt(text=self.__data["PASSWORD"],
                                                          key="REQ2022407").get_data())
            else:
                # This is for no use the host keys
                opciones = pysftp.CnOpts()
                opciones.hostkeys = None

                self.__connection = pysftp.Connection(host=self.__data["SERVER"],
                                                      port=int(self.__data["PORT"]),
                                                      username=mf.decrypt(text=self.__data["USER"],
                                                                          key="REQ2022407").get_data(),
                                                      password=mf.decrypt(text=self.__data["PASSWORD"],
                                                                          key="REQ2022407").get_data(),
                                                      cnopts=opciones)
            # Fill answer object with status and message.
            answer.load(status=True,
                        message='Established Connection to ' + self.__data["TYPE"])
        except Exception as exc:
            # Fill answer object with status and error message.
            answer.load(status=False,
                        message=self._print_error(process=process,
                                                  message=exc))
        # Return answer object.
        return answer

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

    def upload_file(self, original_file, end_file):
        """
        Subir archivos al servidor FTP o SFTP.

        Params:
            * **original_file (String):** Recibe la ruta absoluta y el archivo a subir. \n
            * **end_file (String, optional):** Nombre con el que se va a guardar el archivo. \n

        Returns:
            **answer (Class):** Devuelve estado, mensaje y datos (diccionario, lista) de la función.

        """

        # process variable
        process = inspect.stack()[0][3]
        # Invoke class Answer.
        answer = Answer()
        try:
            # Choose the type of server.
            if str(self.__data["TYPE"]).upper() == "FTP":
                with open(original_file, 'rb') as file:
                    self.__connection.storbinary('STOR ' + end_file, file)
            elif str(self.__data["TYPE"]).upper() == "SFTP":
                self.__connection.put(original_file, end_file)
            answer.load(status=True,
                        message=end_file + ' file was uploaded to ' + self.__data["TYPE"])
        except (pysftp.CredentialException, pysftp.ConnectionException, Exception) as exc:
            # Fill answer object with status and error message.
            answer.load(status=False,
                        message=self._print_error(process=process,
                                                  message=exc))
        # Return answer object.
        return answer
