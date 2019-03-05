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


class ErrorDeSegmentacion(Exception):
    """
    Indica que un programa trató de leer una posición de memoria que no tenía asignada.
    """


class TecladoEnConsola(object):
    """
    Un teclado que lee por consola.
    """

    def lea(self):
        return input()


class EstadoMaquina:
    def __init__(self, memoria, pivote):
        self.memoria = memoria
        self.variables = {}
        self.etiquetas = {}
        self.programas = {}
        self.pantalla = []
        self.impresora = []
        self.terminados = {}
        self.pivote = pivote

    @classmethod
    def para(cls, maquina):
        memoria = [{}] * maquina.tamano_memoria
        apuntador = maquina.tamano_kernel + 1
        return cls(memoria, apuntador)

    def copiar(self):
        estado = self.__class__(copy.deepcopy(self.memoria), self.pivote)
        estado.variables = copy.deepcopy(self.variables)
        estado.etiquetas = copy.deepcopy(self.etiquetas)
        estado.programas = copy.deepcopy(self.programas)
        estado.impresora = copy.deepcopy(self.impresora)
        estado.pantalla = copy.deepcopy(self.pantalla)
        estado.terminados = copy.deepcopy(self.terminados)
        return estado

    def siguiente_instruccion(self):
        if not self.programas:
            return None
        nombre, programa = next(iter(self.programas.items()))
        posicion = programa["inicio"] + programa["contador"]
        dato = self.memoria[posicion]
        if dato.get("tipo") != "CODIGO" or dato.get("programa") != nombre:
            raise ErrorDeSegmentacion(
                f"El programa {nombre} intentó ejecutar código fuera de su región de código."
            )
        return nombre, dato.get("valor")

    def nada_por_hacer(self):
        return not self.programas

    def buscar_variable(self, programa, varialbe):
        posicion = self.variables[programa][varialbe]
        return self.memoria[posicion].copy()

    def asignar_variable(self, programa, varialbe, dato):
        posicion = self.variables[programa][varialbe]
        if isinstance(dato, str):
            self.memoria[posicion]["valor"] = dato
        else:
            self.memoria[posicion] = dato

    def asignar_acumulador(self, programa, dato):
        self.asignar_variable(programa, "acumulador", dato)

    def acumulador(self, programa, *, por_defecto=None):
        return self.buscar_variable(programa, "acumulador").get("valor", por_defecto)

    def vaya(self, programa, etiqueta):
        self.programas[programa]["contador"] = self.etiquetas[programa][etiqueta]

    def agregar_a_memoria(self, dato):
        posicion = self.pivote
        self.memoria[posicion] = dato
        self.pivote = self.pivote + 1
        return posicion

    def incrementar_contador(self, programa):
        self.programas[programa]["contador"] += 1


class Maquina(object):
    """
    Representa un ch computador.
    """

    def __init__(self, tamano_memoria, tamano_kernel, teclado=None):
        self.tamano_memoria = tamano_memoria
        self.tamano_kernel = tamano_kernel
        self.teclado = teclado or TecladoEnConsola()

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
            nuevo_estado.asignar_acumulador(programa, dato.get("valor"))
        elif operacion == "almacene":
            variable, = argumentos
            dato = nuevo_estado.acumulador(programa)
            nuevo_estado.asignar_variable(programa, variable, dato)
        elif operacion == "vaya":
            etiqueta, = argumentos
            nuevo_estado.vaya(programa, etiqueta)
            return nuevo_estado
        elif operacion == "vayasi":
            positivo, negativo = argumentos
            bandera = float(nuevo_estado.acumulador(programa, por_defecto="0"))
            if bandera > 0:
                nuevo_estado.vaya(programa, positivo)
            elif bandera < 0:
                nuevo_estado.vaya(programa, negativo)
            else:
                nuevo_estado.incrementar_contador(programa)
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
            acumulador = float(nuevo_estado.acumulador(programa, por_defecto="0"))
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
            nuevo_estado.asignar_acumulador(programa, str(resultado))
        elif operacion in ("concatene", "elimine", "extraiga"):
            operando, = argumentos
            acumulador = nuevo_estado.acumulador(programa, por_defecto=" ")
            if operacion == "concatene":
                resultado = acumulador + operando
            if operacion == "elimine":
                resultado = acumulador.replace(operando, "")
            if operacion == "extraiga":
                resultado = acumulador[: int(operando)]
            nuevo_estado.asignar_acumulador(programa, resultado)
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
            nuevo_estado.impresora.append((programa, mensaje))
        elif operacion == "muestre":
            variable, = argumentos
            mensaje = estado.buscar_variable(programa, variable)["valor"]
            nuevo_estado.pantalla.append((programa, mensaje))
        elif operacion == "retorne":
            nuevo_estado.terminados[programa] = linea
            del nuevo_estado.programas[programa]
            return nuevo_estado
        nuevo_estado.incrementar_contador(programa)
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
        try:
            codigo, variables, etiquetas = verificar(programa)
        except ErrorDeSintaxis as e:
            raise ChProgramaInvalido(str(e))

        programa = f"{len(estado.programas) + len(estado.terminados):03d}"
        posicion_inicial = estado.pivote

        nuevo_estado = estado.copiar()
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

        # Agregar la variable reservada acumulador
        posicion = nuevo_estado.agregar_a_memoria(
            {
                "nombre": "acumulador",
                "programa": programa,
                "tipo": "MULTIPLE",
                "valor": " ",
            }
        )
        nuevo_estado.variables[programa]["acumulador"] = posicion

        # Tener en cuenta las etiquetas
        for nombre, linea in etiquetas.items():
            nuevo_estado.etiquetas[programa][nombre] = linea

        nuevo_estado.programas[programa] = {
            "inicio": posicion_inicial,
            "contador": 0,
            "datos": posicion_inicial + len(codigo),
            "final": posicion_inicial + len(codigo) + len(variables) + 1,
        }

        return nuevo_estado
