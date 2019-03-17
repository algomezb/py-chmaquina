import pytest

from chmaquina.maquina import (
    Maquina,
    ChProgramaInvalido,
    ErrorDeEjecucion,
    SinMemoriaSuficiente,
)


class TecladoFalso:
    def lea(self):
        return "entrada de usuario"


def verificar_estados_iguales(estado, otro, menos=None):
    if menos is None:
        menos = {}
    campos = ["memoria", "variables", "etiquetas", "programas", "pivote"]
    for campo in campos:
        assert menos.get(campo, getattr(estado, campo)) == getattr(otro, campo)


@pytest.fixture
def maquina():

    return Maquina(tamano_memoria=1024, tamano_kernel=128, teclado=TecladoFalso())


@pytest.fixture()
def factorial():
    instrucciones = [
        "nueva               unidad           I         1",
        "nueva m I 5  ",
        "nueva respuesta I 1",
        "nueva intermedia I 0",
        "cargue m",
        "almacene respuesta",
        "reste unidad",
        "almacene intermedia",
        "cargue respuesta",
        "multiplique intermedia",
        "almacene respuesta",
        "cargue intermedia",
        "reste unidad",
        "vayasi itere fin",
        "etiqueta itere 8",
        "etiqueta fin 19",
        "muestre respuesta",
        "imprima respuesta",
        "retorne 0",
    ]
    return "\n".join(instrucciones)


def test_encender(maquina):
    estado = maquina.encender()
    assert len(estado.memoria) == maquina.tamano_memoria
    assert estado.pivote == maquina.tamano_kernel + 1


def test_paso_sin_programa(maquina):
    estado = maquina.encender()
    siguiente = maquina.paso(estado)
    assert estado == siguiente


def test_cargar_programa(maquina):
    instrucciones = ["nueva variable C hola que hace", "etiqueta fin 3", "retorne 0"]
    programa = "\n".join(instrucciones)
    estado = maquina.encender()
    siguiente = maquina.cargar(estado, programa)
    assert siguiente.programas["000"]["contador"] == 0
    # Una variable mas 1 acumulador
    assert siguiente.pivote == estado.pivote + len(instrucciones) + 2
    assert siguiente.variables == {
        "000": {"variable": estado.pivote + 3, "acumulador": estado.pivote + 3 + 1}
    }
    assert siguiente.etiquetas == {"000": {"fin": 2}}
    assert siguiente.programas == {
        "000": {
            "inicio": estado.pivote,
            "contador": 0,
            "datos": estado.pivote + 3,
            "final": estado.pivote + 3 + 2,
            "tiempo_llegada": 0,
            "tiempo_rafaga": 1,
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
            "contador": 0,
            "datos": estado.pivote + 3,
            "final": estado.pivote + 5,
            "tiempo_llegada": 0,
            "tiempo_rafaga": 1,
        },
        "001": {
            "inicio": estado.pivote + 5,
            "contador": 0,
            "datos": estado.pivote + 5 + 3,
            "final": estado.pivote + 5 + 3 + 2,
            "tiempo_llegada": 1,
            "tiempo_rafaga": 1,
        },
    }


def test_cargar_programa_invalido(maquina):
    instrucciones = ["no exactamente un programa", "etiqueta fin 3", "retorne 0"]
    programa = "\n".join(instrucciones)
    estado = maquina.encender()
    with pytest.raises(ChProgramaInvalido):
        maquina.cargar(estado, programa)


@pytest.mark.parametrize(
    "linea", ["nueva variable I 1", "etiqueta fin 2", "// comentario"]
)
def test_lineas_sin_efecto(linea, maquina):
    instrucciones = [linea, "retorne 0"]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    linea_ejecutada = maquina.paso(programa_cargado)
    verificar_estados_iguales(
        programa_cargado,
        linea_ejecutada,
        menos={
            "programas": {"000": {**programa_cargado.programas["000"], "contador": 1}}
        },
    )


def test_cargar_variable(maquina):
    instrucciones = ["nueva variable C hola", "cargue variable", "retorne 0"]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    variable_cargada = maquina.correr(programa_cargado, pasos=2)
    variable_cargada.acumulador("000") == "hola"


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
    nuevo = maquina.correr(programa_cargado, pasos=2)
    assert nuevo.buscar_variable("000", "variable")["valor"] == "entrada de usuario"


