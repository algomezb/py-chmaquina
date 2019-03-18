class ErrorDeSintaxis(Exception):
    """
    Indica un error de sintaxis en el programa.
    """


class ChProgramaInvalido(Exception):
    """
    Indica que un ch programa no es valido.
    """


class ErrorDeEjecucion(Exception):
    """
    Indica que hubo un error en la ejecución del programa.
    """


class ErrorDeSegmentacion(Exception):
    """
    Indica que un programa trató de leer una posición de memoria que no tenía asignada.
    """


class SinMemoriaSuficiente(Exception):
    """
    Indica que la memoria de la máquina no es suficiente para ejecutar una acción.
    """
