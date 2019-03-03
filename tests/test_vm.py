import pytest

from chmaquina.maquina import Maquina, ChProgramaInvalido


def verificar_estados_iguales(estado, otro, menos=None):
    if menos is None:
        menos = {}
    campos = ["memoria", "variables", "etiquetas", "programas", "contador", "pivote"]
    for campo in campos:
        assert menos.get(campo, getattr(estado, campo)) == getattr(otro, campo)


@pytest.fixture
def maquina():
    class TecladoFalso:
        def leer(self):
            return "entrada de usuario"

    return Maquina(tamano_memoria=1024, tamano_kernel=128, teclado=TecladoFalso())


def test_encender(maquina):
    estado = maquina.encender()
    assert len(estado.memoria) == maquina.tamano_memoria
    assert estado.contador == maquina.tamano_kernel + 1
    assert estado.pivote == maquina.tamano_kernel + 1


def test_paso_sin_programa(maquina):
    estado = maquina.encender()
    siguiente = maquina.paso(estado)
    assert estado == siguiente


def test_cargar_programa(maquina):
    instrucciones = ["nueva variable C hola que hace", "etiqueta fin 3", "retorne 0"]
    programa = "\n".join(instrucciones)
    num_variables = 1
    estado = maquina.encender()
    siguiente = maquina.cargar(estado, programa)
    assert siguiente.contador == estado.contador
    assert siguiente.pivote == estado.pivote + len(instrucciones) + num_variables
    assert siguiente.variables == {"000": {"variable": siguiente.pivote - 1}}
    assert siguiente.etiquetas == {"000": {"fin": estado.pivote + 2}}
    assert siguiente.programas == {
        "000": {
            "inicio": estado.pivote,
            "datos": estado.pivote + 3,
            "final": estado.pivote + 3 + 1,
        }
    }
    assert siguiente.memoria[estado.pivote + 0] == {
        "tipo": "CODIGO",
        "programa": "000",
        "nombre": "L001",
        "valor": "nueva variable C hola que hace",
    }
    assert siguiente.memoria[estado.pivote + 1] == {
        "tipo": "CODIGO",
        "programa": "000",
        "nombre": "L002",
        "valor": "etiqueta fin 3",
    }
    assert siguiente.memoria[estado.pivote + 2] == {
        "tipo": "CODIGO",
        "programa": "000",
        "nombre": "L003",
        "valor": "retorne 0",
    }
    assert siguiente.memoria[estado.pivote + 3] == {
        "tipo": "C",
        "programa": "000",
        "nombre": "variable",
        "valor": "hola que hace",
    }


def test_cargar_dos_programas(maquina):
    instrucciones = ["nueva variable C hola que hace", "etiqueta fin 3", "retorne 0"]
    programa = "\n".join(instrucciones)
    estado = maquina.encender()
    siguiente = maquina.cargar(estado, programa)
    siguiente = maquina.cargar(siguiente, programa)
    assert siguiente.programas == {
        "000": {
            "inicio": estado.pivote,
            "datos": estado.pivote + 3,
            "final": estado.pivote + 4,
        },
        "001": {
            "inicio": estado.pivote + 4,
            "datos": estado.pivote + 7,
            "final": estado.pivote + 8,
        },
    }


def test_cargar_programa_invalido(maquina):
    instrucciones = ["no exactamente un programa", "etiqueta fin 3", "retorne 0"]
    programa = "\n".join(instrucciones)
    estado = maquina.encender()
    with pytest.raises(ChProgramaInvalido):
        maquina.cargar(estado, programa)


@pytest.mark.parametrize(
    "linea", ["nueva variable I 1", "etiqueta fin 2", "// comentario", ""]
)
def test_lineas_sin_efecto(linea, maquina):
    instrucciones = [linea, "retorne 0"]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    linea_ejecutada = maquina.paso(programa_cargado)
    verificar_estados_iguales(
        programa_cargado,
        linea_ejecutada,
        menos={"contador": programa_cargado.contador + 1},
    )


def test_cargar_variable(maquina):
    instrucciones = ["nueva variable C hola", "cargue variable", "retorne 0"]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    variable_cargada = maquina.correr(programa_cargado, pasos=2)
    verificar_estados_iguales(
        programa_cargado,
        variable_cargada,
        menos={
            "contador": programa_cargado.contador + 2,
            "memoria": [
                {
                    "programa": "***",
                    "tipo": "MULTIPLE",
                    "nombre": "acumulador",
                    "valor": "hola",
                },
                *programa_cargado.memoria[1:],
            ],
        },
    )


def test_almacenar_variable(maquina):
    instrucciones = [
        "nueva a C hola",
        "nueva b C",
        "cargue a",
        "almacene b",
        "retorne 0",
    ]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    nuevo = maquina.correr(programa_cargado, pasos=4)
    assert programa_cargado.buscar_variable("000", "a")["valor"] == "hola"
    assert programa_cargado.buscar_variable("000", "b")["valor"] == " "
    assert (
        nuevo.buscar_variable("000", "a")["valor"]
        == nuevo.buscar_variable("000", "b")["valor"]
    )


def test_vaya(maquina):
    instrucciones = [
        "etiqueta fin 5",
        "vaya fin",
        "// comentario",
        "// mas comentario",
        "retorne 0",
    ]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    nuevo = maquina.correr(programa_cargado, pasos=2)
    assert nuevo.siguiente_instruccion() == ("000", "retorne 0")


@pytest.mark.parametrize("valor,linea", [(-1, 5), (3, 1)])
def test_vayasi_rama_positiva(maquina, valor, linea):
    instrucciones = [
        f"nueva variable I {valor}",
        "cargue variable",
        "vayasi itere fin",
        "// comentario",
        "etiqueta itere 1",
        "etiqueta fin 5",
        "retorne 0",
    ]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    nuevo = maquina.correr(programa_cargado, pasos=3)
    assert nuevo.siguiente_instruccion() == ("000", instrucciones[linea - 1])


def test_lea_variable(maquina):
    instrucciones = ["nueva variable C", "lea variable", "retorne 0"]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    nuevo = maquina.correr(programa_cargado, pasos=3)
    assert nuevo.buscar_variable("000", "variable")["valor"] == "entrada de usuario"