@pytest.mark.parametrize(
    "operacion,a,b,resultado",
    [
        ("sume", "1", "3", "4"),
        ("reste", "1", "3", "-2"),
        ("multiplique", "3", "3", "9"),
        ("divida", "3", "2", "1.5"),
        ("potencia", "3", "2", "9"),
        ("modulo", "3", "2", "1"),
    ],
)
def test_operaciones_aritmeticas(maquina, operacion, a, b, resultado):
    instrucciones = [
        f"nueva a R {a}",
        f"nueva b R {b}",
        "cargue a",
        f"{operacion} b",
        "retorne 0",
    ]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    nuevo = maquina.correr(programa_cargado, pasos=4)
    # TODO: No se debe hacer esta comparación entre flotantes
    assert float(nuevo.acumulador("000")) == float(resultado)


@pytest.mark.parametrize(
    "operacion,a,b,resultado",
    [
        ("divida", "3", "0", "1.5"),
        ("potencia", "0", "-2", "9"),
        ("modulo", "3", "0", "1"),
    ],
)
def test_operaciones_aritmeticas_invalidas(maquina, operacion, a, b, resultado):
    instrucciones = [
        f"nueva a R {a}",
        f"nueva b R {b}",
        "cargue a",
        f"{operacion} b",
        "retorne 0",
    ]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    with pytest.raises(ErrorDeEjecucion):
        maquina.correr(programa_cargado, pasos=4)


@pytest.mark.parametrize(
    "operacion,a,b,resultado",
    [
        ("concatene", "ho", "la", "hola"),
        ("elimine", "holala", "la", "ho"),
        ("extraiga", "hola", "3", "hol"),
    ],
)
def test_operaciones_con_cadenas(maquina, operacion, a, b, resultado):
    instrucciones = [f"nueva a C {a}", "cargue a", f"{operacion} {b}", "retorne 0"]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    nuevo = maquina.correr(programa_cargado, pasos=3)
    # TODO: No se debe hacer esta comparación entre flotantes
    assert nuevo.acumulador("000") == resultado


@pytest.mark.parametrize(
    "operacion,a,b,resultado",
    [
        ("O", "1", "0", "1"),
        ("O", "0", "0", "0"),
        ("Y", "1", "0", "0"),
        ("Y", "1", "1", "1"),
    ],
)
def test_operaciones_logicas(maquina, operacion, a, b, resultado):
    instrucciones = [
        f"nueva a L {a}",
        f"nueva b L {b}",
        f"nueva resultado L",
        f"{operacion} a b resultado",
        "retorne 0",
    ]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    nuevo = maquina.correr(programa_cargado, pasos=4)
    # TODO: No se debe hacer esta comparación entre flotantes
    assert nuevo.buscar_variable("000", "resultado")["valor"] == resultado


@pytest.mark.parametrize("operando,resultado", [("0", "1"), ("1", "0")])
def test_operacion_no(maquina, operando, resultado):
    instrucciones = [
        f"nueva operando L {operando}",
        f"nueva resultado L",
        "NO operando resultado",
        "retorne 0",
    ]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    nuevo = maquina.correr(programa_cargado, pasos=3)
    assert nuevo.buscar_variable("000", "resultado")["valor"] == resultado


def test_imprima_valor(maquina):
    instrucciones = [f"nueva variable C hola mundo", f"imprima variable", "retorne 0"]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    nuevo = maquina.correr(programa_cargado, pasos=2)
    assert ("000", "hola mundo") in nuevo.impresora


def test_muestre_valor_en_pantalla(maquina):
    instrucciones = [f"nueva variable C hola mundo", f"muestre variable", "retorne 0"]
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, "\n".join(instrucciones))
    nuevo = maquina.correr(programa_cargado, pasos=2)
    assert ("000", "hola mundo") in nuevo.pantalla


def test_factorial(maquina, factorial):
    estado = maquina.encender()
    programa_cargado = maquina.cargar(estado, factorial)
    nuevo = maquina.correr(programa_cargado)
    assert ("000", "120.0") in nuevo.impresora
    assert ("000", "120.0") in nuevo.pantalla


def test_factoria_2_veces(maquina, factorial):
    estado = maquina.encender()
    estado = maquina.cargar(estado, factorial)
    estado = maquina.cargar(estado, factorial)
    nuevo = maquina.correr(estado)
    assert [("000", "120.0"), ("001", "120.0")] == nuevo.impresora
    assert [("000", "120.0"), ("001", "120.0")] == nuevo.impresora


