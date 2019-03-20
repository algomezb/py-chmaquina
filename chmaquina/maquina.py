import copy
import math
import random
import sys

from chmaquina.sintaxis import ErrorDeSintaxis, verificar, estimar
from chmaquina.estado import EstadoMaquina
from chmaquina.errores import ErrorDeEjecucion, ChProgramaInvalido, SinMemoriaSuficiente


class TecladoEnConsola(object):
    """
    Un teclado que lee por consola.
    """

    def lea(self):
        return input()


class Maquina(object):
    """
    Representa un ch computador.
    """

    def __init__(
        self, tamano_memoria, tamano_kernel, teclado=None, quantum=None, algoritmo=None
    ):
        self.tamano_memoria = tamano_memoria
        self.tamano_kernel = tamano_kernel
        self.teclado = teclado or TecladoEnConsola()
        self.quantum = quantum or sys.maxsize
        self.algoritmo = algoritmo or "FCFS"

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
            return estado.avanzar_tiempo(1)
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
            return nuevo_estado.avanzar_tiempo(1)
        elif operacion == "vayasi":
            positivo, negativo = argumentos
            bandera = float(nuevo_estado.acumulador(programa, por_defecto="0"))
            if bandera > 0:
                nuevo_estado.vaya(programa, positivo)
            elif bandera < 0:
                nuevo_estado.vaya(programa, negativo)
            else:
                nuevo_estado.incrementar_contador(programa)
            return nuevo_estado.avanzar_tiempo(1)
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
            nuevo_estado.terminados[programa] = nuevo_estado.programas[programa]
            del nuevo_estado.programas[programa]
            nuevo_estado.listos.remove(programa)
            return nuevo_estado
        duracion = 1
        if operacion in ("lea", "imprima", "muestre", "almacene", "cargue"):
            duracion = random.randint(1, 9)
        elif operacion in ("nueva", "etiqueta"):
            duracion = 0
        return nuevo_estado.incrementar_contador(programa).avanzar_tiempo(duracion)

    def correr(self, estado, pasos=None):
        nuevo_estado = estado.copiar()
        if pasos is not None:
            for _, nuevo_estado in zip(range(pasos), self.iterar(estado)):
                pass
            return nuevo_estado
        for nuevo_estado in self.iterar(estado):
            pass
        return nuevo_estado

    def iterar(self, estado):
        """
        Ejecuta la ch maquina retornando cada estado hasta que no haya nada por hacer.
        """
        inicial = estado.copiar()
        nuevo_estado = estado.copiar()
        while not nuevo_estado.nada_por_hacer():
            temporal = self.paso(nuevo_estado)
            tiempo_transcurrido = temporal.reloj - inicial.reloj
            quantum_agotado = tiempo_transcurrido >= self.quantum
            programa_terminado = len(inicial.terminados) < len(temporal.terminados)
            if quantum_agotado or programa_terminado:
                temporal = self.planear(temporal)
                inicial = temporal.copiar()
            if temporal.nada_por_hacer():
                temporal = self.planear(temporal)
            nuevo_estado = temporal
            yield nuevo_estado

    def cargar(self, estado, programa):
        """
        Carga un chprograma en la máquina.
        """
        try:
            codigo, variables, etiquetas = verificar(programa)
        except ErrorDeSintaxis as e:
            raise ChProgramaInvalido from e

        programa = f"{len(estado.programas) + len(estado.terminados):03d}"
        posicion_inicial = estado.pivote
        memoria_disponible = len(estado.memoria) - posicion_inicial
        # espacio necesario para el código, las variables y el contador
        memoria_requerida = len(codigo) + len(variables)

        if memoria_disponible < memoria_requerida:
            raise SinMemoriaSuficiente(
                "La máquina no cuenta con la memoria suficiente para almacenar el programa"
            )

        nuevo_estado = estado.copiar()
        nuevo_estado.variables[programa] = {}
        nuevo_estado.etiquetas[programa] = {}

        # Escribir el código en memoria
        for numero, linea in enumerate(codigo, start=1):
            nuevo_estado.agregar_a_memoria(
                {
                    "nombre": f"L{numero:03d}",
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
                "valor": "",
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
            "tiempo_llegada": estado.tiempo_llegada,
            "tiempo_rafaga": estimar(codigo),
        }

        nuevo_estado.tiempo_llegada += math.ceil(len(codigo) / 4)

        if nuevo_estado.programas[programa]["tiempo_llegada"] <= nuevo_estado.reloj:
            nuevo_estado.listos.append(programa)

        return nuevo_estado

    def planear(self, estado):
        """
        Planea la ejecución de acuerdo al algoritmo a cualquier momento.
        """
        planeado = estado.copiar()

        for nombre, _ in estado.programas_disponibles:
            if nombre not in planeado.listos:
                planeado.listos.append(nombre)

        if self.algoritmo == "RR":
            planeado.listos = planeado.listos[-1:] + planeado.listos[:-1]

        if self.algoritmo == "SJF":
            planeado.listos = list(
                sorted(
                    planeado.listos, key=lambda n: estado.programas[n]["tiempo_rafaga"]
                )
            )

        if self.algoritmo == "FCFS":
            planeado.listos = list(
                sorted(
                    planeado.listos,
                    key=lambda programa: estado.programas[programa]["tiempo_llegada"],
                )
            )

        return planeado
