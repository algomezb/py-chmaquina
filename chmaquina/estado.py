import copy

from chmaquina.errores import ErrorDeSegmentacion


class EstadoMaquina:
    def __init__(self, memoria, pivote):
        self.memoria = memoria
        self.variables = {}
        self.etiquetas = {}
        self.programas = {}
        self.listos = []

        self.pantalla = []
        self.impresora = []
        self.terminados = {}

        self.pivote = pivote
        self.tiempo_llegada = 0
        self.reloj = 0

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
        estado.listos = copy.deepcopy(self.listos)

        estado.impresora = copy.deepcopy(self.impresora)
        estado.pantalla = copy.deepcopy(self.pantalla)
        estado.terminados = copy.deepcopy(self.terminados)

        estado.tiempo_llegada = self.tiempo_llegada
        estado.reloj = self.reloj

        return estado

    def siguiente_instruccion(self):
        if not self.listos:
            return None

        nombre = self.listos[0]
        programa = self.programas[nombre]
        posicion = programa["inicio"] + programa["contador"]
        dato = self.memoria[posicion]

        # Protección de memoria básica
        if dato.get("tipo") != "CODIGO" or dato.get("programa") != nombre:
            raise ErrorDeSegmentacion(
                f"El programa {nombre} intentó ejecutar código fuera de su región de código."
            )

        return nombre, dato.get("valor")

    def nada_por_hacer(self):
        return not self.listos

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
        valor = self.buscar_variable(programa, "acumulador").get("valor")
        return valor if valor else por_defecto

    def vaya(self, programa, etiqueta):
        self.programas[programa]["contador"] = self.etiquetas[programa][etiqueta]

    def agregar_a_memoria(self, dato):
        posicion = self.pivote
        self.memoria[posicion] = dato
        self.pivote = self.pivote + 1
        return posicion

    def incrementar_contador(self, programa):
        self.programas[programa]["contador"] += 1
        return self

    def avanzar_tiempo(self, tiempo):
        self.reloj += tiempo
        if self.reloj > self.tiempo_llegada:
            self.tiempo_llegada = self.reloj
        return self

    @property
    def programas_disponibles(self):
        ordenados = sorted(self.programas.items(), key=lambda p: p[1]["tiempo_llegada"])
        for nombre, programa in ordenados:
            if programa["tiempo_llegada"] <= self.reloj:
                yield nombre, programa
