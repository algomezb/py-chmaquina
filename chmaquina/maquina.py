from chmaquina.verificacion import verificar


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
        estado = self.__class__(self.memoria[:], self.contador, self.pivote)
        estado.variables = self.variables.copy()
        estado.etiquetas = self.etiquetas.copy()
        estado.programas = self.programas.copy()
        return estado

    def siguiente_instruccion(self):
        if self.memoria[self.contador].get("tipo") != "CODIGO":
            return None
        return self.memoria[self.contador].get("valor")

    def agregar_a_memoria(self, nombre, tipo, valor):
        posicion = self.pivote
        self.memoria[posicion] = {"nombre": nombre, "tipo": tipo, "valor": valor}
        self.pivote = self.pivote + 1
        return posicion


class Maquina(object):
    """
    Representa un ch computador.
    """

    def __init__(self, tamano_memoria, tamano_kernel):
        self.tamano_memoria = tamano_memoria
        self.tamano_kernel = tamano_kernel

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

    def cargar(self, estado, programa):
        """
        Carga un chprograma en la máquina.
        """
        nuevo_estado = estado.copiar()
        codigo, variables, etiquetas = verificar(programa)

        posicion_inicial = nuevo_estado.pivote
        programa = f"{len(nuevo_estado.programas):03d}"
        nuevo_estado.variables[programa] = {}
        nuevo_estado.etiquetas[programa] = {}

        # Escribir el código en memoria
        for i, linea in enumerate(codigo):
            nuevo_estado.agregar_a_memoria(f"{i:03d}", "CODIGO", linea)

        # Escribir las variables en memoria
        for nombre, datos in variables.items():
            posicion = nuevo_estado.agregar_a_memoria(nombre, **datos)
            nuevo_estado.variables[programa][nombre] = posicion

        # Tener en cuenta las etiquetas
        for nombre, linea in etiquetas.items():
            nuevo_estado.etiquetas[programa][nombre] = linea + posicion_inicial

        return nuevo_estado
