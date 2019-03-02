import pytest

from chmaquina.verificacion import verificar, ErrorDeSintaxis


@pytest.fixture
def factorial():
    return """
nueva               unidad           I         1
nueva m I 5
nueva respuesta I 1
nueva intermedia I 0
cargue m
almacene respuesta
reste unidad
almacene intermedia
cargue respuesta
multiplique intermedia
almacene respuesta
cargue intermedia
reste unidad
vayasi itere fin
etiqueta itere 8
etiqueta fin 19
muestre respuesta
imprima respuesta
retorne 0
    """.strip()


OPERACIONES_CON_VARIABLES = [
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
    "elimine",
    "extraiga",
]

OPERACIONES_LOGICAS = ["Y", "O"]

OPERACIONES_DE_CONTROL = ["vaya", "vayasi"]

OPERACIONES_DE_IO = ["muestre", "imprima"]

TODAS_LAS_OPERACIONES = (
    OPERACIONES_CON_VARIABLES
    + OPERACIONES_LOGICAS
    + OPERACIONES_DE_CONTROL
    + OPERACIONES_DE_IO
)


def test_verificacion_programa_complejo(factorial):
    verificar(factorial)


@pytest.mark.parametrize("instruccion", TODAS_LAS_OPERACIONES)
def test_verificar_nueva_variable_sin_argumentos(instruccion):
    programa = f"{instruccion}"
    with pytest.raises(ErrorDeSintaxis):
        verificar(programa)


@pytest.mark.parametrize("operacion", OPERACIONES_CON_VARIABLES + OPERACIONES_DE_IO)
def test_operaciones_con_variables_indefinidas(operacion):
    with pytest.raises(ErrorDeSintaxis):
        verificar(f"{operacion} variable_indefinida")


@pytest.mark.parametrize("operacion", OPERACIONES_CON_VARIABLES + OPERACIONES_DE_IO)
def test_operaciones_con_variables_definidas(operacion):
    programa = f"nueva mi_variable C mi variable bien definida\n{operacion} mi_variable"
    verificar(programa)


def test_verificar_nueva_variable_tipo_incorrecto():
    programa = """nueva etiqueta D"""
    with pytest.raises(ErrorDeSintaxis):
        verificar(programa)


@pytest.mark.parametrize(
    "tipo,valor",
    [("I", "hola"), ("I", "1.4"), ("R", "hola"), ("R", "1,5"), ("L", "FALSO")],
)
def test_nueva_valor_tipo_incorrecto(tipo, valor):
    programa = f"nueva etiqueta {tipo} {valor}"
    with pytest.raises(ErrorDeSintaxis):
        verificar(programa)


@pytest.mark.parametrize(
    "tipo,valor", [("I", "1"), ("I", "14"), ("R", "3.14"), ("L", "1")]
)
def test_nueva_valor_tipo_correcto(tipo, valor):
    programa = f"nueva etiqueta {tipo} {valor}"
    verificar(programa)


def test_etiqueta_argumentos_equivocados():
    programa = "etiqueta nueva hola"
    with pytest.raises(ErrorDeSintaxis):
        verificar(programa)


def test_etiqueta_argumentos_correctos():
    programa = "etiqueta nueva 1"
    verificar(programa)


@pytest.mark.parametrize("operacion", OPERACIONES_LOGICAS)
def test_operaciones_logicas_con_variables_indefinidas(operacion):
    programa = f"{operacion} a b c"
    with pytest.raises(ErrorDeSintaxis):
        verificar(programa)


@pytest.mark.parametrize("operacion", OPERACIONES_LOGICAS)
def test_operaciones_logicas_con_variables_definidas(operacion):
    definiciones = "\n".join(f"nueva {var} L 1" for var in ("a", "b", "c"))
    programa = f"{definiciones}\n{operacion} a b c"
    verificar(programa)


def test_no_con_variables_indefinidas():
    programa = "NO a b"
    with pytest.raises(ErrorDeSintaxis):
        verificar(programa)


def test_no_con_variables_definidas():
    definiciones = "\n".join(f"nueva {var} L 1" for var in ("a", "b"))
    programa = f"{definiciones}\nNO a b"
    verificar(programa)


@pytest.mark.parametrize("operacion", OPERACIONES_DE_IO)
def test_operaciones_de_io_con_argumento_acumulador(operacion):
    programa = f"{operacion} acumulador"
    verificar(programa)


def test_retorne_con_parametros_invalidos():
    with pytest.raises(ErrorDeSintaxis):
        verificar("retorne hola")


def test_retorne_con_parametros_validos():
    verificar("retorne")
    verificar("retorne 1")


def test_operacion_desconocida():
    with pytest.raises(ErrorDeSintaxis):
        verificar("operacion desconocida")


def test_vaya_etiquetas_indefinidas():
    programa = "vaya fin"
    with pytest.raises(ErrorDeSintaxis):
        verificar(programa)