def test_factoria_despues_de_correr(maquina, factorial):
    estado = maquina.encender()
    estado = maquina.cargar(estado, factorial)
    estado = maquina.cargar(estado, factorial)
    estado = maquina.correr(estado)
    estado = maquina.cargar(estado, factorial)
    nuevo = maquina.correr(estado)
    assert [("000", "120.0"), ("001", "120.0"), ("002", "120.0")] == nuevo.impresora
    assert [("000", "120.0"), ("001", "120.0"), ("002", "120.0")] == nuevo.impresora


def test_cargar_programa_sin_memoria_suficiente(factorial):
    maquina = Maquina(10, 9, teclado=TecladoFalso())
    estado = maquina.encender()
    with pytest.raises(SinMemoriaSuficiente):
        maquina.cargar(estado, factorial)


def test_incremento_de_tiempo_al_correr(maquina, monkeypatch):
    programa = ["nueva variable I 3", "multiplique variable"]
    estado = maquina.encender()
    estado = maquina.cargar(estado, "\n".join(programa))
    estado = maquina.correr(estado, pasos=2)
    assert estado.reloj == 1


def test_incremento_operacion_io(maquina, monkeypatch):
    monkeypatch.setattr("random.randint", lambda x, y: 3)
    programa = ["nueva variable I 3", "lea variable"]
    estado = maquina.encender()
    estado = maquina.cargar(estado, "\n".join(programa))
    estado = maquina.correr(estado, pasos=2)
    assert estado.reloj == 3


def test_incremento_cero_operaciones_declarativas(maquina):
    programa = ["nueva variable I 3", "etiqueta inicio 1"]
    estado = maquina.encender()
    estado = maquina.cargar(estado, "\n".join(programa))
    estado = maquina.correr(estado, pasos=2)
    assert estado.reloj == 0
    assert estado.programas["000"]["contador"] == 2


def test_incremento_en_saltos(maquina):
    programa = ["etiqueta fin 3", "vaya fin"]
    estado = maquina.encender()
    estado = maquina.cargar(estado, "\n".join(programa))
    estado = maquina.correr(estado, pasos=2)
    assert estado.reloj == 1
    assert estado.programas["000"]["contador"] == 2


def test_cargar_programa_con_tiempo_de_llegada(maquina):
    programa = "\n".join(["nueva variable C"] * 4)
    estado = maquina.encender()
    estado = maquina.cargar(estado, programa)
    estado = maquina.cargar(estado, programa)
    estado = maquina.cargar(estado, programa)
    assert estado.programas["000"]["tiempo_llegada"] == 0
    assert estado.programas["001"]["tiempo_llegada"] == 1
    assert estado.programas["002"]["tiempo_llegada"] == 2


def test_cargar_programa_con_tiempo_de_llegada_no_multiplo_de_4(maquina):
    programa = "\n".join(["nueva variable C"] * 5)
    estado = maquina.encender()
    estado = maquina.cargar(estado, programa)
    estado = maquina.cargar(estado, programa)
    assert estado.programas["000"]["tiempo_llegada"] == 0
    assert estado.programas["001"]["tiempo_llegada"] == 2


def test_cargar_programa_despues_de_corrida(maquina):
    programa = "\n".join(
        ["nueva var I", "sume var", "sume var", "sume var", "retorne 0"]
    )
    estado = maquina.encender()
    estado = maquina.cargar(estado, programa)
    assert estado.programas["000"]["tiempo_llegada"] == 0
    estado = maquina.correr(estado)
    assert estado.reloj == 3
    estado = maquina.cargar(estado, programa)
    assert estado.programas["001"]["tiempo_llegada"] == 3
    estado = maquina.cargar(estado, programa)
    assert estado.programas["002"]["tiempo_llegada"] == 5


def test_correr_programa_por_tiempo_menor_al_tiempo_de_ejecución(maquina):
    maquina.quantum = 1
    programa = "\n".join(
        ["nueva var I", "sume var", "sume var", "sume var", "retorne 0"]
    )
    estado = maquina.encender()
    estado = maquina.cargar(estado, programa)
    estado = maquina.cargar(estado, programa)
    nuevo_estado = maquina.correr(estado)
    assert len(nuevo_estado.programas) == 2
    assert nuevo_estado.siguiente_instruccion()[0] == "000"
    assert nuevo_estado.programas["000"]["contador"] == 1


def test_tiempo_de_rafaga_del_programa(maquina):
    programa = "\n".join(
        ["nueva var I", "sume var", "sume var", "sume var", "retorne 0"]
    )
    estado = maquina.encender()
    estado = maquina.cargar(estado, programa)
    assert estado.programas['000']['tiempo_rafaga'] == 4

