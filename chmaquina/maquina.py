import copy

from chmaquina.verificacion import verificar, ErrorDeSintaxis


class ChProgramaInvalido(Exception):
    """
    Indica que un ch programa no es valido.
    """


class TecladoEnConsola(object):
    """
    Un teclado que lee por consola.
    """

    def leer(self):
        return input()


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
            else:
                nuevo_estado.vaya(programa, negativo)
            return nuevo_estado
        elif operacion == "lea":
            variable, = argumentos
            valor = self.teclado.leer()
            nuevo_estado.asignar_variable(programa, variable, valor)
        nuevo_estado.incrementar_contador()
        return nuevo_estado

    def correr(self, estado, pasos=None):
        nuevo_estado = estado
        for _ in range(pasos or 1):
            nuevo_estado = self.paso(nuevo_estado)
        return nuevo_estado

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
