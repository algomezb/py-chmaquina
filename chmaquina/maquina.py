import copy

from chmaquina.verificacion import verificar, ErrorDeSintaxis


class ChProgramaInvalido(Exception):
    """
    Indica que un ch programa no es valido.
    """


class ErrorDeEjecucion(Exception):
    """
    Indica que hubo un error en la ejecución del programa.
    """


class TecladoEnConsola(object):
    """
    Un teclado que lee por consola.
    """

    def lea(self):
        return input()


class ImpresoraEnConsola(object):
    """
    Una impresora que muestra mensajes en consola.
    """

    def imprima(self, mensaje):
        print("[IMPRESORA]", mensaje)


class PantallaEnConsola(object):
    """
    Una pantalla que muestra mensajes en consola.
    """

    def muestre(self, mensaje):
        print("[PANTALLA]", mensaje)


class EstadoMaquina:
    def __init__(self, memoria, contador, pivote):
        self.memoria = memoria
        self.variables = {}
        self.etiquetas = {}
        self.programas = {}
        self.contador = contador
        self.pivote = pivote

    @classmethod
    def para(cls, maquina):
        memoria = [{}] * maquina.tamano_memoria
        apuntador = maquina.tamano_kernel + 1
        return cls(memoria, apuntador, apuntador)

    def copiar(self):
        estado = self.__class__(copy.deepcopy(self.memoria), self.contador, self.pivote)
        estado.variables = copy.deepcopy(self.variables)
        estado.etiquetas = copy.deepcopy(self.etiquetas)
        estado.programas = copy.deepcopy(self.programas)
        return estado

    def siguiente_instruccion(self):
        if self.memoria[self.contador].get("tipo") != "CODIGO":
            return None
        dato = self.memoria[self.contador]
        return dato.get("programa"), dato.get("valor")

    def nada_por_hacer(self):
        # FIXME: Cola de procesos?
        siguiente = self.siguiente_instruccion()
        if siguiente is None:
            return True
        operacion, *_ = siguiente[1].lstrip().split()
        return operacion == "retorne"

    def buscar_variable(self, programa, varialbe):
        posicion = self.variables[programa][varialbe]
        return self.memoria[posicion].copy()

    def asignar_variable(self, programa, varialbe, dato):
        posicion = self.variables[programa][varialbe]
        if isinstance(dato, str):
            self.memoria[posicion]["valor"] = dato
        else:
            self.memoria[posicion] = dato

    def asignar_acumulador(self, dato):
        self.memoria[0] = {
            "programa": "***",
            "nombre": "acumulador",
            "tipo": "MULTIPLE",
            "valor": dato,
        }

    def acumulador(self, por_defecto=None):
        return self.memoria[0].get("valor", por_defecto)

    def vaya(self, programa, etiqueta):
        self.contador = self.etiquetas[programa][etiqueta]

    def agregar_a_memoria(self, dato):
        posicion = self.pivote
        self.memoria[posicion] = dato
        self.pivote = self.pivote + 1
        return posicion

    def incrementar_contador(self):
        self.contador += 1


