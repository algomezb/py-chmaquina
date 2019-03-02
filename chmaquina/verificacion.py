import re


class ErrorDeSintaxis(Exception):
    """
    Indica un error de sintaxis en el programa.
    """


class Contexto(object):
    def __init__(self):
        self.variables = set()
        self.etiquetas = set()
        self.etiquetas_requeridas = set()

    def definir_variable(self, variable):
        self.variables.add(variable)

    def variable_definida(self, variable):
        return variable in self.variables

    def requerir_etiqueta(self, etiqueta):
        return self.etiquetas_requeridas.add(etiqueta)

    def definir_etiqueta(self, etiqueta):
        return self.etiquetas.add(etiqueta)

    @property
    def etiquetas_faltantes(self):
        return self.etiquetas_requeridas - self.etiquetas

    def __repr__(self):
        return "\n".join(
            [
                f"{self.__class__.__name__} {{",
                f"  variables: {self.variables},",
                f"  etiquetas: {self.etiquetas}",
                f"  etiquetas_requeridas: {self.etiquetas_requeridas}",
                "}}",
            ]
        )


class VerificadorCh(object):
    def __init__(self, programa):
        self.programa = programa
        self.contexto = Contexto()

    @staticmethod
    def numero_de_argumentos(argumentos, _min, _max=None):
        if _max is None:
            if len(argumentos) != _min:
                raise ErrorDeSintaxis(f"Se esperaban exactamente {_min} argumentos")
        elif len(argumentos) < _min or len(argumentos) > _max:
            raise ErrorDeSintaxis(f"Se esperaban entre {_min} y {_max} argumentos")

    @staticmethod
    def es_tipo(cadena):
        """
        Verifica si una cadena es un tipo válido.
        """
        tipos_validos = ["C", "I", "R", "L"]
        if cadena.upper() not in tipos_validos:
            raise ErrorDeSintaxis(f"{cadena} no es un tipo válido")

    @staticmethod
    def es_de_tipo(tipo, valor):
        """
        Verifica si un valor es del tipo dado.
        """
        tipo = tipo.upper()
        if tipo == "C":
            # Nada que hacer todo valor puede ser tipo cadena
            pass
        elif tipo == "I":
            if not re.match(r"^\d+$", valor):
                raise ErrorDeSintaxis(f"El valor '{valor}' no es de tipo {tipo}")
        elif tipo == "R":
            if not re.match(r"^\d+\.?\d+$", valor):
                raise ErrorDeSintaxis(f"El valor '{valor}' no es de tipo {tipo}")
        elif tipo == "L":
            if valor not in ["0", "1"]:
                raise ErrorDeSintaxis(f"El valor '{valor}' no es de tipo {tipo}")
        else:
            raise ErrorDeSintaxis(f"{tipo} no es un tipo válido")

    def ya_definida(self, variable):
        """
        Verifica que una variable ya esté definida.
        """
        if not self.contexto.variable_definida(variable):
            raise ErrorDeSintaxis(
                f"La variable '{variable}' no está definida antes de usarla"
            )

    def etiquetas_completas(self):
        """
        Verifica que todas las etiquetas requeridas están definidas.
        """
        print(self.contexto)
        faltantes = self.contexto.etiquetas_faltantes
        if faltantes:
            raise ErrorDeSintaxis(f"No se han definido las etiquetas {faltantes}")

    def verificar_linea(self, linea):
        """
        Verifica que una linea sea válida.

        - No verifica que las variables no se redefinan.
        - No verifica que las etiquetas apunten a una linea de código valida.
        """
        linea = linea.strip()
        tokens = linea.split()
        if not tokens:
            # Linea vacía
            return
        if linea.startswith("//"):
            # comentario
            return
        instruccion, *argumentos = tokens
        if instruccion == "nueva":
            # nueva variable C hola que hace
            # nueva <variable> <tipo> [valor... valor valor]
            instruccion, *argumentos = linea.split(maxsplit=3)
            self.numero_de_argumentos(argumentos, 2, 3)
            variable, tipo, *_ = argumentos
            self.es_tipo(tipo)
            if len(argumentos) == 3:
                valor = argumentos[2]
                self.es_de_tipo(tipo, valor)
            self.contexto.definir_variable(variable)
        elif instruccion == "vaya":
            # vaya <etiqueta>
            self.numero_de_argumentos(argumentos, 1)
            etiqueta, = argumentos
            self.contexto.requerir_etiqueta(etiqueta)
        elif instruccion == "vayasi":
            # vayasi <etiqueta> <etiqueta>
            self.numero_de_argumentos(argumentos, 2)
            rama1, rama2 = argumentos
            self.contexto.requerir_etiqueta(rama1)
            self.contexto.requerir_etiqueta(rama2)
        elif instruccion == "etiqueta":
            # vayasi <etiqueta> <linea>
            self.numero_de_argumentos(argumentos, 2)
            etiqueta, linea = argumentos
            self.es_de_tipo("I", linea)
            self.contexto.definir_etiqueta(etiqueta)
        elif instruccion in (
            "cargue",
            "almacene",
            "lea",
            "sume",
            "reste",
            "multiplique",
            "divida",
            "potencia",
            "modulo",
            "concatene",
        ):
            # operador <variable>
            self.numero_de_argumentos(argumentos, 1)
            variable, = argumentos
            self.ya_definida(variable)
        elif instruccion == "elimine":
            # elimine <cadena>
            self.numero_de_argumentos(argumentos, 1)
        elif instruccion == "extraiga":
            # elimine <numero>
            self.numero_de_argumentos(argumentos, 1)
            numero, = argumentos
            self.es_de_tipo("I", numero)
        elif instruccion in ("Y", "O"):
            # operador <variable> <variable> <variable>
            self.numero_de_argumentos(argumentos, 3)
            for variable in argumentos:
                self.ya_definida(variable)
        elif instruccion == "NO":
            self.numero_de_argumentos(argumentos, 2)
            for variable in argumentos:
                self.ya_definida(variable)
        elif instruccion in ("muestre", "imprima"):
            self.numero_de_argumentos(argumentos, 1)
            variable, = argumentos
            if variable != "acumulador":
                self.ya_definida(variable)
        elif instruccion in "retorne":
            self.numero_de_argumentos(argumentos, 0, 1)
            if argumentos:
                valor, = argumentos
                self.es_de_tipo("I", valor)
        else:
            raise ErrorDeSintaxis(f"Instrucción desconocida: '{linea}'")

    def verificar(self):
        self.contexto = Contexto()
        for linea in self.programa.split("\n"):
            self.verificar_linea(linea)
        self.etiquetas_completas()


def verificar(programa):
    """
    Verifica un ch programa dado (como string).
    """
    verificador = VerificadorCh(programa)
    return verificador.verificar()