class Maquina(object):
    """
    Representa un ch computador.
    """

    def __init__(
        self, tamano_memoria, tamano_kernel, teclado=None, impresora=None, pantalla=None
    ):
        self.tamano_memoria = tamano_memoria
        self.tamano_kernel = tamano_kernel
        self.teclado = teclado or TecladoEnConsola()
        self.impresora = impresora or ImpresoraEnConsola()
        self.pantalla = pantalla or PantallaEnConsola()

    def encender(self):
        """
        Retorna un estado inicial para la máquina.
        """
        return EstadoMaquina.para(self)

    def paso(self, estado):
        """
        Toma un estado y ejecuta un paso.
        """
        instruccion = estado.siguiente_instruccion()
        if instruccion == None:
            return estado
        programa, linea = instruccion
        linea = linea.strip()
        nuevo_estado = estado.copiar()
        operacion, *argumentos = linea.split()
        if operacion == "cargue":
            variable, = argumentos
            dato = nuevo_estado.buscar_variable(programa, variable)
            nuevo_estado.asignar_acumulador(dato.get("valor"))
        elif operacion == "almacene":
            variable, = argumentos
            dato = nuevo_estado.acumulador()
            nuevo_estado.asignar_variable(programa, variable, dato)
        elif operacion == "vaya":
            etiqueta, = argumentos
            nuevo_estado.vaya(programa, etiqueta)
            return nuevo_estado
        elif operacion == "vayasi":
            positivo, negativo = argumentos
            bandera = float(nuevo_estado.acumulador(por_defecto="0"))
            if bandera > 0:
                nuevo_estado.vaya(programa, positivo)
            elif bandera < 0:
                nuevo_estado.vaya(programa, negativo)
            else:
                nuevo_estado.incrementar_contador()
            return nuevo_estado
        elif operacion == "lea":
            variable, = argumentos
            valor = self.teclado.lea()
            nuevo_estado.asignar_variable(programa, variable, valor)
        elif operacion in (
            "sume",
            "reste",
            "multiplique",
            "divida",
            "potencia",
            "modulo",
        ):
            variable, = argumentos
            acumulador = float(nuevo_estado.acumulador("0"))
            variable = float(nuevo_estado.buscar_variable(programa, variable)["valor"])
            if operacion == "sume":
                resultado = acumulador + variable
            if operacion == "reste":
                resultado = acumulador - variable
            if operacion == "multiplique":
                resultado = acumulador * variable
            try:
                if operacion == "divida":
                    resultado = acumulador / variable
                if operacion == "potencia":
                    resultado = acumulador ** variable
                if operacion == "modulo":
                    resultado = acumulador % variable
            except ZeroDivisionError:
                raise ErrorDeEjecucion("Se encontró una division por cero.")
            nuevo_estado.asignar_acumulador(str(resultado))
        elif operacion in ("concatene", "elimine", "extraiga"):
            operando, = argumentos
            acumulador = nuevo_estado.acumulador(" ")
            if operacion == "concatene":
                resultado = acumulador + operando
            if operacion == "elimine":
                resultado = acumulador.replace(operando, "")
            if operacion == "extraiga":
                resultado = acumulador[: int(operando)]
            nuevo_estado.asignar_acumulador(resultado)
        elif operacion in ("Y", "O"):
            a, b, salida, = argumentos
            a = estado.buscar_variable(programa, a)["valor"] == "1"
            b = estado.buscar_variable(programa, b)["valor"] == "1"
            if operacion == "O":
                resultado = "1" if a or b else "0"
            if operacion == "Y":
                resultado = "1" if a and b else "0"
            nuevo_estado.asignar_variable(programa, salida, resultado)
        elif operacion == "NO":
            operando, salida, = argumentos
            operando = estado.buscar_variable(programa, operando)["valor"] == "1"
            resultado = "1" if not operando else "0"
            nuevo_estado.asignar_variable(programa, salida, resultado)
        elif operacion == "imprima":
            variable, = argumentos
            mensaje = estado.buscar_variable(programa, variable)["valor"]
            self.impresora.imprima(mensaje)
        elif operacion == "muestre":
            variable, = argumentos
            mensaje = estado.buscar_variable(programa, variable)["valor"]
            self.pantalla.muestre(mensaje)
        nuevo_estado.incrementar_contador()
        return nuevo_estado

    def correr(self, estado, pasos=None):
        nuevo_estado = estado.copiar()
        if pasos is None:
            while not nuevo_estado.nada_por_hacer():
                nuevo_estado = self.paso(nuevo_estado)
            return nuevo_estado

        for _ in range(pasos):
            nuevo_estado = self.paso(nuevo_estado)

        return nuevo_estado

    def iterar(self, estado):
        nuevo_estado = estado.copiar()
        while not nuevo_estado.nada_por_hacer():
            nuevo_estado = self.paso(nuevo_estado)
            yield nuevo_estado

    def cargar(self, estado, programa):
        """
        Carga un chprograma en la máquina.
        """
        nuevo_estado = estado.copiar()
        try:
            codigo, variables, etiquetas = verificar(programa)
        except ErrorDeSintaxis as e:
            raise ChProgramaInvalido(str(e))

        posicion_inicial = nuevo_estado.pivote
        programa = f"{len(nuevo_estado.programas):03d}"
        nuevo_estado.variables[programa] = {}
        nuevo_estado.etiquetas[programa] = {}

        # Escribir el código en memoria
        for i, linea in enumerate(codigo):
            nuevo_estado.agregar_a_memoria(
                {
                    "nombre": f"L{i + 1:03d}",
                    "programa": programa,
                    "tipo": "CODIGO",
                    "valor": linea,
                }
            )

        # Escribir las variables en memoria
        for nombre, datos in variables.items():
            posicion = nuevo_estado.agregar_a_memoria(
                {"nombre": nombre, "programa": programa, **datos}
            )
            nuevo_estado.variables[programa][nombre] = posicion

        # Tener en cuenta las etiquetas
        for nombre, linea in etiquetas.items():
            nuevo_estado.etiquetas[programa][nombre] = linea + posicion_inicial

        nuevo_estado.programas[programa] = {
            "inicio": estado.pivote,
            "datos": estado.pivote + len(codigo),
            "final": estado.pivote + len(codigo) + len(variables),
        }

        return nuevo_estado
